import argparse
import os
import re
import subprocess
import tempfile

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from compiler_ast.ast_utils import parse_diagnostics
from context_extractor import extract_context, extract_expected_actual
from error_classifier import classify_error
from security_explainer import (
    analyze_security_implications,
    compare_explanations,
    get_security_recommendation,
)

device = "mps" if torch.backends.mps.is_available() else "cpu"

try:
    model = AutoModelForSeq2SeqLM.from_pretrained("./final_model").to(device)
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained("./final_model")
    MODEL_AVAILABLE = True
except Exception:
    MODEL_AVAILABLE = False


ERROR_EXPLANATIONS = {
    "expected ';'": "This error indicates a semicolon is missing at the end of a statement. In C, every statement must end with a semicolon so the compiler can properly understand where the statement finishes.",
    "undeclared identifier": "This error means a variable is being used before it has been declared. In C, variables must be declared with a data type before they can be used.",
    "use of undeclared identifier": "This error means a variable is being used before it has been declared. In C, variables must be declared with a data type before they can be used.",
    "incompatible pointer to integer": "This error indicates a type mismatch - a pointer value is being assigned or compared to an integer. In C, pointers and integers are different types and cannot be used interchangeably.",
    "type mismatch": "This error indicates incompatible data types are being used together. In C, assignments and operations must use compatible types.",
    "expected ')'": "This error indicates a missing closing parenthesis. Function calls and control structures require matching pairs of parentheses.",
    "expected '('": "This error indicates a missing opening parenthesis. Function calls and control structures require matching pairs of parentheses.",
    "unknown type name": "This error means an unrecognized type name is being used. This could be a typo or a missing include statement for a custom type.",
    "implicit declaration of function": "This error indicates a function is being called before the compiler has seen its declaration. In C, functions should be declared or defined before they are used.",
    "variable-sized object may not be initialized": "This error occurs when trying to initialize a variable-length array, which is not allowed in C.",
    "expected expression": "This error indicates the compiler encountered unexpected syntax where it expected a valid expression.",
    "duplicate case value": "This error occurs in a switch statement when two case labels have the same value.",
    "break statement not within loop or switch": "This error means a break statement appears outside of a loop or switch statement where it's not valid.",
    "continue statement not within loop": "This error means a continue statement appears outside of a loop where it's not valid.",
    "member reference base": "This error indicates an issue with accessing a member of a struct or union, possibly using the wrong operator (. vs ->).",
    "array index out of bounds": "This warning indicates accessing an array element with an index that may be outside the valid range.",
    "unused variable": "This warning indicates a variable is declared but never used in the code.",
    "variable set but not used": "This warning indicates a variable is assigned a value but that value is never read.",
    "comparison of unsigned expression": "This warning indicates a potentially problematic comparison involving unsigned integers.",
    "result of comparison is always": "This warning indicates a comparison that will always evaluate to true or false.",
    "division by zero": "This error indicates an attempt to divide by zero, which is undefined behavior.",
    "invalid operands to binary": "This error indicates that the operands used with a binary operator are not compatible with that operator.",
    "too few arguments to function call": "This error means a function call is missing required arguments.",
    "too many arguments to function call": "This error means a function call has more arguments than the function expects.",
}


CATEGORY_FIX_STEPS = {
    "Missing token": "Insert the missing token at the reported location and recompile to reveal any follow-up errors.",
    "Undefined symbol": "Declare the variable before first use and ensure the name matches exactly in all references.",
    "Scope error": "Move the declaration to a broader scope or pass the value as a function argument.",
    "Type mismatch": "Align both operand types using the correct variable type or an explicit safe conversion.",
    "Implicit declaration": "Include the required header and verify the function signature before calling it.",
    "Pointer-int mismatch": "Use a pointer variable for addresses and integer variables for numeric values; avoid unsafe casts.",
    "Array bounds": "Ensure index checks use valid limits and never access beyond array length.",
    "Printf format mismatch": "Match each format specifier with the exact argument type (for example %d for int, %s for char*).",
    "Scanf format mismatch": "Match the scanf format with the destination type and pass addresses where required.",
    "Function argument mismatch": "Update the call site to pass the exact number and type of parameters required by the function.",
    "Unknown": "Start by fixing the first reported diagnostic, then recompile and continue iteratively.",
}


def get_explanation_for_error(error_text):
    """Get explanation based on error type using pattern matching."""
    error_lower = error_text.lower()

    for pattern, explanation in ERROR_EXPLANATIONS.items():
        if pattern.lower() in error_lower:
            return explanation

    return f"The compiler detected a syntax or semantic error: {error_text}. This violates C language rules and must be fixed for successful compilation."


