import os
import re

AST_FILE = os.path.join("compiler_ast", "ast_output.txt")

def extract_node_type(line):
    match = re.search(r'\b([A-Za-z]+Stmt|[A-Za-z]+Decl|[A-Za-z]+Expr)\b', line or "")
    return match.group(1) if match else "Unknown"


def _line_depth(line):
    # Depth proxy: where AST node type token begins in the dump line.
    match = re.search(r'([A-Za-z]+Stmt|[A-Za-z]+Decl|[A-Za-z]+Expr)', line or "")
    return match.start() if match else 10**9

def parse_ast(error_line):
    node_line = None
    parent_line = None

    with open(AST_FILE, "r") as f:
        lines = f.readlines()

    target_idx = None
    for i, line in enumerate(lines):
        if f"line:{error_line}:" in line and extract_node_type(line) != "Unknown":
            target_idx = i
            break

    if target_idx is not None:
        node_line = lines[target_idx].strip()
        node_depth = _line_depth(lines[target_idx])

        for j in range(target_idx - 1, -1, -1):
            candidate = lines[j]
            if extract_node_type(candidate) == "Unknown":
                continue
            if _line_depth(candidate) < node_depth:
                parent_line = candidate.strip()
                break

    node_type = extract_node_type(node_line) if node_line else "Unknown"
    parent_type = extract_node_type(parent_line) if parent_line else "Unknown"

    return node_type, parent_type
