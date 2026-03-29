#!/usr/bin/env python3
"""Web frontend for compiler diagnostics and NLP explanations."""

import os
import time

from flask import Flask, jsonify, render_template, request

from explain_error import MODEL_AVAILABLE, explain_source_code

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")

DEFAULT_CODE = """#include <stdio.h>

int main() {
    int x = 10
    printf(\"x = %d\\n\", x);
    return 0;
}
"""


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
        }
    )


@app.post("/api/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}

    source_code = payload.get("code", "")
    compiler = payload.get("compiler", "clang")
    warnings_enabled = bool(payload.get("warnings", True))
    security_enabled = bool(payload.get("security", True))
    prefer_model = bool(payload.get("prefer_model", True))

    if compiler not in {"clang", "gcc"}:
        return jsonify({"error": "Invalid compiler. Use clang or gcc."}), 400

    if not source_code.strip():
        return jsonify({"error": "Code input is empty."}), 400

    if len(source_code) > 60000:
        return jsonify({"error": "Code input too large. Limit is 60,000 characters."}), 400

    flags = []
    if warnings_enabled:
        flags.extend(["-Wall", "-Wextra", "-Wpedantic", "-Wformat-security"])

    started = time.perf_counter()
    try:
        result = explain_source_code(
            source_code,
            compiler=compiler,
            compiler_flags=flags,
            show_security=security_enabled,
            prefer_model=prefer_model,
        )
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    result["meta"] = {
        "compiler": compiler,
        "warnings_enabled": warnings_enabled,
        "security_enabled": security_enabled,
        "prefer_model": prefer_model,
        "model_available": MODEL_AVAILABLE,
        "elapsed_ms": elapsed_ms,
    }

    return jsonify(result)


if __name__ == "__main__":
    # Port 5000 can be occupied by system services on macOS.
    port = int(os.getenv("NLP_EXPLAINER_PORT", "8000"))
    app.run(host="127.0.0.1", port=port, debug=True)
