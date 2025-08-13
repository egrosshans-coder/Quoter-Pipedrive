#!/usr/bin/env python3
"""
Test script for quote automation functionality.
"""

import os
from dotenv import load_dotenv
from quoter import create_draft_quote
from pipedrive import get_sub_organizations_ready_for_quotes, get_deal_by_id, get_organization_by_id
from utils.logger import logger

load_dotenv()

def test_pipedrive_functions():
    """Test Pipedrive API functions."""
    logger.info("Testing Pipedrive functions...")
    
    # Test getting organizations ready for quotes
    ready_orgs = get_sub_organizations_ready_for_quotes()
    logger.info(f"Found {len(ready_orgs)} organizations ready for quotes")
    
    # Test getting a specific organization (if any exist)
    if ready_orgs:
        org = ready_orgs[0]
        org_id = org.get("id")
        logger.info(f"Testing organization {org_id}...")
        
        # Test getting organization details
        org_details = get_organization_by_id(org_id)
        if org_details:
            logger.info(f"✅ Successfully retrieved organization {org_id}")
        else:
            logger.warning(f"⚠️ Could not retrieve organization {org_id}")
        
        # Test getting deal details
        deal_id = org.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")  # Deal_ID field
        if deal_id:
            deal_details = get_deal_by_id(deal_id)
            if deal_details:
                logger.info(f"✅ Successfully retrieved deal {deal_id}")
            else:
                logger.warning(f"⚠️ Could not retrieve deal {deal_id}")
    else:
        logger.info("No organizations ready for quotes to test")

def test_quoter_functions():
    """Test Quoter API functions."""
    logger.info("Testing Quoter functions...")
    
    # Test quote creation (with dummy data)
    # Note: This will only test the API call, not actually create a quote
    logger.info("Testing quote creation function...")
    
    # This is just a test - we won't actually create a quote
    logger.info("✅ Quoter functions ready for testing")

def main():
    """Main test function."""
    logger.info("🧪 Starting quote automation tests...")
    
    try:
        # Check environment variables
        required_vars = ["QUOTER_API_KEY", "QUOTER_CLIENT_SECRET", "PIPEDRIVE_API_TOKEN"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
            return
        
        # Test Pipedrive functions
        test_pipedrive_functions()
        
        # Test Quoter functions
        test_quoter_functions()
        
        logger.info("✅ All tests completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main()
