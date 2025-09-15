#!/usr/bin/env python3
"""
Test updating an existing quote with cover letter content
"""

import requests
import json
from quoter import get_access_token

def test_update_existing_quote():
    """Test updating an existing quote with cover letter content"""
    
    print("🔍 TESTING UPDATE EXISTING QUOTE")
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
    
    # Use one of our existing test quotes
    quote_id = "quot_32hgZs8DMWD7JPARwCuy9PWcNT2"  # The ip_text test quote
    
    cover_letter_content = "UPDATED COVER LETTER - This content was added via PATCH request to existing quote."
    
    # Test different update payload structures
    update_payloads = [
        {
            "name": "UPDATED QUOTE NAME",
            "ip_text": cover_letter_content
        },
        {
            "name": "UPDATED QUOTE NAME", 
            "data": {
                "Quote": {
                    "ip_text": cover_letter_content
                }
            }
        },
        {
            "name": "UPDATED QUOTE NAME",
            "cover_letter": cover_letter_content
        },
        {
            "name": "UPDATED QUOTE NAME",
            "data[Quote][ip_text]": cover_letter_content
        }
    ]
    
    for i, payload in enumerate(update_payloads):
        print(f"\n🧪 Testing update payload {i+1}:")
        print(json.dumps(payload, indent=2))
        
        try:
            # Try PATCH request
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
            else:
                print(f"❌ PATCH FAILED")
                
                # Try PUT request as alternative
                print(f"🔄 Trying PUT request...")
                response = requests.put(
                    f"https://api.quoter.com/v1/quotes/{quote_id}",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                
                print(f"📥 PUT Response:")
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
                
                if response.status_code in [200, 201]:
                    print(f"✅ PUT SUCCESS!")
                else:
                    print(f"❌ PUT FAILED")
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\n🔗 Check the quote URL to see if any update worked:")
    print(f"https://tlciscreative.quoter.com/admin/quotes/draft_by_public_id/{quote_id}")

if __name__ == "__main__":
    test_update_existing_quote()
