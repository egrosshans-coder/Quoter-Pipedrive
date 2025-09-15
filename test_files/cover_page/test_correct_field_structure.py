#!/usr/bin/env python3
"""
Test the correct field structure for Cover Letter section
"""

import requests
import json
from quoter import get_access_token
from template_mapping_enhanced import get_template_info

def test_correct_cover_letter_field():
    """Test using the correct nested field structure for Cover Letter"""
    
    print("🔍 TESTING CORRECT COVER LETTER FIELD STRUCTURE")
    print("=" * 60)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get access token")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get cover letter from template
    template_info = get_template_info("floating-video")
    cover_letter = template_info.get('cover_letter', '') if template_info else ''
    
    print(f"📝 Cover letter content:")
    print(f"Length: {len(cover_letter)} characters")
    print(f"Content preview: {cover_letter[:200]}...")
    print()
    
    # Use the correct nested field structure from DOM inspection
    quote_data = {
        "contact_id": "cont_32fYTamKMMZXCXNVFJx3qtISNIN",
        "template_id": "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG",
        "currency_abbr": "USD",
        "name": "CORRECT FIELD STRUCTURE TEST",
        "data": {
            "Quote": {
                "ip_text": cover_letter  # Correct field name from DOM inspection
            }
        }
    }
    
    print(f"📤 API Request payload:")
    print(json.dumps(quote_data, indent=2))
    print()
    
    try:
        print("🚀 Making API call with correct field structure...")
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json=quote_data,
            headers=headers,
            timeout=10
        )
        
        print(f"📥 API Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            quote_id = data.get("id")
            if quote_id:
                print(f"✅ Quote created successfully!")
                print(f"Quote ID: {quote_id}")
                print(f"Quote URL: {data.get('url', 'N/A')}")
                print()
                print("🎯 SUCCESS! This should now write to Cover Letter section!")
                print("🔗 Check the quote URL to verify the cover letter appears in the correct section")
            else:
                print("❌ No quote ID in response")
        else:
            print("❌ API call failed")
            
    except Exception as e:
        print(f"❌ Error making API call: {e}")

if __name__ == "__main__":
    test_correct_cover_letter_field()
