"""
Security-Aware Compiler Error Explanation Module

This module identifies compiler errors that are commonly linked to insecure fixes
and provides security-aware explanations that warn against unsafe quick fixes.
"""

import re

# Security-linked error patterns and their secure explanations
SECURITY_ERROR_PATTERNS = {
    # Type Casting Issues
    "cast from pointer to integer": {
        "category": "Type Casting",
        "severity": "HIGH",
        "insecure_fix": "Casting pointers to integers can lead to buffer overflows and memory corruption.",
        "secure_explanation": "Use proper pointer types or standard types like uintptr_t from <stdint.h> when pointer-integer conversion is absolutely necessary. Avoid casting between pointers and integers as it can hide bugs and create security vulnerabilities.",
        "cwe": "CWE-192: Integer Coercion Error",
        "risk": "May cause memory corruption, information disclosure, or code execution on 64-bit systems."
    },
    "cast to smaller integer type": {
        "category": "Type Casting",
        "severity": "HIGH",
        "insecure_fix": "Truncating values through casts can lead to integer overflow vulnerabilities.",
        "secure_explanation": "Validate that values fit within the target type range before casting. Use size_t for sizes and ptrdiff_t for pointer differences. Consider using safe integer conversion functions.",
        "cwe": "CWE-190: Integer Overflow or Wraparound",
        "risk": "Integer truncation can lead to buffer overflows or incorrect security checks."
    },
    "implicit conversion": {
        "category": "Type Casting",
        "severity": "MEDIUM",
        "insecure_fix": "Implicit conversions can silently introduce bugs in security-critical code.",
        "secure_explanation": "Use explicit casts with proper validation. Enable compiler warnings (-Wconversion) to catch implicit conversions. Use static analysis tools to identify dangerous conversions.",
        "cwe": "CWE-192: Integer Coercion Error",
        "risk": "May cause unexpected behavior in boundary checks or size calculations."
    },
    
    # Ignoring Warnings
    "unused variable": {
        "category": "Ignored Warnings",
        "severity": "MEDIUM",
        "insecure_fix": "Silencing unused variable warnings without understanding may hide incomplete security logic.",
        "secure_explanation": "Review why the variable is unused - it may indicate incomplete error handling or security checks. If intentionally unused (e.g., for API compatibility), explicitly mark with (void)var or [[maybe_unused]].",
        "cwe": "CWE-563: Assignment to Variable without Use",
        "risk": "May indicate missing security checks or incomplete validation logic."
    },
    "unused result": {
        "category": "Ignored Warnings", 
        "severity": "HIGH",
        "insecure_fix": "Ignoring function return values can bypass critical error checks.",
        "secure_explanation": "Always check return values of security-critical functions (malloc, fread, fgets, etc.). Unchecked returns can lead to null pointer dereferences or use of uninitialized data.",
        "cwe": "CWE-252: Unchecked Return Value",
        "risk": "Can lead to null pointer dereference, use of uninitialized memory, or missed error conditions."
    },
    "implicit declaration of function": {
        "category": "Ignored Warnings",
        "severity": "HIGH", 
        "insecure_fix": "Calling functions without proper declarations can cause incorrect calling conventions.",
        "secure_explanation": "Always include proper headers for functions. Implicit declarations assume int return type which is wrong for pointers. This can cause crashes or security issues on 64-bit systems.",
        "cwe": "CWE-628: Function Call with Incorrectly Specified Arguments",
        "risk": "May cause stack corruption, incorrect parameter passing, or return value truncation."
    },
    "format specifies type": {
        "category": "Ignored Warnings",
        "severity": "CRITICAL",
        "insecure_fix": "Format string mismatches can lead to format string vulnerabilities.",
        "secure_explanation": "Always match format specifiers to argument types. Use %zu for size_t, %zd for ssize_t, %jd for intmax_t. Never pass user input directly as format string - use printf('%s', user_input) not printf(user_input).",
        "cwe": "CWE-134: Use of Externally-Controlled Format String",
        "risk": "Format string vulnerabilities can lead to information disclosure or arbitrary code execution."
    },
    "format string is not a string literal": {
        "category": "Ignored Warnings",
        "severity": "CRITICAL",
        "insecure_fix": "Treating user-controlled input as the format string can create exploitable format string vulnerabilities.",
        "secure_explanation": "Always keep format strings constant, for example printf('%s', user_input). Never pass external input as the first argument to printf-like functions.",
        "cwe": "CWE-134: Use of Externally-Controlled Format String",
        "risk": "Attackers may read memory or write memory via format tokens such as %x and %n."
    },
    
    # Disabling Checks
    "sign-compare": {
        "category": "Disabled Checks",
        "severity": "MEDIUM",
        "insecure_fix": "Disabling sign comparison warnings can hide integer overflow bugs.",
        "secure_explanation": "Fix the underlying type mismatch instead of suppressing warnings. Use consistent signed/unsigned types. Add explicit bounds checks when mixing signed and unsigned values.",
        "cwe": "CWE-190: Integer Overflow or Wraparound",
        "risk": "Sign mismatches can cause infinite loops or bypass security bounds checks."
    },
    "comparison of integers of different signs": {
        "category": "Disabled Checks",
        "severity": "MEDIUM",
        "insecure_fix": "Ignoring signed/unsigned comparison warnings can hide boundary-check failures.",
        "secure_explanation": "Use consistent integer types in comparisons, or cast safely after explicit range checks.",
        "cwe": "CWE-190: Integer Overflow or Wraparound",
        "risk": "Signed negatives may become large unsigned values, bypassing index and size checks."
    },
    "tautological comparison": {
        "category": "Disabled Checks",
        "severity": "MEDIUM",
        "insecure_fix": "Tautological comparisons may indicate logic errors in security checks.",
        "secure_explanation": "Review the comparison logic - always-true or always-false conditions often indicate bugs. Unsigned values compared to < 0 are always false, which may break error handling.",
        "cwe": "CWE-570: Expression Always False",
        "risk": "May indicate broken security checks that never trigger."
    },
    "logical not parentheses": {
        "category": "Disabled Checks",
        "severity": "LOW",
        "insecure_fix": "Operator precedence bugs can invert security logic.",
        "secure_explanation": "Use explicit parentheses to clarify operator precedence. !a == b is (!a) == b, not !(a == b). This can completely invert authentication or validation logic.",
        "cwe": "CWE-783: Operator Precedence Logic Error",
        "risk": "Can invert security checks, allowing unauthorized access."
    },
    
    # Buffer and Memory Issues
    "array subscript is": {
        "category": "Buffer Security",
        "severity": "HIGH",
        "insecure_fix": "Out-of-bounds array access can corrupt memory or leak data.",
        "secure_explanation": "Always validate array indices against bounds. Use sizeof(array)/sizeof(array[0]) for stack arrays. Consider using safer alternatives like strlcpy/strlcat or bounds-checking wrappers.",
        "cwe": "CWE-787: Out-of-bounds Write",
        "risk": "Buffer overflows are a leading cause of exploitable vulnerabilities."
    },
    "string length": {
        "category": "Buffer Security",
        "severity": "MEDIUM",
        "insecure_fix": "Using strlen on untrusted input without bounds can cause DoS.",
        "secure_explanation": "Use strnlen() with a maximum length for untrusted input. Never assume strings are null-terminated when reading from external sources.",
        "cwe": "CWE-130: Improperly Modeled Data Space",
        "risk": "Can cause denial of service or read beyond buffer boundaries."
    },
    "null passed to": {
        "category": "Buffer Security",
        "severity": "HIGH",
        "insecure_fix": "Null pointer dereferences can crash programs or be exploited.",
        "secure_explanation": "Always validate pointers before use. Check return values of allocation functions. Use assertions in debug builds to catch null dereferences early.",
        "cwe": "CWE-476: NULL Pointer Dereference",
        "risk": "Can cause crashes or be exploited in combination with other vulnerabilities."
    },
    
    # Input Validation Issues  
    "sizeof on array function parameter": {
        "category": "Input Validation",
        "severity": "MEDIUM",
        "insecure_fix": "Using sizeof on function parameters gives pointer size, not array size.",
        "secure_explanation": "Pass array size as a separate parameter. sizeof on function parameters returns sizeof(pointer). Document size requirements clearly in function interfaces.",
        "cwe": "CWE-467: Incorrect Calculation of Buffer Size",
        "risk": "Can lead to buffer overflows when size calculations are wrong."
    },
    "comparison of unsigned expression >= 0": {
        "category": "Input Validation",
        "severity": "LOW",
        "insecure_fix": "Dead code from tautological comparisons may hide real validation bugs.",
        "secure_explanation": "Remove dead comparisons and review validation logic. If signed values are needed, use appropriate signed types. Document why unsigned types are used.",
        "cwe": "CWE-570: Expression Always False",
        "risk": "Indicates potential logic errors in input validation."
    },
    "call to undeclared library function": {
        "category": "Ignored Warnings",
        "severity": "HIGH",
        "insecure_fix": "Calling undeclared library APIs can cause undefined behavior due to assumed signatures.",
        "secure_explanation": "Include the correct header so the compiler knows the exact function signature and return type.",
        "cwe": "CWE-628: Function Call with Incorrectly Specified Arguments",
        "risk": "Incorrect calling conventions may corrupt stack/register state on some platforms."
    },
}


