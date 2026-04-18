from web_app import app
import json
from unittest.mock import patch

def run_test():
    client = app.test_client()
    payload = {
        "code": "int main(){return 0;}",
        "codecarbon": True,
        "codecarbon_compare": False,
        "security": False
    }
    
    # Mocking EmissionsTracker to allow the code to run without sudo/hardware access
    with patch('codecarbon.EmissionsTracker'):
        response = client.post('/api/analyze', json=payload)
        data = response.get_json()
        
        meta = data.get('meta', {})
        cc = meta.get('codecarbon', {})
        comparison = cc.get('comparison')
        
        if comparison is None:
            print("FAILED: comparison object missing")
            return

        print(f"comparison_enabled: {comparison.get('enabled')}")
        print(f"without_tracking_runtime_ms: {comparison.get('without_tracking_runtime_ms')}")
        print(f"with_tracking_runtime_ms: {comparison.get('with_tracking_runtime_ms')}")
        print(f"runtime_overhead_ms: {comparison.get('runtime_overhead_ms')}")

if __name__ == "__main__":
    run_test()
