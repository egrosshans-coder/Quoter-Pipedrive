#!/usr/bin/env python3
"""
Test script to create a draft quote using the webhook system
This will create a real draft quote in Quoter with the dual URL system
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_webhook_quote():
    """Create a test quote using the webhook system"""
    
    print("🧪 TESTING WEBHOOK QUOTE CREATION")
    print("=" * 50)
    
    # Test data using real deal 2536 (ZZ19)
    test_data = {
        "deal_id": "2536",
        "organization_name": "ZZ19-Org-2536",
        "person_name": "ZZ19 Lastname",
        "person_email": "zz19@gmail.com",
        "deal_title": "ZZ19 Deal 2536",
        "template_key": "floating-video"
    }
    
    print(f"📋 Test Data:")
    print(f"   Deal ID: {test_data['deal_id']}")
    print(f"   Organization: {test_data['organization_name']}")
    print(f"   Person: {test_data['person_name']}")
    print(f"   Template: {test_data['template_key']}")
    
    # Create webhook payload
    webhook_payload = {
        "meta": {
            "v": 2,
            "action": "updated",
            "object": "organization",
            "id": 999999,
            "domain": "tlciscreative"
        },
        "current": {
            "id": 999999,
            "name": test_data['organization_name'],
            "15034cf07d05ceb15f0a89dcbdcc4f596348584e": test_data['deal_id'],  # Deal ID field
            "owner_id": {
                "value": 12345,
                "name": "Maurice Capillaire"
            }
        }
    }
    
    print(f"\n🚀 Sending webhook to create draft quote...")
    print(f"   Webhook URL: http://localhost:5000/webhook")
    print(f"   Payload: {webhook_payload}")
    
    try:
        # Send webhook to local webhook handler
        response = requests.post(
            "http://localhost:5000/webhook",
            json=webhook_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"✅ SUCCESS: Webhook sent successfully!")
            print(f"   Response: {response.text}")
            
            print(f"\n🔗 Next Steps:")
            print(f"   1. Go to: https://tlciscreative.quoter.com/admin/quotes/")
            print(f"   2. Look for a new draft quote with title containing 'ZZ19 Deal 2536'")
            print(f"   3. Check the cover letter for both URL buttons")
            print(f"   4. Test the Web View and PDF Download links")
            
        else:
            print(f"❌ FAILED: Webhook request failed")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Could not connect to webhook handler")
        print(f"   Make sure the webhook handler is running at http://localhost:5000")
        print(f"   Start it with: python webhook_handler.py")
        
    except Exception as e:
        print(f"❌ ERROR: Exception during webhook test")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    return True

if __name__ == "__main__":
    try:
        test_webhook_quote()
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
