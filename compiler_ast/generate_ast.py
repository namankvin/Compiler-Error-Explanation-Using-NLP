import subprocess
import os

AST_DIR = "compiler_ast"
AST_FILE = os.path.join(AST_DIR, "ast_output.txt")

def generate_ast(source_file):
    print("Generating AST...")

    os.makedirs(AST_DIR, exist_ok=True)

    command = [
        "clang",
        "-fno-color-diagnostics",
        "-Xclang",
        "-ast-dump",
        "-fsyntax-only",
        source_file
    ]

    with open(AST_FILE, "w") as f:
        subprocess.run(command, stdout=f, stderr=subprocess.DEVNULL)

    print("Clean AST saved.")