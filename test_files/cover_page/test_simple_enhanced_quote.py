#!/usr/bin/env python3
"""
Simple test using existing Quoter contact instead of Pipedrive data
This will create a draft quote with template bundles using a real Quoter contact
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token, get_quoter_products
from template_mapping_enhanced import get_template_line_items, TEMPLATE_BUNDLES

def get_existing_quoter_contact(access_token):
    """
    Get an existing Quoter contact to use for testing
    """
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    try:
        # Get contacts from Quoter
        response = requests.get('https://api.quoter.com/v1/contacts', headers=headers)
        if response.status_code == 200:
            data = response.json()
            contacts = data.get('data', [])
            
            if contacts:
                # Use the first contact
                contact = contacts[0]
                print(f"📞 Using existing Quoter contact:")
                print(f"   ID: {contact.get('id')}")
                print(f"   Name: {contact.get('name', 'N/A')}")
                print(f"   Email: {contact.get('email', 'N/A')}")
                return contact.get('id')
            else:
                print("❌ No contacts found in Quoter")
                return None
        else:
            print(f"❌ Failed to get contacts: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting contacts: {e}")
        return None

def create_simple_enhanced_quote():
    """Create a quote using existing Quoter contact and template bundles"""
    
    print("🧪 TESTING SIMPLE ENHANCED QUOTE CREATION")
    print("=" * 50)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get access token")
        return None
    
    print("✅ Got access token")
    
    # Get existing Quoter contact
    contact_id = get_existing_quoter_contact(access_token)
    if not contact_id:
        print("❌ No contact available for testing")
        return None
    
    # Get template info
    template_key = "floating-video"
    template_info = TEMPLATE_BUNDLES.get(template_key)
    if not template_info:
        print(f"❌ Template '{template_key}' not found!")
        return None
    
    print(f"\n🎯 Template Info:")
    print(f"   Name: {template_info['name']}")
    print(f"   Total items: {len(template_info.get('template_specific_items', [])) + len(template_info.get('universal_items', []))}")
    
    # Show cover letter preview
    cover_letter = template_info.get('cover_letter', '')
    print(f"\n📝 Cover Letter Preview:")
    print("-" * 30)
    
    # Replace field codes with test data
    preview_letter = cover_letter
    preview_letter = preview_letter.replace('{{person.first_name}}', 'John')
    preview_letter = preview_letter.replace('{{deal.title}}', 'Test Event')
    preview_letter = preview_letter.replace('{{deal.id}}', '1234')
    preview_letter = preview_letter.replace('{{deal.owner_name}}', 'Maurice Capillaire')
    preview_letter = preview_letter.replace('{{quote.url}}', 'https://tlciscreative.quoter.com/quote/webview/TEST-UUID-HERE')
    preview_letter = preview_letter.replace('{{quote.pdf_url}}', 'https://tlciscreative.quoter.com/quote/download/TEST-UUID-HERE')
    
    print(preview_letter)
    print("-" * 30)
    
    # Check URLs
    has_web_url = '{{quote.url}}' in cover_letter
    has_pdf_url = '{{quote.pdf_url}}' in cover_letter
    
    print(f"\n✅ URL Analysis:")
    print(f"   Web View URL: {'✅ Present' if has_web_url else '❌ Missing'}")
    print(f"   PDF Download URL: {'✅ Present' if has_pdf_url else '❌ Missing'}")
    
    if has_web_url and has_pdf_url:
        print(f"\n🎉 SUCCESS: Both URL types are present!")
    
    # Create the quote
    print(f"\n🚀 Creating draft quote...")
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Use Basic template for now (we can enhance template selection later)
    quote_data = {
        "contact_id": contact_id,
        "template_id": "tmpl_30O6JTDIbApan1B5gh9hF2w1tfL",  # Basic template
        "currency_abbr": "USD",
        "name": f"Test Quote - {template_info['name']}",
        "cover_letter": cover_letter  # Include our enhanced cover letter
    }
    
    try:
        response = requests.post("https://api.quoter.com/v1/quotes", json=quote_data, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            quote_id = data.get("id")
            
            if quote_id:
                print(f"✅ SUCCESS: Draft quote created!")
                print(f"   Quote ID: {quote_id}")
                print(f"   Name: {data.get('name', 'N/A')}")
                print(f"   Contact ID: {contact_id}")
                
                print(f"\n🔗 Next Steps:")
                print(f"   1. Go to: https://tlciscreative.quoter.com/admin/quotes/")
                print(f"   2. Find quote: '{data.get('name', 'Unknown')}'")
                print(f"   3. Check the cover letter for both URL buttons")
                print(f"   4. Verify the dual URL system is working")
                
                return data
            else:
                print("❌ Quote created but no ID returned")
                return None
        else:
            print(f"❌ Failed to create quote: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating quote: {e}")
        return None

if __name__ == "__main__":
    try:
        create_simple_enhanced_quote()
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
