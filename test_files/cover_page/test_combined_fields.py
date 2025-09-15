#!/usr/bin/env python3
"""
Test combining cover_letter and cover_page fields in one quote
"""

import requests
import json
from quoter import get_access_token
from template_mapping_enhanced import get_template_info

def test_combined_fields():
    """Test using both cover_letter and cover_page fields together"""
    
    print("🔍 TESTING COMBINED FIELDS")
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
    
    # Get content from template
    template_info = get_template_info("floating-video")
    cover_letter = template_info.get('cover_letter', '') if template_info else ''
    appended_content = template_info.get('appended_content', '') if template_info else ''
    
    print(f"📝 Cover letter content: {len(cover_letter)} characters")
    print(f"📝 Appended content: {len(appended_content)} characters")
    print()
    
    # Create quote with ALL fields to see what happens
    quote_data = {
        "contact_id": "cont_32fYTamKMMZXCXNVFJx3qtISNIN",
        "template_id": "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG",
        "currency_abbr": "USD",
        "name": "COMBINED FIELDS TEST",
        "cover_letter": "COVER LETTER FIELD - " + cover_letter[:100] + "...",
        "cover_page": "COVER PAGE FIELD - " + cover_letter[:100] + "...",
        "appended_content": "APPENDED CONTENT FIELD - " + appended_content[:100] + "..."
    }
    
    print(f"📤 API Request payload:")
    print(json.dumps(quote_data, indent=2))
    print()
    
    try:
        print("🚀 Creating quote with ALL fields...")
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
                print("🔍 Check all sections:")
                print("  - Cover Page: Should show 'COVER PAGE FIELD'")
                print("  - Cover Letter: Should show 'COVER LETTER FIELD'")
                print("  - Appended Content: Should show 'APPENDED CONTENT FIELD'")
            else:
                print("❌ No quote ID in response")
        else:
            print("❌ API call failed")
            
    except Exception as e:
        print(f"❌ Error making API call: {e}")

if __name__ == "__main__":
    test_combined_fields()
