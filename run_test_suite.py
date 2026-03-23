#!/usr/bin/env python3
"""
Week 11 Test Suite Runner

Runs all test cases and collects compiler diagnostics for validation.
"""

import subprocess
import os
import json
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Runs test cases and collects compiler output."""
    
    def __init__(self, test_dir="test_suite"):
        self.test_dir = Path(test_dir)
        self.results = []
        self.compiler_flags = ["-Wall", "-Wextra", "-Wpedantic", "-Werror=format-security"]
        
    def run_test(self, filepath: Path) -> dict:
        """Run a single test file and collect results."""
        result = {
            "file": str(filepath),
            "category": filepath.parent.name,
            "compiler": "clang",
            "flags": self.compiler_flags,
            "stdout": "",
            "stderr": "",
            "return_code": None,
            "warnings": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            cmd = ["clang"] + self.compiler_flags + ["-c", str(filepath), "-o", "/dev/null"]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            result["return_code"] = proc.returncode
            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            
            # Parse warnings and errors
            for line in proc.stderr.split('\n'):
                if 'warning:' in line:
                    result["warnings"].append(line.strip())
                elif 'error:' in line:
                    result["errors"].append(line.strip())
                    
        except subprocess.TimeoutExpired:
            result["error"] = "Compilation timeout"
        except FileNotFoundError:
            result["error"] = "Clang compiler not found"
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def run_all_tests(self) -> list:
        """Run all tests in the test suite."""
        print("=" * 70)
        print("WEEK 11 TEST SUITE RUNNER")
        print("=" * 70)
        
        categories = ["beginner_programs", "student_errors", "edge_cases"]
        
        for category in categories:
            cat_dir = self.test_dir / category
            if not cat_dir.exists():
                print(f"\n⚠️  Category directory not found: {category}")
                continue
                
            print(f"\n📁 Running tests in: {category}")
            print("-" * 50)
            
            for test_file in sorted(cat_dir.glob("*.c")):
                print(f"  Testing: {test_file.name}")
                result = self.run_test(test_file)
                self.results.append(result)
                
                status = "✓" if result["return_code"] == 0 else "✗"
                w_count = len(result["warnings"])
                e_count = len(result["errors"])
                
                print(f"    {status} Return: {result['return_code']}, "
                      f"Warnings: {w_count}, Errors: {e_count}")
        
        return self.results
    
    def save_results(self, output_file="test_results.json"):
        """Save test results to JSON file."""
        with open(output_file, 'w') as f:
            json.dump({
                "test_run": {
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": len(self.results),
                    "categories": list(set(r["category"] for r in self.results))
                },
                "results": self.results
            }, f, indent=2)
        print(f"\n📄 Results saved to: {output_file}")
    
    def print_summary(self):
        """Print test run summary."""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["return_code"] == 0)
        failed = total - passed
        
        total_warnings = sum(len(r["warnings"]) for r in self.results)
        total_errors = sum(len(r["errors"]) for r in self.results)
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed (no errors): {passed}")
        print(f"Failed (with errors): {failed}")
        print(f"Total Warnings: {total_warnings}")
        print(f"Total Errors: {total_errors}")
        
        print("\nResults by Category:")
        categories = {}
        for r in self.results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0, "warnings": 0, "errors": 0}
            categories[cat]["total"] += 1
            if r["return_code"] == 0:
                categories[cat]["passed"] += 1
            categories[cat]["warnings"] += len(r["warnings"])
            categories[cat]["errors"] += len(r["errors"])
        
        for cat, stats in categories.items():
            print(f"\n  {cat}:")
            print(f"    Tests: {stats['total']}, Passed: {stats['passed']}")
            print(f"    Warnings: {stats['warnings']}, Errors: {stats['errors']}")


def main():
    runner = TestRunner()
    runner.run_all_tests()
    runner.save_results()
    runner.print_summary()


if __name__ == "__main__":
    main()
