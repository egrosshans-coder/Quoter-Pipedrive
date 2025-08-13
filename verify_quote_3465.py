#!/usr/bin/env python3
"""
Verify the quote we just created for organization 3465.
"""

from quoter import get_access_token
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def verify_quote_3465():
    """Verify the quote we created for organization 3465"""
    print("🔍 Verifying Quote for Organization 3465")
    print("=" * 60)
    
    # The quote ID we created
    quote_id = "quot_316ZA2Gr27LwOucwVqY8aqH4UNv"
    
    # Get OAuth token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"📋 Checking quote: {quote_id}")
    
    # Try to get the quote details
    try:
        response = requests.get(
            f"https://api.quoter.com/v1/quotes/{quote_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Quote found!")
            print(f"   Quote ID: {data.get('id', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Title: {data.get('title', 'N/A')}")
            print(f"   Quote Number: {data.get('quote_number', 'N/A')}")
            print(f"   URL: {data.get('url', 'N/A')}")
            
            # Show all available fields
            print(f"\n📋 All Quote Fields:")
            for key, value in data.items():
                print(f"   {key}: {value}")
                
        else:
            print(f"❌ Failed to get quote: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error getting quote: {e}")
    
    # Also check if we can see it in the quotes list
    print(f"\n🔍 Checking quotes list...")
    try:
        response = requests.get(
            "https://api.quoter.com/v1/quotes",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get("data", [])
            print(f"✅ Found {len(quotes)} quotes in system")
            
            # Look for our specific quote
            found_quote = None
            for quote in quotes:
                if quote.get('id') == quote_id:
                    found_quote = quote
                    break
            
            if found_quote:
                print(f"✅ Our quote is in the quotes list!")
                print(f"   Status: {found_quote.get('status', 'N/A')}")
                print(f"   Title: {found_quote.get('title', 'N/A')}")
            else:
                print(f"❌ Our quote is NOT in the quotes list")
                print(f"   This might indicate an issue with the creation")
                
        else:
            print(f"❌ Failed to get quotes list: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting quotes list: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Verification Complete!")
    print("Check the output above to see what's happening with the quote.")

if __name__ == "__main__":
    verify_quote_3465()
