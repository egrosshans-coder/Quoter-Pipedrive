#!/usr/bin/env python3
"""
Test script to create a draft quote using deal 2530 with "Basic" template.
This fetches real deal data from Pipedrive and tests the webhook.
"""

import sys
import os
import json
import requests

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipedrive import get_deal_by_id, get_organization_by_id
from quoter import create_comprehensive_quote_from_pipedrive

def test_deal_2530_basic_template():
    """
    Test creating a quote with deal 2530 and Basic template.
    """
    print("🧪 Testing Deal 2530 with Basic Template")
    print("=" * 60)
    
    deal_id = "2530"
    
    try:
        # Fetch real deal data from Pipedrive
        print(f"📋 Fetching deal {deal_id} from Pipedrive...")
        deal_data = get_deal_by_id(deal_id)
        
        if not deal_data:
            print(f"❌ Deal {deal_id} not found in Pipedrive")
            return False
        
        print(f"✅ Found deal: {deal_data.get('title', 'N/A')}")
        
        # Get organization ID from deal
        org_id = deal_data.get('org_id', {}).get('value') if isinstance(deal_data.get('org_id'), dict) else deal_data.get('org_id')
        
        if not org_id:
            print(f"❌ No organization ID found in deal {deal_id}")
            return False
        
        print(f"📋 Organization ID: {org_id}")
        
        # Fetch organization data
        print(f"📋 Fetching organization {org_id} from Pipedrive...")
        org_data = get_organization_by_id(org_id)
        
        if not org_data:
            print(f"❌ Organization {org_id} not found in Pipedrive")
            return False
        
        org_name = org_data.get('name', 'Unknown Organization')
        print(f"✅ Found organization: {org_name}")
        
        # Add Basic template selection to deal data (enum value 441)
        deal_data['42ab0c919271cb24f3587f0b01ea2af166019c8d'] = '441'  # Template field - Basic template
        
        # Prepare organization data for quote creation
        organization_data = {
            "id": str(org_id),
            "name": org_name,
            "15034cf07d05ceb15f0a89dcbdcc4f596348584e": deal_id  # Deal ID field
        }
        
        print(f"📋 Template: Basic (enum: 441)")
        print()
        
        # Create the quote using the same function the webhook uses
        print("🎯 Creating quote with Basic template...")
        quote_data = create_comprehensive_quote_from_pipedrive(organization_data, deal_data)
        
        if quote_data:
            print("✅ Quote created successfully!")
            print(f"   Quote ID: {quote_data.get('id')}")
            print(f"   Quote Name: {quote_data.get('name', 'N/A')}")
            print(f"   Quote Number: {quote_data.get('number', 'N/A')}")
            print(f"   Template ID: {quote_data.get('template_id', 'N/A')}")
            print(f"   Contact ID: {quote_data.get('person', {}).get('public_id', 'N/A')}")
            print()
            print("🎯 Check Quoter to see if the Basic template was applied!")
            print("   The quote should have:")
            print("   ✅ Basic template cover page")
            print("   ✅ Basic template cover letter") 
            print("   ✅ Basic template terms & conditions")
            print("   ❌ No line items (need to be added manually)")
            return True
        else:
            print("❌ Quote creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_webhook_with_real_data():
    """
    Test the webhook endpoint with real deal 2530 data.
    """
    print("🌐 Testing Webhook Endpoint with Real Deal 2530")
    print("=" * 60)
    
    try:
        # Fetch real deal data first
        deal_data = get_deal_by_id("2530")
        if not deal_data:
            print("❌ Deal 2530 not found")
            return False
        
        org_id = deal_data.get('org_id', {}).get('value') if isinstance(deal_data.get('org_id'), dict) else deal_data.get('org_id')
        org_data = get_organization_by_id(org_id)
        org_name = org_data.get('name', 'Unknown Organization')
        
        # Webhook payload with real data
        webhook_payload = {
            "{{organization.id}}": str(org_id),
            "{{organization.name}}": org_name,
            "454a3767bce03a880b31d78a38c480d6870e0f1b": "289",  # QBO Status
            "{{organization.454a3767bce03a880b31d78a38c480d6870e0f1b}}": "289"
        }
        
        print(f"📋 Organization: {org_name} (ID: {org_id})")
        print(f"📋 Deal: 2530")
        print()
        
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
    print("🚀 Starting Deal 2530 Basic Template Test")
    print()
    
    # Test 1: Direct function call with real data
    print("Test 1: Direct Quote Creation with Real Deal Data")
    success1 = test_deal_2530_basic_template()
    print()
    
    # Test 2: Webhook endpoint with real data
    print("Test 2: Webhook Endpoint with Real Data")
    success2 = test_webhook_with_real_data()
    print()
    
    if success1 or success2:
        print("🎉 At least one test succeeded!")
        print("Check Quoter to see if the Basic template was applied to the quote.")
    else:
        print("❌ Both tests failed")

