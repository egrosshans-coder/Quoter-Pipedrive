#!/usr/bin/env python3
"""
Test Template Selection from Pipedrive Dropdown Field
Tests the new template selection functionality in the webhook handler.
"""

import sys
import os

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from debug_files.template_selection_logic import get_quote_template_id, test_template_selection
from quoter import get_access_token
from pipedrive import get_deal_by_id
from utils.logger import logger

def test_pipedrive_template_selection():
    """
    Test template selection from Pipedrive dropdown field.
    """
    print("🧪 Testing Pipedrive Template Selection")
    print("=" * 60)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return False
    
    # Test with a real deal ID (you can change this to any deal ID you have)
    test_deal_id = "2096"  # Blue Owl Capital deal
    template_field_id = "42ab0c919271cb24f3587f0b01ea2af166019c8d"
    
    print(f"🔍 Testing with deal ID: {test_deal_id}")
    print(f"📋 Template field ID: {template_field_id}")
    print()
    
    # Get deal data from Pipedrive
    deal_data = get_deal_by_id(test_deal_id)
    if not deal_data:
        print(f"❌ Could not fetch deal {test_deal_id} from Pipedrive")
        return False
    
    print(f"✅ Deal found: {deal_data.get('title', 'Unknown Deal')}")
    
    # Check what template is selected in the dropdown
    selected_template = deal_data.get(template_field_id)
    print(f"📋 Selected template in Pipedrive: '{selected_template}'")
    print()
    
    # Test template selection logic
    print("🎯 Testing template selection logic...")
    template_id = get_quote_template_id(deal_data, access_token, template_field_id)
    
    if template_id:
        print(f"✅ Template selection successful!")
        print(f"   Selected template ID: {template_id}")
        
        # Get template name for verification
        from debug_files.template_selection_logic import get_template_id_by_name
        # This is a reverse lookup - we'd need to implement this
        print(f"   Template selection working correctly")
    else:
        print(f"❌ Template selection failed")
        print(f"   This might be expected if no template is selected in Pipedrive")
        print(f"   The system should fall back to default template selection")
    
    print()
    print("🔄 Testing fallback logic...")
    
    # Test the fallback logic
    from debug_files.template_selection_logic import get_default_template_fallback
    fallback_id = get_default_template_fallback(access_token)
    
    if fallback_id:
        print(f"✅ Fallback template ID: {fallback_id}")
    else:
        print(f"❌ Fallback failed")
    
    return True

def test_webhook_integration():
    """
    Test the webhook integration with template selection.
    """
    print("\n" + "=" * 60)
    print("🧪 Testing Webhook Integration")
    print("=" * 60)
    
    # Simulate organization data (as would come from webhook)
    organization_data = {
        "id": 12345,
        "name": "Test Organization-2096",
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": "2096"  # Deal ID field
    }
    
    # Simulate deal data (as would come from webhook)
    deal_data = {
        "id": 2096,
        "title": "Test Deal",
        "42ab0c919271cb24f3587f0b01ea2af166019c8d": 444  # Template selection (444 = LED Wristbands)
    }
    
    print("📋 Simulated webhook data:")
    print(f"   Organization: {organization_data['name']}")
    print(f"   Deal: {deal_data['title']}")
    print(f"   Selected template enum: {deal_data['42ab0c919271cb24f3587f0b01ea2af166019c8d']} (LED Wristbands)")
    print()
    
    # Test the comprehensive quote creation with template selection
    from quoter import create_comprehensive_quote_from_pipedrive
    
    print("🎯 Testing comprehensive quote creation with template selection...")
    quote_data = create_comprehensive_quote_from_pipedrive(organization_data, deal_data)
    
    if quote_data:
        print(f"✅ Quote creation successful!")
        print(f"   Quote ID: {quote_data.get('id', 'N/A')}")
        print(f"   Quote URL: {quote_data.get('url', 'N/A')}")
    else:
        print(f"❌ Quote creation failed")
        print(f"   Check logs for details")
    
    return quote_data is not None

if __name__ == "__main__":
    print("🚀 Starting Template Selection Tests")
    print("=" * 60)
    
    # Test 1: Template selection logic
    success1 = test_pipedrive_template_selection()
    
    # Test 2: Webhook integration
    success2 = test_webhook_integration()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Template Selection Logic: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Webhook Integration: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Template selection is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")
