#!/usr/bin/env python3
"""
Test script to check what GET /quotes returns from Quoter API.
"""

import requests
import json
from quoter import get_access_token

def test_get_quotes():
    """Test GET /quotes endpoint to see what it returns."""
    
    print("🧪 Testing GET /quotes endpoint")
    print("=" * 50)
    
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return
    
    print(f"✅ Got access token: {access_token[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test GET /quotes
        print("\n📡 Testing GET /quotes...")
        response = requests.get(
            "https://api.quoter.com/v1/quotes",
            headers=headers,
            timeout=10
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response structure:")
            print(json.dumps(data, indent=2))
            
            # Check if we can see our created quotes
            quotes = data.get("data", [])
            print(f"\n📋 Found {len(quotes)} quotes:")
            
            for i, quote in enumerate(quotes[:5]):  # Show first 5
                print(f"  {i+1}. ID: {quote.get('id')}")
                print(f"     Number: {quote.get('number', 'N/A')}")
                print(f"     Name: {quote.get('name', 'N/A')}")
                print(f"     Status: {quote.get('status', 'N/A')}")
                print(f"     Contact: {quote.get('person', {}).get('name', 'N/A')}")
                print(f"     Organization: {quote.get('organization', 'N/A')}")
                print()
                
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_get_quotes()
