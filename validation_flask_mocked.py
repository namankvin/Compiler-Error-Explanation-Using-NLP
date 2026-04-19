import json
from unittest.mock import patch
import os

# Mock codecarbon before importing app
with patch('codecarbon.EmissionsTracker') as MockTracker:
    # Setup mock
    instance = MockTracker.return_value
    instance.start.return_value = None
    instance.stop.return_value = 0.001
    
    from web_app import app

    def run_test():
        client = app.test_client()
        
        # Test 1: Errors and Warnings
        payload1 = {
            "code": "void main() { int x }", 
            "codecarbon": False
        }
        resp1 = client.post('/api/analyze', json=payload1)
        data1 = resp1.get_json()
        diags = data1.get('diagnostics', [])
        # Ensure we capture levels correctly (level might be missing if parser failed)
        levels = [d.get('level', 'unknown') for d in diags]
        
        print(f"Test 1 - Success: {data1.get('success')}, DiagCount: {len(diags)}, Ignored: {data1.get('meta', {}).get('ignored_warning_count')}")
        print(f"Levels: {levels}")

        # Test 2: CodeCarbon True
        payload2 = {"code": "int main() { return 0; }", "codecarbon": True}
        resp2 = client.post('/api/analyze', json=payload2)
        data2 = resp2.get_json()
        cc = data2.get('meta', {}).get('codecarbon', {})
        
        print(f"Test 2 - CC Requested: {cc.get('requested')}, Enabled: {cc.get('enabled')}")
        print(f"Tracking exists: {'tracking' in cc}")

        # Assertion: If levels were found, they should be 'error' because we filter out warnings
        all_error = all(lvl == 'error' for lvl in levels) if levels else True
        print(f"PASS: {all_error}" if all_error else "FAIL: Mixed levels")

    if __name__ == '__main__':
        run_test()
