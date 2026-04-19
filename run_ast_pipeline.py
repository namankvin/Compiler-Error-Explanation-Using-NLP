import sys

from context_extractor import extract_context, extract_token, extract_expected_actual
from compiler_ast.generate_ast import generate_ast
from compiler_ast.parse_ast import parse_ast
from compiler_ast.ast_utils import get_error_line, parse_diagnostics
from compiler_ast.ast_logger import log_unified
from error_classifier import classify_error


def main():

    if len(sys.argv) < 2:
        print("Usage: python run_ast_pipeline.py <source_file> [compiler]")
        return

    source_file = sys.argv[1]
    compiler = sys.argv[2] if len(sys.argv) > 2 else "clang"

    # Detect compiler error
    _, _, error_output = get_error_line(source_file, compiler=compiler)
    diagnostics = parse_diagnostics(error_output)

    if not diagnostics:
        print("No compiler error detected.")
        return

    print(f"Detected {len(diagnostics)} diagnostic(s) using {compiler}.")

    # Generate AST once, then map each diagnostic.
    generate_ast(source_file, compiler="clang")

    with open(source_file, "r") as f:
        source_lines = f.readlines()

    for diag in diagnostics:
        error_line = diag["line"]
        error_column = diag["column"]
        error_output_single = diag["raw"]

        print(f"Processing {diag['level']} at line {error_line}")

        # Classify error
        classification = classify_error(error_output_single)

        cleaned_message = classification["cleaned_message"]
        category = classification["category"]
        phase = classification["phase"]
        violated_rule = classification["violated_rule"]

        expected_actual = extract_expected_actual(cleaned_message)
        if expected_actual["expected"] != "Unknown" or expected_actual["actual"] != "Unknown":
            violated_rule = (
                f"{violated_rule} Expected: {expected_actual['expected']}. "
                f"Actual: {expected_actual['actual']}."
            )

        print(f"Classified as: {category} | Phase: {phase}")

        # Extract text context
        context = extract_context(source_file, error_line)

        # Extract token
        if error_line <= len(source_lines):
            actual_line = source_lines[error_line - 1]
        else:
            actual_line = ""

        token = extract_token(actual_line, error_column)

        # Parse AST
        node, parent = parse_ast(error_line)

        # Log unified entry
        log_unified(
            source_file,
            error_line,
            error_output_single,
            cleaned_message,
            context,
            token,
            node,
            parent,
            category,
            phase,
            violated_rule,
        )


if __name__ == "__main__":
    main()