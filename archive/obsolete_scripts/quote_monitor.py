#!/usr/bin/env python3
"""
Quote Monitor - Main script for quote automation
Monitors for sub-organizations ready for quote creation and creates draft quotes in Quoter.
"""

import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from quoter import create_quote_from_pipedrive_org
from pipedrive import get_sub_organizations_ready_for_quotes, get_deal_by_id, get_organization_by_id
from utils.logger import logger
from notification import send_quote_created_notification

load_dotenv()

def process_ready_organizations():
    """
    Process organizations that are ready for quote creation.
    """
    logger.info("🔍 Checking for organizations ready for quote creation...")
    
    # Get organizations ready for quotes
    ready_orgs = get_sub_organizations_ready_for_quotes()
    
    if not ready_orgs:
        logger.info("No organizations ready for quote creation")
        return
    
    logger.info(f"Found {len(ready_orgs)} organizations ready for quote creation")
    
    for org in ready_orgs:
        try:
            org_id = org.get("id")
            org_name = org.get("name")
            deal_id = org.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")  # Deal_ID field
            
            if not deal_id:
                logger.warning(f"Organization {org_id} ({org_name}) has no associated deal ID")
                continue
            
            logger.info(f"Processing organization {org_id} ({org_name}) for deal {deal_id}")
            
            # Get deal information
            deal_data = get_deal_by_id(deal_id)
            if not deal_data:
                logger.warning(f"Could not find deal {deal_id} for organization {org_id}")
                continue
            
            deal_title = deal_data.get("title", f"Deal {deal_id}")
            
            # Create draft quote using enhanced Pipedrive integration
            quote_data = create_quote_from_pipedrive_org(org)
            
            if quote_data:
                # Send notification
                send_quote_created_notification(quote_data, deal_data, org)
                
                # TODO: Optionally update the organization status to indicate quote was created
                logger.info(f"✅ Successfully processed organization {org_id} for deal {deal_id}")
            else:
                logger.error(f"❌ Failed to create quote for organization {org_id} (deal {deal_id})")
                
        except Exception as e:
            logger.error(f"❌ Error processing organization {org.get('id', 'Unknown')}: {e}")

def main():
    """
    Main function that runs the quote monitoring process.
    """
    logger.info("🚀 Starting Quote Monitor...")
    
    try:
        # Check if we have the required environment variables
        if not os.getenv("QUOTER_API_KEY") or not os.getenv("QUOTER_CLIENT_SECRET"):
            logger.error("Missing Quoter API credentials in environment variables")
            return
        
        if not os.getenv("PIPEDRIVE_API_TOKEN"):
            logger.error("Missing Pipedrive API token in environment variables")
            return
        
        # Process ready organizations
        process_ready_organizations()
        
        logger.info("✅ Quote Monitor completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Quote Monitor failed: {e}")
        raise

if __name__ == "__main__":
    main()
