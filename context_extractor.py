import re

def extract_line_number(error_message):
    match = re.search(r':(\d+):', error_message)
    if match:
        return int(match.group(1))
    return None

def extract_context(source_file, line_number, window=2):
    with open(source_file, 'r') as f:
        lines = f.readlines()

    start = max(0, line_number - window - 1)
    end = min(len(lines), line_number + window)

    context = []
    for i in range(start, end):
        context.append(f"{i+1}: {lines[i].rstrip()}")

    return context

#def extract_token(line):
#    tokens = re.findall(r'\w+|[^\s\w]', line)
#    return tokens[0] if tokens else "N/A"

def main():
    source_file = input("Enter source file name: ")
    error_message = input("Paste compiler error message: ")

    line_number = extract_line_number(error_message)

    if not line_number:
        print("Could not detect line number.")
        return

    context = extract_context(source_file, line_number)

    error_line = context[2] if len(context) > 2 else context[0]
    # token = extract_token(error_line)

    print("\n--- Extracted Context ---")
    print(f"Error at line: {line_number}\n")

    for line in context:
        print(line)

    # print(f"\nToken near error: {token}")

if __name__ == "__main__":
    main()
