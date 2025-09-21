#!/usr/bin/env python3
"""
Enhanced Quote Creation with Template Bundle System
Replaces single instructional item with comprehensive template items
"""

import requests
import os
from dotenv import load_dotenv
from utils.logger import logger

# Import the enhanced template mapping system
from template_mapping_enhanced import get_template_line_items, get_template_info

load_dotenv()
CLIENT_ID = os.getenv("QUOTER_API_KEY")
CLIENT_SECRET = os.getenv("QUOTER_CLIENT_SECRET")

def get_template_name_from_id(template_id, access_token):
    """
    Get template name from template ID for bundle mapping
    
    Args:
        template_id (str): Quoter template ID
        access_token (str): Quoter API access token
        
    Returns:
        str: Template name/slug or None if not found
    """
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    try:
        response = requests.get('https://api.quoter.com/v1/quote_templates', headers=headers)
        if response.status_code == 200:
            data = response.json()
            templates = data.get('data', [])
            
            for template in templates:
                if template.get('id') == template_id:
                    # Try to get slug or name for mapping
                    template_slug = template.get('slug', '').lower().replace('-', '_')
                    template_name = template.get('name', '').lower().replace(' ', '-')
                    
                    # Map to our bundle names
                    if 'floating' in template_slug or 'floating' in template_name:
                        return 'floating-video'
                    elif 'led' in template_slug or 'wristband' in template_slug:
                        return 'led-wristbands'
                    
                    logger.info(f"📋 Template found: {template.get('name')} (ID: {template_id})")
                    return template_slug or template_name
            
            logger.warning(f"⚠️ Template ID {template_id} not found in templates list")
            return None
        else:
            logger.warning(f"⚠️ Failed to get templates: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"❌ Error getting template name: {e}")
        return None

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

def add_template_line_items_to_quote(quote_id, template_name, access_token):
    """
    Add all template line items to a quote using the bundle system
    
    Args:
        quote_id (str): Quote ID
        template_name (str): Template name (e.g., 'floating-video')
        access_token (str): Quoter API access token
        
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"📦 Adding template line items using bundle system...")
    logger.info(f"   Template: {template_name}")
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Get all items for this template (using stored pricing for performance)
    all_items = get_template_line_items(template_name)
    logger.info(f"📋 Found {len(all_items)} items to add")
    
    successful_items = 0
    failed_items = 0
    
    for i, item in enumerate(all_items, 1):
        logger.info(f"   [{i}/{len(all_items)}] Adding: {item['name']} ({item['sku']})")
        
        # Create line item data directly from template bundle (100% copy/paste concept)
        line_item_data = {
            "quote_id": quote_id,
            "name": item['name'],
            "item_code": item['sku'],  # Use correct field for SKU
            "category": item['type'],
            "description": f"{item['name']} - {item['type']}",
            "quantity": 1,
            "unit_price": float(item.get('price', 0))  # Use stored price from bundle
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
    logger.info(f"📊 Template line items summary:")
    logger.info(f"   ✅ Successful items: {successful_items}")
    logger.info(f"   ⚠️ Failed items: {failed_items}")
    logger.info(f"   📋 Total items attempted: {len(all_items)}")
    
    return successful_items > 0

def add_default_instructional_item(quote_id, access_token):
    """
    Add the default instructional item as fallback
    
    Args:
        quote_id (str): Quote ID
        access_token (str): Quoter API access token
    """
    logger.info(f"📋 Adding default instructional item...")
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Use the existing instructional item from Quoter
    existing_item_id = "item_31IIdw4C1GHIwU05yhnZ2B88S2B"
    
    # Get the full item details
    item_response = requests.get(f'https://api.quoter.com/v1/items/{existing_item_id}', headers=headers)
    if item_response.status_code == 200:
        item_data = item_response.json()
        item_name = item_data.get('name', '01-Draft Quote-Instructions (delete before sending quote)')
        item_category = item_data.get('category', 'DJ')
        item_description = item_data.get('description', '')
        
        # Add the instructional line item
        line_item_data = {
            "quote_id": quote_id,
            "item_id": existing_item_id,
            "name": item_name,
            "category": item_category,
            "description": item_description,
            "quantity": 1,
            "unit_price": 1.00
        }
        
        line_item_response = requests.post('https://api.quoter.com/v1/line_items', 
                                        headers=headers, json=line_item_data)
        
        if line_item_response.status_code in [200, 201]:
            logger.info(f"✅ Default instructional item added successfully")
        else:
            logger.warning(f"⚠️ Failed to add instructional line item: {line_item_response.status_code}")
    else:
        logger.warning(f"⚠️ Failed to get instructional item details: {item_response.status_code}")

def create_comprehensive_quote_with_bundles(organization_data, deal_data=None):
    """
    Enhanced quote creation with template bundle system
    
    This function creates a quote and then adds all template-specific items
    using the bundle system we designed.
    
    Args:
        organization_data (dict): Organization data from Pipedrive
        deal_data (dict, optional): Deal data from Pipedrive for template selection
        
    Returns:
        dict: Quote data if created successfully, None otherwise
    """
    # Import the original function components we need
    from quoter import get_access_token, get_quote_required_fields, create_comprehensive_contact_from_pipedrive
    from pipedrive import get_deal_by_id, get_person_by_id
    
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth token for comprehensive quote creation")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get template selection from Pipedrive dropdown field if deal_data is provided
    template_id = None
    if deal_data:
        from template_selection_logic import get_quote_template_id
        template_field_id = "42ab0c919271cb24f3587f0b01ea2af166019c8d"
        template_result = get_quote_template_id(deal_data, access_token, template_field_id)
        
        if template_result:
            # Extract template_id from the tuple returned by get_quote_template_id
            template_id, template_name = template_result
            logger.info(f"✅ Using template from Pipedrive dropdown: {template_id}")
        else:
            logger.info("🔄 Pipedrive template not found, using fallback logic")
    
    # Get required fields for quote creation
    # NOTE: Quoter API is ignoring template_id parameter, so we'll use default template
    # and add Floating Video content via Template Bundle system instead
    required_fields = get_quote_required_fields(access_token)
    if not required_fields:
        logger.error("Failed to get required fields for quote creation")
        return None
    
    # Override with the correct Floating Video template if identified
    if template_id and template_name:
        required_fields["template_id"] = template_id
        logger.info(f"🔍 DEBUG: Overriding with {template_name} template: {template_id}")
    else:
        logger.info(f"🔍 DEBUG: Using default template: {required_fields.get('template_id')}")
    
    # Extract organization and deal information
    org_name = organization_data.get("name", "Unknown Organization")
    org_id = organization_data.get("id")
    deal_id = organization_data.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")
    
    if not deal_id:
        logger.error(f"❌ No deal ID found in organization {org_id}")
        return None
    
    logger.info(f"🎯 Creating comprehensive quote with bundles for organization: {org_name}")
    logger.info(f"   Organization ID: {org_id}")
    logger.info(f"   Deal ID: {deal_id}")
    
    # Get deal and contact information
    if not deal_data:
        deal_data = get_deal_by_id(deal_id)
        if not deal_data:
            logger.error(f"❌ Failed to get deal {deal_id} from Pipedrive")
            return None
    
    person_data = deal_data.get("person_id", {})
    if isinstance(person_data, list) and person_data:
        primary_contact = person_data[0]
    elif isinstance(person_data, dict):
        primary_contact = person_data
    else:
        logger.error(f"❌ No person data found in deal {deal_id}")
        return None
    
    contact_id = primary_contact.get("value")
    if not contact_id:
        logger.error(f"❌ No contact ID found in person data")
        return None
    
    # Get full contact data and create in Quoter
    contact_data = get_person_by_id(contact_id)
    if not contact_data:
        logger.error(f"❌ Failed to get person {contact_id} from Pipedrive")
        return None
    
    contact_id = create_comprehensive_contact_from_pipedrive(contact_data, organization_data)
    if not contact_id:
        logger.error("❌ Failed to create comprehensive contact in Quoter")
        return None
    
    logger.info(f"✅ Contact created/updated in Quoter: {contact_id}")
    
    # Get deal title for quote naming
    deal_title = deal_data.get("title", f"Deal {deal_id}")
    
    # Create the initial quote (using default template since Quoter API ignores template_id)
    quote_data = {
        "contact_id": contact_id,
        "template_id": required_fields["template_id"],
        "currency_abbr": required_fields["currency_abbr"],
        "name": f"Quote for {deal_title}"
    }
    
    # COMMENTED OUT FOR TESTING - Let Quoter handle template content automatically
    # Add Floating Video cover letter and content if template was selected
    # if template_id and template_name:
    #     logger.info(f"🎯 Adding Floating Video content via Template Bundle system...")
    #     template_info = get_template_info(template_name)
    #     if template_info:
    #         cover_letter = template_info.get('cover_letter', '')
    #         appended_content = template_info.get('appended_content', '')
    #         
    #         if cover_letter and cover_letter.strip():
    #             quote_data["cover_letter"] = cover_letter
    #             logger.info(f"📝 Added Floating Video cover letter")
    #             logger.info(f"🔍 DEBUG: Cover letter content: {cover_letter[:200]}...")
    #         
    #         if appended_content and appended_content.strip():
    #             quote_data["appended_content"] = appended_content
    #             logger.info(f"📝 Added Floating Video appended content")
    
    logger.info("🧪 TESTING: Letting Quoter handle template content automatically")
    
    try:
        logger.info(f"📝 Creating comprehensive draft quote...")
        logger.info(f"🔍 DEBUG: Quote data being sent: {quote_data}")
        response = requests.post("https://api.quoter.com/v1/quotes", json=quote_data, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            data = response.json()
            quote_id = data.get("id")
            
            if quote_id:
                logger.info(f"🎉 SUCCESS! Comprehensive draft quote created:")
                logger.info(f"   Quote ID: {quote_id}")
                logger.info(f"   Name: {data.get('name', 'N/A')}")
                
                # Step 2: Add template-specific line items using bundle system
                logger.info(f"📋 Adding template-specific line items to quote...")
                
                # Use the template name we already have from Pipedrive selection
                # template_name = get_template_name_from_id(required_fields["template_id"], access_token)
                
                if template_name:
                    logger.info(f"🎯 Using template mapping for: {template_name}")
                    
                    # Add template-specific line items
                    success = add_template_line_items_to_quote(quote_id, template_name, access_token)
                    if success:
                        logger.info(f"✅ Template line items added successfully for {template_name}")
                    else:
                        logger.warning(f"⚠️ Some template line items failed to add for {template_name}")
                        logger.info(f"📋 Adding default instructional item as fallback")
                        add_default_instructional_item(quote_id, access_token)
                else:
                    logger.warning(f"⚠️ Could not determine template name, adding default instructional item")
                    add_default_instructional_item(quote_id, access_token)
                
                logger.info(f"📊 Quote created with comprehensive contact data and template line items")
                
                return data
            else:
                logger.error("❌ Quote created but no ID returned")
                return None
        else:
            logger.error(f"❌ Failed to create quote: {response.status_code}")
            logger.error(f"   Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error creating comprehensive quote: {e}")
        return None

# Test function
if __name__ == "__main__":
    logger.info("🧪 Testing enhanced quote creation with bundles...")
    
    # Test data
    test_org_data = {
        "id": "test_org_123",
        "name": "Test Organization-2096",
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": "2096"
    }
    
    test_deal_data = {
        "id": 2096,
        "title": "Test Deal",
        "person_id": {"value": "test_contact_123"}
    }
    
    result = create_comprehensive_quote_with_bundles(test_org_data, test_deal_data)
    if result:
        logger.info(f"✅ Test quote created successfully!")
    else:
        logger.error("❌ Test quote creation failed")
