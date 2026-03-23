import subprocess
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from context_extractor import extract_context
from security_explainer import (
    analyze_security_implications,
    get_security_recommendation,
    generate_security_report,
    compare_explanations
)

# Load trained model
device = "mps" if torch.backends.mps.is_available() else "cpu"

try:
    model = AutoModelForSeq2SeqLM.from_pretrained("./final_model").to(device)
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained("./final_model")
    MODEL_AVAILABLE = True
except Exception:
    MODEL_AVAILABLE = False


ERROR_EXPLANATIONS = {
    "expected ';'": "This error indicates a semicolon is missing at the end of a statement. In C, every statement must end with a semicolon so the compiler can properly understand where the statement finishes.",
    "undeclared identifier": "This error means a variable is being used before it has been declared. In C, variables must be declared with a data type before they can be used.",
    "use of undeclared identifier": "This error means a variable is being used before it has been declared. In C, variables must be declared with a data type before they can be used.",
    "incompatible pointer to integer": "This error indicates a type mismatch - a pointer value is being assigned or compared to an integer. In C, pointers and integers are different types and cannot be used interchangeably.",
    "type mismatch": "This error indicates incompatible data types are being used together. In C, assignments and operations must use compatible types.",
    "expected ')'": "This error indicates a missing closing parenthesis. Function calls and control structures require matching pairs of parentheses.",
    "expected '('": "This error indicates a missing opening parenthesis. Function calls and control structures require matching pairs of parentheses.",
    "unknown type name": "This error means an unrecognized type name is being used. This could be a typo or a missing include statement for a custom type.",
    "implicit declaration of function": "This error indicates a function is being called before the compiler has seen its declaration. In C, functions should be declared or defined before they are used.",
    "variable-sized object may not be initialized": "This error occurs when trying to initialize a variable-length array, which is not allowed in C.",
    "expected expression": "This error indicates the compiler encountered unexpected syntax where it expected a valid expression.",
    "duplicate case value": "This error occurs in a switch statement when two case labels have the same value.",
    "break statement not within loop or switch": "This error means a break statement appears outside of a loop or switch statement where it's not valid.",
    "continue statement not within loop": "This error means a continue statement appears outside of a loop where it's not valid.",
    "member reference base": "This error indicates an issue with accessing a member of a struct or union, possibly using the wrong operator (. vs ->).",
    "array index out of bounds": "This warning indicates accessing an array element with an index that may be outside the valid range.",
    "unused variable": "This warning indicates a variable is declared but never used in the code.",
    "variable set but not used": "This warning indicates a variable is assigned a value but that value is never read.",
    "comparison of unsigned expression": "This warning indicates a potentially problematic comparison involving unsigned integers.",
    "result of comparison is always": "This warning indicates a comparison that will always evaluate to true or false.",
    "division by zero": "This error indicates an attempt to divide by zero, which is undefined behavior.",
    "invalid operands to binary": "This error indicates that the operands used with a binary operator are not compatible with that operator.",
    "too few arguments to function call": "This error means a function call is missing required arguments.",
    "too many arguments to function call": "This error means a function call has more arguments than the function expects.",
}


def get_explanation_for_error(error_text):
    """Get explanation based on error type using pattern matching"""
    error_lower = error_text.lower()
    
    for pattern, explanation in ERROR_EXPLANATIONS.items():
        if pattern.lower() in error_lower:
            return explanation
    
    return f"The compiler detected a syntax or semantic error: {error_text}. This violates C language rules and must be fixed for successful compilation."


def compile_code(file, flags=None):
    """Compile C code and capture compiler errors"""
    
    cmd = ["clang"]
    if flags:
        cmd.extend(flags)
    cmd.append(file)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return result.stderr


def extract_error_and_code(error_message, file):
    """Extract error message and code context"""

    error_text = None
    line_number = None

    lines = error_message.split("\n")

    for line in lines:
        # Look for both errors and warnings
        if "error:" in line or "warning:" in line:

            # Example line:
            # test.c:4:15: error: expected ';' at end of declaration
            # test.c:9:27: warning: format specifies type 'int'

            parts = line.split("error:") if "error:" in line else line.split("warning:")
            if len(parts) > 1:
                error_text = parts[1].strip()

                try:
                    location = line.split(":")
                    line_number = int(location[1])
                except:
                    line_number = None

                break

    code_context = "<unknown>"

    if line_number:
        try:
            code_context = "\n".join(extract_context(file, line_number))
        except:
            pass

    return error_text, code_context


