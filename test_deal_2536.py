#!/usr/bin/env python3
"""
Test quoter.py with deal 2536
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Import the functions
from quoter_enhanced import create_comprehensive_quote_with_bundles
from pipedrive import get_deal_by_id

def test_deal_2536():
    print("🎯 TESTING DEAL 2536")
    print("=" * 50)
    
    # Use deal 2536
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
    
    # Extract real contact data from deal
    person_data = deal_data.get('person_id', {})
    org_data = deal_data.get('org_id', {})
    
    # Get email from person data
    email = "test@example.com"  # Default fallback
    if person_data.get('email') and isinstance(person_data['email'], list):
        email = person_data['email'][0].get('value', email)
    elif isinstance(person_data.get('email'), str):
        email = person_data['email']
    
    # Create organization data with real contact info
    organization_data = {
        "id": f"org_{deal_id}",
        "name": org_data.get('name', f"ZZ19-Org-{deal_id}"),
        "email": email,
        "person_name": person_data.get('name', 'ZZ19 Lastname'),
        "phone": person_data.get('phone', [{}])[0].get('value', '') if person_data.get('phone') else '',
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": deal_id  # Deal_ID custom field
    }
    
    print(f"📋 Using real contact data:")
    print(f"   Person: {organization_data['person_name']}")
    print(f"   Email: {organization_data['email']}")
    print(f"   Organization: {organization_data['name']}")
    print(f"   Phone: {organization_data['phone']}")
    
    print("🚀 Creating quote using comprehensive function...")
    
    # Use the comprehensive function that should read template from deal
    quote_data = create_comprehensive_quote_with_bundles(organization_data, deal_data)
    
    if quote_data:
        quote_id = quote_data.get("id")
        template_id = quote_data.get("template_id")
        
        print(f"✅ Quote created successfully!")
        print(f"   Quote ID: {quote_id}")
        print(f"   Template ID: {template_id}")
        print(f"   URL: {quote_data.get('url', 'N/A')}")
        
        return quote_id
    else:
        print("❌ Failed to create quote")
        return None

if __name__ == "__main__":
    quote_id = test_deal_2536()
    if quote_id:
        print(f"\n🔗 Check the quote URL to verify the template")
    else:
        print(f"\n❌ Test failed")
