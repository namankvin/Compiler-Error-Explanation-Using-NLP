import os
import random
import csv
import re

from error_classifier import classify_error
from context_extractor import extract_context
from compiler_ast.ast_utils import get_error_line


TEMP_FILE = "temp_test.c"
OUTPUT_DATASET = "generated_dataset.csv"

SAMPLE_COUNT = 1000

VALID_TYPES = ["int", "float", "double", "char"]
VAR_NAMES = ["x", "count", "value", "num", "temp", "total", "score"]
INT_VALUES = [str(random.randint(1, 100)) for _ in range(200)]


# TEMPLATE GENERATORS

def generate_missing_semicolon():
    var = random.choice(VAR_NAMES)
    value = random.choice(INT_VALUES)
    dtype = random.choice(["int", "float", "double"])

    return f"""
int main() {{
    {dtype} {var} = {value}
    return 0;
}}
"""


def generate_undefined_variable():
    var = random.choice(VAR_NAMES)
    value = random.choice(INT_VALUES)

    return f"""
int main() {{
    {var} = {value};
    return 0;
}}
"""


def generate_type_mismatch():
    var = random.choice(VAR_NAMES)
    dtype = random.choice(["int", "float", "double"])

    return f"""
int main() {{
    {dtype} {var} = "hello";
    return 0;
}}
"""


def generate_scope_error():
    var = random.choice(VAR_NAMES)
    value = random.choice(INT_VALUES)
    dtype = random.choice(["int", "float", "double"])

    return f"""
int main() {{
    if (1) {{
        {dtype} {var} = {value};
    }}
    {var} = 5;
    return 0;
}}
"""


ERROR_GENERATORS = [
    generate_missing_semicolon,
    generate_undefined_variable,
    generate_type_mismatch,
    generate_scope_error
]


def build_prompt(cleaned_message, context):
    context_text = "\n".join(context)

    return f"""Explain the following compiler error:

Error:
{cleaned_message}

Code:
{context_text}
"""

def extract_variable_from_context(context):
    for line in context:
        match = re.search(r"\b(int|float|double|char)\s+(\w+)\s*=", line)
        if match:
            return match.group(2)
    return None


def generate_dynamic_explanation(category, cleaned_message, context):

    variations_intro = [
        "This error indicates that",
        "The compiler is reporting that",
        "This message means that"
    ]

    intro = random.choice(variations_intro)

    # Extract variable name if present
    var_match = re.search(r"'(.*?)'", cleaned_message)
    variable = var_match.group(1) if var_match else None

    if category == "Missing token":

        if ";" in cleaned_message:
            return f"{intro} a semicolon is missing at the end of a statement. In C, every statement must end with a semicolon so the compiler can properly understand where the statement finishes."

        return f"{intro} a required symbol is missing. C follows strict syntax rules, and missing symbols prevent the compiler from parsing the code correctly."

    elif category == "Undefined symbol":

        if variable:
            return f"{intro} the variable '{variable}' is being used before it has been declared. In C, variables must be declared with a data type before they can be used."
        else:
            return f"{intro} a variable is used before it has been declared. In C, every variable must be declared before it is referenced."

    elif category == "Type mismatch":

        variable = extract_variable_from_context(context)

        if variable:
            return f"{intro} the variable '{variable}' is assigned a value of an incompatible data type. In C, assignments must use compatible types, otherwise the compiler cannot safely perform the conversion."
        else:
            return f"{intro} incompatible data types are being used together. In C, assignments must use compatible types."

    elif category == "Scope error":

        if variable:
            return f"{intro} the variable '{variable}' is accessed outside the block where it was declared. In C, variables are only visible within their declared scope."
        else:
            return f"{intro} a variable is accessed outside its declared scope. In C, variables are limited to the block in which they are defined."

    return "The compiler detected a rule violation in the program."


# DATASET CREATION

def generate_dataset():

    with open(OUTPUT_DATASET, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["input_text", "target_text"])

        samples_per_category = SAMPLE_COUNT // 4

        for generator in ERROR_GENERATORS:

            generated = 0

            while generated < samples_per_category:

                code = generator()

                with open(TEMP_FILE, "w") as f:
                    f.write(code)

                error_line, error_column, error_output = get_error_line(TEMP_FILE)

                if not error_line:
                    continue

                classification = classify_error(error_output)

                category = classification["category"]

                if category == "Unknown":
                    continue

                cleaned = classification["cleaned_message"]
                phase = classification["phase"]
                violated_rule = classification["violated_rule"]

                context = extract_context(TEMP_FILE, error_line)

                prompt = build_prompt(cleaned, context)
                explanation = generate_dynamic_explanation(category, cleaned, context)

                writer.writerow([prompt, explanation])

                generated += 1

                print(f"Generated {generated}/{samples_per_category} for {category}")

    os.remove(TEMP_FILE)


if __name__ == "__main__":
    generate_dataset()