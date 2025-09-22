#!/usr/bin/env python3
"""
Check what fields are available in an existing quote
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token
import requests

def check_quote_fields():
    print("🔍 CHECKING QUOTE FIELDS")
    print("=" * 50)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ No access token")
        return
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Use one of the quotes we created earlier
    quote_id = "quot_32hcKDfHkPeH82RLFJzvbChTkjQ"
    
    try:
        print(f"📋 Getting quote details for: {quote_id}")
        response = requests.get(
            f"https://api.quoter.com/v1/quotes/{quote_id}",
            headers=headers,
            timeout=10
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Quote details retrieved!")
            print(f"\n📋 Available fields:")
            
            # Print all fields in the response
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"   {key}: {value[:100]}... (length: {len(value)})")
                else:
                    print(f"   {key}: {value}")
            
            # Look specifically for cover letter related fields
            print(f"\n🔍 Looking for cover letter fields:")
            cover_fields = [k for k in data.keys() if 'cover' in k.lower() or 'letter' in k.lower() or 'content' in k.lower()]
            for field in cover_fields:
                print(f"   {field}: {data[field]}")
                
        else:
            print(f"❌ Failed to get quote: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_quote_fields()
