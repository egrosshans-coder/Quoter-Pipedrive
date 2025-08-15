#!/usr/bin/env python3
"""
Test script to simulate sending a webhook payload to our custom webhook server.
This will test the deal association logic without needing Quoter to actually send webhooks.
"""

import requests
import json

def test_webhook():
    """Test our custom webhook with simulated Quoter data."""
    
    # Simulate the webhook payload that Quoter would send
    # Based on the Zapier webhook data you provided earlier
    test_webhook_data = {
        "event_type": "quote.created",
        "id": "quot_316zYtlHF4enuMG8eDmQCY0JVtO",
        "number": "PD-2096",
        "organization": "Blue Owl Capital-2096",
        "person": {
            "first_name": "Robert",
            "last_name": "Lee"
        },
        "status": "draft",
        "timestamp": "1754856000"
    }
    
    webhook_url = "http://localhost:5001/webhook/quoter"
    
    print("🧪 Testing Custom Webhook Server")
    print("=" * 50)
    print(f"📡 Sending test webhook to: {webhook_url}")
    print(f"📋 Test data: {json.dumps(test_webhook_data, indent=2)}")
    print()
    
    try:
        # Send POST request to our webhook
        response = requests.post(
            webhook_url,
            json=test_webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print()
            print("✅ Webhook processed successfully!")
            print(f"   Deal ID: {result.get('deal_id')}")
            print(f"   Organization: {result.get('organization')}")
            
            if result.get('manual_steps_required'):
                print("   Manual steps required:")
                for step in result['manual_steps_required']:
                    print(f"     • {step}")
        else:
            print("❌ Webhook failed")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to webhook server")
        print("   Make sure the webhook server is running on port 5000")
        print("   Run: python3 custom_webhook.py")
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

if __name__ == "__main__":
    test_webhook()
