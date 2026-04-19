import json
from unittest.mock import patch
from web_app import app

with patch('codecarbon.EmissionsTracker') as MockTracker:
    instance = MockTracker.return_value
    instance.start.return_value = None
    instance.stop.return_value = 0.001
    
    def run_test():
        client = app.test_client()
        payload1 = {"code": "void main() { int x }", "codecarbon": False}
        data1 = client.post('/api/analyze', json=payload1).get_json()
        diags = data1.get('diagnostics', [])
        
        # Access nested key item['diagnostic']['level']
        levels = [d.get('diagnostic', {}).get('level') for d in diags]
        ignored = data1.get('meta', {}).get('ignored_warning_count', 0)
        
        print(f"Diagnostics Count: {len(diags)}")
        print(f"Ignored Warning Count: {ignored}")
        print(f"Levels: {levels}")
        
        all_error = all(lvl == 'error' for lvl in levels) if levels else False
        print(f"Assertion (All levels are error): {all_error}")

        payload2 = {"code": "int main() { return 0; }", "codecarbon": True}
        data2 = client.post('/api/analyze', json=payload2).get_json()
        cc = data2.get('meta', {}).get('codecarbon', {})
        print(f"CodeCarbon - Requested: {cc.get('requested')}, Enabled: {cc.get('enabled')}, Available: {cc.get('available')}")

    if __name__ == '__main__':
        run_test()
