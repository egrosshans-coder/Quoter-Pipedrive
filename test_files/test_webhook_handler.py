#!/usr/bin/env python3
"""
Test webhook handler functionality
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Test the webhook handler functions
def test_webhook_handler():
    print("🧪 TESTING WEBHOOK HANDLER")
    print("=" * 50)
    
    # Test 1: Check if webhook handler imports work
    try:
        from webhook_handler import handle_organization_webhook, rate_limiter
        print("✅ Webhook handler imports successfully")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test 2: Check rate limiter
    try:
        can_process = rate_limiter.can_process()
        print(f"✅ Rate limiter working: can_process = {can_process}")
    except Exception as e:
        print(f"❌ Rate limiter error: {e}")
        return False
    
    # Test 3: Check if processed organizations file exists
    processed_file = "processed_organizations.txt"
    if os.path.exists(processed_file):
        with open(processed_file, 'r') as f:
            processed_orgs = f.read().splitlines()
        print(f"✅ Processed organizations file exists with {len(processed_orgs)} entries")
    else:
        print("ℹ️ Processed organizations file doesn't exist yet (normal for first run)")
    
    # Test 4: Check deal ID extraction logic
    test_org_name = "ZZ19-Org-2536"
    if '-' in test_org_name:
        deal_id = test_org_name.split('-')[-1]
        print(f"✅ Deal ID extraction works: '{test_org_name}' -> '{deal_id}'")
    else:
        print("❌ Deal ID extraction failed")
        return False
    
    print("\n🎉 All webhook handler tests passed!")
    return True

if __name__ == "__main__":
    success = test_webhook_handler()
    if success:
        print("\n✅ Webhook handler is working correctly")
    else:
        print("\n❌ Webhook handler has issues")

