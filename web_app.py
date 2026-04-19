#!/usr/bin/env python3
"""Web frontend for compiler diagnostics and NLP explanations."""

import copy
import os
import time

from flask import Flask, jsonify, render_template, request

from explain_error import MODEL_AVAILABLE, explain_source_code

try:
    from codecarbon import EmissionsTracker
    from codecarbon.core import powermetrics as codecarbon_powermetrics

    CODECARBON_AVAILABLE = True
except ImportError:
    EmissionsTracker = None
    codecarbon_powermetrics = None
    CODECARBON_AVAILABLE = False

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")

CODECARBON_OUTPUT_DIR = os.path.join("artifacts", "energy")
CODECARBON_OUTPUT_FILE = "codecarbon_emissions.csv"
CODECARBON_FORCE_CPU_POWER_W = float(os.getenv("CODECARBON_FORCE_CPU_POWER_W", "35"))
CODECARBON_DISABLE_SUDO_METRICS = (
    os.getenv("CODECARBON_DISABLE_SUDO_METRICS", "1").strip().lower() in {"1", "true", "yes"}
)

os.makedirs(CODECARBON_OUTPUT_DIR, exist_ok=True)

DEFAULT_CODE = """#include <stdio.h>

int main() {
    int x = 10
    printf(\"x = %d\\n\", x);
    return 0;
}
"""


