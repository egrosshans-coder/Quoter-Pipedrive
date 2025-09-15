#!/usr/bin/env python3
"""
Test flat field structure for Cover Letter section
"""

import requests
import json
from quoter import get_access_token

def test_flat_field_structure():
    """Test different ways to structure the field name"""
    
    print("🔍 TESTING FLAT FIELD STRUCTURE")
    print("=" * 50)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get access token")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    cover_letter_content = "TEST FLAT FIELD - This should appear in Cover Letter section."
    
    # Test different flat field name variations
    flat_fields_to_test = [
        "ip_text",                    # Just the field name
        "Quote[ip_text]",            # Bracketed format
        "data_Quote_ip_text",        # Underscore format
        "data.Quote.ip_text",        # Dot notation as flat field
        "data[Quote][ip_text]"       # Exact bracket format
    ]
    
    for field_name in flat_fields_to_test:
        print(f"\n🧪 Testing flat field: '{field_name}'")
        
        quote_data = {
            "contact_id": "cont_32fYTamKMMZXCXNVFJx3qtISNIN",
            "template_id": "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG",
            "currency_abbr": "USD",
            "name": f"Flat Field Test - {field_name}",
            field_name: cover_letter_content
        }
        
        try:
            response = requests.post(
                "https://api.quoter.com/v1/quotes",
                json=quote_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                quote_id = data.get("id")
                quote_url = data.get("url")
                print(f"✅ SUCCESS with '{field_name}'")
                print(f"   Quote ID: {quote_id}")
                print(f"   URL: {quote_url}")
                print(f"   🔗 Check if this appears in Cover Letter section")
            else:
                print(f"❌ FAILED with '{field_name}' - Status: {response.status_code}")
                if response.status_code == 400:
                    print(f"   Error: {response.text}")
                    
        except Exception as e:
            print(f"❌ ERROR with '{field_name}': {e}")

if __name__ == "__main__":
    test_flat_field_structure()
