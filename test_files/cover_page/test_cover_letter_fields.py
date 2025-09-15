#!/usr/bin/env python3
"""
Test what cover letter fields actually work in Quoter
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token, create_or_find_contact_in_quoter
import requests

def test_cover_letter_fields():
    print("🧪 TESTING COVER LETTER FIELD REPLACEMENT")
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
    
    # Test with simple field codes first
    simple_cover_letter = """Dear Customer,

This is a test quote to see what fields work.

Contact: {{person.first_name}} {{person.last_name}}
Organization: {{person.organization}}
Quote Name: {{quote.name}}

Best regards,
Sales Team"""

    print("🔍 Testing simple field codes...")
    print(f"Cover letter preview:\n{simple_cover_letter}")
    
    # Create quote data
    quote_data = {
        "contact_id": contact_id,
        "template_id": template_id,
        "currency_abbr": "USD",
        "name": "Field Test Quote",
        "cover_letter": simple_cover_letter
    }
    
    try:
        print("\n🚀 Creating test quote...")
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
                print(f"✅ Test quote created!")
                print(f"   Quote ID: {quote_id}")
                print(f"   URL: {data.get('url', 'N/A')}")
                
                # Check the quote to see if fields were replaced
                print(f"\n🔗 Check the quote at: {data.get('url', 'N/A')}")
                print("   Look at the cover letter to see which fields were replaced")
                
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
    quote_id = test_cover_letter_fields()
    if quote_id:
        print(f"\n📋 Check the quote to see which fields work")
    else:
        print(f"\n❌ Test failed")
