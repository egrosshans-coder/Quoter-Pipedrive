#!/usr/bin/env python3
"""
Test with Existing Webhook Data

Simulate the exact webhook payload from September 18 to debug the data extraction issues.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quoter import create_comprehensive_quote_from_pipedrive

def test_with_existing_webhook_data():
    """Test with the exact webhook payload from logs."""
    
    print("🧪 TESTING WITH EXISTING WEBHOOK DATA")
    print("=" * 60)
    print("Using exact payload from September 18 logs")
    print()
    
    # Exact webhook payload from your logs
    webhook_organization_data = {
        "{{organization.id}}": "3913",
        "{{organization.454a3767bce03a880b31d78a38c480d6870e0f1b}}": "QBO-SubCust",
        "{{organization.name}}": "ZZ28-Org-2571",
        "{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}": "Floating Video",
        "{{deal.title}}": "ZZ28-Deal",
        "{{deal.id}}": "2571",
        "{{deal.person_name}}": "ZZ28 My Lastname",
        "{{person.email}}": "zz28@gmail.com"
    }
    
    # Create the hybrid organization data (like webhook_handler.py does)
    normalized_org_data = {
        # Simple format for quoter.py compatibility
        "id": "3913",
        "name": "ZZ28-Org-2571", 
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": "2571",
        # Keep webhook fields for optimization
        "{{deal.person_name}}": webhook_organization_data.get('{{deal.person_name}}'),
        "{{deal.title}}": webhook_organization_data.get('{{deal.title}}'),
        "{{deal.id}}": webhook_organization_data.get('{{deal.id}}'),
        "{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}": webhook_organization_data.get('{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}'),
        "{{person.email}}": webhook_organization_data.get('{{person.email}}')
    }
    
    # Mock deal data (like webhook_handler.py creates)
    deal_data = {
        'id': 2571,
        'title': 'ZZ28-Deal',
        '42ab0c919271cb24f3587f0b01ea2af166019c8d': 'Floating Video'
    }
    
    print("📦 NORMALIZED ORG DATA:")
    import json
    print(json.dumps(normalized_org_data, indent=2))
    print()
    
    print("📋 DEAL DATA:")
    print(json.dumps(deal_data, indent=2))
    print()
    
    print("🚀 TESTING QUOTER.PY WITH DEBUG LOGGING...")
    print("-" * 50)
    
    # Test quoter.py with the exact data structure
    result = create_comprehensive_quote_from_pipedrive(normalized_org_data, deal_data)
    
    if result:
        print(f"✅ SUCCESS: Quote created!")
        print(f"   Quote ID: {result.get('id')}")
        print(f"   URL: {result.get('url', 'N/A')}")
    else:
        print(f"❌ FAILED: No quote created")
    
    return result

if __name__ == "__main__":
    test_with_existing_webhook_data()
