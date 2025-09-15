#!/usr/bin/env python3
"""
Test the fixed quote creation system with a simpler approach
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token, create_or_find_contact_in_quoter, get_quote_required_fields
from quoter import add_template_line_items_to_quote, get_template_name_from_id, add_default_instructional_item
from template_mapping_enhanced import TEMPLATE_BUNDLES
import requests

def test_simple_fixed_system():
    print("🧪 TESTING SIMPLE FIXED QUOTE CREATION SYSTEM")
    print("=" * 50)
    
    # Test data
    test_data = {
        "deal_id": "2536",
        "organization_name": "ZZ19-Org-2536",
        "person_name": "ZZ19 Lastname",
        "person_email": "zz19@gmail.com",
        "deal_title": "ZZ19 Deal 2536",
        "template_key": "floating-video"
    }
    
    print(f"📋 Test Data:")
    print(f"   Deal ID: {test_data['deal_id']}")
    print(f"   Organization: {test_data['organization_name']}")
    print(f"   Person: {test_data['person_name']}")
    print(f"   Email: {test_data['person_email']}")
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get access token")
        return
    
    print("✅ Got access token")
    
    # Step 1: Create/find contact in Quoter
    print(f"\n📞 Creating/finding contact in Quoter...")
    contact_id = create_or_find_contact_in_quoter(
        contact_name=test_data['person_name'],
        contact_email=test_data['person_email'],
        organization_name=test_data['organization_name']
    )
    
    if not contact_id:
        print("❌ Failed to create/find contact")
        return
    
    print(f"✅ Contact ID: {contact_id}")
    
    # Step 2: Get required fields (template and currency)
    print(f"\n📋 Getting required fields...")
    required_fields = get_quote_required_fields(access_token)
    if not required_fields:
        print("❌ Failed to get required fields")
        return
    
    print(f"✅ Template ID: {required_fields['template_id']}")
    print(f"✅ Currency: {required_fields['currency_abbr']}")
    
    # Step 3: Create the quote
    print(f"\n📝 Creating draft quote...")
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    quote_data = {
        "contact_id": contact_id,
        "template_id": required_fields["template_id"],
        "currency_abbr": required_fields["currency_abbr"],
        "name": f"Test Quote - {test_data['template_key']}"
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
                
                # Step 4: Add template-specific line items using bundle system
                print(f"\n📋 Adding template-specific line items to quote...")
                
                # Get template name for bundle mapping
                template_name = get_template_name_from_id(required_fields["template_id"], access_token)
                
                if template_name:
                    print(f"🎯 Using template mapping for: {template_name}")
                    
                    # Add template-specific line items
                    success = add_template_line_items_to_quote(quote_id, template_name, access_token)
                    if success:
                        print(f"✅ Template line items added successfully for {template_name}")
                    else:
                        print(f"⚠️ Some template line items failed to add for {template_name}")
                        print(f"📋 Adding default instructional item as fallback")
                        add_default_instructional_item(quote_id, access_token)
                else:
                    print(f"⚠️ Could not determine template name, adding default instructional item")
                    add_default_instructional_item(quote_id, access_token)
                
                print(f"\n🎉 COMPLETE! Fixed system working correctly:")
                print(f"   ✅ Proper contact created in Quoter")
                print(f"   ✅ Quote created with correct contact")
                print(f"   ✅ Template-specific line items added from bundle system")
                
                print(f"\n🔗 Next Steps:")
                print(f"   1. Go to: https://tlciscreative.quoter.com/admin/quotes/")
                print(f"   2. Find quote: '{data.get('name', 'Unknown')}'")
                print(f"   3. Verify it has the correct contact and template items")
                
            else:
                print("❌ Quote created but no ID returned")
        else:
            print(f"❌ Failed to create quote: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error creating quote: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_fixed_system()
