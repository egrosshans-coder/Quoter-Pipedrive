#!/usr/bin/env python3
"""
Test field names for Cover Letter section (not Cover Page)
"""

import requests
import json
from quoter import get_access_token

def test_cover_letter_section_fields():
    """Test field names that might write to Cover Letter section"""
    
    print("🔍 TESTING COVER LETTER SECTION FIELDS")
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
    
    cover_letter_content = "TEST COVER LETTER SECTION - This should appear in Cover Letter section, not Cover Page."
    
    # Test field names that might write to Cover Letter section
    letter_fields_to_test = [
        "cover_letter",      # Official API docs field
        "letter_content",
        "letter_text", 
        "cover_letter_content",
        "letter_body",
        "cover_text",
        "letter_section"
    ]
    
    for field_name in letter_fields_to_test:
        print(f"\n🧪 Testing Cover Letter field: '{field_name}'")
        
        quote_data = {
            "contact_id": "cont_32fYTamKMMZXCXNVFJx3qtISNIN",
            "template_id": "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG",
            "currency_abbr": "USD",
            "name": f"Cover Letter Test - {field_name}",
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
                
        except Exception as e:
            print(f"❌ ERROR with '{field_name}': {e}")

if __name__ == "__main__":
    test_cover_letter_section_fields()
