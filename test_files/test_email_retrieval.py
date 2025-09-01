#!/usr/bin/env python3
"""
Test script to debug email address retrieval from Pipedrive.
This will help us understand why update_contact_address is failing.
"""
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipedrive import update_contact_address
from utils.logger import logger

load_dotenv()

def test_email_retrieval():
    """Test email retrieval with sample contact data."""
    logger.info("🧪 Testing Email Address Retrieval from Pipedrive")
    logger.info("=" * 60)
    
    # Test with the exact structure we expect from Quoter webhook
    test_contact_data = {
        "first_name": "Robert",
        "last_name": "Lee", 
        "email_address": "robert.lee@blueowl.com",
        "organization": "Blue Owl Capital-2096",
        "addresses": {
            "billing": {
                "line1": "464 W 39th St",
                "line2": "",
                "city": "Los Angeles",
                "state": {
                    "code": "CA",
                    "name": "California"
                },
                "country": {
                    "code": "US",
                    "name": "United States"
                },
                "postal_code": "90731"
            }
        },
        "telephone_numbers": {
            "work": "212-970-6981",
            "mobile": "212-970-6981"
        }
    }
    
    logger.info(f"📋 Test contact data structure:")
    logger.info(f"   Keys: {list(test_contact_data.keys())}")
    logger.info(f"   Email: {test_contact_data.get('email_address')}")
    logger.info(f"   Addresses: {test_contact_data.get('addresses')}")
    
    logger.info("\n🎯 Testing update_contact_address function...")
    
    try:
        result = update_contact_address(test_contact_data)
        if result:
            logger.info("✅ update_contact_address succeeded!")
        else:
            logger.warning("⚠️ update_contact_address returned False")
    except Exception as e:
        logger.error(f"❌ update_contact_address failed with exception: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 Email Retrieval Test Complete!")

if __name__ == "__main__":
    test_email_retrieval()