def compile_code(file_path, compiler="clang", flags=None, syntax_only=True):
    """Compile C code and capture compiler diagnostics."""
    cmd = [compiler]
    if syntax_only:
        cmd.append("-fsyntax-only")
    if flags:
        cmd.extend(flags)
    cmd.append(file_path)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"Compiler '{compiler}' not found on this system.") from exc

    return result.stderr


def extract_diagnostics_with_context(error_message, file_path):
    """Parse all diagnostics and enrich with code context/classification."""
    diagnostics = parse_diagnostics(error_message)
    if not diagnostics:
        return []

    enriched = []
    for diagnostic in diagnostics:
        line_number = diagnostic["line"]
        context_lines = extract_context(file_path, line_number)
        code_context = "\n".join(context_lines)

        classification = classify_error(diagnostic["raw"])
        expected_actual = extract_expected_actual(diagnostic["message"])

        enriched.append(
            {
                **diagnostic,
                "code_context": code_context,
                "code_context_lines": context_lines,
                "classification": classification,
                "expected_actual": expected_actual,
            }
        )

    return enriched


def extract_error_and_code(error_message, file_path):
    """Backward-compatible helper that returns first diagnostic and context."""
    diagnostics = extract_diagnostics_with_context(error_message, file_path)
    if not diagnostics:
        return None, "<unknown>"

    return diagnostics[0]["message"], diagnostics[0]["code_context"]


def format_diagnostic_input(error_text, code_context):
    return f"""Explain the following compiler error:

Error:
{error_text}

Code:
{code_context}
"""


def format_error(error_message, file_path):
    """Convert first compiler diagnostic to model input (legacy behavior)."""
    error_text, code_context = extract_error_and_code(error_message, file_path)

    if not error_text:
        return None

    return format_diagnostic_input(error_text, code_context)


def _generate_model_explanation(input_text):
    if not MODEL_AVAILABLE:
        return None

    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            num_beams=5,
            repetition_penalty=1.2,
            no_repeat_ngram_size=3,
            early_stopping=True,
            do_sample=False,
        )

    return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()


