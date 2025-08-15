#!/usr/bin/env python3
"""
Quick check of the quote we just created to see what fields are populated.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token
from utils.logger import logger
import requests

def main():
    """Check the status of the quote we just created."""
    load_dotenv()
    
    quote_id = "quot_316zYtlHF4enuMG8eDmQCY0JVtO"
    
    logger.info(f"🔍 Checking quote {quote_id}...")
    
    # Get OAuth token
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth token")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get quote details
    try:
        response = requests.get(
            f"https://api.quoter.com/v1/quotes/{quote_id}",
            headers=headers,
            timeout=10
        )
        
        logger.info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            quote_data = response.json()
            logger.info("📋 Quote Details:")
            logger.info(f"   ID: {quote_data.get('id')}")
            logger.info(f"   Number: {quote_data.get('number')}")
            logger.info(f"   Name: {quote_data.get('name')}")
            logger.info(f"   Status: {quote_data.get('status')}")
            logger.info(f"   Contact ID: {quote_data.get('contact_id')}")
            logger.info(f"   Template ID: {quote_data.get('template_id')}")
            
            # Check for custom fields
            custom_fields = quote_data.get('custom_fields', {})
            if custom_fields:
                logger.info("   Custom Fields:")
                for key, value in custom_fields.items():
                    logger.info(f"     {key}: {value}")
            else:
                logger.info("   No custom fields found")
                
        else:
            logger.error(f"Failed to get quote: {response.text}")
            
    except Exception as e:
        logger.error(f"Error checking quote: {e}")

if __name__ == "__main__":
    main()
