#!/usr/bin/env python3
"""
Test script using the enhanced quote creation system
This will create a real draft quote with template bundles and dual URL system
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter_enhanced import create_comprehensive_quote_with_bundles
from template_mapping_enhanced import TEMPLATE_BUNDLES

def test_enhanced_quote():
    """Create a test quote using the enhanced system with template bundles"""
    
    print("🧪 TESTING ENHANCED QUOTE CREATION WITH BUNDLES")
    print("=" * 60)
    
    # Test data using real deal 2536 (ZZ19)
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
    print(f"   Template: {test_data['template_key']}")
    
    # Get template info
    template_info = TEMPLATE_BUNDLES.get(test_data['template_key'])
    if not template_info:
        print(f"❌ Template '{test_data['template_key']}' not found!")
        return
    
    print(f"\n🎯 Template Info:")
    print(f"   Name: {template_info['name']}")
    print(f"   Description: {template_info.get('description', 'N/A')}")
    
    # Show the cover letter content
    cover_letter = template_info.get('cover_letter', '')
    print(f"\n📝 Cover Letter Preview:")
    print("-" * 30)
    
    # Replace field codes with test data
    preview_letter = cover_letter
    preview_letter = preview_letter.replace('{{person.first_name}}', test_data['person_name'])
    preview_letter = preview_letter.replace('{{deal.title}}', test_data['deal_title'])
    preview_letter = preview_letter.replace('{{deal.id}}', test_data['deal_id'])
    preview_letter = preview_letter.replace('{{deal.owner_name}}', 'Maurice Capillaire')
    preview_letter = preview_letter.replace('{{quote.url}}', 'https://tlciscreative.quoter.com/quote/webview/TEST-UUID-HERE')
    preview_letter = preview_letter.replace('{{quote.pdf_url}}', 'https://tlciscreative.quoter.com/quote/download/TEST-UUID-HERE')
    
    print(preview_letter)
    print("-" * 30)
    
    # Check if both URL types are present
    has_web_url = '{{quote.url}}' in cover_letter or 'https://tlciscreative.quoter.com/quote/webview/' in cover_letter
    has_pdf_url = '{{quote.pdf_url}}' in cover_letter or 'https://tlciscreative.quoter.com/quote/download/' in cover_letter
    
    print(f"\n✅ URL Analysis:")
    print(f"   Web View URL: {'✅ Present' if has_web_url else '❌ Missing'}")
    print(f"   PDF Download URL: {'✅ Present' if has_pdf_url else '❌ Missing'}")
    
    if has_web_url and has_pdf_url:
        print(f"\n🎉 SUCCESS: Both URL types are present in the template!")
        print(f"   Your team can now choose between:")
        print(f"   • Web View (interactive, mobile-friendly)")
        print(f"   • PDF Download (printable, offline)")
    else:
        print(f"\n⚠️  WARNING: Some URL types are missing!")
    
    print(f"\n📊 Template Statistics:")
    print(f"   Total items: {len(template_info.get('template_specific_items', [])) + len(template_info.get('universal_items', []))}")
    print(f"   Template-specific items: {len(template_info.get('template_specific_items', []))}")
    print(f"   Universal items: {len(template_info.get('universal_items', []))}")
    
    print(f"\n🚀 CREATING ENHANCED DRAFT QUOTE...")
    print(f"   This will create a real draft quote using the enhanced system")
    print(f"   Template: {template_info['name']}")
    print(f"   Deal: {test_data['deal_title']}")
    print(f"   Features: Template bundles, cover letters, dual URLs")
    
    # Create the actual draft quote using enhanced system
    try:
        # Mock organization data for the test
        organization_data = {
            "id": 999999,  # Mock org ID
            "name": test_data['organization_name'],
            "15034cf07d05ceb15f0a89dcbdcc4f596348584e": test_data['deal_id'],  # Deal ID field
            "owner_id": {
                "value": 12345,
                "name": "Maurice Capillaire"
            }
        }
        
        # Mock deal data for the test
        deal_data = {
            "id": int(test_data['deal_id']),
            "title": test_data['deal_title'],
            "person_id": {
                "value": 67890,
                "name": test_data['person_name']
            }
        }
        
        print(f"\n📝 Creating enhanced draft quote...")
        result = create_comprehensive_quote_with_bundles(organization_data, deal_data)
        
        if result:
            print(f"✅ SUCCESS: Enhanced draft quote created!")
            print(f"   Quote ID: {result.get('id', 'Unknown')}")
            print(f"   Quote Title: {result.get('name', 'Unknown')}")
            
            print(f"\n🔗 Next Steps:")
            print(f"   1. Go to: https://tlciscreative.quoter.com/admin/quotes/")
            print(f"   2. Find the quote: '{result.get('name', 'Unknown')}'")
            print(f"   3. Check the cover letter for both URL buttons")
            print(f"   4. Verify all template line items were added")
            print(f"   5. Test the Web View and PDF Download links")
            
        else:
            print(f"❌ FAILED: Could not create enhanced draft quote")
            print(f"   Check the logs above for specific error details")
            
    except Exception as e:
        print(f"❌ ERROR: Exception during enhanced quote creation")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    return True

if __name__ == "__main__":
    try:
        test_enhanced_quote()
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
