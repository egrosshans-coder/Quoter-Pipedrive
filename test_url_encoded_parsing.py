#!/usr/bin/env python3
"""
Test script to simulate the exact URL-encoded parsing that happens in the webhook handler.
This will help us identify where the email field is getting lost during parsing.
"""
import os
import sys
import json
from urllib.parse import parse_qs, unquote
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger

def test_url_encoded_parsing():
    """Test the exact URL-encoded parsing logic from the webhook handler."""
    logger.info("🧪 Testing URL-Encoded Webhook Data Parsing")
    logger.info("=" * 60)
    
    # Simulate the exact raw webhook data that Quoter sends
    # This is the format we saw in the logs: hash=...&timestamp=...&data=%7B...%7D
    raw_webhook_data = (
        "hash=32aa8271a5f8d869317faa985196cbf7"
        "&timestamp=1755306343"
        "&data=%7B%22id%22%3A%227228156%22%2C%22account_id%22%3A%2210104%22%2C%22parent_quote_id%22%3Anull%2C%22revision%22%3Anull%2C%22name%22%3A%22Quote+for+Blue+Owl+Capital-2096%22%2C%22number%22%3A%227%22%2C%22status%22%3A%22pending%22%2C%22person%22%3A%7B%22id%22%3A%221725219%22%2C%22public_id%22%3A%22cont_31IMDsmHdlYFe4Y1mK6oninSGge%22%2C%22first_name%22%3A%22Robert%22%2C%22last_name%22%3A%22Lee%22%2C%22organization%22%3A%22Blue+Owl+Capital-2096%22%2C%22email_address%22%3A%22robert.lee%40blueowl.com%22%2C%22addresses%22%3A%7B%22billing%22%3A%7B%22line1%22%3A%22464+W+39th+St%22%2C%22city%22%3A%22Los+Angeles%22%2C%22state%22%3A%7B%22code%22%3A%22CA%22%7D%2C%22postal_code%22%3A%2290731%22%7D%7D%7D%7D"
    )
    
    logger.info(f"📋 Raw webhook data (simulated):")
    logger.info(f"   Length: {len(raw_webhook_data)}")
    logger.info(f"   Data: {raw_webhook_data[:100]}...")
    
    # Step 1: Parse the form data (exactly as webhook handler does)
    logger.info(f"\n🔍 Step 1: Parsing form data with parse_qs")
    form_data = parse_qs(raw_webhook_data)
    logger.info(f"   Form data keys: {list(form_data.keys())}")
    
    # Step 2: Extract the 'data' field
    logger.info(f"\n🔍 Step 2: Extracting 'data' field")
    if 'data' in form_data and form_data['data']:
        encoded_json = form_data['data'][0]
        logger.info(f"   Encoded JSON length: {len(encoded_json)}")
        logger.info(f"   Encoded JSON: {encoded_json[:100]}...")
    else:
        logger.error("❌ No 'data' field found in form data")
        return
    
    # Step 3: URL decode the JSON
    logger.info(f"\n🔍 Step 3: URL decoding JSON")
    decoded_json = unquote(encoded_json)
    logger.info(f"   Decoded JSON length: {len(decoded_json)}")
    logger.info(f"   Decoded JSON: {decoded_json[:200]}...")
    
    # Step 4: Parse the JSON
    logger.info(f"\n🔍 Step 4: Parsing JSON")
    try:
        data = json.loads(decoded_json)
        logger.info(f"   ✅ JSON parsed successfully")
        logger.info(f"   Top level keys: {list(data.keys())}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON parsing failed: {e}")
        return
    
    # Step 5: Extract person data (exactly as webhook handler does)
    logger.info(f"\n🔍 Step 5: Extracting person data")
    person_data = data.get('person', {})
    logger.info(f"   Person data keys: {list(person_data.keys())}")
    
    # Step 6: Check for email field
    logger.info(f"\n🔍 Step 6: Checking email field")
    email = person_data.get('email_address')
    logger.info(f"   Email from person.email_address: '{email}'")
    
    if not email:
        logger.warning("⚠️ No email address found in person data")
        logger.warning(f"   Available person fields: {list(person_data.keys())}")
        
        # Check if email might be in a different location
        all_fields = []
        def find_fields(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if key == 'email' or 'email' in key.lower():
                        all_fields.append(f"{current_path}: {value}")
                    find_fields(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_fields(item, f"{path}[{i}]")
        
        find_fields(data)
        if all_fields:
            logger.info(f"   Found email-related fields: {all_fields}")
    else:
        logger.info("✅ Email address found successfully")
    
    # Step 7: Simulate the exact webhook handler logic
    logger.info(f"\n🔍 Step 7: Simulating webhook handler logic")
    contact_data = person_data
    contact_id = contact_data.get('public_id')
    
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
    logger.info("🎯 URL-Encoded Parsing Test Complete!")

if __name__ == "__main__":
    test_url_encoded_parsing()
