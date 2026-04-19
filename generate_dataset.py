import os
import random
import csv
import re
import argparse

from error_classifier import classify_error
from context_extractor import extract_context
from compiler_ast.ast_utils import get_error_line


TEMP_FILE = "temp_test.c"
OUTPUT_DATASET = "generated_dataset.csv"

SAMPLE_COUNT = 2500  # 25 error types × 100 samples each
SAMPLES_PER_CATEGORY = 100

VALID_TYPES = ["int", "float", "double", "char"]
# Use fixed variable names per generator to avoid cross-contamination
VAR_NAMES = ["x", "count", "value", "num", "temp", "total", "score"]
INT_VALUES = [str(random.randint(1, 100)) for _ in range(200)]


# TEMPLATE GENERATORS

def generate_missing_semicolon():
    value = random.choice(INT_VALUES)
    return f"""
int main() {{
    int a = {value}
    return 0;
}}
"""


def generate_undefined_variable():
    value = random.choice(INT_VALUES)
    return f"""
int main() {{
    y = {value};
    return 0;
}}
"""


def generate_type_mismatch():
    # Generate pointer-float assignment error (incompatible type, not pointer-to-int)
    return f"""
int main() {{
    int *p;
    float f = 3.14;
    p = f;
    return 0;
}}
"""


def generate_scope_error():
    # Generate "variable-sized object may not be initialized" error
    return f"""
int main() {{
    int n = 5;
    int arr[n] = {1, 2, 3, 4, 5};
    return 0;
}}
"""

def generate_uninitialized_use():
    # Generate const modification error
    return f"""
int main() {{
    const int uninit = 5;
    uninit = 10;
    return 0;
}}
"""

def generate_empty_loop_body():
    return f"""
int main() {{
    int i = 0;
    while (i < 10);
    {{
        i++;
    }}
    return 0;
}}
"""

def generate_assignment_in_if():
    return f"""
int main() {{
    int flag = 0;
    if (flag = 5) {{
        return 1;
    }}
    return 0;
}}
"""

def generate_string_compare():
    return f"""
#include <stdio.h>
int main() {{
    char *s1 = "hello";
    if (s1 == "world") {{
        return 1;
    }}
    return 0;
}}
"""

def generate_sizeof_array_param():
    return f"""
void func(int arr[10]) {{
    int s = sizeof(arr);
}}
int main() {{
    int a[10];
    func(a);
    return 0;
}}
"""

def generate_scanf_missing_ampersand():
    return f"""
#include <stdio.h>
int main() {{
    int input;
    scanf("%d", input);
    return 0;
}}
"""

def generate_missing_return():
    return f"""
int func() {{
    int result = 5;
}}
int main() {{
    func();
    return 0;
}}
"""

def generate_float_modulo():
    return f"""
int main() {{
    float fval = 5.5;
    int y = fval % 2;
    return 0;
}}
"""

def generate_array_bounds():
    return f"""
int main() {{
    int myarr[5];
    myarr[5] = 10;
    return 0;
}}
"""

def generate_printf_format_mismatch():
    return f"""
#include <stdio.h>
int main() {{
    printf("%d", "hello");
    return 0;
}}
"""

def generate_scanf_format_mismatch():
    return f"""
#include <stdio.h>
int main() {{
    float fnum;
    scanf("%d", &fnum);
    return 0;
}}
"""

def generate_implicit_declaration():
    return f"""
int main() {{
    printf("hello");
    return 0;
}}
"""

def generate_pointer_int_mismatch():
    return f"""
int main() {{
    int x = 5;
    int *p = x;
    return 0;
}}
"""

def generate_dereference_non_pointer():
    return f"""
int main() {{
    int val = 5;
    *val = 10;
    return 0;
}}
"""

def generate_member_access_non_struct():
    return f"""
int main() {{
    int obj = 5;
    obj.a = 10;
    return 0;
}}
"""

def generate_function_argument_mismatch():
    return f"""
void f(int x) {{}}
int main() {{
    f(1, 2);
    return 0;
}}
"""

def generate_void_return_value():
    return f"""
void f() {{
    return 1;
}}
int main() {{
    f();
    return 0;
}}
"""

def generate_division_by_zero():
    return f"""
int main() {{
    int x = 5 / 0;
    return 0;
}}
"""

def generate_multiple_definition():
    return f"""
int main() {{
    int var;
    int var;
    return 0;
}}
"""

def generate_bitwise_logical_mixup():
    return f"""
int main() {{
    int cond = 1;
    if (cond & cond == 1) {{}}
    return 0;
}}
"""

