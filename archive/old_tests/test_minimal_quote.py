#!/usr/bin/env python3
"""
Test script to create a quote with minimal fields and see if Quoter's native 
Pipedrive integration works automatically.
"""

import requests
import json
from quoter import get_access_token, get_quote_required_fields

def test_minimal_quote():
    """Test creating a quote with only essential fields."""
    
    print("🧪 Testing Minimal Quote Creation")
    print("=" * 50)
    print("Goal: See if Quoter's native Pipedrive integration works automatically")
    print()
    
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return
    
    print(f"✅ Got access token: {access_token[:20]}...")
    
    # Get required fields (template and currency only)
    required_fields = get_quote_required_fields(access_token)
    if not required_fields:
        print("❌ Failed to get required fields")
        return
    
    print(f"✅ Got template ID: {required_fields['template_id']}")
    print(f"✅ Got currency: {required_fields['currency_abbr']}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Test with organization 3465 (Blue Owl Capital-2096)
    test_deal_id = "2096"
    test_org_name = "Blue Owl Capital"
    
    print(f"\n🎯 Testing with Deal ID: {test_deal_id}")
    print(f"🎯 Organization: {test_org_name}")
    
    # Create quote with ONLY essential fields
    quote_data = {
        "template_id": required_fields["template_id"],
        "currency_abbr": required_fields["currency_abbr"],
        "pipedrive_deal_id": test_deal_id,
        "status": "draft"
    }
    
    print(f"\n📤 Sending minimal quote data:")
    print(f"   Template ID: {required_fields['template_id']}")
    print(f"   Currency: {required_fields['currency_abbr']}")
    print(f"   Pipedrive Deal ID: {test_deal_id}")
    print(f"   Status: draft")
    print()
    print("❌ NOT including:")
    print("   - contact_id")
    print("   - name/title")
    print("   - organization_name")
    print("   - number")
    print()
    print("🎯 Hypothesis: Quoter should auto-populate everything from Pipedrive")
    
    try:
        print(f"\n📡 Creating quote...")
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json=quote_data,
            headers=headers,
            timeout=10
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            quote_id = data.get("id")
            
            if quote_id:
                print(f"✅ Successfully created quote {quote_id}")
                print(f"📋 Quote data:")
                print(json.dumps(data, indent=2))
                
                print(f"\n🔍 Key fields to check:")
                print(f"   - pipedrive_deal_id: {data.get('pipedrive_deal_id', 'NOT SET')}")
                print(f"   - name: {data.get('name', 'NOT SET')}")
                print(f"   - number: {data.get('number', 'NOT SET')}")
                print(f"   - contact_id: {data.get('contact_id', 'NOT SET')}")
                
                print(f"\n🎯 Next steps:")
                print(f"   1. Check this quote in Quoter UI")
                print(f"   2. See if contact/org data auto-populated")
                print(f"   3. Check if deal association is working")
                
                return data
            else:
                print(f"❌ No quote ID in response: {data}")
                return None
        else:
            print(f"❌ Failed to create quote: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    test_minimal_quote()
