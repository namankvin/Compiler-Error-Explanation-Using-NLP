import re

def extract_clean_message(error_message):
    # Extract only the core compiler error message.
    match = re.search(r"error:\s*(.*)", error_message, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return error_message.strip()


def classify_error(error_message):
    cleaned = extract_clean_message(error_message).lower()

    # Missing Token (Parsing)
    if re.search(r"expected\s+';'", cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Missing token",
            "phase": "Parsing",
            "violated_rule": "Statements in C must end with a semicolon."
        }

    if re.search(r"expected\s+'\)'", cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Missing token",
            "phase": "Parsing",
            "violated_rule": "Parentheses must be properly closed."
        }

    if re.search(r"expected\s+'\}'", cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Missing token",
            "phase": "Parsing",
            "violated_rule": "Braces must be properly closed."
        }

    # Undefined Symbol
    if re.search(r"undeclared", cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Undefined symbol",
            "phase": "Semantic Analysis",
            "violated_rule": "Variables must be declared before they are used."
        }

    # Scope Error
    if re.search(r"not declared in this scope", cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Scope error",
            "phase": "Semantic Analysis",
            "violated_rule": "Variables can only be accessed within their declared scope."
        }

    # Type Mismatch
    if re.search(r"incompatible", cleaned) or re.search(r"invalid conversion", cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Type mismatch",
            "phase": "Semantic Analysis",
            "violated_rule": "Assignments and expressions must use compatible data types."
        }

    # Fallback
    return {
        "cleaned_message": cleaned,
        "category": "Unknown",
        "phase": "Unknown",
        "violated_rule": "The compiler detected a rule violation that is not yet classified."
    }