def generate_duplicate_case():
    return f"""
#include <stdio.h>
int main() {{
    int switchvar = 1;
    switch(switchvar) {{
        case 1:
            printf("one");
        case 1:
            printf("one again");
            break;
    }}
    return 0;
}}
"""

def generate_goto_label():
    return f"""
int main() {{
    goto end;
    int x = 5;
    end:
    return 0;
}}
"""

def generate_const_modification():
    return f"""
int main() {{
    const int x = 5;
    x = 10;
    return 0;
}}
"""

def generate_vla_in_struct():
    return f"""
struct S {{
    int arr[];
}};
int main() {{
    return 0;
}}
"""

ERROR_GENERATORS = [
    generate_missing_semicolon,
    generate_undefined_variable,
    generate_type_mismatch,
    generate_scope_error,
    generate_empty_loop_body,
    generate_assignment_in_if,
    generate_string_compare,
    generate_sizeof_array_param,
    generate_scanf_missing_ampersand,
    generate_missing_return,
    generate_float_modulo,
    generate_uninitialized_use,
    generate_array_bounds,
    generate_printf_format_mismatch,
    generate_scanf_format_mismatch,
    generate_implicit_declaration,
    generate_pointer_int_mismatch,
    generate_dereference_non_pointer,
    generate_member_access_non_struct,
    generate_function_argument_mismatch,
    generate_void_return_value,
    generate_division_by_zero,
    generate_multiple_definition,
    generate_bitwise_logical_mixup,
    generate_duplicate_case
]

# Verify we have exactly 25 error generators
assert len(ERROR_GENERATORS) == 25, f"Expected 25 error generators, got {len(ERROR_GENERATORS)}"


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
        match = re.search(r"\b(?:const\s+)?(?:unsigned\s+)?(int|float|double|char)\s*\*?\s*(\w+)(?:\s*\[\s*\d*\s*\])?\s*[,=;]", line)
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

    elif category == "Empty body":
        return f"{intro} there is a semicolon immediately after a loop or if-statement. This creates an 'empty body', meaning the code inside the braces won't actually be part of the loop. It's like telling someone to start a race but immediately saying 'Stop'."

    elif category == "Assignment in condition":
        return f"{intro} you are using a single equals sign (=) inside a condition. In C, = is for assignment, while == is for comparison. This condition will always be true if the assigned value is non-zero, which is usually not what you want."

    elif category == "String comparison":
        return f"{intro} you are trying to compare two strings using ==. In C, this compares the memory addresses of the strings, not their actual text. To compare the content of strings, you must use the strcmp() function."

    elif category == "Sizeof array param":
        return f"{intro} you are using sizeof on an array that was passed as a function parameter. In C, arrays 'decay' into pointers when passed to functions, so sizeof will return the size of a pointer (usually 4 or 8 bytes) instead of the actual array size."

    elif category == "Scanf missing ampersand":
        return f"{intro} you are passing a variable's value instead of its address to scanf. Think of it like giving a delivery driver the name of a person ('John') instead of their actual home address. Use '&' to provide the address so scanf knows where to store the data."

    elif category == "Missing return":
        return f"{intro} your function is supposed to return a value (like an int) but it reaches the end without doing so. It's like a waiter taking your order but never bringing the food. The program expecting a result will get a random, incorrect value."

    elif category == "Float modulo":
        return f"{intro} you are using the modulo operator (%) on a decimal number (float/double). Modulo is for finding remainders of whole numbers only. Like trying to find the remainder of a cut piece of fabric—it only makes sense when dealing with whole 'units' or integers."

    elif category == "Uninitialized use":
        return f"{intro} you are using a variable before giving it a value. In C, new variables contain 'garbage' data from previous programs. It's like trying to read a page in a notebook before you've written anything on it—you'll just see leftover scribbles."

    elif category == "Array bounds":
        return f"{intro} you are trying to access an index that doesn't exist in your array. If you have 5 lockers, you can't put something in the 6th one. C doesn't stop you, but it can crash your program or corrupt other data."

    elif category == "Printf format mismatch":
        return f"{intro} the placeholder (like %d) doesn't match the type of the data you provided. It's like trying to fit a square peg in a round hole. The compiler needs the right 'viewing lens' to display your data correctly."

    elif category == "Scanf format mismatch":
        return f"{intro} you told scanf to look for one type of data (like an integer), but provided a variable of a different type (like a float). It's like a translator listening for French but receiving Spanish—the result will be total nonsense."

    elif category == "Implicit declaration":
        return f"{intro} you are using a function that the compiler hasn't heard of yet. Usually, this means you forgot to add an #include at the top of your file (like #include <stdio.h>). It's like calling a person by name before they've been introduced to the group."

    elif category == "Pointer-int mismatch":
        return f"{intro} you are trying to treat a memory address (pointer) like a regular number, or vice-versa. They are different 'units' of measurement. Like trying to add 5 miles to 5 gallons—the math just doesn't work that way."

    elif category == "Dereference non-pointer":
        return f"{intro} you are using '*' on a variable that isn't a pointer. The '*' means 'go to the address stored in this variable'. If the variable isn't an address, the computer gets lost trying to follow directions that don't exist."

    elif category == "Member access non-struct":
        return f"{intro} you are using '.' to look inside a variable that isn't a structure. It's like trying to open a drawer in a solid brick—only 'containers' (structs) have parts you can look inside of."

    elif category == "Function argument mismatch":
        return f"{intro} you are providing the wrong number of arguments to a function. If a car requires 4 tires to run, providing only 2 (or trying to add 6) will prevent it from working properly. Check the function's definition."

    elif category == "Void return value":
        return f"{intro} a 'void' function is trying to return a value. 'Void' means 'this function returns nothing'. It's like a volunteer refusing to accept payment—they are specifically defined not to give anything back."

    elif category == "Division by zero":
        return f"{intro} your code is trying to divide by zero. In math, this is impossible and results in an undefined state. It's like trying to share 10 cookies among zero people—the situation simply cannot happen."

    elif category == "Multiple definition":
        return f"{intro} you have defined the same variable name twice in the same scope. The compiler doesn't know which one you mean when you use that name later. It's like having two people in a small room both named 'Alex'—confusion is inevitable."

    elif category == "Bitwise-logical mixup":
        return f"{intro} you used '&' (bitwise) where you likely meant '&&' (logical). Bitwise operators look at individual bits (microscopic level), while logical operators look at true/false values (macroscopic level). For 'if' statements, you almost always want '&&'."

    elif category == "Duplicate case":
        return f"{intro} two case labels in the switch statement have the same value. The compiler can't decide which case to execute when that value matches. It's like having two doors with the same number—the program won't know which one to open."

    elif category == "VLA initialization":
        return f"{intro} you are trying to initialize a variable-length array (VLA) at the time of declaration. In C, VLAs have sizes determined at runtime, so they cannot be initialized with a fixed list of values. It's like trying to fill a balloon with a specific amount of water before you know how big it will be."

    elif category == "Const modification":
        return f"{intro} you are trying to change the value of a variable that was declared as 'const'. Once a const variable is initialized, its value cannot be changed. Think of it like a plaque on a wall—you can read it, but you can't erase or modify what's written."

    return "The compiler detected a rule violation in the program."


