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
    cc = meta.get('codecarbon', {})
    
    diagnostics_count = len(diags)
    first_diag = diags[0] if diags else {}
    has_explanation_first = 'explanation' in first_diag or 'message' in first_diag
    has_security_first = 'security_analysis' in first_diag
    codecarbon_requested = cc.get('requested', False)
    has_comparison = 'comparison' in cc
    has_with_without_runtimes = 'runtimes' in cc or ('with_codecarbon' in cc and 'without_codecarbon' in cc)

    print(f"diagnostics_count: {diagnostics_count}")
    print(f"has_explanation_first: {has_explanation_first}")
    print(f"has_security_first: {has_security_first}")
    print(f"codecarbon_requested: {codecarbon_requested}")
    print(f"has_comparison: {has_comparison}")
    print(f"has_with_without_runtimes: {has_with_without_runtimes}")
