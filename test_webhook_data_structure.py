#!/usr/bin/env python3
"""
Test script to simulate the exact webhook data structure from Quoter.
This will help us identify where the email field is getting lost.
"""
import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger

load_dotenv()

def test_webhook_data_structure():
    """Test the exact webhook data structure from Quoter."""
    logger.info("🧪 Testing Webhook Data Structure Simulation")
    logger.info("=" * 60)
    
    # Simulate the exact data structure from the webhook logs
    # Based on the logs we saw earlier
    simulated_webhook_data = {
        "id": "7228156",
        "account_id": "10104",
        "parent_quote_id": None,
        "revision": None,
        "name": "Quote for Blue Owl Capital-2096",
        "number": "7",
        "status": "pending",
        "person": {
            "id": "1725219",
            "public_id": "cont_31IMDsmHdlYFe4Y1mK6oninSGge",
            "first_name": "Robert",
            "last_name": "Lee",
            "organization": "Blue Owl Capital-2096",
            "title": "",
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
                },
                "shipping": None
            },
            "telephone_numbers": {
                "work": "212-970-6981",
                "mobile": "212-970-6981",
                "fax": None
            },
            "email_address": "robert.lee@blueowl.com",
            "website": None
        },
        "total": {
            "upfront": "2,575.00",
            "recurring": None
        }
    }
    
    logger.info(f"📋 Simulated webhook data structure:")
    logger.info(f"   Top level keys: {list(simulated_webhook_data.keys())}")
    
    # Extract person data exactly as the webhook handler does
    person_data = simulated_webhook_data.get('person', {})
    logger.info(f"   Person data keys: {list(person_data.keys())}")
    
    # Check for email field
    email = person_data.get('email_address')
    logger.info(f"   Email from person.email_address: '{email}'")
    
    # Check if email exists in different possible locations
    possible_email_fields = ['email_address', 'email', 'emailAddress', 'email_address']
    for field in possible_email_fields:
        value = person_data.get(field)
        logger.info(f"   {field}: '{value}'")
    
    # Simulate the exact webhook handler logic
    contact_data = person_data
    contact_id = contact_data.get('public_id')
    
    logger.info(f"\n🔍 Simulating webhook handler logic:")
    logger.info(f"   contact_data = quote_data.get('person', {{}})")
    logger.info(f"   contact_data type: {type(contact_data)}")
    logger.info(f"   contact_data keys: {list(contact_data.keys())}")
    logger.info(f"   contact_id: {contact_id}")
    
    # Check what would be passed to update_contact_address
    logger.info(f"\n🎯 Data that would be passed to update_contact_address:")
    logger.info(f"   contact_data: {contact_data}")
    
    # Test the email extraction
    email = contact_data.get('email_address', '')
    logger.info(f"   email = contact_data.get('email_address', ''): '{email}'")
    
    if not email:
        logger.warning("⚠️ No email address found in contact_data")
        logger.warning(f"   Available fields in contact_data: {list(contact_data.keys())}")
    else:
        logger.info("✅ Email address found successfully")
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 Webhook Data Structure Test Complete!")

if __name__ == "__main__":
    test_webhook_data_structure()
