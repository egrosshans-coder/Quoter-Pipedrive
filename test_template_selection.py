#!/usr/bin/env python3
"""
Test script to verify template selection and quote creation for Blue Owl Capital-2096.
This tests the complete workflow with the "test" template.
"""

from pipedrive import get_organization_by_id
from quoter import create_quote_from_pipedrive_org
from utils.logger import logger
import os
from dotenv import load_dotenv

load_dotenv()

def test_template_selection_and_quote():
    """
    Test template selection and quote creation for Blue Owl Capital-2096.
    """
    print("🧪 Testing Template Selection and Quote Creation")
    print("=" * 60)
    
    # Check if we have the required environment variables
    if not os.getenv("QUOTER_API_KEY") or not os.getenv("QUOTER_CLIENT_SECRET"):
        print("❌ Missing Quoter API credentials in environment variables")
        print("   Please set QUOTER_API_KEY and QUOTER_CLIENT_SECRET")
        return
    
    if not os.getenv("PIPEDRIVE_API_TOKEN"):
        print("❌ Missing Pipedrive API token in environment variables")
        print("   Please set PIPEDRIVE_API_TOKEN")
        return
    
    print("✅ Environment variables configured")
    print()
    
    # Test with specific organization: Blue Owl Capital-2096
    org_id = 3465  # Blue Owl Capital-2096
    print(f"🔍 Testing with organization ID: {org_id}")
    print("-" * 50)
    
    # Get organization data directly
    org_data = get_organization_by_id(org_id)
    if not org_data:
        print(f"❌ Could not find organization {org_id}")
        return
    
    org_name = org_data.get("name", "Unknown")
    print(f"📋 Organization: {org_name}")
    
    # Check if it's ready for quotes
    qbo_status = org_data.get("454a3767bce03a880b31d78a38c480d6870e0f1b")
    deal_id = org_data.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")
    
    print(f"📊 QBO Status: {qbo_status}")
    print(f"📊 Deal ID: {deal_id}")
    
    if str(qbo_status) != "289" or not deal_id:
        print("❌ Organization not ready for quotes")
        print("   QBO Status should be 289 (QBO-SubCust)")
        print("   Deal ID should be present")
        return
    
    print("✅ Organization is ready for quote creation")
    print()
    
    # Extract deal ID from org name
    if "-" in org_name:
        extracted_deal_id = org_name.split("-")[-1]
        print(f"📋 Extracted deal ID from name: {extracted_deal_id}")
        
        try:
            int(extracted_deal_id)  # Validate it's a number
            print(f"✅ Deal ID validation: PASSED")
        except ValueError:
            print(f"❌ Deal ID validation: FAILED - '{extracted_deal_id}' is not a valid number")
            return
    else:
        print(f"❌ Organization name format invalid: {org_name}")
        print("   Expected format: 'CompanyName-1234'")
        return
    
    print()
    print("🎯 Ready to test quote creation with 'test' template!")
    print()
    print("⚠️  This will create an ACTUAL quote in Quoter")
    print("   Template: 'test' (not 'Managed Service Proposal')")
    print("   Organization: Blue Owl Capital-2096")
    print("   Deal ID: 2096")
    print()
    
    # Confirm before proceeding
    confirm = input("Do you want to proceed with creating the quote? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Quote creation cancelled")
        return
    
    # Now create the actual quote
    print("🚀 Creating quote in Quoter with 'test' template...")
    print("   This will:")
    print("   1. Select 'test' template (not 'Managed Service Proposal')")
    print("   2. Extract deal ID from org name")
    print("   3. Get deal info from Pipedrive")
    print("   4. Extract contact information")
    print("   5. Create quote in Quoter with 'test' template")
    print()
    
    try:
        quote_data = create_quote_from_pipedrive_org(org_data)
        
        if quote_data:
            print("🎉 SUCCESS! Quote created successfully!")
            print(f"   Quote ID: {quote_data.get('id')}")
            print(f"   Quote Number: {quote_data.get('quote_number', 'N/A')}")
            print(f"   URL: {quote_data.get('url', 'N/A')}")
            print()
            print("✅ Next steps:")
            print("   1. Check Quoter dashboard for the new quote")
            print("   2. Verify 'test' template is being used")
            print("   3. Verify contact information is populated")
            print("   4. Verify organization and deal details are correct")
        else:
            print("❌ FAILED! Quote creation failed")
            print("   Check the logs above for error details")
            
    except Exception as e:
        print(f"❌ ERROR during quote creation: {e}")
        raise

def main():
    """
    Main function to test template selection and quote creation.
    """
    try:
        test_template_selection_and_quote()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
