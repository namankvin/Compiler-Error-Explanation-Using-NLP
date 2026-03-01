import os
import re

AST_FILE = os.path.join("compiler_ast", "ast_output.txt")

def extract_node_type(line):
    match = re.search(r'\b([A-Za-z]+Stmt|[A-Za-z]+Decl|[A-Za-z]+Expr)\b', line)
    return match.group(1) if match else "Unknown"

def parse_ast(error_line):
    node_line = None
    parent_line = None

    with open(AST_FILE, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if f"line:{error_line}:" in line:
            node_line = line.strip()

            for j in range(i-1, -1, -1):
                if "|" in lines[j]:
                    parent_line = lines[j].strip()
                    break
            break

    node_type = extract_node_type(node_line) if node_line else "Unknown"
    parent_type = extract_node_type(parent_line) if parent_line else "Unknown"

    return node_type, parent_type
