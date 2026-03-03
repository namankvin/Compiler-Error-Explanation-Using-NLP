import re


def extract_context(source_file, line_number, window=2):
    with open(source_file, 'r') as f:
        lines = f.readlines()

    start = max(0, line_number - window - 1)
    end = min(len(lines), line_number + window)

    context = []
    for i in range(start, end):
        context.append(f"{i+1}: {lines[i].rstrip()}")

    return context


def extract_token(line, column):
    if not line.strip():
        return "N/A"

    if column > len(line):
        return "End of line"

    for match in re.finditer(r'\w+|[^\s\w]', line):
        start, end = match.span()
        if start <= column - 1 < end:
            return match.group()

    return "End of line"