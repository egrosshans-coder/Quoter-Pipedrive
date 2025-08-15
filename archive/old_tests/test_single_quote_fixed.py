#!/usr/bin/env python3
"""
Simple test to create ONE quote and see if contact data populates correctly.
"""

from pipedrive import get_organization_by_id
from quoter import create_quote_from_pipedrive_org

def test_single_quote_fixed():
    """Test creating ONE quote with fixed contact logic."""
    
    print("🧪 Testing Single Quote Creation with Fixed Contact Logic")
    print("=" * 60)
    print("Goal: Create ONE quote and see if contact data populates")
    print()
    
    # Get the real organization data from Pipedrive (ID 3465)
    print("📡 Fetching organization data from Pipedrive...")
    org_data = get_organization_by_id(3465)
    
    if not org_data:
        print("❌ Failed to fetch organization data")
        return
    
    print(f"✅ Got organization data:")
    print(f"   Name: {org_data.get('name')}")
    print(f"   ID: {org_data.get('id')}")
    
    # Check if it has the Deal_ID custom field
    deal_id = org_data.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")
    if deal_id:
        print(f"   Deal ID: {deal_id}")
    else:
        print("   Deal ID: NOT FOUND")
        print("   Available custom fields:")
        for key, value in org_data.items():
            if key.startswith("15034"):  # Custom field keys
                print(f"     {key}: {value}")
        return
    
    print()
    print("📝 Creating quote...")
    print("Expected behavior:")
    print("  ✅ Should find existing Robert Lee contact")
    print("  ✅ Contact data should populate from existing contact")
    print("  ✅ Template should be 'Managed Service Proposal'")
    print("  ✅ Quote number should show 'PD-2096'")
    print("  ✅ Organization should be 'Blue Owl Capital'")
    print()
    
    try:
        # Create the quote using the real organization data
        quote_data = create_quote_from_pipedrive_org(org_data)
        
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
    test_single_quote_fixed()
