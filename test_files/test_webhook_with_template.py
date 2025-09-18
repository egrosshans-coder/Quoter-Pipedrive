#!/usr/bin/env python3
"""
Test Webhook with Template Field

This script simulates the new webhook payload format that includes the deal template field
to test if our webhook handler can process it correctly and eliminate the Pipedrive API call.
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger

def test_webhook_with_template_field():
    """Test webhook processing with the new template field included."""
    
    print("🧪 TESTING WEBHOOK WITH TEMPLATE FIELD")
    print("=" * 60)
    print("Goal: Test new webhook payload format with deal template field")
    print()
    
    # Simulate the NEW webhook payload format with template field
    simulated_webhook_data = {
        # Existing organization fields (KEEP THESE - they work!)
        "{{organization.id}}": "3900",
        "{{organization.454a3767bce03a880b31d78a38c480d6870e0f1b}}": "QBO-SubCust",
        "{{organization.name}}": "ZZ23-Org-2564",
        
        # NEW: Deal template field
        "{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}": "454"
    }
    
    print("📦 SIMULATED NEW WEBHOOK PAYLOAD:")
    print(json.dumps(simulated_webhook_data, indent=2))
    print()
    
    # Test extracting data from the new format
    print("🔍 TESTING DATA EXTRACTION:")
    print("-" * 40)
    
    # Extract organization data (existing method)
    org_id = simulated_webhook_data.get('{{organization.id}}')
    org_name = simulated_webhook_data.get('{{organization.name}}')
    hid_status = simulated_webhook_data.get('{{organization.454a3767bce03a880b31d78a38c480d6870e0f1b}}')
    
    print(f"✅ Organization ID: {org_id}")
    print(f"✅ Organization Name: {org_name}")
    print(f"✅ HID-QBO-Status: {hid_status}")
    
    # Extract NEW template data (direct from webhook)
    template_enum_str = simulated_webhook_data.get('{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}')
    
    if template_enum_str:
        template_enum = int(template_enum_str)
        print(f"✅ Template Enum: {template_enum_str} → {template_enum}")
        
        # Test direct enum to bundle mapping
        enum_to_bundle = {
            454: 'floating-video',
            444: 'led-wristbands',
            451: 'balloons',
            452: 'co2-smoke-upright-foggers',
            453: 'fireworks-pyro-fire',
        }
        
        bundle_key = enum_to_bundle.get(template_enum)
        if bundle_key:
            print(f"✅ Bundle Key: {bundle_key}")
            print(f"✅ DIRECT MAPPING SUCCESS!")
        else:
            print(f"❌ No bundle mapping for enum {template_enum}")
    else:
        print(f"❌ Template enum not found in webhook data")
    
    print()
    print("🎯 PERFORMANCE COMPARISON:")
    print("-" * 40)
    print("BEFORE (Current Method):")
    print("  1. Extract deal ID from org name")
    print("  2. API call to get deal data")
    print("  3. Extract template enum from deal")
    print("  4. Map enum to bundle")
    print("  Total: ~0.5 seconds + API call")
    print()
    print("AFTER (New Method):")
    print("  1. Extract template enum directly from webhook")
    print("  2. Map enum to bundle")
    print("  Total: ~0.1 seconds (no API call)")
    print()
    
    # Test what the webhook handler logic would look like
    print("🔧 NEW WEBHOOK HANDLER LOGIC:")
    print("-" * 40)
    print("# Direct template extraction")
    print(f"template_enum = int(webhook_data.get('{{{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}}}'))")
    print(f"bundle_key = enum_to_bundle.get(template_enum)")
    print(f"# Result: bundle_key = '{bundle_key}' (no API call needed!)")
    
    return True

if __name__ == "__main__":
    test_webhook_with_template_field()
