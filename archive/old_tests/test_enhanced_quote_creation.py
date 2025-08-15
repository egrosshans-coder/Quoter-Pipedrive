#!/usr/bin/env python3
"""
Test script for enhanced quote creation with native Quoter-Pipedrive integration.
Tests the complete workflow from organization detection to quote creation.
"""

from pipedrive import get_sub_organizations_ready_for_quotes
from quoter import create_quote_from_pipedrive_org
from utils.logger import logger
import os
from dotenv import load_dotenv

load_dotenv()

def test_enhanced_quote_creation():
    """
    Test the enhanced quote creation system.
    """
    print("🧪 Testing Enhanced Quote Creation System")
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
    
    # Get organizations ready for quotes
    print("🔍 Finding organizations ready for quote creation...")
    ready_orgs = get_sub_organizations_ready_for_quotes()
    
    if not ready_orgs:
        print("❌ No organizations ready for quotes found")
        return
    
    print(f"✅ Found {len(ready_orgs)} organizations ready for quotes")
    print()
    
    # Test with the first organization (dry run - don't actually create quotes)
    test_org = ready_orgs[0]
    org_name = test_org.get("name", "Unknown")
    org_id = test_org.get("id")
    
    print(f"🔍 Testing with organization: {org_name} (ID: {org_id})")
    print("-" * 50)
    
    # Extract deal ID from org name
    if "-" in org_name:
        deal_id = org_name.split("-")[-1]
        print(f"📋 Extracted deal ID: {deal_id}")
        
        try:
            int(deal_id)  # Validate it's a number
            print(f"✅ Deal ID validation: PASSED")
        except ValueError:
            print(f"❌ Deal ID validation: FAILED - '{deal_id}' is not a valid number")
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
    print(f"   1. Extract deal ID: {deal_id}")
    print(f"   2. Get deal info from Pipedrive")
    print(f"   3. Extract contact information")
    print(f"   4. Create quote in Quoter with:")
    print(f"      - Quote number: PD-{deal_id}")
    print(f"      - Organization: {org_name}")
    print(f"      - Contact details from Pipedrive")
    print(f"      - Deal information linked")
    
    print()
    print("=" * 60)
    print("🎯 Enhanced Quote Creation Test Complete!")
    print()
    print("Next steps:")
    print("1. Run 'python quote_monitor.py' to create actual quotes")
    print("2. Check Quoter dashboard for new draft quotes")
    print("3. Verify contact information is properly populated")

def main():
    """
    Main function to run the enhanced quote creation test.
    """
    try:
        test_enhanced_quote_creation()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
