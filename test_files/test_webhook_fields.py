#!/usr/bin/env python3
"""
Test Webhook Fields - Verify what data Quoter webhooks capture

This script helps us understand what fields are available in the webhook payload
when quotes are published in Quoter.
"""

import requests
import json
import sys
import os

def test_quoter_webhook_fields():
    """
    Test the Quoter webhook endpoint with sample data to see what fields are captured.
    """
    print("🧪 Testing Quoter Webhook Field Capture")
    print("=" * 60)
    
    # Sample webhook data based on what we expect Quoter to send
    sample_webhook_data = {
        "event": "quote.published",
        "timestamp": "2025-08-14T20:00:00Z",
        "data": {
            "id": "quot_test123",
            "name": "Test Quote for Organization",
            "number": "Q-2025-001",  # Quoter's assigned number
            "status": "published",
            "total": 1500.00,
            "currency": "USD",
            "contact_id": "cont_test456",
            "organization_name": "Test Organization",
            "created_at": "2025-08-14T19:00:00Z",
            "published_at": "2025-08-14T20:00:00Z",
            "template_id": "tmpl_test789",
            "line_items": [
                {
                    "id": "item_test123",
                    "name": "Test Service",
                    "quantity": 1,
                    "unit_price": 1500.00,
                    "total": 1500.00
                }
            ]
        }
    }
    
    print("📤 Sample Webhook Data:")
    print(json.dumps(sample_webhook_data, indent=2))
    print()
    
    # Test the webhook endpoint
    webhook_url = "http://localhost:5000/webhook/quoter/quote-published"
    
    try:
        print(f"📡 Sending test webhook to: {webhook_url}")
        print("   (Make sure webhook_handler.py is running on port 5000)")
        print()
        
        response = requests.post(
            webhook_url,
            json=sample_webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Webhook endpoint is working!")
            print("   Check the webhook_handler.py logs to see what fields were processed")
        else:
            print(f"\n❌ Webhook endpoint returned error: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection failed to {webhook_url}")
        print("   Make sure webhook_handler.py is running:")
        print("   python3 webhook_handler.py")
    except Exception as e:
        print(f"\n❌ Error testing webhook: {e}")
    
    print("\n" + "=" * 60)
    print("🔍 Next Steps:")
    print("1. Start webhook_handler.py: python3 webhook_handler.py")
    print("2. Run this test: python3 test_webhook_fields.py")
    print("3. Check webhook_handler.py logs for field processing")
    print("4. Modify sample data to test different scenarios")

if __name__ == "__main__":
    print("🚀 Webhook Field Testing Tool")
    print("=" * 60)
    
    # Test the Quoter webhook endpoint
    test_quoter_webhook_fields()
    
    print("\n🎯 Summary:")
    print("This tool helps verify what fields are captured by our webhook endpoints.")
    print("Run it while webhook_handler.py is running to see the complete data flow.")
