import os

LOG_FILE = "unified_logs.txt"


def get_next_entry_number():
    if not os.path.exists(LOG_FILE):
        return 1

    with open(LOG_FILE, "r") as f:
        return f.read().count("=== Error Context Entry") + 1


def log_unified(source_file,error_line,raw_error,cleaned_error,context,token,node,parent,category,phase,violated_rule):

    entry_no = get_next_entry_number()

    with open(LOG_FILE, "a") as log:

        log.write(f"\n=== Error Context Entry {entry_no} ===\n")
        log.write(f"Error ID: ERR_{entry_no:03d}\n")
        log.write(f"Source File: {source_file}\n")
        log.write(f"Error Line: {error_line}\n\n")

        log.write("Raw Compiler Error:\n")
        log.write(raw_error + "\n\n")

        log.write("Cleaned Error Message:\n")
        log.write(cleaned_error + "\n\n")

        log.write("--- TEXT CONTEXT ---\n")
        for line in context:
            log.write(line + "\n")

        log.write(f"\nToken Near Error: {token}\n\n")

        log.write("--- CLASSIFICATION ---\n")
        log.write(f"Error Category: {category}\n")
        log.write(f"Compiler Phase: {phase}\n")
        log.write(f"Violated Rule: {violated_rule}\n\n")

        if category == "Unknown":
            log.write("WARNING: Unclassified error pattern.\n\n")

        log.write("--- AST CONTEXT ---\n")
        log.write(f"AST Node Type: {node}\n")
        log.write(f"Parent Node Type: {parent}\n")

        log.write("=" * 40 + "\n")

    print("Unified log entry written to root unified_logs.txt")