#!/usr/bin/env python3
"""
Enhanced Quote Creator
Uses the template mapping system to create comprehensive quotes with all template items
"""

import requests
import json
from quoter import get_access_token
from template_mapping_enhanced import get_template_line_items, get_template_info, get_item_by_sku
from utils.logger import logger

def find_item_id_by_sku(sku, access_token):
    """
    Find Quoter item ID by SKU code
    
    Args:
        sku (str): Item SKU code
        access_token (str): Quoter API access token
        
    Returns:
        str: Item ID or None if not found
    """
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Search for item by SKU with pagination
    page = 1
    while page <= 5:  # Check first 5 pages
        search_params = {'search': sku, 'page': page, 'limit': 100}
        response = requests.get('https://api.quoter.com/v1/items', headers=headers, params=search_params)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])
            
            for item in items:
                if item.get('sku') == sku:
                    logger.info(f"✅ Found item: {item.get('name')} (ID: {item.get('id')})")
                    return item.get('id')
            
            if len(items) == 0:
                break
            page += 1
        else:
            logger.error(f"❌ Error searching for item {sku}: {response.status_code}")
            break
    
    logger.warning(f"⚠️ Item with SKU {sku} not found")
    return None

def create_comprehensive_quote_with_bundles(contact_id, template_name, quote_name, access_token):
    """
    Create a comprehensive quote with all template items using the bundle system
    
    Args:
        contact_id (str): Quoter contact ID
        template_name (str): Template identifier (e.g., 'floating-video')
        quote_name (str): Name for the quote
        access_token (str): Quoter API access token
        
    Returns:
        dict: Quote data if successful, None otherwise
    """
    logger.info(f"🚀 Creating comprehensive quote with bundles...")
    logger.info(f"   Template: {template_name}")
    logger.info(f"   Contact: {contact_id}")
    logger.info(f"   Quote Name: {quote_name}")
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Get template information
    template_info = get_template_info(template_name)
    if not template_info:
        logger.error(f"❌ Template '{template_name}' not found")
        return None
    
    logger.info(f"📋 Using template: {template_info['name']}")
    
    # Step 1: Create the initial quote
    quote_data = {
        "contact_id": contact_id,
        "name": quote_name,
        "currency_abbr": "USD"
    }
    
    logger.info(f"📤 Creating initial quote...")
    response = requests.post('https://api.quoter.com/v1/quotes', headers=headers, json=quote_data)
    
    if response.status_code not in [200, 201]:
        logger.error(f"❌ Failed to create quote: {response.status_code}")
        logger.error(f"   Error: {response.text[:200]}")
        return None
    
    quote_result = response.json()
    quote_id = quote_result.get('id')
    logger.info(f"✅ Quote created successfully: {quote_id}")
    
    # Step 2: Get all template items
    all_items = get_template_line_items(template_name)
    logger.info(f"📦 Adding {len(all_items)} items to quote...")
    
    # Step 3: Add each item to the quote
    successful_items = 0
    failed_items = 0
    
    for i, item in enumerate(all_items, 1):
        logger.info(f"   [{i}/{len(all_items)}] Adding: {item['name']} ({item['sku']})")
        
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
            "category": item['type'],  # Use type as category
            "description": f"{item['type']} Item - {item['name']}",
            "quantity": 1,
            "unit_price": 1.00  # Default price, will be updated by Quoter
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
    logger.info(f"📊 Quote creation summary:")
    logger.info(f"   ✅ Successful items: {successful_items}")
    logger.info(f"   ⚠️ Failed items: {failed_items}")
    logger.info(f"   📋 Total items attempted: {len(all_items)}")
    
    if successful_items > 0:
        logger.info(f"🎉 Quote {quote_id} created with {successful_items} items!")
        return {
            "id": quote_id,
            "name": quote_name,
            "template": template_name,
            "successful_items": successful_items,
            "failed_items": failed_items,
            "total_items": len(all_items)
        }
    else:
        logger.error(f"❌ No items were added to quote {quote_id}")
        return None

def test_quote_creation():
    """
    Test function to create a sample quote
    """
    logger.info("🧪 Testing enhanced quote creation...")
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        logger.error("❌ Failed to get access token")
        return
    
    # Test with floating video template
    contact_id = "cont_test123"  # Replace with actual contact ID
    template_name = "floating-video"
    quote_name = "Test Floating Video Quote with Bundles"
    
    result = create_comprehensive_quote_with_bundles(
        contact_id=contact_id,
        template_name=template_name,
        quote_name=quote_name,
        access_token=access_token
    )
    
    if result:
        logger.info(f"✅ Test quote created successfully!")
        logger.info(f"   Quote ID: {result['id']}")
        logger.info(f"   Items added: {result['successful_items']}/{result['total_items']}")
    else:
        logger.error("❌ Test quote creation failed")

if __name__ == "__main__":
    test_quote_creation()
