import json
from web_app import app
from unittest.mock import patch

with patch('codecarbon.EmissionsTracker'):
    client = app.test_client()
    payload = {
        "code": "#include <stdio.h>\nint main(){\n int x = 10\n printf(\"%d\\n\", x);\n return 0;\n}"
    }
    response = client.post('/api/analyze', json=payload)
    data = response.get_json()
    
    diags = data.get('diagnostics', [])
    meta = data.get('meta', {})
    
    # 2) First diagnostic having explanation and security_analysis
    first_diag = diags[0] if diags else {}
    has_explanation_first = 'explanation' in first_diag
    has_security_first = 'security_analysis' in first_diag
    
    # 3) meta.codecarbon.comparison keys
    cc = meta.get('codecarbon', {})
    comp = cc.get('comparison', {})
    has_without = 'without_tracking_runtime_ms' in comp
    has_with = 'with_tracking_runtime_ms' in comp

    print(f"has_explanation_first: {has_explanation_first}")
    print(f"has_security_first: {has_security_first}")
    print(f"has_comparison_keys: {has_without and has_with}")
