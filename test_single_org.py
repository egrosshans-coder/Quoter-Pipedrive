#!/usr/bin/env python3
"""
Test script for quote creation with a single sub-organization (3465).
Tests the complete workflow without fetching all organizations.
"""

from pipedrive import get_organization_by_id, get_deal_by_id
from quoter import create_quote_from_pipedrive_org
from utils.logger import logger
import os
from dotenv import load_dotenv

load_dotenv()

def test_single_organization_quote():
    """
    Test quote creation for a single organization (ID: 3465).
    """
    print("🧪 Testing Single Organization Quote Creation")
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
    
    # Test with specific organization ID: 3465
    org_id = 3465
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
    print("🎯 Ready to test quote creation!")
    print()
    print("⚠️  This is a DRY RUN - no actual quotes will be created")
    print("   To create actual quotes, run: python quote_monitor.py")
    print()
    
    # Show what would happen
    print("📋 What would happen when creating the quote:")
    print(f"   1. Extract deal ID: {extracted_deal_id}")
    print(f"   2. Get deal info from Pipedrive")
    print(f"   3. Extract contact information")
    print(f"   4. Create quote in Quoter with:")
    print(f"      - Quote number: PD-{extracted_deal_id}")
    print(f"      - Organization: {org_name}")
    print(f"      - Contact details from Pipedrive")
    print(f"      - Deal information linked")
    print(f"   5. Quoter automatically populates contact/org/deal info")
    
    print()
    print("=" * 60)
    print("🎯 Single Organization Test Complete!")
    print()
    print("Next steps:")
    print("1. Run 'python quote_monitor.py' to create actual quotes")
    print("2. Check Quoter dashboard for new draft quotes")
    print("3. Verify contact information is properly populated")

def main():
    """
    Main function to run the single organization test.
    """
    try:
        test_single_organization_quote()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
