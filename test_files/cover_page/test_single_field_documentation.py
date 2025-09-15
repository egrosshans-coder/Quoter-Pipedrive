#!/usr/bin/env python3
"""
Single field test to document exactly what works for cover letter
"""

import requests
import json
from quoter import get_access_token

def test_single_field_with_documentation():
    """Test ONE field at a time with clear documentation"""
    
    print("🔍 SINGLE FIELD TEST WITH DOCUMENTATION")
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
    
    # Simple, clear cover letter content
    cover_content = "TEST COVER LETTER - This is a simple test to see if cover letter displays correctly."
    
    # Test ONLY the cover_letter field (the one from official docs)
    print(f"🧪 Testing ONLY 'cover_letter' field")
    print(f"Content: {cover_content}")
    print()
    
    quote_data = {
        "contact_id": "cont_32fYTamKMMZXCXNVFJx3qtISNIN",
        "template_id": "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG", 
        "currency_abbr": "USD",
        "name": "SINGLE FIELD TEST - cover_letter",
        "cover_letter": cover_content
    }
    
    print(f"📤 API Request:")
    print(json.dumps(quote_data, indent=2))
    print()
    
    try:
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json=quote_data,
            headers=headers,
            timeout=10
        )
        
        print(f"📥 API Response:")
        print(f"Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            quote_id = data.get("id")
            quote_url = data.get("url")
            
            print(f"✅ SUCCESS!")
            print(f"Quote ID: {quote_id}")
            print(f"Quote URL: {quote_url}")
            print()
            print("📋 DOCUMENTATION:")
            print("-" * 40)
            print(f"Field tested: cover_letter")
            print(f"Template used: tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG (Floating Video)")
            print(f"Content: {cover_content}")
            print(f"API Status: {response.status_code} (SUCCESS)")
            print()
            print("🔗 NEXT STEP:")
            print(f"Check this URL: {quote_url}")
            print("Look for the cover letter content in the quote")
            print("Report back: COVER LETTER VISIBLE or COVER LETTER BLANK")
            
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_single_field_with_documentation()
