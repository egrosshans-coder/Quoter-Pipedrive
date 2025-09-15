#!/usr/bin/env python3
"""
Debug test to check if cover letter is being sent correctly in API request
"""

import requests
import json
from quoter import get_access_token
from template_mapping_enhanced import get_template_info

def test_cover_letter_api_call():
    """Test creating a quote with cover letter and log the exact API request"""
    
    print("🔍 DEBUGGING COVER LETTER API CALL")
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
    
    # Get cover letter from template
    template_info = get_template_info("floating-video")
    cover_letter = template_info.get('cover_letter', '') if template_info else ''
    
    print(f"📝 Cover letter content:")
    print(f"Length: {len(cover_letter)} characters")
    print(f"Content preview: {cover_letter[:200]}...")
    print()
    
    # Prepare quote data
    quote_data = {
        "contact_id": "cont_32fYTamKMMZXCXNVFJx3qtISNIN",  # Existing contact
        "template_id": "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG",  # Floating Video template
        "currency_abbr": "USD",
        "name": "DEBUG Cover Letter Test",
        "cover_letter": cover_letter
    }
    
    print(f"📤 API Request payload:")
    print(json.dumps(quote_data, indent=2))
    print()
    
    try:
        print("🚀 Making API call...")
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
                print("🔗 Check the quote URL to see if cover letter appears")
            else:
                print("❌ No quote ID in response")
        else:
            print("❌ API call failed")
            
    except Exception as e:
        print(f"❌ Error making API call: {e}")

if __name__ == "__main__":
    test_cover_letter_api_call()