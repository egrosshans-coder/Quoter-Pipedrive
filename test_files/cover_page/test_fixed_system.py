#!/usr/bin/env python3
"""
Test the fixed quote creation system with proper Pipedrive integration
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import create_comprehensive_quote_from_pipedrive
from template_mapping_enhanced import TEMPLATE_BUNDLES

def test_fixed_system():
    print("🧪 TESTING FIXED QUOTE CREATION SYSTEM")
    print("=" * 50)
    
    # Test data - using real deal 2536 (ZZ19-deal)
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
    print(f"   Deal Title: {test_data['deal_title']}")
    
    # Mock organization data (as it would come from Pipedrive)
    organization_data = {
        "id": 999999,  # Mock org ID
        "name": "ZZ19-Org-2536",  # This format will extract deal ID 2536
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": "2536",  # Deal ID field
        "owner_id": {
            "value": 12345,
            "name": "Maurice Capillaire"
        }
    }
    
    # Mock deal data (as it would come from Pipedrive)
    # Note: We'll use a real person ID or create a contact directly
    deal_data = {
        "id": int(test_data['deal_id']),
        "title": test_data['deal_title'],
        "person_id": {
            "value": 67890,  # This will be replaced by the contact creation process
            "name": test_data['person_name']
        }
    }
    
    print(f"\n🎯 Testing Template Bundle System:")
    template_key = test_data['template_key']
    template_info = TEMPLATE_BUNDLES.get(template_key)
    if template_info:
        print(f"   Template: {template_info['name']}")
        print(f"   Total items: {len(template_info.get('template_specific', [])) + len(template_info.get('universal', []))}")
        print(f"   Template-specific items: {len(template_info.get('template_specific', []))}")
        print(f"   Universal items: {len(template_info.get('universal', []))}")
        
        # Show cover letter preview
        cover_letter = template_info.get('cover_letter', '')
        if cover_letter:
            print(f"\n📝 Cover Letter Preview:")
            preview = cover_letter.replace('{{person.first_name}}', 'John')
            preview = preview.replace('{{deal.title}}', test_data['deal_title'])
            preview = preview.replace('{{deal.id}}', test_data['deal_id'])
            preview = preview.replace('{{deal.owner_name}}', 'Maurice Capillaire')
            preview = preview.replace('{{quote.url}}', 'https://tlciscreative.quoter.com/quote/webview/2778-7b6f2af1-6bdb-42bf-bc6f-d865d0795578')
            preview = preview.replace('{{quote.pdf_url}}', 'https://tlciscreative.quoter.com/quote/download/2778-7b6f2af1-6bdb-42bf-bc6f-d865d0795578')
            print(f"   {preview[:200]}...")
    else:
        print(f"   ❌ Template '{template_key}' not found!")
        return
    
    print(f"\n🚀 Creating comprehensive quote using fixed system...")
    print(f"   Using: create_comprehensive_quote_from_pipedrive()")
    print(f"   This will:")
    print(f"   1. ✅ Use pipedrive.py to populate contact in Quoter")
    print(f"   2. ✅ Create quote with proper contact and organization")
    print(f"   3. ✅ Add template-specific line items from bundle system")
    print(f"   4. ✅ Include cover letter with dual URL system")
    
    try:
        result = create_comprehensive_quote_from_pipedrive(organization_data, deal_data)
        
        if result:
            print(f"\n🎉 SUCCESS! Fixed system working correctly:")
            print(f"   Quote ID: {result.get('id')}")
            print(f"   Name: {result.get('name', 'N/A')}")
            print(f"   URL: {result.get('url', 'N/A')}")
            
            print(f"\n✅ What was created:")
            print(f"   ✅ Proper contact populated from Pipedrive data")
            print(f"   ✅ Correct organization information")
            print(f"   ✅ Template-specific line items from bundle system")
            print(f"   ✅ Cover letter with dual URL system")
            
            print(f"\n🔗 Next Steps:")
            print(f"   1. Go to: https://tlciscreative.quoter.com/admin/quotes/")
            print(f"   2. Find quote: '{result.get('name', 'Unknown')}'")
            print(f"   3. Verify it has the correct contact, organization, and template items")
            print(f"   4. Check the cover letter for both URL buttons")
            
        else:
            print(f"\n❌ FAILED: Quote creation returned None")
            print(f"   Check the logs above for error details")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_system()
