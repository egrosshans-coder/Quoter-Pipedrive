#!/usr/bin/env python3
"""
Retry ZZ11 quote creation manually
This simulates what the webhook would do for ZZ11
"""

import os
import sys
from dotenv import load_dotenv
from pipedrive import get_organization_by_id, get_deal_by_id
from quoter import create_comprehensive_quote_from_pipedrive
from utils.logger import logger

load_dotenv()

def retry_zz11():
    """Manually retry ZZ11 quote creation"""
    
    # ZZ11 organization ID (you'll need to get this from Pipedrive)
    # Let's try to find it by searching for organizations with "ZZ11" in the name
    logger.info("🔍 Searching for ZZ11 organization...")
    
    # First, let's get the organization ID for ZZ11
    # We'll need to search for it or you can provide the ID
    org_id = input("Enter the ZZ11 organization ID from Pipedrive: ").strip()
    
    if not org_id:
        logger.error("❌ No organization ID provided")
        return False
    
    try:
        # Get organization data
        logger.info(f"📋 Fetching organization {org_id} data...")
        organization_data = get_organization_by_id(org_id)
        
        if not organization_data:
            logger.error(f"❌ Could not find organization {org_id}")
            return False
        
        logger.info(f"✅ Found organization: {organization_data.get('name', 'Unknown')}")
        
        # Extract deal ID from organization name
        org_name = organization_data.get('name', '')
        if '-' in org_name:
            deal_id = org_name.split('-')[-1]
            logger.info(f"🎯 Extracted deal ID: {deal_id} from organization: {org_name}")
        else:
            logger.error(f"❌ Organization name '{org_name}' does not contain deal ID")
            return False
        
        # Get deal data
        logger.info(f"📋 Fetching deal {deal_id} data...")
        deal_data = get_deal_by_id(deal_id)
        
        if not deal_data:
            logger.error(f"❌ Could not find deal {deal_id}")
            return False
        
        logger.info(f"✅ Found deal: {deal_data.get('title', 'Unknown')}")
        
        # Create the quote
        logger.info("🚀 Creating quote for ZZ11...")
        quote_data = create_comprehensive_quote_from_pipedrive(organization_data, deal_data)
        
        if quote_data:
            logger.info(f"✅ Successfully created quote for ZZ11!")
            logger.info(f"   Quote ID: {quote_data.get('id')}")
            logger.info(f"   Quote Name: {quote_data.get('name')}")
            logger.info(f"   Status: {quote_data.get('status')}")
            return True
        else:
            logger.error("❌ Failed to create quote for ZZ11")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error retrying ZZ11: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔄 Retrying ZZ11 quote creation...")
    success = retry_zz11()
    
    if success:
        logger.info("🎉 ZZ11 quote creation completed successfully!")
    else:
        logger.error("💥 ZZ11 quote creation failed!")
        sys.exit(1)