def format_error(error_message, file):
    """Convert compiler error to model input"""

    error_text, code_context = extract_error_and_code(error_message, file)

    if not error_text:
        return None

    input_text = f"""Explain the following compiler error:

Error:
{error_text}

Code:
{code_context}
"""

    return input_text


def generate_explanation(input_text, error_text):
    """Generate explanation using trained NLP model or fallback to rule-based"""
    
    # First try rule-based explanation
    rule_explanation = get_explanation_for_error(error_text)
    
    # If we have a rule-based match, use it
    if rule_explanation != f'The compiler detected a syntax or semantic error: {error_text}. This violates C language rules and must be fixed for successful compilation.':
        return rule_explanation
    
    # Fallback to model if available
    if MODEL_AVAILABLE:
        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,
                num_beams=5,
                repetition_penalty=1.5,
                no_repeat_ngram_size=2,
                early_stopping=True,
                do_sample=False
            )

        explanation = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # If model just copies input, use generic fallback
        if input_text.strip()[:50] in explanation or len(explanation) < 20:
            return f"The compiler detected a syntax or semantic error: {error_text}. This violates C language rules and must be fixed for successful compilation."
        
        return explanation.strip()
    
    return f"The compiler detected a syntax or semantic error: {error_text}. This violates C language rules and must be fixed for successful compilation."


def explain_file(file, show_security=False, show_comparison=False, compiler_flags=None):

    print(f"\nCompiling {file}...\n")

    error_message = compile_code(file, compiler_flags)

    if not error_message:
        print("No compiler errors detected.")
        return

    print("Compiler Output:\n")
    print(error_message)

    input_text = format_error(error_message, file)

    if not input_text:
        print("Could not parse compiler error.")
        return

    # Extract error text for rule-based matching
    error_text, code_context = extract_error_and_code(error_message, file)
    
    explanation = generate_explanation(input_text, error_text)

    print("\nGenerated Explanation:\n")
    print("--------------------------------------------------")
    print(explanation)
    print("--------------------------------------------------")

    # Security-aware analysis
    if show_security or show_comparison:
        security_analysis = analyze_security_implications(error_text, code_context)
        
        if show_comparison and security_analysis:
            print(compare_explanations(explanation, security_analysis))
        elif show_security:
            if security_analysis:
                print("\n🔒 SECURITY ANALYSIS:\n")
                print(f"Severity: {security_analysis.get('severity', 'Unknown')}")
                print(f"Category: {security_analysis.get('category', 'Unknown')}")
                print(f"CWE Reference: {security_analysis.get('cwe', 'N/A')}")
                print(f"\nSecurity Risk:\n  {security_analysis.get('risk', 'N/A')}")
                print(f"\nSecure Fix:\n  {security_analysis.get('explanation', 'N/A')}")
                print(f"\n⚠️  Warning:\n  {security_analysis.get('insecure_fix_warning', 'N/A')}")
                
                print("\nRecommendations:")
                for rec in get_security_recommendation(security_analysis.get('category', '')):
                    print(f"  • {rec}")
            else:
                print("\nℹ️  No specific security concerns identified for this error.")


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:
        print("Usage: python explain_error.py <file.c> [--security] [--compare] [--warnings]")
        print("  --security  Show security analysis for the error")
        print("  --compare   Show comparison between standard and security-aware explanations")
        print("  --warnings  Enable -Wall -Wextra compiler warnings")
        exit()

    file = sys.argv[1]
    show_security = "--security" in sys.argv or "-s" in sys.argv
    show_comparison = "--compare" in sys.argv or "-c" in sys.argv
    use_warnings = "--warnings" in sys.argv or "-w" in sys.argv
    
    compiler_flags = ["-Wall", "-Wextra"] if use_warnings else None
    
    explain_file(file, show_security=show_security, show_comparison=show_comparison, compiler_flags=compiler_flags)