def _is_low_quality_explanation(explanation, input_text):
    if not explanation:
        return True

    normalized = " ".join(explanation.split())
    if len(normalized) < 35:
        return True

    # Model copied prompt.
    if input_text.strip()[:50] in normalized:
        return True

    # Obvious repetitive degeneration.
    words = normalized.lower().split()
    if len(words) > 20:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.35:
            return True

    # Repeated sentence degeneration.
    sentences = [
        sentence.strip().lower()
        for sentence in re.split(r"[.!?]+", normalized)
        if sentence.strip()
    ]
    if len(sentences) >= 3 and len(set(sentences)) <= max(1, len(sentences) // 2):
        return True

    # Strongly generic explanations are less useful in competitive settings.
    generic_phrases = [
        "compiler detected a syntax or semantic error",
        "must be fixed for successful compilation",
    ]
    if sum(1 for phrase in generic_phrases if phrase in normalized.lower()) >= 2:
        return True

    return False


def _generate_explanation_with_source(input_text, error_text, prefer_model=True):
    """Return explanation text and source type for downstream quality fusion."""
    generic_fallback = (
        f"The compiler detected a syntax or semantic error: {error_text}. "
        "This violates C language rules and must be fixed for successful compilation."
    )
    rule_explanation = get_explanation_for_error(error_text)
    has_specific_rule = rule_explanation != generic_fallback

    if prefer_model and MODEL_AVAILABLE:
        model_explanation = _generate_model_explanation(input_text)
        if model_explanation and not _is_low_quality_explanation(model_explanation, input_text):
            return model_explanation, "model"

    if has_specific_rule:
        return rule_explanation, "rule"

    if not prefer_model and MODEL_AVAILABLE:
        model_explanation = _generate_model_explanation(input_text)
        if model_explanation and not _is_low_quality_explanation(model_explanation, input_text):
            return model_explanation, "model"

    return generic_fallback, "fallback"


def _get_focus_line(diagnostic):
    line_number = diagnostic.get("line", 0)
    target_prefix = f"{line_number}:"
    for line in diagnostic.get("code_context_lines", []):
        if line.startswith(target_prefix):
            return line.split(":", 1)[1].strip()
    return ""


def _build_hybrid_explanation(diagnostic, base_explanation, security_analysis=None):
    """Fuse base explanation with actionable, category-aware guidance."""
    classification = diagnostic.get("classification", {})
    category = classification.get("category", "Unknown")
    phase = classification.get("phase", "Unknown")

    fix_step = CATEGORY_FIX_STEPS.get(category, CATEGORY_FIX_STEPS["Unknown"])

    sections = [
        base_explanation.strip(),
        f"Likely cause: {category} ({phase}).",
    ]

    sections.append(f"Suggested fix: {fix_step}")

    return "\n".join(sections)


def _estimate_confidence(diagnostic, explanation_source):
    score = 0.5
    classification = diagnostic.get("classification", {})

    if classification.get("category", "Unknown") != "Unknown":
        score += 0.15

    expected_actual = diagnostic.get("expected_actual", {})
    if expected_actual.get("expected") != "Unknown" or expected_actual.get("actual") != "Unknown":
        score += 0.1

    if explanation_source == "model":
        score += 0.1
    elif explanation_source == "rule":
        score += 0.2

    return round(min(score, 0.95), 2)


def generate_explanation(input_text, error_text, prefer_model=True):
    """Generate explanation using model-first strategy with robust fallback."""
    explanation, _ = _generate_explanation_with_source(
        input_text,
        error_text,
        prefer_model=prefer_model,
    )
    return explanation


def explain_compiler_output(
    error_message,
    file_path,
    show_security=False,
    show_comparison=False,
    prefer_model=True,
):
    diagnostics = extract_diagnostics_with_context(error_message, file_path)
    if not diagnostics:
        return []

    explained = []
    for diagnostic in diagnostics:
        error_text = diagnostic["message"]
        code_context = diagnostic["code_context"]
        input_text = format_diagnostic_input(error_text, code_context)

        base_explanation, explanation_source = _generate_explanation_with_source(
            input_text,
            error_text,
            prefer_model=prefer_model,
        )
        security_analysis = None
        if show_security:
            security_analysis = analyze_security_implications(error_text, code_context)

        explanation = _build_hybrid_explanation(
            diagnostic,
            base_explanation,
            security_analysis=security_analysis,
        )

        payload = {
            "diagnostic": diagnostic,
            "input_text": input_text,
            "explanation": explanation,
            "strategy": f"hybrid:{explanation_source}",
            "confidence": _estimate_confidence(diagnostic, explanation_source),
            "security_analysis": security_analysis,
            "security_recommendations": [],
            "comparison": None,
        }

        if security_analysis:
            payload["security_recommendations"] = get_security_recommendation(
                security_analysis.get("category", "")
            )

        if show_comparison:
            payload["comparison"] = compare_explanations(explanation, security_analysis)

        explained.append(payload)

    return explained


def explain_source_code(
    source_code,
    compiler="clang",
    compiler_flags=None,
    show_security=True,
    prefer_model=True,
):
    """Compile source text and return structured diagnostics + explanations."""
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as temp_file:
            temp_file.write(source_code)
            temp_path = temp_file.name

        stderr_output = compile_code(temp_path, compiler=compiler, flags=compiler_flags)
        diagnostics = parse_diagnostics(stderr_output)

        # Guard against false success when compiler returns non-parseable fatal messages.
        has_error_text = bool(re.search(r"\b(fatal\s+error|error):", stderr_output, re.IGNORECASE))

        if not diagnostics and not has_error_text:
            return {
                "success": True,
                "compiler_output": stderr_output,
                "diagnostics": [],
            }

        if not diagnostics and has_error_text:
            fallback_message = "Compilation failed with an unparsed compiler diagnostic."
            for line in (stderr_output or "").splitlines():
                stripped = line.strip()
                if stripped:
                    fallback_message = stripped
                    break

            fallback_diagnostic = {
                "file": temp_path,
                "line": 0,
                "column": 0,
                "level": "error",
                "message": fallback_message,
                "raw": fallback_message,
                "code_context": "<context unavailable>",
                "code_context_lines": [],
                "classification": classify_error(fallback_message),
                "expected_actual": extract_expected_actual(fallback_message),
            }

            input_text = format_diagnostic_input(
                fallback_diagnostic["message"], fallback_diagnostic["code_context"]
            )
            base_explanation, explanation_source = _generate_explanation_with_source(
                input_text,
                fallback_diagnostic["message"],
                prefer_model=prefer_model,
            )

            security_analysis = None
            recommendations = []
            if show_security:
                security_analysis = analyze_security_implications(
                    fallback_diagnostic["message"], fallback_diagnostic["code_context"]
                )
                if security_analysis:
                    recommendations = get_security_recommendation(
                        security_analysis.get("category", "")
                    )

            explanation = _build_hybrid_explanation(
                fallback_diagnostic,
                base_explanation,
                security_analysis=security_analysis,
            )

            return {
                "success": False,
                "compiler_output": stderr_output,
                "diagnostics": [
                    {
                        "diagnostic": fallback_diagnostic,
                        "input_text": input_text,
                        "explanation": explanation,
                        "strategy": f"hybrid:{explanation_source}",
                        "confidence": _estimate_confidence(
                            fallback_diagnostic,
                            explanation_source,
                        ),
                        "security_analysis": security_analysis,
                        "security_recommendations": recommendations,
                        "comparison": None,
                    }
                ],
            }

        explained = explain_compiler_output(
            stderr_output,
            temp_path,
            show_security=show_security,
            show_comparison=False,
            prefer_model=prefer_model,
        )

        return {
            "success": False,
            "compiler_output": stderr_output,
            "diagnostics": explained,
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

def explain_file(
    file_path,
    show_security=False,
    show_comparison=False,
    compiler_flags=None,
    compiler="clang",
    prefer_model=True,
):
    print(f"\nCompiling {file_path} using {compiler}...\n")

    error_message = compile_code(file_path, compiler=compiler, flags=compiler_flags)
    diagnostics = parse_diagnostics(error_message)

    if not diagnostics:
        print("No compiler errors detected.")
        return

    print("Compiler Output:\n")
    print(error_message)

    explained = explain_compiler_output(
        error_message,
        file_path,
        show_security=show_security,
        show_comparison=show_comparison,
        prefer_model=prefer_model,
    )

    for index, item in enumerate(explained, start=1):
        diagnostic = item["diagnostic"]
        classification = diagnostic["classification"]
        expected_actual = diagnostic["expected_actual"]

        print("\n" + "=" * 60)
        print(f"Diagnostic #{index}: {diagnostic['level'].upper()}")
        print(f"Location: line {diagnostic['line']}, column {diagnostic['column']}")
        print(f"Message: {diagnostic['message']}")
        print(
            f"Category: {classification['category']} | Phase: {classification['phase']}"
        )
        print(
            f"Expected: {expected_actual['expected']} | Actual: {expected_actual['actual']}"
        )

        print("\nGenerated Explanation:")
        print("-" * 60)
        print(item["explanation"])
        print("-" * 60)

        if show_comparison and item["comparison"]:
            print(item["comparison"])
        elif show_security:
            security_analysis = item["security_analysis"]
            if security_analysis:
                print("\nSecurity Analysis:")
                print(f"Severity: {security_analysis.get('severity', 'Unknown')}")
                print(f"Category: {security_analysis.get('category', 'Unknown')}")
                print(f"CWE Reference: {security_analysis.get('cwe', 'N/A')}")
                print(f"Risk: {security_analysis.get('risk', 'N/A')}")
                print(f"Secure Fix: {security_analysis.get('explanation', 'N/A')}")
                print(
                    f"Warning Against Insecure Fixes: "
                    f"{security_analysis.get('insecure_fix_warning', 'N/A')}"
                )
                if item["security_recommendations"]:
                    print("Recommendations:")
                    for recommendation in item["security_recommendations"]:
                        print(f"  - {recommendation}")
            else:
                print("\nNo specific security concerns identified for this diagnostic.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Explain compiler diagnostics using NLP.")
    parser.add_argument("file", help="Path to C source file")
    parser.add_argument(
        "--security",
        "-s",
        action="store_true",
        help="Show security analysis for diagnostics",
    )
    parser.add_argument(
        "--compare",
        "-c",
        action="store_true",
        help="Show comparison between standard and security-aware explanations",
    )
    parser.add_argument(
        "--warnings",
        "-w",
        action="store_true",
        help="Enable common warning flags",
    )
    parser.add_argument(
        "--compiler",
        choices=["clang", "gcc"],
        default="clang",
        help="Compiler to use for diagnostics",
    )
    parser.add_argument(
        "--rule-first",
        action="store_true",
        help="Use rule explanations first, then model fallback",
    )
    args = parser.parse_args()

    warning_flags = ["-Wall", "-Wextra", "-Wpedantic"] if args.warnings else None

    explain_file(
        args.file,
        show_security=args.security,
        show_comparison=args.compare,
        compiler_flags=warning_flags,
        compiler=args.compiler,
        prefer_model=not args.rule_first,
    )