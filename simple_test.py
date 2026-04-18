import json
from unittest.mock import patch
import sys

# Mock EmissionsTracker to avoid sudo/hardware issues and see default config
with patch('codecarbon.EmissionsTracker'):
    from web_app import app

    def run_test():
        client = app.test_client()
        payload = {
            "code": "int main(){return 0;}",
            "codecarbon": True,
            "security": False
        }
        
        try:
            response = client.post('/api/analyze', json=payload)
            if response.status_code == 200:
                print("HTTP Success: True")
                data = response.get_json()
                meta = data.get('meta', {})
                cc = meta.get('codecarbon', {})
                
                print(f"Requested: {cc.get('requested')}")
                print(f"Enabled: {cc.get('enabled')}")
                print(f"Available: {cc.get('available')}")
                print(f"Non-Privileged Mode: {cc.get('non_privileged_mode')}")
                print(f"Sudo Prompts Disabled: {cc.get('sudo_prompts_disabled')}")
                
                tracking = cc.get('tracking', {})
                print(f"Tracking Mode: {tracking.get('tracking_mode')}")
                print(f"CPU Estimation Mode: {tracking.get('cpu_estimation_mode')}")
            else:
                print(f"HTTP Success: False (Status {response.status_code})")
        except Exception as e:
            print(f"Error: {e}")

    if __name__ == "__main__":
        run_test()
