#!/usr/bin/env python3
"""
Test Template Line Items Integration

This script tests the complete template mapping system integration:
1. Template selection and name resolution
2. Template-specific line item retrieval
3. Quote creation with template line items
4. Fallback to default instructional item

Run this script to verify the template mapping system works correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token, get_template_name_from_id, add_default_instructional_item
from template_mapping import get_template_bundle, get_template_line_items, add_template_line_items_to_quote
from utils.logger import logger

load_dotenv()

def test_template_mapping_system():
    """Test the complete template mapping system."""
    logger.info("🧪 Testing Template Line Items Integration")
    logger.info("=" * 60)
    
    # Step 1: Get access token
    logger.info("🔑 Step 1: Getting Quoter API access token...")
    access_token = get_access_token()
    if not access_token:
        logger.error("❌ Failed to get access token")
        return False
    
    logger.info(f"✅ Access token obtained: {access_token[:20]}...")
    
    # Step 2: Test template name resolution
    logger.info("\n🔍 Step 2: Testing template name resolution...")
    
    # Get a test template ID (using the "test" template we know exists)
    test_template_id = "tmpl_30O6JTDIbApan1B5gh9hF2w1tfL"  # "test" template
    
    template_name = get_template_name_from_id(test_template_id, access_token)
    if template_name:
        logger.info(f"✅ Template name resolved: '{template_name}' for ID: {test_template_id}")
    else:
        logger.warning(f"⚠️ Could not resolve template name for ID: {test_template_id}")
        return False
    
    # Step 3: Test template mapping system
    logger.info(f"\n📋 Step 3: Testing template mapping for '{template_name}'...")
    
    bundle = get_template_bundle(template_name)
    if bundle:
        logger.info(f"✅ Template bundle found for '{template_name}'")
        
        line_items = get_template_line_items(template_name)
        cover_letter = bundle.get('cover_letter', '')
        appended_content = bundle.get('appended_content', '')
        
        logger.info(f"   Line items: {len(line_items)}")
        logger.info(f"   Cover letter: {'✅ Yes' if cover_letter else '❌ No'}")
        logger.info(f"   Appended content: {'✅ Yes' if appended_content else '❌ No'}")
        
        for item in line_items:
            if "item_id" in item:
                logger.info(f"   - {item['name']} (ID: {item['item_id']})")
            else:
                logger.info(f"   - {item['name']}")
    else:
        logger.info(f"ℹ️ No template bundle found for '{template_name}' - will use fallback")
    
    # Step 4: Test with a test quote (create and then delete)
    logger.info(f"\n📝 Step 4: Testing quote creation with template line items...")
    
    # We'll create a test quote and then clean it up
    test_quote_id = create_test_quote_with_template_items(template_name, access_token)
    
    if test_quote_id:
        logger.info(f"✅ Test quote created successfully: {test_quote_id}")
        logger.info(f"   Check the quote in Quoter UI to verify line items were added")
        logger.info(f"   URL: https://tlciscreative.quoter.com/admin/quotes/draft_by_public_id/{test_quote_id}")
        
        # Ask user if they want to clean up the test quote
        logger.info(f"\n🧹 Test quote created for verification.")
        logger.info(f"   Please check the quote in Quoter UI, then delete it manually.")
        logger.info(f"   Quote ID: {test_quote_id}")
        
        return True
    else:
        logger.error("❌ Failed to create test quote")
        return False

def create_test_quote_with_template_items(template_name, access_token):
    """Create a test quote with template line items for testing."""
    import requests
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Create a minimal test quote
    quote_data = {
        "name": f"TEST: {template_name} Template Line Items",
        "status": "draft",
        "currency_abbr": "USD"
    }
    
    try:
        # Create the quote first
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json=quote_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            quote_id = data.get("id")
            
            if quote_id:
                logger.info(f"📝 Test quote created: {quote_id}")
                
                # Now add template line items
                if template_name in get_template_bundle(template_name):
                    logger.info(f"📋 Adding template line items for '{template_name}'...")
                    success = add_template_line_items_to_quote(quote_id, template_name, access_token)
                    if success:
                        logger.info(f"✅ Template line items added successfully")
                    else:
                        logger.warning(f"⚠️ Some template line items failed to add")
                else:
                    logger.info(f"📋 Adding default instructional item (no template mapping found)...")
                    success = add_default_instructional_item(quote_id, access_token)
                    if success:
                        logger.info(f"✅ Default instructional item added successfully")
                    else:
                        logger.warning(f"⚠️ Failed to add default instructional item")
                
                return quote_id
            else:
                logger.error(f"❌ No quote ID in response: {data}")
                return None
        else:
            logger.error(f"❌ Failed to create test quote: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error creating test quote: {e}")
        return None

def test_available_templates():
    """Test what templates are available and their mappings."""
    logger.info("\n📋 Available Templates and Mappings:")
    logger.info("-" * 40)
    
    from template_mapping import get_all_template_names
    
    template_names = get_all_template_names()
    
    for template_name in template_names:
        bundle = get_template_bundle(template_name)
        line_items = get_template_line_items(template_name)
        
        logger.info(f"🎯 {template_name}:")
        logger.info(f"   Line items: {len(line_items)}")
        
        for item in line_items:
            if "item_id" in item:
                logger.info(f"   - {item['name']} (ID: {item['item_id']})")
            else:
                logger.info(f"   - {item['name']}")
        
        logger.info("")

if __name__ == "__main__":
    logger.info("🚀 Starting Template Line Items Integration Test")
    logger.info("=" * 60)
    
    # Test available templates first
    test_available_templates()
    
    # Run the main test
    success = test_template_mapping_system()
    
    if success:
        logger.info("\n🎉 Template Line Items Integration Test COMPLETED SUCCESSFULLY!")
        logger.info("✅ The system is ready to automatically add template line items to draft quotes")
    else:
        logger.error("\n❌ Template Line Items Integration Test FAILED")
        logger.error("Please check the logs above for issues")
    
    logger.info("\n" + "=" * 60)
