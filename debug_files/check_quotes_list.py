#!/usr/bin/env python3
"""
Check what quotes are available and their structure
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token
import requests

def check_quotes_list():
    print("🔍 CHECKING QUOTES LIST")
    print("=" * 50)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ No access token")
        return
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    try:
        print(f"📋 Getting quotes list...")
        response = requests.get(
            "https://api.quoter.com/v1/quotes",
            headers=headers,
            timeout=10
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get("data", [])
            print(f"✅ Found {len(quotes)} quotes")
            
            if quotes:
                # Look at the first quote to see its structure
                first_quote = quotes[0]
                print(f"\n📋 First quote structure:")
                for key, value in first_quote.items():
                    if isinstance(value, str) and len(value) > 100:
                        print(f"   {key}: {value[:100]}... (length: {len(value)})")
                    else:
                        print(f"   {key}: {value}")
                
                # Look for cover letter fields
                print(f"\n🔍 Cover letter related fields:")
                cover_fields = [k for k in first_quote.keys() if 'cover' in k.lower() or 'letter' in k.lower() or 'content' in k.lower()]
                for field in cover_fields:
                    print(f"   {field}: {first_quote[field]}")
                    
                return first_quote
            else:
                print("❌ No quotes found")
                return None
        else:
            print(f"❌ Failed to get quotes: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    quote = check_quotes_list()
    if quote:
        print(f"\n✅ Found quote structure")
    else:
        print(f"\n❌ Failed to get quotes")