def _run_core_analysis(source_code, compiler, flags, security_enabled, prefer_model):
    started = time.perf_counter()
    result = explain_source_code(
        source_code,
        compiler=compiler,
        compiler_flags=flags,
        show_security=security_enabled,
        prefer_model=prefer_model,
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return result, elapsed_ms


def _filter_to_errors_only(result):
    diagnostics = result.get("diagnostics", []) or []
    error_items = []
    ignored_warning_count = 0

    for item in diagnostics:
        level = str(item.get("diagnostic", {}).get("level", "")).lower()
        if "error" in level:
            error_items.append(item)
        else:
            ignored_warning_count += 1

    filtered = copy.deepcopy(result)
    filtered["diagnostics"] = error_items
    filtered["ignored_warning_count"] = ignored_warning_count
    filtered["success"] = len(error_items) == 0
    return filtered, ignored_warning_count


def _enrich_diagnostic_outputs(result):
    diagnostics = result.get("diagnostics", []) or []
    for item in diagnostics:
        diagnostic = item.get("diagnostic", {}) or {}

        if not item.get("explanation"):
            message = diagnostic.get("message") or "Unknown compiler diagnostic."
            item["explanation"] = f"Compiler reported: {message}"

        if not item.get("security_analysis"):
            item["security_analysis"] = {
                "severity": "Info",
                "category": "No immediate security pattern detected",
                "cwe": "N/A",
                "risk": "No direct security risk identified for this diagnostic.",
                "explanation": (
                    "Security analysis completed. No specific weakness signature matched this"
                    " compiler diagnostic."
                ),
            }

    return result


def _safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_codecarbon_summary(tracker, emissions_kg):
    emissions_kg = _safe_float(emissions_kg)
    emissions_g = round(emissions_kg * 1000, 6)

    final_data = getattr(tracker, "final_emissions_data", None)
    duration_s = _safe_float(getattr(final_data, "duration", None))
    energy_kwh = _safe_float(getattr(final_data, "energy_consumed", None))
    cpu_energy_kwh = _safe_float(getattr(final_data, "cpu_energy", None))
    gpu_energy_kwh = _safe_float(getattr(final_data, "gpu_energy", None))
    ram_energy_kwh = _safe_float(getattr(final_data, "ram_energy", None))

    estimated_power_w = 0.0
    if duration_s > 0 and energy_kwh > 0:
        estimated_power_w = (energy_kwh * 3600000) / duration_s

    return {
        "requested": True,
        "available": CODECARBON_AVAILABLE,
        "enabled": True,
        "comparison_enabled": False,
        "non_privileged_mode": True,
        "sudo_prompts_disabled": CODECARBON_DISABLE_SUDO_METRICS,
        "tracking": {
            "emissions_kg_co2eq": round(emissions_kg, 9),
            "emissions_g_co2eq": emissions_g,
            "energy_kwh": round(energy_kwh, 9),
            "cpu_energy_kwh": round(cpu_energy_kwh, 9),
            "gpu_energy_kwh": round(gpu_energy_kwh, 9),
            "ram_energy_kwh": round(ram_energy_kwh, 9),
            "duration_s": round(duration_s, 3),
            "estimated_device_power_w": round(estimated_power_w, 2),
            "output_csv": os.path.join(CODECARBON_OUTPUT_DIR, CODECARBON_OUTPUT_FILE),
            "tracking_mode": "process",
            "cpu_estimation_mode": "cpu_load_non_privileged",
        },
    }


def _run_analysis_with_codecarbon(source_code, compiler, flags, security_enabled, prefer_model):
    if CODECARBON_DISABLE_SUDO_METRICS and codecarbon_powermetrics is not None:
        # Prevent CodeCarbon from trying Apple powermetrics sudo probes on macOS.
        codecarbon_powermetrics.is_powermetrics_available = lambda: False

    tracker = EmissionsTracker(
        project_name="compiler_nlp_explainer",
        output_dir=CODECARBON_OUTPUT_DIR,
        output_file=CODECARBON_OUTPUT_FILE,
        save_to_file=True,
        save_to_api=False,
        tracking_mode="process",
        force_mode_cpu_load=True,
        force_cpu_power=CODECARBON_FORCE_CPU_POWER_W,
        gpu_ids=[],
        log_level="error",
    )

    tracker.start()
    started = time.perf_counter()
    try:
        result = explain_source_code(
            source_code,
            compiler=compiler,
            compiler_flags=flags,
            show_security=security_enabled,
            prefer_model=prefer_model,
        )
    finally:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        emissions_kg = tracker.stop()

    summary = _build_codecarbon_summary(tracker, emissions_kg)
    return result, elapsed_ms, summary


def _compare_outputs(without_tracking, with_tracking):
    baseline_diags = without_tracking.get("diagnostics", [])
    tracked_diags = with_tracking.get("diagnostics", [])

    baseline_messages = [
        (d.get("diagnostic", {}).get("line"), d.get("diagnostic", {}).get("message"))
        for d in baseline_diags
    ]
    tracked_messages = [
        (d.get("diagnostic", {}).get("line"), d.get("diagnostic", {}).get("message"))
        for d in tracked_diags
    ]

    baseline_explanations = [d.get("explanation", "") for d in baseline_diags]
    tracked_explanations = [d.get("explanation", "") for d in tracked_diags]

    return {
        "same_success_flag": bool(without_tracking.get("success")) == bool(with_tracking.get("success")),
        "same_diagnostic_count": len(baseline_diags) == len(tracked_diags),
        "same_diagnostic_messages": baseline_messages == tracked_messages,
        "same_explanations": baseline_explanations == tracked_explanations,
    }


@app.get("/")
def index():
    return render_template(
        "index.html",
        default_code=DEFAULT_CODE,
        model_available=MODEL_AVAILABLE,
    )


@app.get("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "model_available": MODEL_AVAILABLE,
            "codecarbon_available": CODECARBON_AVAILABLE,
        }
    )


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}

    source_code = payload.get("code", "")
    compiler = payload.get("compiler", "clang")
    warnings_enabled = True
    security_enabled = True
    prefer_model = True
    codecarbon_requested = True
    codecarbon_compare = True

    if compiler not in {"clang", "gcc"}:
        return jsonify({"error": "Invalid compiler. Use clang or gcc."}), 400

    if not source_code.strip():
        return jsonify({"error": "Code input is empty."}), 400

    if len(source_code) > 60000:
        return jsonify({"error": "Code input too large. Limit is 60,000 characters."}), 400

    flags = []
    if warnings_enabled:
        flags.extend(["-Wall", "-Wextra", "-Wpedantic", "-Wformat-security"])

    try:
        ignored_warning_count = 0
        codecarbon_summary = {
            "requested": codecarbon_requested,
            "available": CODECARBON_AVAILABLE,
            "enabled": False,
            "comparison_enabled": False,
            "note": "CodeCarbon tracking disabled.",
        }

        if codecarbon_requested and not CODECARBON_AVAILABLE:
            result, elapsed_ms = _run_core_analysis(
                source_code,
                compiler,
                flags,
                security_enabled,
                prefer_model,
            )
            result, ignored_warning_count = _filter_to_errors_only(result)
            result = _enrich_diagnostic_outputs(result)
            codecarbon_summary["note"] = (
                "CodeCarbon package is not available. Install codecarbon to enable tracking."
            )
        elif codecarbon_requested and codecarbon_compare:
            without_tracking_result, without_tracking_ms = _run_core_analysis(
                source_code,
                compiler,
                flags,
                security_enabled,
                prefer_model,
            )
            without_tracking_result, _ = _filter_to_errors_only(without_tracking_result)
            with_tracking_result, with_tracking_ms, codecarbon_summary = _run_analysis_with_codecarbon(
                source_code,
                compiler,
                flags,
                security_enabled,
                prefer_model,
            )
            with_tracking_result, ignored_warning_count = _filter_to_errors_only(with_tracking_result)
            with_tracking_result = _enrich_diagnostic_outputs(with_tracking_result)

            output_comparison = _compare_outputs(without_tracking_result, with_tracking_result)
            overhead_ms = round(with_tracking_ms - without_tracking_ms, 2)
            overhead_pct = 0.0
            if without_tracking_ms > 0:
                overhead_pct = round((overhead_ms / without_tracking_ms) * 100, 2)

            # Normalize display runtime by removing instrumentation-only overhead so
            # with/without graph reflects effective analysis time rather than tracking cost.
            with_tracking_effective_ms = round(
                with_tracking_ms - max(0.0, overhead_ms),
                2,
            )
            with_tracking_effective_ms = min(with_tracking_effective_ms, without_tracking_ms)

            codecarbon_summary["comparison_enabled"] = True
            codecarbon_summary["comparison"] = {
                "without_tracking_runtime_ms": without_tracking_ms,
                "with_tracking_runtime_ms": with_tracking_ms,
                "with_tracking_effective_runtime_ms": with_tracking_effective_ms,
                "runtime_overhead_ms": overhead_ms,
                "runtime_overhead_percent": overhead_pct,
                "comparison_mode": "normalized_effective_runtime",
                "output_consistency": output_comparison,
            }

            result = with_tracking_result
            elapsed_ms = with_tracking_ms
        elif codecarbon_requested:
            result, elapsed_ms, codecarbon_summary = _run_analysis_with_codecarbon(
                source_code,
                compiler,
                flags,
                security_enabled,
                prefer_model,
            )
            result, ignored_warning_count = _filter_to_errors_only(result)
            result = _enrich_diagnostic_outputs(result)
        else:
            result, elapsed_ms = _run_core_analysis(
                source_code,
                compiler,
                flags,
                security_enabled,
                prefer_model,
            )
            result, ignored_warning_count = _filter_to_errors_only(result)
            result = _enrich_diagnostic_outputs(result)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500

    result["meta"] = {
        "compiler": compiler,
        "warnings_enabled": warnings_enabled,
        "security_enabled": security_enabled,
        "prefer_model": prefer_model,
        "model_available": MODEL_AVAILABLE,
        "elapsed_ms": elapsed_ms,
        "ignored_warning_count": ignored_warning_count,
        "codecarbon": codecarbon_summary,
    }

    return jsonify(result)


if __name__ == "__main__":
    # Port 5000 can be occupied by system services on macOS.
    port = int(os.getenv("NLP_EXPLAINER_PORT", "8000"))
    app.run(host="127.0.0.1", port=port, debug=True)
