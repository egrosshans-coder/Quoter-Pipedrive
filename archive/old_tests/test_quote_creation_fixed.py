#!/usr/bin/env python3
"""
Test script to create a quote and see if contact data now populates correctly
with the fixed contact logic.
"""

from quoter import create_quote_from_pipedrive_org
from pipedrive import get_sub_organizations_ready_for_quotes

def test_quote_creation_fixed():
    """Test quote creation with fixed contact logic."""
    
    print("🧪 Testing Quote Creation with Fixed Contact Logic")
    print("=" * 60)
    print("Goal: See if contact data now populates correctly")
    print()
    
    # Get organizations ready for quotes
    print("📡 Fetching organizations ready for quotes...")
    orgs = get_sub_organizations_ready_for_quotes()
    
    if not orgs:
        print("❌ No organizations found")
        return
    
    print(f"✅ Found {len(orgs)} organizations")
    
    # Test with the first organization
    test_org = orgs[0]
    print(f"\n🎯 Testing with organization: {test_org.get('name')}")
    print(f"   ID: {test_org.get('id')}")
    print(f"   Deal ID: {test_org.get('deal_id')}")
    print(f"   Contact: {test_org.get('contact_name')}")
    print(f"   Email: {test_org.get('contact_email')}")
    print()
    
    print("📝 Creating quote...")
    print("Expected behavior:")
    print("  ✅ Contact data should populate from existing contact")
    print("  ✅ Template should be 'Managed Service Proposal'")
    print("  ✅ Quote number should show 'PD-####'")
    print("  ✅ Organization should be correct")
    print()
    
    try:
        # Create the quote
        quote_data = create_quote_from_pipedrive_org(test_org)
        
        if quote_data:
            print("🎉 SUCCESS! Quote created:")
            print(f"   Quote ID: {quote_data.get('id')}")
            print(f"   Name: {quote_data.get('name')}")
            print(f"   Number: {quote_data.get('number')}")
            print(f"   Status: {quote_data.get('status')}")
            print(f"   Contact ID: {quote_data.get('contact_id')}")
            print(f"   Template ID: {quote_data.get('template_id')}")
            print(f"   Pipedrive Deal ID: {quote_data.get('pipedrive_deal_id')}")
            
            print(f"\n🔍 Next steps:")
            print(f"   1. Check this quote in Quoter UI")
            print(f"   2. Verify contact/org data is populated")
            print(f"   3. Check if quote number shows correctly")
            print(f"   4. Look for deal association options")
            
        else:
            print("❌ Failed to create quote")
            
    except Exception as e:
        print(f"❌ Error creating quote: {e}")

if __name__ == "__main__":
    test_quote_creation_fixed()
