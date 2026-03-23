import subprocess
import re


def get_error_line(source_file):
    command = ["clang", "-fsyntax-only", source_file]
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)

    error_output = result.stderr

    line_match = re.search(r":(\d+):(\d+): (error|warning):", error_output)

    if line_match:
        error_line = int(line_match.group(1))
        error_column = int(line_match.group(2))
        return error_line, error_column, error_output

    return None, None, error_output