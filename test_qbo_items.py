#!/usr/bin/env python3
"""
Test script to check if QBO Items API is accessible
"""

import os
import requests
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

def test_qbo_items_api():
    """Test if we can access the QBO Items API"""
    
    # Get access token
    token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": os.getenv('QBO_REFRESH_TOKEN')
    }
    
    try:
        response = requests.post(token_url, headers=headers, data=data, 
                               auth=(os.getenv('QBO_CLIENT_ID'), os.getenv('QBO_CLIENT_SECRET')))
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            logger.error("❌ No access token received")
            return False
            
        logger.info("✅ Successfully obtained QBO access token")
        
        # Test Items API
        base_url = "https://quickbooks.api.intuit.com"
        company_id = os.getenv('QBO_COMPANY_ID')
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        # Try to get items
        url = f"{base_url}/v3/company/{company_id}/items"
        
        logger.info(f"🔍 Testing QBO Items API: {url}")
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            items = result.get("QueryResponse", {}).get("Item", [])
            logger.info(f"✅ SUCCESS! Found {len(items)} items in QBO")
            logger.info("🎉 QBO Items API is working!")
            return True
        else:
            logger.error(f"❌ Items API failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing QBO Items API: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing QBO Items API Access")
    logger.info("=" * 50)
    
    success = test_qbo_items_api()
    
    if success:
        logger.info("\n🎉 QBO Items API is working! You can now sync items.")
    else:
        logger.info("\n❌ QBO Items API is not working. Please check your QBO settings.")
        logger.info("   Make sure Items/Inventory tracking is enabled in QBO.")
