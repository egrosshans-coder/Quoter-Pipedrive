#!/usr/bin/env python3
"""
Test different field names for cover letter content
"""

import requests
import json
from quoter import get_access_token

def test_alternative_cover_fields():
    """Test different field names that might be used for cover letter content"""
    
    print("🔍 TESTING ALTERNATIVE COVER FIELDS")
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
    
    cover_letter_content = """Dear Customer,

Thank you for the opportunity to work with you. We've prepared a custom proposal to support your upcoming Floating Video project.

Below you'll find a breakdown of services, equipment, and pricing. Our goal is to deliver the highest quality experience with a focus on creativity, reliability, and flawless execution.

If you have any questions, please feel free to reach out to me directly. You can accept the proposal online by clicking the "Accept Quote" button.

Sincerely,

Sales Team
TLC Creative"""
    
    # Test different possible field names
    field_names_to_test = [
        "cover_letter",
        "cover_page", 
        "cover_page_content",
        "letter_content",
        "cover_content",
        "intro_letter",
        "introduction",
        "cover_text",
        "letter",
        "cover_note",
        "intro_content",
        "cover_section",
        "letter_section"
    ]
    
    for field_name in field_names_to_test:
        print(f"\n🧪 Testing field: '{field_name}'")
        
        quote_data = {
            "contact_id": "cont_32fYTamKMMZXCXNVFJx3qtISNIN",
            "template_id": "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG",
            "currency_abbr": "USD",
            "name": f"Test {field_name}",
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
                print(f"   🔗 Check this URL to see if cover content appears")
            else:
                print(f"❌ FAILED with '{field_name}' - Status: {response.status_code}")
                if response.status_code == 400:
                    print(f"   Error: {response.text}")
                    
        except Exception as e:
            print(f"❌ ERROR with '{field_name}': {e}")

if __name__ == "__main__":
    test_alternative_cover_fields()
