#!/usr/bin/env python3
"""
Test different cover letter field names
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token
import requests

def test_cover_letter_field_names():
    print("🔍 TESTING COVER LETTER FIELD NAMES")
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
    
    # Test different field names for cover letter
    cover_letter_text = "Dear Customer,\n\nThis is a test cover letter to see which field name works.\n\nBest regards,\nSales Team"
    
    field_names_to_test = [
        "cover_letter",
        "cover_letter_content", 
        "cover_page_content",
        "cover_page",
        "letter_content",
        "content",
        "description",
        "notes"
    ]
    
    for field_name in field_names_to_test:
        print(f"\n🧪 Testing field name: {field_name}")
        
        # Create quote data with different field names
        quote_data = {
            "contact_id": contact_id,
            "template_id": template_id,
            "currency_abbr": "USD",
            "name": f"Test {field_name}",
            field_name: cover_letter_text
        }
        
        try:
            response = requests.post(
                "https://api.quoter.com/v1/quotes",
                json=quote_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                quote_id = data.get("id")
                print(f"   ✅ Quote created: {quote_id}")
                
                # Try to get quote details to see if the field was saved
                get_response = requests.get(
                    f"https://api.quoter.com/v1/quotes/{quote_id}",
                    headers=headers,
                    timeout=10
                )
                
                if get_response.status_code == 200:
                    quote_details = get_response.json()
                    saved_content = quote_details.get(field_name)
                    if saved_content:
                        print(f"   ✅ Field {field_name} saved successfully!")
                        print(f"   📋 Content: {saved_content[:50]}...")
                        return field_name, quote_id
                    else:
                        print(f"   ❌ Field {field_name} not saved")
                else:
                    print(f"   ❌ Cannot retrieve quote: {get_response.status_code}")
            else:
                print(f"   ❌ Failed to create quote: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n❌ No working field name found")
    return None, None

if __name__ == "__main__":
    field_name, quote_id = test_cover_letter_field_names()
    if field_name:
        print(f"\n🎉 SUCCESS! Working field name: {field_name}")
        print(f"🔗 Quote URL: https://tlciscreative.quoter.com/admin/quotes/draft_by_public_id/{quote_id}")
    else:
        print(f"\n❌ No working field name found")