CODE_SECURITY_PATTERNS = {
    r"\bgets\s*\(": {
        "category": "Buffer Security",
        "severity": "CRITICAL",
        "explanation": "Replace gets with fgets and enforce strict input length limits.",
        "cwe": "CWE-242: Use of Inherently Dangerous Function",
        "risk": "gets has no bounds checks and can be exploited for buffer overflow attacks.",
    },
    r"\bstrcpy\s*\(": {
        "category": "Buffer Security",
        "severity": "HIGH",
        "explanation": "Use bounded APIs like snprintf/strlcpy and validate destination buffer size.",
        "cwe": "CWE-120: Buffer Copy without Checking Size of Input",
        "risk": "Unbounded copies may overflow buffers and enable arbitrary code execution.",
    },
    r"\bsprintf\s*\(": {
        "category": "Buffer Security",
        "severity": "HIGH",
        "explanation": "Use snprintf with explicit buffer length to prevent overflow.",
        "cwe": "CWE-120: Buffer Copy without Checking Size of Input",
        "risk": "Unbounded formatted output can overrun stack/heap buffers.",
    },
    r"\bprintf\s*\(\s*[A-Za-z_]\w*\s*\)": {
        "category": "Ignored Warnings",
        "severity": "CRITICAL",
        "explanation": "Never pass variable input as the format argument; use printf('%s', input).",
        "cwe": "CWE-134: Use of Externally-Controlled Format String",
        "risk": "User-controlled format strings can leak or overwrite memory.",
    },
}

