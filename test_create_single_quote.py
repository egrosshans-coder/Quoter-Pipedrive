#!/usr/bin/env python3
"""
Test script to create a single quote for organization 3465.
This will test the complete quote creation workflow.
"""

from pipedrive import get_organization_by_id
from quoter import create_quote_from_pipedrive_org
from utils.logger import logger
import os
from dotenv import load_dotenv

load_dotenv()

def create_single_quote():
    """
    Create a single quote for organization 3465.
    """
    print("🎯 Creating Single Quote for Organization 3465")
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
    print(f"🔍 Working with organization ID: {org_id}")
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
        return
    
    print("✅ Organization is ready for quote creation")
    print()
    
    # Now create the actual quote
    print("🚀 Creating quote in Quoter...")
    print("   This will:")
    print("   1. Extract deal ID from org name")
    print("   2. Get deal info from Pipedrive")
    print("   3. Extract contact information")
    print("   4. Create quote in Quoter")
    print("   5. Quoter will auto-populate contact/org/deal info")
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
            print("   2. Verify contact information is populated")
            print("   3. Verify organization and deal details are correct")
        else:
            print("❌ FAILED! Quote creation failed")
            print("   Check the logs above for error details")
            
    except Exception as e:
        print(f"❌ ERROR during quote creation: {e}")
        raise

def main():
    """
    Main function to create a single quote.
    """
    try:
        create_single_quote()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
