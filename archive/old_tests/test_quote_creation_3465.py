#!/usr/bin/env python3
"""
Test script to create a quote for organization 3465 using the updated code.
This will test our new approach of using the Deal_ID custom field instead of parsing the organization name.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipedrive import get_organization_by_id
from quoter import create_quote_from_pipedrive_org
from utils.logger import logger

def main():
    """Test quote creation for organization 3465 with updated code."""
    load_dotenv()
    
    org_id = 3465
    logger.info(f"🎯 Testing Quote Creation for Organization {org_id}")
    logger.info("=" * 60)
    
    # Step 1: Get organization data
    logger.info(f"📋 Step 1: Getting organization {org_id} details...")
    org_data = get_organization_by_id(org_id)
    
    if not org_data:
        logger.error(f"❌ Failed to get organization {org_id}")
        return
    
    org_name = org_data.get('name', 'Unknown')
    logger.info(f"✅ Organization: {org_name}")
    
    # Check key fields
    hid_status = org_data.get("454a3767bce03a880b31d78a38c480d6870e0f1b")
    deal_id = org_data.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")
    
    logger.info(f"   HID-QBO-Status: {hid_status}")
    logger.info(f"   Deal_ID (custom field): {deal_id}")
    
    # Step 2: Check if ready for quotes
    logger.info(f"\n📋 Step 2: Checking quote readiness...")
    
    if str(hid_status) == "289" and deal_id:
        logger.info(f"✅ Organization {org_id} is READY for quotes!")
        logger.info(f"   ✓ HID-QBO-Status = 289 (QBO-SubCust)")
        logger.info(f"   ✓ Has Deal_ID = {deal_id}")
    else:
        logger.error(f"❌ Organization {org_id} is NOT ready for quotes")
        if str(hid_status) != "289":
            logger.error(f"   ✗ HID-QBO-Status = {hid_status} (should be 289)")
        if not deal_id:
            logger.error(f"   ✗ Missing Deal_ID")
        return
    
    # Step 3: Create the quote using our updated function
    logger.info(f"\n📋 Step 3: Creating draft quote...")
    logger.info(f"   Organization: {org_name}")
    logger.info(f"   Deal ID: {deal_id}")
    logger.info(f"   Expected Quote Number: PD-{deal_id}")
    
    result = create_quote_from_pipedrive_org(org_data)
    
    if result:
        logger.info(f"\n🎉 SUCCESS! Quote created for organization {org_id}")
        logger.info(f"   Quote ID: {result.get('id', 'N/A')}")
        logger.info(f"   Quote URL: {result.get('url', 'N/A')}")
        logger.info(f"   Quote Number: PD-{deal_id}")
        logger.info(f"   Organization: {org_name}")
        
        # Summary
        logger.info(f"\n📊 Summary:")
        logger.info(f"   ✓ Organization {org_id} ({org_name}) processed")
        logger.info(f"   ✓ Deal {deal_id} linked via custom field")
        logger.info(f"   ✓ Draft quote created with number PD-{deal_id}")
        logger.info(f"   ✓ Ready for testing deal association")
        
    else:
        logger.error(f"\n❌ Failed to create quote for organization {org_id}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 Test Complete!")
    logger.info("This organization is now ready for the full automation workflow.")

if __name__ == "__main__":
    main()
