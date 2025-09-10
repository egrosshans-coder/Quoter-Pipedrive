#!/usr/bin/env python3
"""
Check Quote Template field enum values in Pipedrive
"""

import os
import requests
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def get_template_enum_values():
    """Get all enum values for the Quote Template field"""
    
    # Pipedrive API credentials
    api_token = os.getenv('PIPEDRIVE_API_TOKEN')
    if not api_token:
        logger.error("❌ PIPEDRIVE_API_TOKEN not found in environment")
        return
    
    # Quote Template field API key
    template_field_key = "42ab0c919271cb24f3587f0b01ea2af166019c8d"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get field details including enum options
        url = f"https://api.pipedrive.com/v1/dealFields/{template_field_key}"
        logger.info(f"🔍 Fetching field details for Quote Template field...")
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            field_data = response.json()
            field_info = field_data.get('data', {})
            
            logger.info(f"✅ Field Name: {field_info.get('name', 'Unknown')}")
            logger.info(f"✅ Field Key: {field_info.get('key', 'Unknown')}")
            logger.info(f"✅ Field Type: {field_info.get('field_type', 'Unknown')}")
            
            # Get enum options
            options = field_info.get('options', [])
            logger.info(f"\n📋 Available Template Options ({len(options)} total):")
            logger.info("=" * 60)
            
            for i, option in enumerate(options, 1):
                option_id = option.get('id')
                option_label = option.get('label', 'No Label')
                logger.info(f"{i:2d}. ID: {option_id:3d} | Label: {option_label}")
            
            # Check if 441 exists
            option_441 = next((opt for opt in options if opt.get('id') == 441), None)
            if option_441:
                logger.info(f"\n✅ Found option 441: {option_441.get('label', 'No Label')}")
            else:
                logger.warning(f"\n❌ Option 441 NOT FOUND in enum values")
                logger.info("Available IDs:", [opt.get('id') for opt in options])
                
        else:
            logger.error(f"❌ Failed to get field details: {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error fetching template enum values: {e}")

if __name__ == "__main__":
    get_template_enum_values()
