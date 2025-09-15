#!/usr/bin/env python3
"""
Test creating a quote with minimal fields to see what's accepted
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token
import requests

def test_minimal_quote():
    print("🔍 TESTING MINIMAL QUOTE CREATION")
    print("=" * 50)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ No access token")
        return
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Use existing contact
    contact_id = "cont_32Z1DJppX9ZfZbsnYZzI88U0VSM"
    
    # Use the Floating Video template
    template_id = "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG"
    
    # Test with minimal required fields only
    minimal_quote_data = {
        "contact_id": contact_id,
        "template_id": template_id,
        "currency_abbr": "USD"
    }
    
    print("🧪 Testing minimal quote creation...")
    print(f"📋 Data: {minimal_quote_data}")
    
    try:
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json=minimal_quote_data,
            headers=headers,
            timeout=10
        )
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            quote_id = data.get("id")
            print(f"✅ Minimal quote created successfully!")
            print(f"   Quote ID: {quote_id}")
            print(f"   URL: {data.get('url', 'N/A')}")
            
            return quote_id
        else:
            print(f"❌ Failed to create minimal quote: {response.status_code}")
            print(f"   Error: {response.text[:300]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    quote_id = test_minimal_quote()
    if quote_id:
        print(f"\n✅ Minimal quote works - the issue is with the cover_letter field")
    else:
        print(f"\n❌ Even minimal quote creation failed")
