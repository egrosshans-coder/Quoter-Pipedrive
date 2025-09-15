#!/usr/bin/env python3
"""
Test that the system correctly selects the template from the Pipedrive deal
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import create_comprehensive_quote_from_pipedrive
from pipedrive import get_deal_by_id

def test_deal_template_selection():
    print("🎯 TESTING DEAL TEMPLATE SELECTION")
    print("=" * 50)
    
    # Use deal 2536 (ZZ19-deal) that you updated
    deal_id = 2536
    
    print(f"📋 Testing with deal ID: {deal_id}")
    
    # Get the actual deal data from Pipedrive
    print("🔍 Fetching deal data from Pipedrive...")
    deal_data = get_deal_by_id(deal_id)
    
    if not deal_data:
        print(f"❌ Failed to get deal {deal_id} from Pipedrive")
        return None
    
    print(f"✅ Deal found: {deal_data.get('title', 'Unknown')}")
    
    # Check the Quote Template field
    template_field_id = "42ab0c919271cb24f3587f0b01ea2af166019c8d"
    template_enum_value = deal_data.get(template_field_id)
    
    print(f"📋 Quote Template field value: {template_enum_value}")
    
    # Create mock organization data with the deal ID
    organization_data = {
        "id": "org_test_2536",
        "name": "ZZ19-Org-2536",
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": deal_id  # Deal_ID custom field
    }
    
    print("🚀 Creating quote using comprehensive function...")
    
    # Use the comprehensive function that should read template from deal
    quote_data = create_comprehensive_quote_from_pipedrive(organization_data, deal_data)
    
    if quote_data:
        quote_id = quote_data.get("id")
        template_id = quote_data.get("template_id")
        
        print(f"✅ Quote created successfully!")
        print(f"   Quote ID: {quote_id}")
        print(f"   Template ID: {template_id}")
        print(f"   URL: {quote_data.get('url', 'N/A')}")
        
        # Check if it's the correct Floating Video template
        if template_id == "tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG":
            print("🎉 SUCCESS! Using correct Floating Video template!")
        else:
            print(f"⚠️ Using template: {template_id} (not Floating Video)")
            
        return quote_id
    else:
        print("❌ Failed to create quote")
        return None

if __name__ == "__main__":
    quote_id = test_deal_template_selection()
    if quote_id:
        print(f"\n🔗 Check the quote URL to verify the template")
    else:
        print(f"\n❌ Test failed")
