#!/usr/bin/env python3
"""
Test script to create a draft quote using the webhook handler with "Basic" template.
This simulates a Pipedrive webhook with the proper template selection.
"""

import requests
import json
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import create_comprehensive_quote_from_pipedrive

def test_basic_template_quote():
    """
    Test creating a quote with the "Basic" template using the webhook handler logic.
    """
    print("🧪 Testing Basic Template Quote Creation")
    print("=" * 60)
    
    # Mock organization data (simulating Pipedrive webhook)
    organization_data = {
        "id": "9999",
        "name": "Test-Basic-Template-9999",
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": "9999"  # Deal ID field
    }
    
    # Mock deal data with "Basic" template selected (enum value 441)
    deal_data = {
        "id": "9999",
        "title": "Test Basic Template Deal",
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": "9999",  # Deal ID field
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": "441"   # Template field - Basic template
    }
    
    print(f"📋 Organization: {organization_data['name']}")
    print(f"📋 Deal: {deal_data['title']}")
    print(f"📋 Template: Basic (enum: 441)")
    print()
    
    try:
        # Create the quote using the same function the webhook uses
        quote_data = create_comprehensive_quote_from_pipedrive(organization_data, deal_data)
        
        if quote_data:
            print("✅ Quote created successfully!")
            print(f"   Quote ID: {quote_data.get('id')}")
            print(f"   Quote Name: {quote_data.get('name', 'N/A')}")
            print(f"   Quote Number: {quote_data.get('number', 'N/A')}")
            print(f"   Template ID: {quote_data.get('template_id', 'N/A')}")
            print()
            print("🎯 Check Quoter to see if the Basic template was applied!")
            return True
        else:
            print("❌ Quote creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating quote: {e}")
        return False

def test_webhook_endpoint():
    """
    Test the webhook endpoint directly with Basic template.
    """
    print("🌐 Testing Webhook Endpoint with Basic Template")
    print("=" * 60)
    
    # Webhook payload with Basic template (enum 441)
    webhook_payload = {
        "{{organization.id}}": "9999",
        "{{organization.name}}": "Test-Basic-Template-9999",
        "454a3767bce03a880b31d78a38c480d6870e0f1b": "289",  # QBO Status
        "{{organization.454a3767bce03a880b31d78a38c480d6870e0f1b}}": "289"
    }
    
    try:
        response = requests.post(
            "http://localhost:10000/webhook/pipedrive/organization",
            json=webhook_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📡 Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                print("✅ Webhook test successful!")
                print(f"   Quote ID: {data.get('quote_id')}")
                return True
            else:
                print(f"⚠️ Webhook returned: {data}")
                return False
        else:
            print(f"❌ Webhook failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Basic Template Quote Test")
    print()
    
    # Test 1: Direct function call
    print("Test 1: Direct Quote Creation Function")
    success1 = test_basic_template_quote()
    print()
    
    # Test 2: Webhook endpoint
    print("Test 2: Webhook Endpoint")
    success2 = test_webhook_endpoint()
    print()
    
    if success1 or success2:
        print("🎉 At least one test succeeded!")
        print("Check Quoter to see if the Basic template was applied to the quote.")
    else:
        print("❌ Both tests failed")