# Insecure quick fixes to warn against
INSECURE_FIXES = {
    "adding (void) cast": "Casting to void may suppress important type warnings without fixing the underlying issue.",
    "using -w flag": "Disabling all warnings (-w) hides potential security vulnerabilities.",
    "adding #pragma warning disable": "Suppressing warnings without fixing them leaves vulnerabilities in place.",
    "removing const qualifier": "Removing const can introduce buffer overflow vulnerabilities.",
    "using gets() instead of fgets()": "gets() has no bounds checking and is removed from C11 standard.",
    "using strcpy instead of strncpy": "strcpy has no bounds checking and can cause buffer overflows.",
    "casting away const": "Casting away const qualifiers can lead to undefined behavior.",
    "ignoring return value": "Not checking return values bypasses error handling and security checks.",
    "using int for pointers": "Using int instead of proper pointer types breaks on 64-bit systems.",
    "disabling ASLR/DEP": "Disabling security features makes exploitation easier.",
}


def analyze_security_implications(error_message, code_context):
    """
    Analyze compiler error for security implications.
    
    Args:
        error_message: The compiler error message
        code_context: The code where the error occurred
        
    Returns:
        dict with security analysis or None if no security concerns
    """
    error_lower = error_message.lower() if error_message else ""
    code_lower = code_context.lower() if code_context else ""
    
    for pattern, security_info in SECURITY_ERROR_PATTERNS.items():
        if pattern.lower() in error_lower:
            return {
                "pattern": pattern,
                "category": security_info["category"],
                "severity": security_info["severity"],
                "explanation": security_info["secure_explanation"],
                "insecure_fix_warning": security_info["insecure_fix"],
                "cwe": security_info["cwe"],
                "risk": security_info["risk"]
            }
    
    # Check for dangerous code patterns first.
    for pattern, security_info in CODE_SECURITY_PATTERNS.items():
        if re.search(pattern, code_lower):
            return {
                "pattern": pattern,
                "category": security_info["category"],
                "severity": security_info["severity"],
                "explanation": security_info["explanation"],
                "insecure_fix_warning": "Directly vulnerable code pattern detected.",
                "cwe": security_info["cwe"],
                "risk": security_info["risk"],
            }

    # Check for insecure patterns in code
    for insecure_pattern, warning in INSECURE_FIXES.items():
        if insecure_pattern.lower() in code_lower:
            return {
                "pattern": insecure_pattern,
                "category": "Insecure Code Pattern",
                "severity": "MEDIUM",
                "explanation": warning,
                "insecure_fix_warning": f"Detected potentially insecure pattern: {insecure_pattern}",
                "cwe": "CWE-676: Use of Potentially Dangerous Function",
                "risk": "This pattern is commonly associated with security vulnerabilities."
            }
    
    return None


