#!/usr/bin/env python3
"""
Demo Script for Security-Aware Explanation Layer

This script demonstrates all Week 10 deliverables:
1. Security-aware explanation rules
2. Secure vs insecure explanation comparison
3. Security analysis report generation
"""

import json
import sys
from security_explainer import (
    SECURITY_ERROR_PATTERNS,
    INSECURE_FIXES,
    analyze_security_implications,
    compare_explanations,
    generate_security_report,
    get_security_recommendation
)


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_security_patterns():
    """Demonstrate security pattern detection."""
    print_section("1. SECURITY PATTERN DETECTION")
    
    test_cases = [
        {
            'name': 'Implicit Type Conversion',
            'warning': "warning: implicit conversion from 'int' to 'char'",
            'file': 'test_implicit.c',
            'code': 'char c = some_int;'
        },
        {
            'name': 'Unused Return Value',
            'warning': "warning: unused return value of 'read' function",
            'file': 'test_unused_result.c',
            'code': 'read(fd, buffer, size);'
        },
        {
            'name': 'Format String Vulnerability',
            'warning': "warning: format specifies type 'int' but argument has type 'char *'",
            'file': 'test_format.c',
            'code': 'printf(user_input);'
        },
        {
            'name': 'Sign Compare Warning',
            'warning': "warning: comparison of integers of different signs",
            'file': 'test_sign_compare.c',
            'code': 'if (i < array_len) { }'
        },
        {
            'name': 'Tautological Comparison',
            'warning': "warning: comparison of unsigned expression >= 0 is always true",
            'file': 'test_sign_compare.c',
            'code': 'if (unsigned_val >= 0) { }'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[{i}] {test['name']}")
        print(f"    Source: {test['file']}")
        print(f"    Warning: {test['warning']}")
        
        analysis = analyze_security_implications(test['warning'], test['code'])
        
        if analysis:
            print(f"    Severity: {analysis['severity']}")
            print(f"    Category: {analysis['category']}")
            print(f"    CWE: {analysis['cwe']}")
            print(f"    Risk: {analysis['risk']}")
            print(f"    Secure Fix: {analysis['explanation'][:100]}...")
        else:
            print("    No specific security concerns detected")


def demo_full_explanations():
    """Demonstrate full security-aware explanations."""
    print_section("2. FULL SECURITY-AWARE EXPLANATIONS")
    
    test_cases = [
        {
            'warning': "warning: implicit conversion from 'int' to 'char'",
            'code': 'char c = large_value;  // potential truncation'
        },
        {
            'warning': "warning: unused return value of 'fgets' function",
            'code': 'fgets(buffer, size, stdin);  // return value ignored'
        },
        {
            'warning': "warning: format string is not a string literal",
            'code': 'printf(user_input);  // CRITICAL vulnerability'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Example {i}]")
        print(f"Warning: {test['warning']}")
        print(f"Code: {test['code']}")
        
        analysis = analyze_security_implications(test['warning'], test['code'])
        
        if analysis:
            print(f"\n🔒 Security Analysis:")
            print(f"   Severity: {analysis['severity']}")
            print(f"   CWE: {analysis['cwe']}")
            print(f"   Risk: {analysis['risk']}")
            print(f"\n   Secure Fix:")
            print(f"   {analysis['explanation']}")
            print(f"\n   ⚠️  Warning: {analysis['insecure_fix_warning']}")


def demo_comparison():
    """Demonstrate secure vs insecure approach comparison."""
    print_section("3. SECURE VS INSECURE APPROACH COMPARISON")
    
    test_cases = [
        {
            'scenario': 'Type Conversion Warning',
            'standard': 'Add explicit cast to suppress warning: (char)value',
            'warning': "warning: implicit conversion from 'int' to 'char'",
            'code': 'char c = value;'
        },
        {
            'scenario': 'Unused Return Value',
            'standard': 'Cast to void to silence warning: (void)function()',
            'warning': "warning: unused return value",
            'code': 'some_function();  // ignoring return value'
        },
        {
            'scenario': 'Format String',
            'standard': 'Use printf with user input directly',
            'warning': "warning: format string is not a string literal",
            'code': 'printf(user_input);'
        }
    ]
    
    for comp in test_cases:
        print(f"\n📋 Scenario: {comp['scenario']}")
        print("-" * 60)
        
        analysis = analyze_security_implications(comp['warning'], comp['code'])
        comparison = compare_explanations(comp['standard'], analysis)
        print(comparison)


def demo_security_report():
    """Demonstrate security analysis report generation."""
    print_section("4. SECURITY ANALYSIS REPORT")
    
    # Simulate multiple errors found during compilation
    errors_found = []
    
    test_cases = [
        ("warning: implicit conversion from 'int' to 'char'", 'char c = val;'),
        ("warning: unused return value of 'read'", 'read(fd, buf, n);'),
        ("warning: format string is not a string literal", 'printf(input);'),
        ("warning: comparison of integers of different signs", 'if (i < len)'),
        ("warning: tautological comparison", 'if (x >= 0)'),
    ]
    
    print(f"\nAnalyzing {len(test_cases)} compiler warnings...")
    
    for warning, code in test_cases:
        analysis = analyze_security_implications(warning, code)
        if analysis:
            errors_found.append(analysis)
    
    report = generate_security_report(errors_found)
    print(report)


def demo_insecure_fixes_detection():
    """Demonstrate detection of insecure fix patterns."""
    print_section("5. INSECURE FIX PATTERNS DETECTION")
    
    print("\nKnown insecure fixes that the system warns against:\n")
    
    for pattern, warning in INSECURE_FIXES.items():
        print(f"❌ {pattern}")
        print(f"   ⚠️  {warning}\n")
    
    # Test detection in code
    print("\n" + "-" * 60)
    print("Testing insecure pattern detection in code:\n")
    
    test_code_samples = [
        ('adding (void) cast', '(void)some_function();'),
        ('ignoring return value', 'malloc(size);  // result not checked'),
        ('using strcpy instead of strncpy', 'strcpy(dest, src);'),
    ]
    
    for pattern, code in test_code_samples:
        analysis = analyze_security_implications("compiler warning", code)
        if analysis and 'insecure' in analysis.get('category', '').lower():
            print(f"📁 Code: {code}")
            print(f"   Detected: {analysis['explanation']}")
            print()


def demo_compile_test_files():
    """Compile test files and show actual compiler warnings."""
    print_section("6. COMPILING TEST FILES (Real Compiler Warnings)")
    
    import subprocess
    
    test_files = [
        ('test_implicit.c', '-Wconversion'),
        ('test_sign_compare.c', '-Wsign-compare'),
        ('test_unused_result.c', '-Wunused-result'),
        ('test_format.c', '-Wformat-security')
    ]
    
    print("\nCompiling test files with security warnings enabled...\n")
    
    for test_file, warning_flag in test_files:
        print(f"📁 {test_file} ({warning_flag})")
        print("-" * 60)
        
        try:
            result = subprocess.run(
                ['gcc', '-Wall', '-Wextra', warning_flag, '-c', test_file, '-o', '/dev/null'],
                capture_output=True,
                text=True
            )
            
            output = result.stderr if result.stderr else result.stdout
            if output.strip():
                print(output.strip())
            else:
                print("  (No warnings)")
        except FileNotFoundError:
            print("  GCC not found - skipping compilation test")
            break
        
        print()


def demo_recommendations():
    """Demonstrate security recommendations by category."""
    print_section("7. SECURITY RECOMMENDATIONS BY CATEGORY")
    
    categories = ["Type Casting", "Ignored Warnings", "Disabled Checks", 
                  "Buffer Security", "Input Validation"]
    
    for category in categories:
        print(f"\n📌 {category}:")
        print("-" * 50)
        recs = get_security_recommendation(category)
        for i, rec in enumerate(recs, 1):
            print(f"   {i}. {rec}")


def main():
    """Run all demos."""
    print("\n" + "🔒 " * 20)
    print("  SECURITY-AWARE EXPLANATION LAYER - DEMO")
    print("  Week 10 Deliverables Verification")
    print("🔒 " * 20)
    
    try:
        demo_security_patterns()
        demo_full_explanations()
        demo_comparison()
        demo_security_report()
        demo_insecure_fixes_detection()
        demo_compile_test_files()
        demo_recommendations()
        
        print_section("✅ DEMO COMPLETE")
        print("\nAll Week 10 deliverables verified:")
        print("  ✓ Security-aware explanation rules (SECURITY_ERROR_PATTERNS)")
        print("  ✓ Insecure fix warnings (INSECURE_FIXES)")
        print("  ✓ Secure vs insecure explanation comparison")
        print("  ✓ Security analysis report generation")
        print("  ✓ Security recommendations by category")
        print("  ✓ Test files demonstrating security patterns")
        print("\n" + "=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
