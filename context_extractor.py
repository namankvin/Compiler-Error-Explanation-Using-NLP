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


def extract_expected_actual(error_text):
    """Extract expected vs actual constructs from compiler diagnostics."""
    if not error_text:
        return {"expected": "Unknown", "actual": "Unknown"}

    expected_match = re.search(r"expected\s+'([^']+)'", error_text)
    if not expected_match:
        expected_match = re.search(r"expects?\s+([^,.;]+)", error_text, re.IGNORECASE)

    actual_match = re.search(r"but\s+(?:the\s+)?argument\s+has\s+type\s+'([^']+)'", error_text)
    if not actual_match:
        actual_match = re.search(r"(?:got|found)\s+'([^']+)'", error_text, re.IGNORECASE)

    expected = expected_match.group(1).strip() if expected_match else "Unknown"
    actual = actual_match.group(1).strip() if actual_match else "Unknown"

    return {
        "expected": expected,
        "actual": actual,
    }