def get_security_recommendation(category):
    """Get general security recommendations based on error category."""
    recommendations = {
        "Type Casting": [
            "Use fixed-width integer types from <stdint.h> for portable code",
            "Validate ranges before narrowing conversions",
            "Use static analysis tools to detect dangerous casts",
            "Document why casts are necessary in security-critical code"
        ],
        "Ignored Warnings": [
            "Treat warnings as errors (-Werror) in security-critical builds",
            "Understand each warning before suppressing it",
            "Use specific warning flags rather than disabling all warnings",
            "Document why specific warnings are suppressed"
        ],
        "Disabled Checks": [
            "Fix the root cause instead of suppressing warnings",
            "Use compiler flags like -Wall -Wextra -Wpedantic",
            "Implement runtime checks for security-critical operations",
            "Use static analysis to catch issues compilers miss"
        ],
        "Buffer Security": [
            "Use bounds-checking functions (strlcpy, snprintf, etc.)",
            "Validate all array indices before access",
            "Use memory-safe abstractions when possible",
            "Enable stack protectors (-fstack-protector-all)"
        ],
        "Input Validation": [
            "Validate all external input before use",
            "Use allowlists rather than denylists",
            "Check for integer overflow in size calculations",
            "Implement defense in depth with multiple validation layers"
        ]
    }
    return recommendations.get(category, [
        "Review code for security implications",
        "Follow secure coding guidelines",
        "Use static analysis tools",
        "Consider threat modeling for this component"
    ])


def generate_security_report(errors_found):
    """
    Generate a security analysis report for found errors.
    
    Args:
        errors_found: List of dicts with error information
        
    Returns:
        Formatted security report string
    """
    if not errors_found:
        return "No security-related compiler errors detected."
    
    report = []
    report.append("=" * 60)
    report.append("SECURITY ANALYSIS REPORT")
    report.append("=" * 60)
    report.append("")
    
    # Group by severity
    by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for error in errors_found:
        severity = error.get("severity", "LOW")
        by_severity.get(severity, by_severity["LOW"]).append(error)
    
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if by_severity[severity]:
            report.append(f"\n[{severity}] Security Issues: {len(by_severity[severity])}")
            report.append("-" * 40)
            for error in by_severity[severity]:
                report.append(f"\n• Pattern: {error.get('pattern', 'Unknown')}")
                report.append(f"  Category: {error.get('category', 'Unknown')}")
                report.append(f"  CWE: {error.get('cwe', 'N/A')}")
                report.append(f"  Risk: {error.get('risk', 'N/A')}")
                report.append(f"  Secure Fix: {error.get('explanation', 'N/A')}")
    
    report.append("")
    report.append("=" * 60)
    report.append("GENERAL RECOMMENDATIONS")
    report.append("=" * 60)
    
    categories = set(e.get("category") for e in errors_found if e.get("category"))
    for category in categories:
        report.append(f"\n{category}:")
        for rec in get_security_recommendation(category):
            report.append(f"  • {rec}")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)


def compare_explanations(standard_explanation, security_analysis):
    """
    Compare standard explanation with security-aware explanation.
    
    Args:
        standard_explanation: Basic compiler error explanation
        security_analysis: Security analysis dict from analyze_security_implications
        
    Returns:
        Formatted comparison string
    """
    comparison = []
    comparison.append("\n" + "=" * 60)
    comparison.append("STANDARD vs SECURITY-AWARE EXPLANATION")
    comparison.append("=" * 60)
    
    comparison.append("\n📋 STANDARD EXPLANATION:")
    comparison.append("-" * 40)
    comparison.append(standard_explanation)
    
    if security_analysis:
        comparison.append("\n🔒 SECURITY-AWARE EXPLANATION:")
        comparison.append("-" * 40)
        comparison.append(f"Severity: {security_analysis.get('severity', 'Unknown')}")
        comparison.append(f"CWE Reference: {security_analysis.get('cwe', 'N/A')}")
        comparison.append(f"\nSecurity Risk:")
        comparison.append(f"  {security_analysis.get('risk', 'N/A')}")
        comparison.append(f"\nSecure Fix:")
        comparison.append(f"  {security_analysis.get('explanation', 'N/A')}")
        comparison.append(f"\n⚠️  Warning Against Insecure Fixes:")
        comparison.append(f"  {security_analysis.get('insecure_fix_warning', 'N/A')}")
    else:
        comparison.append("\nℹ️  No specific security concerns identified for this error.")
        comparison.append("   Standard explanation applies.")
    
    comparison.append("\n" + "=" * 60)
    
    return "\n".join(comparison)
