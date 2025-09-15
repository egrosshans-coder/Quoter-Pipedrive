#!/usr/bin/env python3
"""
Test appended_content field to see if it writes to Appended Content section
"""

import requests
import json
from quoter import get_access_token
from template_mapping_enhanced import get_template_info

def test_appended_content():
    """Test if appended_content field writes to Appended Content section"""
    
    print("🔍 TESTING APPENDED_CONTENT FIELD")
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
    
    # Get appended content from template
    template_info = get_template_info("floating-video")
    appended_content = template_info.get('appended_content', '') if template_info else ''
    
    print(f"📝 Appended content:")
    print(f"Length: {len(appended_content)} characters")
    print(f"Content preview: {appended_content[:200]}...")
    print()
    
    # Create quote with appended_content field (official API field)
    quote_data = {
        "contact_id": "cont_32fYTamKMMZXCXNVFJx3qtISNIN",
        "template_id": "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG",
        "currency_abbr": "USD",
        "name": "APPENDED CONTENT TEST",
        "appended_content": appended_content  # Official API field from docs
    }
    
    print(f"📤 API Request payload:")
    print(json.dumps(quote_data, indent=2))
    print()
    
    try:
        print("🚀 Creating quote with appended_content field...")
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
                print("🎯 This should write to Appended Content section!")
                print("🔗 Check the quote URL to see if content appears in Appended Content section")
            else:
                print("❌ No quote ID in response")
        else:
            print("❌ API call failed")
            
    except Exception as e:
        print(f"❌ Error making API call: {e}")

if __name__ == "__main__":
    test_appended_content()
