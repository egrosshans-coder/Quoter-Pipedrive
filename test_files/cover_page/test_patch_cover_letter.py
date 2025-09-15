#!/usr/bin/env python3
"""
Test PATCH request to update Cover Letter section after quote creation
"""

import requests
import json
from quoter import get_access_token

def test_patch_cover_letter():
    """Test updating Cover Letter section via PATCH request"""
    
    print("🔍 TESTING PATCH REQUEST FOR COVER LETTER SECTION")
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
    
    # Use our most recent quote
    quote_id = "quot_32hh4qOrEcIyl0BL4ZiR2J2C43n"
    
    cover_letter_content = "PATCH TEST - This content was added via PATCH request to Cover Letter section."
    
    # Test different PATCH payload structures for Cover Letter section
    patch_payloads = [
        # Test 1: Direct field
        {
            "cover_letter_content": cover_letter_content
        },
        # Test 2: Nested structure
        {
            "data": {
                "Quote": {
                    "cover_letter_content": cover_letter_content
                }
            }
        },
        # Test 3: Letter-specific fields
        {
            "letter_content": cover_letter_content
        },
        # Test 4: Section-specific fields
        {
            "letter_section": cover_letter_content
        },
        # Test 5: Try the DOM field name
        {
            "data": {
                "Quote": {
                    "ip_text": cover_letter_content
                }
            }
        }
    ]
    
    for i, payload in enumerate(patch_payloads):
        print(f"\n🧪 Testing PATCH payload {i+1}:")
        print(json.dumps(payload, indent=2))
        
        try:
            response = requests.patch(
                f"https://api.quoter.com/v1/quotes/{quote_id}",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            print(f"📥 PATCH Response:")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code in [200, 201]:
                print(f"✅ PATCH SUCCESS!")
                print(f"🔗 Check quote URL to see if content appears in Cover Letter section:")
                print(f"https://tlciscreative.quoter.com/admin/quotes/draft_by_public_id/{quote_id}")
            else:
                print(f"❌ PATCH FAILED")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_patch_cover_letter()
