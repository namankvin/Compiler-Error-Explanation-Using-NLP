import re

def extract_clean_message(error_message):
    # Extract only the core compiler error/warning message.
    match = re.search(r"(error|warning):\s*(.*)", error_message, re.IGNORECASE)
    if match:
        return match.group(2).strip()
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

    # 8. Implicit declaration (missing include) - MUST be before "undeclared" check
    if "implicit declaration of function" in cleaned or ("call to undeclared library function" in cleaned and "printf" in cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Implicit declaration",
            "phase": "Semantic Analysis",
            "violated_rule": "You must include the header file (like <stdio.h>) that defines the function."
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

    # 9 & 10. Pointer-to-int mismatch - MUST be before general "incompatible" check
    if "incompatible" in cleaned and ("pointer to integer" in cleaned or "integer to pointer" in cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Pointer-int mismatch",
            "phase": "Semantic Analysis",
            "violated_rule": "You cannot mix pointers and integers without an explicit cast."
        }

    # 20. Const modification - MUST be before general "incompatible" check
    if "cannot assign to variable" in cleaned and "const-qualified type" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Const modification",
            "phase": "Semantic Analysis",
            "violated_rule": "A const-qualified variable cannot be modified after initialization."
        }

    # Type Mismatch
    if re.search(r"incompatible", cleaned) or re.search(r"invalid conversion", cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Type mismatch",
            "phase": "Semantic Analysis",
            "violated_rule": "Assignments and expressions must use compatible data types."
        }

    # Empty Body Warning (-Wempty-body)
    if re.search(r"empty body", cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Empty body",
            "phase": "Parsing/Syntax",
            "violated_rule": "An empty body (like a semicolon right after a loop) might be a mistake."
        }

    # Assignment in Condition (-Wparentheses)
    if re.search(r"using the result of an assignment as a condition", cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Assignment in condition",
            "phase": "Semantic Analysis",
            "violated_rule": "Using '=' instead of '==' in a condition is a common error."
        }

    # String Comparison (-Wstring-compare)
    if re.search(r"comparison against a string literal", cleaned) or (re.search(r"array comparison", cleaned) and "constant" in cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "String comparison",
            "phase": "Semantic Analysis",
            "violated_rule": "In C, you cannot compare strings using '=='; use strcmp instead."
        }

    # Sizeof on Array Parameter (-Wsizeof-array-argument)
    if re.search(r"sizeof on array function parameter", cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Sizeof array param",
            "phase": "Semantic Analysis",
            "violated_rule": "sizeof on an array parameter returns the size of a pointer, not the array."
        }

    # 1. Scanf missing ampersand
    if "format specifies type" in cleaned and "int *" in cleaned and "but the argument has type 'int'" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Scanf missing ampersand",
            "phase": "Semantic Analysis",
            "violated_rule": "scanf requires the address of the variable (&var) to store the input."
        }

    # 2. Missing return in non-void function
    if "non-void function" in cleaned and "does not return a value" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Missing return",
            "phase": "Semantic Analysis",
            "violated_rule": "Functions with a return type (like int) must return a value."
        }

    # 3. Float modulo
    if "invalid operands to binary expression" in cleaned and ("'float'" in cleaned or "'double'" in cleaned) and "'int'" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Float modulo",
            "phase": "Semantic Analysis",
            "violated_rule": "The modulo operator (%) only works with integers."
        }

    # 4. Uninitialized variable use
    if "is uninitialized when used here" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Uninitialized use",
            "phase": "Semantic Analysis",
            "violated_rule": "Variables must be assigned a value before being used."
        }

    # 5. Array index out of bounds
    if "array index" in cleaned and "is past the end of the array" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Array bounds",
            "phase": "Semantic Analysis",
            "violated_rule": "You cannot access an index outside the declared size of the array."
        }

    # 6. Printf format mismatch
    if "format specifies type" in cleaned and "but the argument has type" in cleaned and "printf" in error_message.lower():
        return {
            "cleaned_message": cleaned,
            "category": "Printf format mismatch",
            "phase": "Semantic Analysis",
            "violated_rule": "The format specifier (like %d) must match the type of the argument."
        }

    # 7. Scanf format mismatch
    if "format specifies type" in cleaned and "but the argument has type" in cleaned and "scanf" in error_message.lower():
        return {
            "cleaned_message": cleaned,
            "category": "Scanf format mismatch",
            "phase": "Semantic Analysis",
            "violated_rule": "scanf specifiers must match the type of the variable address."
        }

    # 11. Dereference non-pointer
    if "indirection requires pointer operand" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Dereference non-pointer",
            "phase": "Semantic Analysis",
            "violated_rule": "The '*' operator can only be used on pointers."
        }

    # 12. Member access on non-struct
    if "member reference base type" in cleaned and "is not a structure" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Member access non-struct",
            "phase": "Semantic Analysis",
            "violated_rule": "The '.' operator can only be used on structures or unions."
        }

    # 13. Too many/few arguments
    if "too many arguments" in cleaned or "too few arguments" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Function argument mismatch",
            "phase": "Semantic Analysis",
            "violated_rule": "The number of arguments provided must match the function definition."
        }

    # 14. Void function returning value
    if "void function" in cleaned and "should not return a value" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Void return value",
            "phase": "Semantic Analysis",
            "violated_rule": "Functions declared as 'void' cannot return a value."
        }

    # 15. Division by zero
    if "division by zero is undefined" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Division by zero",
            "phase": "Semantic Analysis",
            "violated_rule": "Mathematically, you cannot divide a number by zero."
        }

    # 16. Multiple definition (Redefinition)
    if "redefinition of" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Multiple definition",
            "phase": "Semantic Analysis",
            "violated_rule": "A variable or function name can only be defined once in the same scope."
        }

    # 17. Bitwise vs Logical mixup
    if "bitwise '&' with boolean operands" in cleaned or "bitwise '|' with boolean operands" in cleaned or ("& has lower precedence than ==" in cleaned):
        return {
            "cleaned_message": cleaned,
            "category": "Bitwise-logical mixup",
            "phase": "Semantic Analysis",
            "violated_rule": "Use '&&' for logical AND conditions, not the bitwise '&'."
        }

    # 18. Duplicate case value
    if "duplicate case value" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "Duplicate case",
            "phase": "Semantic Analysis",
            "violated_rule": "Each case in a switch statement must have a unique value."
        }

    # 19. Variable-sized object initialization
    if "variable-sized object may not be initialized" in cleaned:
        return {
            "cleaned_message": cleaned,
            "category": "VLA initialization",
            "phase": "Semantic Analysis",
            "violated_rule": "Variable-length arrays cannot be initialized at declaration."
        }

    # Fallback
    return {
        "cleaned_message": cleaned,
        "category": "Unknown",
        "phase": "Unknown",
        "violated_rule": "The compiler detected a rule violation that is not yet classified."
    }