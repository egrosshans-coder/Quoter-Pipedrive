#!/usr/bin/env python3
"""
Simple check for ZZ deals using the existing pipedrive functions
"""

import os
from dotenv import load_dotenv
from pipedrive import get_all_deals
from utils.logger import logger

load_dotenv()

def check_zz_deals():
    """Check for deals beginning with ZZ"""
    
    try:
        logger.info("🔍 Fetching all deals to find ZZ deals...")
        
        # Get all deals
        deals = get_all_deals()
        
        if not deals:
            logger.error("❌ No deals found")
            return
        
        # Filter for ZZ deals
        zz_deals = []
        for deal in deals:
            title = deal.get('title', '')
            if title and title.upper().startswith('ZZ'):
                zz_deals.append(deal)
        
        logger.info(f"✅ Found {len(zz_deals)} deals beginning with 'ZZ'")
        
        if zz_deals:
            logger.info("\n📋 ZZ Deals:")
            logger.info("=" * 60)
            
            for i, deal in enumerate(zz_deals, 1):
                deal_id = deal.get('id', 'Unknown')
                title = deal.get('title', 'No Title')
                stage = deal.get('stage_id', 'Unknown')
                org_id = deal.get('org_id', {}).get('value', 'No Org')
                org_name = deal.get('org_id', {}).get('name', 'No Org Name')
                value = deal.get('value', 'No Value')
                currency = deal.get('currency', 'USD')
                status = deal.get('status', 'Unknown')
                
                logger.info(f"\n{i}. Deal ID: {deal_id}")
                logger.info(f"   Title: {title}")
                logger.info(f"   Stage ID: {stage}")
                logger.info(f"   Organization: {org_name} (ID: {org_id})")
                logger.info(f"   Value: {currency} {value}")
                logger.info(f"   Status: {status}")
        else:
            logger.info("📭 No deals found beginning with 'ZZ'")
            
    except Exception as e:
        logger.error(f"❌ Error checking ZZ deals: {e}")

if __name__ == "__main__":
    check_zz_deals()
