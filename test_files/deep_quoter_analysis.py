#!/usr/bin/env python3
"""
Deep analysis of Quoter API to find hierarchy field
"""

import os
import json
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

def deep_quoter_analysis():
    """Deep analysis of Quoter API to find hierarchy field"""
    from quoter import get_access_token
    import requests
    
    quoter_token = get_access_token()
    
    logger.info("🔍 Deep analysis of Quoter API...")
    
    # Get a single item to see the full raw response
    url = f"https://api.quoter.com/v1/items"
    headers = {
        'Authorization': f'Bearer {quoter_token}',
        'Content-Type': 'application/json'
    }
    params = {
        'page': 1,
        'per_page': 1
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"📊 Raw API response structure:")
        logger.info(f"Keys in response: {list(data.keys())}")
        
        if 'data' in data and len(data['data']) > 0:
            item = data['data'][0]
            logger.info(f"\n📋 First item raw JSON:")
            logger.info(json.dumps(item, indent=2))
            
            # Look for any field that might contain hierarchy
            logger.info(f"\n🔍 Looking for hierarchy patterns in all fields:")
            for key, value in item.items():
                if isinstance(value, str):
                    if ':' in value and not any(x in value for x in ['T', 'Z', 'http', 'www']):
                        logger.info(f"  {key}: '{value}' (potential hierarchy)")
                elif isinstance(value, dict):
                    logger.info(f"  {key}: {value} (dictionary)")
                    # Check if any values in the dict contain colons
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str) and ':' in sub_value and not any(x in sub_value for x in ['T', 'Z', 'http', 'www']):
                            logger.info(f"    {sub_key}: '{sub_value}' (potential hierarchy)")
                elif isinstance(value, list):
                    logger.info(f"  {key}: {value} (list)")
                    # Check if any items in the list contain colons
                    for i, list_item in enumerate(value):
                        if isinstance(list_item, str) and ':' in list_item and not any(x in list_item for x in ['T', 'Z', 'http', 'www']):
                            logger.info(f"    [{i}]: '{list_item}' (potential hierarchy)")
        else:
            logger.error("No data in response")
    else:
        logger.error(f"Failed to fetch Quoter items: {response.status_code}")
        logger.error(f"Response: {response.text}")
    
    # Try to get Nitrogen regulator specifically
    logger.info(f"\n🔍 Getting Nitrogen regulator specifically...")
    
    # Search for Nitrogen regulator
    search_url = f"https://api.quoter.com/v1/items"
    search_params = {
        'page': 1,
        'per_page': 100,
        'search': 'nitrogen'
    }
    
    search_response = requests.get(search_url, headers=headers, params=search_params)
    
    if search_response.status_code == 200:
        search_data = search_response.json()
        logger.info(f"📊 Search results for 'nitrogen':")
        logger.info(f"Found {len(search_data.get('data', []))} items")
        
        for item in search_data.get('data', []):
            if 'nitrogen' in item.get('name', '').lower():
                logger.info(f"\n📋 Nitrogen item found:")
                logger.info(json.dumps(item, indent=2))
                break
    else:
        logger.error(f"Search failed: {search_response.status_code}")
        logger.error(f"Response: {search_response.text}")

if __name__ == "__main__":
    deep_quoter_analysis()




