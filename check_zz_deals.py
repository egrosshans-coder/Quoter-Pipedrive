#!/usr/bin/env python3
"""
Check all deals in Pipedrive that begin with 'ZZ'
"""

import requests
import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

def get_all_zz_deals():
    """Get all deals that begin with 'ZZ'"""
    
    if not API_TOKEN:
        logger.error("❌ No Pipedrive API token found")
        return []
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Search for deals with "ZZ" in the title
        search_url = f"{BASE_URL}/deals/search"
        params = {
            "term": "ZZ",
            "fields": "title",
            "exact_match": "false"
        }
        
        logger.info("🔍 Searching for deals beginning with 'ZZ'...")
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            deals = data.get('data', {}).get('items', [])
            
            logger.info(f"✅ Found {len(deals)} deals with 'ZZ' in the title")
            
            # Get detailed info for each deal
            detailed_deals = []
            for deal in deals:
                deal_id = deal.get('id')
                if deal_id:
                    # Get full deal details
                    deal_url = f"{BASE_URL}/deals/{deal_id}"
                    deal_response = requests.get(deal_url, headers=headers, timeout=10)
                    
                    if deal_response.status_code == 200:
                        deal_data = deal_response.json().get('data', {})
                        detailed_deals.append(deal_data)
            
            return detailed_deals
        else:
            logger.error(f"❌ Failed to search deals: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        logger.error(f"❌ Error searching deals: {e}")
        return []

def display_zz_deals(deals):
    """Display all ZZ deals in a formatted way"""
    
    if not deals:
        logger.info("📭 No ZZ deals found")
        return
    
    logger.info(f"\n📋 Found {len(deals)} deals beginning with 'ZZ':")
    logger.info("=" * 80)
    
    for i, deal in enumerate(deals, 1):
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
        
        # Check for custom fields that might be relevant
        custom_fields = deal.get('custom_fields', {})
        if custom_fields:
            logger.info(f"   Custom Fields:")
            for field_key, field_value in custom_fields.items():
                if field_value and field_value != 'None':
                    logger.info(f"     {field_key}: {field_value}")

def main():
    """Main function"""
    logger.info("🚀 Starting ZZ deals search...")
    
    deals = get_all_zz_deals()
    display_zz_deals(deals)
    
    logger.info(f"\n✅ Search completed. Found {len(deals)} deals.")

if __name__ == "__main__":
    main()
