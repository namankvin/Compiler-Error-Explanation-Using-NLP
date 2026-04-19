import json
from unittest.mock import patch

# Mock codecarbon
with patch('codecarbon.EmissionsTracker') as MockTracker:
    instance = MockTracker.return_value
    instance.start.return_value = None
    instance.stop.return_value = 0.001
    
    from web_app import app

    def run_test():
        client = app.test_client()
        
        # Test 1
        payload1 = {"code": "void main() { int x }", "codecarbon": False}
        data1 = client.post('/api/analyze', json=payload1).get_json()
        diags = data1.get('diagnostics', [])
        levels = [d.get('level') for d in diags]
        
        print(f"Test 1 - Success: {data1.get('success')}, Diags: {len(diags)}, Ignored: {data1.get('meta', {}).get('ignored_warning_count')}")
        print(f"Levels: {levels}")

        # Test 2
        payload2 = {"code": "int main() { return 0; }", "codecarbon": True}
        data2 = client.post('/api/analyze', json=payload2).get_json()
        cc = data2.get('meta', {}).get('codecarbon', {})
        print(f"Test 2 - Requested: {cc.get('requested')}, Enabled: {cc.get('enabled')}, Available: {cc.get('available')}")
        print(f"Has Tracking: {'tracking' in cc}")

        # The check requested: all returned diagnostic levels contain 'error'
        # In actual run, levels was [None], let's check why.
        # But for the summary, we follow the execution results.
        all_error = all(l == 'error' for l in levels)
        print(f"PASS: {all_error}" if all_error else "FAIL: Some levels not 'error'")

    if __name__ == '__main__':
        run_test()
