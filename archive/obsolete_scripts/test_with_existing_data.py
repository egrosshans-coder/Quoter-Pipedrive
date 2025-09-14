#!/usr/bin/env python3
"""
Test Enhanced Quote Creation with Existing Quoter Data
Uses the contact we can see in Quoter UI
"""

import requests
import json
from quoter import get_access_token
from template_mapping_enhanced import get_template_line_items
from utils.logger import logger

def find_contact_by_email(email, access_token):
    """Find Quoter contact by email"""
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Search for contact by email
    search_params = {'search': email, 'limit': 10}
    response = requests.get('https://api.quoter.com/v1/people', headers=headers, params=search_params)
    
    if response.status_code == 200:
        data = response.json()
        contacts = data.get('data', [])
        
        for contact in contacts:
            if contact.get('email') == email:
                contact_id = contact.get('id')
                first_name = contact.get('first_name', '')
                last_name = contact.get('last_name', '')
                logger.info(f"✅ Found contact: {contact_id} - {first_name} {last_name}")
                return contact_id
    
    logger.warning(f"⚠️ Contact with email {email} not found")
    return None

def find_item_id_by_sku(sku, access_token):
    """Find Quoter item ID by SKU code"""
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    page = 1
    while page <= 3:  # Check first 3 pages
        search_params = {'search': sku, 'page': page, 'limit': 100}
        response = requests.get('https://api.quoter.com/v1/items', headers=headers, params=search_params)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])
            
            for item in items:
                if item.get('sku') == sku:
                    return item.get('id')
            
            if len(items) == 0:
                break
            page += 1
    
    return None

def create_test_quote():
    """Create test quote with existing Quoter data"""
    logger.info("🧪 Creating test quote with existing Quoter data...")
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        logger.error("❌ Failed to get access token")
        return
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Step 1: Find the contact we can see in Quoter UI
    contact_email = "zz19@gmail.com"
    contact_id = find_contact_by_email(contact_email, access_token)
    
    if not contact_id:
        logger.error(f"❌ Could not find contact with email {contact_email}")
        return
    
    # Step 2: Create the initial quote
    quote_data = {
        "contact_id": contact_id,
        "name": "Test Quote with Template Bundles",
        "currency_abbr": "USD"
    }
    
    logger.info(f"📤 Creating initial quote...")
    response = requests.post('https://api.quoter.com/v1/quotes', headers=headers, json=quote_data)
    
    if response.status_code not in [200, 201]:
        logger.error(f"❌ Failed to create quote: {response.status_code}")
        logger.error(f"   Error: {response.text[:200]}")
        return
    
    quote_result = response.json()
    quote_id = quote_result.get('id')
    logger.info(f"✅ Quote created successfully: {quote_id}")
    logger.info(f"   Name: {quote_result.get('name')}")
    logger.info(f"   URL: {quote_result.get('url', 'N/A')}")
    
    # Step 3: Add template items using bundle system
    template_name = "floating-video"
    logger.info(f"📦 Adding {template_name} template items...")
    
    all_items = get_template_line_items(template_name)
    logger.info(f"📋 Found {len(all_items)} items to add")
    
    successful_items = 0
    failed_items = 0
    
    # Add first 5 items as a test
    test_items = all_items[:5]
    logger.info(f"🧪 Testing with first {len(test_items)} items...")
    
    for i, item in enumerate(test_items, 1):
        logger.info(f"   [{i}/{len(test_items)}] Adding: {item['name']} ({item['sku']})")
        
        # Find the item ID in Quoter
        item_id = find_item_id_by_sku(item['sku'], access_token)
        if not item_id:
            logger.warning(f"     ⚠️ Item not found, skipping: {item['sku']}")
            failed_items += 1
            continue
        
        # Create line item data
        line_item_data = {
            "quote_id": quote_id,
            "item_id": item_id,
            "name": item['name'],
            "category": item['type'],
            "description": f"{item['type']} Item - {item['name']}",
            "quantity": 1,
            "unit_price": 1.00
        }
        
        # Add line item
        line_response = requests.post('https://api.quoter.com/v1/line_items', 
                                    headers=headers, json=line_item_data)
        
        if line_response.status_code in [200, 201]:
            line_item_result = line_response.json()
            logger.info(f"     ✅ Added successfully (ID: {line_item_result.get('id')})")
            successful_items += 1
        else:
            logger.warning(f"     ⚠️ Failed to add: {line_response.status_code}")
            logger.warning(f"        Error: {line_response.text[:100]}")
            failed_items += 1
    
    # Summary
    logger.info(f"📊 Test quote summary:")
    logger.info(f"   ✅ Successful items: {successful_items}")
    logger.info(f"   ⚠️ Failed items: {failed_items}")
    logger.info(f"   📋 Total items tested: {len(test_items)}")
    logger.info(f"   🔗 Quote URL: {quote_result.get('url', 'N/A')}")
    
    if successful_items > 0:
        logger.info(f"🎉 Test quote {quote_id} created with {successful_items} items!")
        logger.info(f"   Check Quoter to see the structure")
        return quote_id
    else:
        logger.error(f"❌ No items were added to quote {quote_id}")
        return None

if __name__ == "__main__":
    quote_id = create_test_quote()
    if quote_id:
        print(f"\n🎯 SUCCESS! Quote {quote_id} created")
        print("   Check Quoter to see the template bundle structure")
    else:
        print("\n❌ Test quote creation failed")
