import json
from unittest.mock import patch
import os

# Set dummy password or skip sudo if possible for mocking
# But here we just want to see the levels. 
# The issue earlier was Levels: [None]. Let's inspect the diagnostic structure.

with patch('codecarbon.EmissionsTracker') as MockTracker:
    instance = MockTracker.return_value
    instance.start.return_value = None
    instance.stop.return_value = 0.001
    
    from web_app import app

    def run_test():
        client = app.test_client()
        
        # 1. Code producing warnings + an error
        payload1 = {
            "code": "void main() { int x }", 
            "codecarbon": False
        }
        
        resp1 = client.post('/api/analyze', json=payload1)
        data1 = resp1.get_json()
        
        diags = data1.get('diagnostics', [])
        ignored = data1.get('meta', {}).get('ignored_warning_count', 0)
        
        # The prompt asked for item['diagnostic']['level'] 
        # but the JSON structure from earlier suggested diagnostics is a list of objects.
        # Let's check keys.
        levels = []
        for d in diags:
            # Try 'level' directly or nested
            lvl = d.get('level')
            levels.append(lvl)
        
        print(f"Diagnostics Count: {len(diags)}")
        print(f"Ignored Warning Count: {ignored}")
        print(f"Levels: {levels}")
        
        # 3. Assert every returned level contains 'error'
        all_error = all(lvl == 'error' for lvl in levels) if levels else False
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
        run_test()
