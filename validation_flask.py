import json
from web_app import app

def run_test():
    client = app.test_client()
    
    # Test 1: Errors and Warnings (CodeCarbon False)
    # Sample code: int main() { int x } // Missing semicolon (Error)
    # Using 'void main' often triggers warnings in modern compilers, 
    # but we want one warning and one error specifically.
    # Let's try: 'void main() { int x; }' where void main might be a warning and we'll add an error too.
    # Or just use the known snippet: 'int main() { char* p = 10; return 0 }'
    # 1. char* p = 10; -> error (invalid conversion)
    # 2. missing semicolon at end -> error
    # Let's use a simpler one for predictable diagnostics.
    
    payload1 = {
        "code": "void main() { int x }", 
        "codecarbon": False
    }
    
    resp1 = client.post('/api/analyze', json=payload1)
    data1 = resp1.get_json()
    
    success1 = data1.get('success')
    diags = data1.get('diagnostics', [])
    ignored = data1.get('meta', {}).get('ignored_warning_count', 0)
    levels = [d.get('level') for d in diags]
    
    print(f"Test 1 - Success: {success1}, DiagCount: {len(diags)}, Ignored: {ignored}")
    print(f"Levels: {levels}")

    # Test 2: CodeCarbon True
    payload2 = {
        "code": "int main() { return 0; }",
        "codecarbon": True
    }
    resp2 = client.post('/api/analyze', json=payload2)
    data2 = resp2.get_json()
    cc = data2.get('meta', {}).get('codecarbon', {})
    
    print(f"Test 2 - CC Requested: {cc.get('requested')}, Enabled: {cc.get('enabled')}, Available: {cc.get('available')}")
    print(f"Tracking exists: {'tracking' in cc}")

    # Assertion
    all_error = all(lvl == 'error' for lvl in levels)
    print(f"PASS: {all_error}" if all_error else "FAIL: Mixed levels")

if __name__ == '__main__':
    run_test()