# DATASET CREATION

def generate_dataset(compiler="clang"):

    with open(OUTPUT_DATASET, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "input_text",
                "target_text",
                "category",
                "phase",
                "violated_rule",
                "compiler",
                "error_line",
            ]
        )

        for generator in ERROR_GENERATORS:

            generated = 0
            attempts = 0

            while generated < SAMPLES_PER_CATEGORY and attempts < SAMPLES_PER_CATEGORY * 10:
                attempts += 1
                code = generator()

                with open(TEMP_FILE, "w") as f:
                    f.write(code)

                error_line, _, error_output = get_error_line(TEMP_FILE, compiler=compiler)

                if not error_line:
                    continue

                classification = classify_error(error_output)
                category = classification["category"]

                if category == "Unknown":
                    print(f"Unknown category for: {error_output}")
                    continue

                cleaned = classification["cleaned_message"]
                phase = classification["phase"]
                violated_rule = classification["violated_rule"]

                context = extract_context(TEMP_FILE, error_line)

                prompt = build_prompt(cleaned, context)
                explanation = generate_dynamic_explanation(category, cleaned, context)

                writer.writerow(
                    [
                        prompt,
                        explanation,
                        category,
                        phase,
                        violated_rule,
                        compiler,
                        error_line,
                    ]
                )

                generated += 1

                print(f"Generated {generated}/{SAMPLES_PER_CATEGORY} for {category}")

    os.remove(TEMP_FILE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate labeled compiler diagnostic dataset.")
    parser.add_argument(
        "--compiler",
        choices=["clang", "gcc"],
        default="clang",
        help="Compiler used to collect diagnostics",
    )
    args = parser.parse_args()
    generate_dataset(compiler=args.compiler)