#!/usr/bin/env python3
"""
Find all deals beginning with ZZ using direct API calls
"""

import requests
import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

def find_zz_deals():
    """Find all deals beginning with ZZ"""
    
    if not API_TOKEN:
        logger.error("❌ No Pipedrive API token found")
        return
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get all deals (with pagination)
        all_deals = []
        start = 0
        limit = 100
        
        while True:
            url = f"{BASE_URL}/deals"
            params = {
                "start": start,
                "limit": limit,
                "status": "all_not_deleted"
            }
            
            logger.info(f"🔍 Fetching deals {start}-{start+limit}...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                deals = data.get('data', [])
                
                if not deals:
                    break
                
                all_deals.extend(deals)
                start += limit
                
                # Check if we got fewer deals than requested (end of data)
                if len(deals) < limit:
                    break
            else:
                logger.error(f"❌ Failed to fetch deals: {response.status_code} - {response.text}")
                break
        
        logger.info(f"✅ Fetched {len(all_deals)} total deals")
        
        # Filter for ZZ deals
        zz_deals = []
        for deal in all_deals:
            title = deal.get('title', '')
            if title and title.upper().startswith('ZZ'):
                zz_deals.append(deal)
        
        logger.info(f"🎯 Found {len(zz_deals)} deals beginning with 'ZZ'")
        
        if zz_deals:
            logger.info("\n📋 ZZ Deals:")
            logger.info("=" * 80)
            
            for i, deal in enumerate(zz_deals, 1):
                deal_id = deal.get('id', 'Unknown')
                title = deal.get('title', 'No Title')
                stage = deal.get('stage_id', 'Unknown')
                org_id = deal.get('org_id', {}).get('value', 'No Org')
                org_name = deal.get('org_id', {}).get('name', 'No Org Name')
                person_id = deal.get('person_id', {}).get('value', 'No Person')
                person_name = deal.get('person_id', {}).get('name', 'No Person Name')
                value = deal.get('value', 'No Value')
                currency = deal.get('currency', 'USD')
                status = deal.get('status', 'Unknown')
                add_time = deal.get('add_time', 'Unknown')
                update_time = deal.get('update_time', 'Unknown')
                
                logger.info(f"\n{i}. Deal ID: {deal_id}")
                logger.info(f"   Title: {title}")
                logger.info(f"   Stage ID: {stage}")
                logger.info(f"   Organization: {org_name} (ID: {org_id})")
                logger.info(f"   Person: {person_name} (ID: {person_id})")
                logger.info(f"   Value: {currency} {value}")
                logger.info(f"   Status: {status}")
                logger.info(f"   Created: {add_time}")
                logger.info(f"   Updated: {update_time}")
                
                # Check for custom fields
                custom_fields = deal.get('custom_fields', {})
                if custom_fields:
                    logger.info(f"   Custom Fields:")
                    for field_key, field_value in custom_fields.items():
                        if field_value and field_value != 'None' and str(field_value).strip():
                            logger.info(f"     {field_key}: {field_value}")
        else:
            logger.info("📭 No deals found beginning with 'ZZ'")
            
    except Exception as e:
        logger.error(f"❌ Error finding ZZ deals: {e}")

if __name__ == "__main__":
    find_zz_deals()
