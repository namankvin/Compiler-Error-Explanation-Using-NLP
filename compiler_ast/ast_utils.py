import subprocess
import re

DIAGNOSTIC_PATTERN = re.compile(
    r"^(?P<file>.*?):(?P<line>\d+):(?P<column>\d+):\s+(?P<level>error|warning):\s+(?P<message>.*)$"
)


def parse_diagnostics(error_output):
    diagnostics = []
    for line in (error_output or "").splitlines():
        match = DIAGNOSTIC_PATTERN.match(line.strip())
        if not match:
            continue

        diagnostics.append(
            {
                "file": match.group("file"),
                "line": int(match.group("line")),
                "column": int(match.group("column")),
                "level": match.group("level"),
                "message": match.group("message"),
                "raw": line.strip(),
            }
        )

    return diagnostics


def get_error_line(source_file, compiler="clang", extra_flags=None):
    command = [compiler, "-fsyntax-only"]
    if extra_flags:
        command.extend(extra_flags)
    command.append(source_file)
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)

    error_output = result.stderr

    diagnostics = parse_diagnostics(error_output)

    if diagnostics:
        error_line = diagnostics[0]["line"]
        error_column = diagnostics[0]["column"]
        return error_line, error_column, error_output

    return None, None, error_output