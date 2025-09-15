#!/usr/bin/env python3
"""
Test with the most basic cover letter fields to see what works
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token
import requests

def test_basic_cover_letter():
    print("🧪 TESTING BASIC COVER LETTER FIELDS")
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
    
    # Test with the most basic fields that should definitely work
    basic_cover_letter = """Dear Customer,

Thank you for your interest in our services.

This quote is for your project.

Best regards,
Sales Team"""

    print("🔍 Testing with NO dynamic fields first...")
    print(f"Cover letter:\n{basic_cover_letter}")
    
    # Create quote data
    quote_data = {
        "contact_id": contact_id,
        "template_id": template_id,
        "currency_abbr": "USD",
        "name": "Basic Test Quote",
        "cover_letter": basic_cover_letter
    }
    
    try:
        print("\n🚀 Creating basic test quote...")
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json=quote_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            quote_id = data.get("id")
            
            if quote_id:
                print(f"✅ Basic quote created!")
                print(f"   Quote ID: {quote_id}")
                print(f"   URL: {data.get('url', 'N/A')}")
                
                print(f"\n🔗 Check the quote at: {data.get('url', 'N/A')}")
                print("   This should show a clean cover letter without template code")
                
                return quote_id
            else:
                print(f"❌ No quote ID in response: {data}")
                return None
        else:
            print(f"❌ Failed to create quote: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    quote_id = test_basic_cover_letter()
    if quote_id:
        print(f"\n📋 If this works, the issue is with the field syntax")
        print(f"   If this also shows template code, Quoter has a bug")
    else:
        print(f"\n❌ Test failed")
