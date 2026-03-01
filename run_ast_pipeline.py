import sys
import re

from context_extractor import extract_context, extract_token
from compiler_ast.generate_ast import generate_ast
from compiler_ast.parse_ast import parse_ast
from compiler_ast.ast_utils import get_error_line
from compiler_ast.ast_logger import log_unified


def main():

    if len(sys.argv) < 2:
        print("Usage: python run_ast_pipeline.py <source_file>")
        return

    source_file = sys.argv[1]

    # Detect compiler error
    error_line, error_output = get_error_line(source_file)

    if not error_line:
        print("No compiler error detected.")
        return

    print(f"Error detected at line {error_line}")

    # Extract text context
    context = extract_context(source_file, error_line)

    # Read actual source line for token extraction
    with open(source_file, "r") as f:
        source_lines = f.readlines()

    if error_line <= len(source_lines):
        actual_line = source_lines[error_line - 1]
    else:
        actual_line = ""

    token = extract_token(actual_line)

    # Generate AST
    generate_ast(source_file)

    # Parse AST
    node, parent = parse_ast(error_line)

    # Log unified entry
    log_unified(
        source_file,
        error_line,
        error_output.strip(),
        context,
        token,
        node,
        parent
    )


if __name__ == "__main__":
    main()
