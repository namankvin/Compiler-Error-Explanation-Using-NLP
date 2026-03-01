import subprocess
import re

def get_error_line(source_file):
    command = ["clang", "-fsyntax-only", source_file]
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)

    error_output = result.stderr

    match = re.search(r":(\d+):\d+: error:", error_output)

    if match:
        return int(match.group(1)), error_output

    return None, error_output