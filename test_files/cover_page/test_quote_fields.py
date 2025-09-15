#!/usr/bin/env python3
"""
Test to check what fields are actually available in a quote object
"""

import requests
from quoter import get_access_token

def test_quote_fields():
    """Get a quote and examine its field structure"""
    
    print("🔍 CHECKING QUOTE FIELDS")
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
    
    # Use the most recent quote ID from our test
    quote_id = "quot_32hdFETZtE0z8ByVwcMCnnjQM44"
    
    try:
        print(f"📥 Getting quote details for: {quote_id}")
        response = requests.get(
            f"https://api.quoter.com/v1/quotes/{quote_id}",
            headers=headers,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Quote retrieved successfully!")
            print()
            print("📋 Available fields in quote object:")
            print("-" * 40)
            
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"{key}: {value[:100]}... (truncated)")
                else:
                    print(f"{key}: {value}")
            
            # Look specifically for cover-related fields
            print()
            print("🔍 Cover-related fields:")
            print("-" * 40)
            cover_fields = [k for k in data.keys() if 'cover' in k.lower() or 'letter' in k.lower()]
            if cover_fields:
                for field in cover_fields:
                    value = data.get(field, '')
                    if isinstance(value, str) and len(value) > 200:
                        print(f"{field}: {value[:200]}... (truncated)")
                    else:
                        print(f"{field}: {value}")
            else:
                print("No cover-related fields found")
                
        else:
            print(f"❌ Failed to get quote: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_quote_fields()
