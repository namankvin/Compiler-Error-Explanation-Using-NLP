from web_app import app
import json
from unittest.mock import patch

def run_test():
    client = app.test_client()

    # Test 1: Security Analysis & Warnings
    payload1 = {
        "code": "void main(){char b[8]; gets(b); int x = 10 return 0;}",
        "security": True,
        "codecarbon": False
    }
    resp1 = client.post('/api/analyze', json=payload1)
    data1 = resp1.get_json()

    diags = data1.get('diagnostics', [])
    meta = data1.get('meta', {})
    ignored = meta.get('ignored_warning_count')

    print(f"Diagnostics: {len(diags)}")
    if diags:
        d = diags[0]
        # Some diag structures use 'explanation' or 'message'
        expl = d.get('explanation') or d.get('message') or ""
        print(f"First Diag Expl Length: {len(expl)}")
        # Check security_analysis field
        print(f"First Diag Security present: {'security_analysis' in d}")
    print(f"Ignored Warning Count: {ignored}")

    # Test 2: CodeCarbon
    payload2 = {
        "code": "int main(){return 0;}",
        "codecarbon": True
    }
    resp2 = client.post('/api/analyze', json=payload2)
    data2 = resp2.get_json()
    cc = data2.get('meta', {}).get('codecarbon', {})

    print(f"CC - Requested: {cc.get('requested')}, Enabled: {cc.get('enabled')}, Available: {cc.get('available')}")
    print(f"CC - NonPrivMode: {cc.get('non_privileged_mode')}")
    # Tracking/CPU estimation usually in 'tracking' or 'config'
    tracking = cc.get('tracking', {})
    print(f"TrackingMode: {tracking.get('tracking_mode')}, CPUEstimationMode: {tracking.get('cpu_estimation_mode')}")

if __name__ == "__main__":
    # Mocking to avoid blocking on password/hardware
    with patch('codecarbon.EmissionsTracker'):
        run_test()
