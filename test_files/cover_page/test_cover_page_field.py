#!/usr/bin/env python3
"""
Test cover_page field to see if it writes to Cover Page section
"""

import requests
import json
from quoter import get_access_token
from template_mapping_enhanced import get_template_info

def test_cover_page_field():
    """Test if cover_page field writes to Cover Page section"""
    
    print("🔍 TESTING COVER_PAGE FIELD")
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
    
    # Get cover letter content from template
    template_info = get_template_info("floating-video")
    cover_letter = template_info.get('cover_letter', '') if template_info else ''
    
    print(f"📝 Cover letter content:")
    print(f"Length: {len(cover_letter)} characters")
    print(f"Content preview: {cover_letter[:200]}...")
    print()
    
    # Create quote with cover_page field (not documented but might work)
    quote_data = {
        "contact_id": "cont_32fYTamKMMZXCXNVFJx3qtISNIN",
        "template_id": "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG",
        "currency_abbr": "USD",
        "name": "COVER PAGE FIELD TEST",
        "cover_page": cover_letter  # Testing cover_page field name
    }
    
    print(f"📤 API Request payload:")
    print(json.dumps(quote_data, indent=2))
    print()
    
    try:
        print("🚀 Creating quote with cover_page field...")
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
                print("🎯 This should write to Cover Page section!")
                print("🔗 Check the quote URL to see if content appears in Cover Page section")
            else:
                print("❌ No quote ID in response")
        else:
            print("❌ API call failed")
            
    except Exception as e:
        print(f"❌ Error making API call: {e}")

if __name__ == "__main__":
    test_cover_page_field()
