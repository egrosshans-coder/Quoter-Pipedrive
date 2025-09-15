#!/usr/bin/env python3
"""
Test creating a Floating Video quote with the correct template
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
# Add the parent directory to the path so we can import from quoter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quoter import get_access_token, create_or_find_contact_in_quoter, add_template_line_items_to_quote
from template_mapping_enhanced import get_template_line_items
from template_mapping_enhanced import get_template_info
import requests

def test_floating_video_quote():
    print("🎯 TESTING FLOATING VIDEO QUOTE WITH CORRECT TEMPLATE")
    print("=" * 60)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ No access token")
        return
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Use existing contact
    contact_id = "cont_32Z1DJppX9ZfZbsnYZzI88U0VSM"
    
    # Use the CORRECT Floating Video template ID
    floating_video_template_id = "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG"  # Primary Floating Video template
    
    print(f"🎯 Using Floating Video template: {floating_video_template_id}")
    
    # Create quote data with the correct template
    quote_data = {
        "contact_id": contact_id,
        "template_id": floating_video_template_id,
        "currency_abbr": "USD",
        "name": "Test Floating Video Quote - Correct Template"
    }
    
    # Get the Floating Video cover letter from our template system
    template_info = get_template_info("floating-video")
    if template_info and template_info.get("cover_letter"):
        quote_data["cover_letter"] = template_info["cover_letter"]
        print("✅ Added Floating Video cover letter")
    else:
        print("⚠️ No cover letter found for floating-video template")
    
    try:
        print("🚀 Creating quote with Floating Video template...")
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
                print(f"✅ Quote created successfully!")
                print(f"   Quote ID: {quote_id}")
                print(f"   Template: {floating_video_template_id}")
                print(f"   URL: {data.get('url', 'N/A')}")
                
                # Add Floating Video line items
                print("📦 Adding Floating Video line items...")
                line_items = get_template_line_items("floating-video")
                
                if line_items:
                    success = add_template_line_items_to_quote(quote_id, line_items, access_token)
                    if success:
                        print("✅ Line items added successfully!")
                    else:
                        print("❌ Failed to add line items")
                else:
                    print("❌ No line items found for floating-video template")
                
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
    quote_id = test_floating_video_quote()
    if quote_id:
        print(f"\n🎉 SUCCESS! Floating Video quote created: {quote_id}")
        print(f"   Check the URL to verify it's using the Floating Video template")
    else:
        print(f"\n❌ FAILED to create Floating Video quote")
