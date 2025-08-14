#!/usr/bin/env python3
"""
Test Comprehensive Quote Creation - Clean Field Mapping

This script tests the simplified comprehensive quote creation function that maps
ALL available Pipedrive data to standard Quoter contact fields.

Goal: Create a clean draft quote with comprehensive contact information,
letting Quoter's native integration handle the Pipedrive linking.
"""

from pipedrive import get_organization_by_id
from quoter import create_comprehensive_quote_from_pipedrive

def test_comprehensive_quote_creation():
    """Test creating a comprehensive quote with clean field mapping."""
    
    print("🧪 Testing Clean Comprehensive Quote Creation")
    print("=" * 60)
    print("Goal: Create clean draft quote with maximum available Pipedrive data")
    print()
    
    # Test with Blue Owl Capital (organization 3465)
    org_id = 3465
    print(f"🎯 Testing with Organization ID: {org_id}")
    print()
    
    # Get the real organization data from Pipedrive
    print("📡 Fetching organization data from Pipedrive...")
    org_data = get_organization_by_id(org_id)
    
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
    print("🔍 Data Available for Contact Mapping:")
    print("-" * 40)
    
    # Show what data we can extract for contact creation
    address_fields = ['address', 'city', 'state', 'postal_code', 'country']
    contact_fields = ['phone', 'email', 'website']
    
    print("🏠 Address Information:")
    for field in address_fields:
        value = org_data.get(field, "NOT FOUND")
        print(f"   {field}: {value}")
    
    print("\n📞 Contact Information:")
    for field in contact_fields:
        value = org_data.get(field, "NOT FOUND")
        print(f"   {field}: {value}")
    
    print()
    print("📝 Creating comprehensive quote...")
    print("Expected behavior:")
    print("  ✅ Should create rich contact with ALL available fields")
    print("  ✅ Should include comprehensive address information")
    print("  ✅ Should create clean, simple draft quote")
    print("  ✅ Should let Quoter's native integration handle linking")
    print()
    
    try:
        # Create the comprehensive quote
        quote_data = create_comprehensive_quote_from_pipedrive(org_data)
        
        if quote_data:
            print("🎉 SUCCESS! Clean comprehensive quote created:")
            print(f"   Quote ID: {quote_data.get('id')}")
            print(f"   Name: {quote_data.get('name')}")
            print(f"   URL: {quote_data.get('url')}")
            
            print(f"\n🔍 Next steps:")
            print(f"   1. Check this quote in Quoter UI")
            print(f"   2. Verify comprehensive contact data is populated")
            print(f"   3. Use Quoter's native dropdowns to link person/org/deal")
            print(f"   4. Complete the quote and publish")
            
            print(f"\n💡 This demonstrates:")
            print(f"   - Clean, simple implementation")
            print(f"   - Maximum data mapping to standard fields")
            print(f"   - Leveraging Quoter's native Pipedrive integration")
            
        else:
            print("❌ Failed to create comprehensive quote")
            
    except Exception as e:
        print(f"❌ Error creating comprehensive quote: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comprehensive_quote_creation()
