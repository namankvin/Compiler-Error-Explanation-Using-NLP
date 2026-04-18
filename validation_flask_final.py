import json
from unittest.mock import patch
from web_app import app

def run_test():
    client = app.test_client()
    
    # 1. Code producing warnings + an error
    # - "void main" is often a warning
    # - "int x" without semicolon is an error
    payload1 = {
        "code": "void main() { int x }", 
        "codecarbon": False
    }
    
    resp1 = client.post('/api/analyze', json=payload1)
    data1 = resp1.get_json()
    
    diags = data1.get('diagnostics', [])
    ignored = data1.get('meta', {}).get('ignored_warning_count', 0)
    levels = [d.get('level') for d in diags]
    
    print(f"Diagnostics Count: {len(diags)}")
    print(f"Ignored Warning Count: {ignored}")
    print(f"Levels: {levels}")
    
    # 3. Assert every returned level contains 'error'
    all_error = all('error' in str(lvl).lower() for lvl in levels) if levels else False
    print(f"Assertion (All levels are error): {all_error}")

    # 4. CodeCarbon test
    payload2 = {
        "code": "int main() { return 0; }",
        "codecarbon": True
    }
    resp2 = client.post('/api/analyze', json=payload2)
    data2 = resp2.get_json()
    cc = data2.get('meta', {}).get('codecarbon', {})
    
    print(f"CodeCarbon - Requested: {cc.get('requested')}, Enabled: {cc.get('enabled')}, Available: {cc.get('available')}")

if __name__ == '__main__':
    # Mocking CodeCarbon to avoid hardware/permission issues during validation
    with patch('codecarbon.EmissionsTracker'):
        run_test()
