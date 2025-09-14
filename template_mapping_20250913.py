#!/usr/bin/env python3
"""
Template Line Items Mapping System

This module defines which line items should be added to quotes based on the selected template.
Since the Quoter API doesn't expose template line items, we maintain our own mapping.

Each template has predefined line items that represent the typical services/products
for that template type.
"""

# Template to Line Items Mapping (using Quoter item IDs)
# Focus: Floating Video template ONLY - other templates will be added one at a time
TEMPLATE_BUNDLES = {
    "Floating Video": {
        "parent_category": "Hologram",
        "child_categories": ["FV", "FV-Graphics"],
        "cover_letter": "Thank you for your interest in our floating video holographic package. This comprehensive solution includes advanced holographic fans and graphics packages to create stunning visual experiences for your event.",
        "appended_content": "This package includes holographic fans in various sizes, graphics packages, and master control systems. Please review all items and contact us with any questions about customization or additional services.",
        "line_items": [
            {
                "item_id": "item_30LOcZVgitq6sXrFcy0HxeAY1xO",
                "name": "FV-Standard Graphics Pkg",
                "category": "FV",
                "quantity": 1
            },
            {
                "item_id": "item_30LOcjM4ykNYQWm5vzzpF8xepSB", 
                "name": "FV-Advanced Graphics Pkg",
                "category": "FV-Graphics",
                "quantity": 1
            },
            {
                "item_id": "item_30LOchoy9I68CG5dpp2NCYmKsa5",
                "name": "FV-Ultimate Graphics Pkg", 
                "category": "FV-Graphics",
                "quantity": 1
            },
            {
                "item_id": "item_30LOcdfoXqWIbrqsoYnGiSvJONC",
                "name": "FV-MasterBox",
                "category": "FV",
                "quantity": 1
            }
        ]
    }
    
    # TODO: Add other templates one at a time as they are completed
    # - Confetti/Streamers
    # - Basic  
    # - Robotics
    # - etc.
}

def get_template_bundle(template_name):
    """
    Get bundle information for a specific template.
    
    Args:
        template_name (str): Name of the template
        
    Returns:
        dict: Bundle information including line items, cover letter, etc.
    """
    return TEMPLATE_BUNDLES.get(template_name, {})

def get_template_line_items(template_name):
    """
    Get line items for a specific template.
    
    Args:
        template_name (str): Name of the template
        
    Returns:
        list: List of line item dictionaries for the template
    """
    bundle = get_template_bundle(template_name)
    return bundle.get('line_items', [])

def get_template_cover_letter(template_name):
    """
    Get cover letter for a specific template.
    
    Args:
        template_name (str): Name of the template
        
    Returns:
        str: Cover letter text for the template
    """
    bundle = get_template_bundle(template_name)
    return bundle.get('cover_letter', '')

def get_template_appended_content(template_name):
    """
    Get appended content for a specific template.
    
    Args:
        template_name (str): Name of the template
        
    Returns:
        str: Appended content text for the template
    """
    bundle = get_template_bundle(template_name)
    return bundle.get('appended_content', '')

def get_all_template_names():
    """
    Get all available template names.
    
    Returns:
        list: List of all template names
    """
    return list(TEMPLATE_BUNDLES.keys())

def add_template_line_items_to_quote(quote_id, template_name, access_token):
    """
    Add template-specific line items to a quote using item IDs.
    
    Args:
        quote_id (str): ID of the quote to add items to
        template_name (str): Name of the template to get items for
        access_token (str): Quoter API access token
        
    Returns:
        bool: True if all items were added successfully, False otherwise
    """
    import requests
    import json
    
    line_items = get_template_line_items(template_name)
    if not line_items:
        print(f"⚠️ No line items defined for template: {template_name}")
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    success_count = 0
    total_items = len(line_items)
    
    print(f"📋 Adding {total_items} line items for template '{template_name}' to quote {quote_id}")
    
    for item in line_items:
        try:
            # Check if this is a new format with item_id or old format
            if "item_id" in item:
                # New format: use item ID to get item details
                item_id = item["item_id"]
                quantity = item.get("quantity", 1)
                
                # Get item details from Quoter API
                item_response = requests.get(
                    f"https://api.quoter.com/v1/items/{item_id}",
                    headers=headers,
                    timeout=10
                )
                
                if item_response.status_code == 200:
                    item_data = item_response.json()
                    item_name = item_data.get("name", item.get("name", "Unknown Item"))
                    item_price = item_data.get("price_decimal", 0)
                    item_description = item_data.get("description", "")
                    
                    # Prepare line item data using item ID
                    line_item_data = {
                        "quote_id": quote_id,
                        "item_id": item_id,
                        "quantity": quantity
                    }
                else:
                    print(f"❌ Failed to get item details for {item_id}: {item_response.status_code}")
                    continue
                    
            else:
                # Old format: use manual item data
                line_item_data = {
                    "quote_id": quote_id,
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "category": item.get("category", ""),
                    "unit_price": item.get("unit_price", 0),
                    "quantity": item.get("quantity", 1)
                }
                item_name = item["name"]
            
            # Add line item to quote
            response = requests.post(
                "https://api.quoter.com/v1/line_items",
                json=line_item_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                line_item_id = data.get("id")
                print(f"✅ Added line item: {item_name} (Line Item ID: {line_item_id})")
                success_count += 1
            else:
                print(f"❌ Failed to add line item '{item_name}': {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error adding line item '{item.get('name', 'Unknown')}': {e}")
    
    print(f"📊 Successfully added {success_count}/{total_items} line items")
    return success_count == total_items

def create_quote_with_template_items(contact_id, template_id, template_name, access_token):
    """
    Create a quote and add template-specific line items with cover letter and appended content.
    
    Args:
        contact_id (str): ID of the contact
        template_id (str): ID of the template
        template_name (str): Name of the template (for line item mapping)
        access_token (str): Quoter API access token
        
    Returns:
        dict: Quote data with line items added, or None if failed
    """
    import requests
    import json
    
    # Get template bundle information
    bundle = get_template_bundle(template_name)
    cover_letter = get_template_cover_letter(template_name)
    appended_content = get_template_appended_content(template_name)
    
    # Create the quote with template customization
    quote_data = {
        "contact_id": contact_id,
        "template_id": template_id,
        "currency_abbr": "USD",
        "name": f"{template_name} Quote"
    }
    
    # Add cover letter and appended content if available
    if cover_letter:
        quote_data["cover_letter"] = cover_letter
    if appended_content:
        quote_data["appended_content"] = appended_content
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"📝 Creating quote with template '{template_name}' (ID: {template_id})")
    if cover_letter:
        print(f"   📄 Cover letter: {cover_letter[:100]}...")
    if appended_content:
        print(f"   📋 Appended content: {appended_content[:100]}...")
    
    # Create the quote
    response = requests.post(
        "https://api.quoter.com/v1/quotes",
        json=quote_data,
        headers=headers,
        timeout=10
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create quote: {response.status_code} - {response.text}")
        return None
    
    quote_result = response.json()
    quote_id = quote_result.get("id")
    
    if not quote_id:
        print("❌ No quote ID returned from quote creation")
        return None
    
    print(f"✅ Quote created successfully: {quote_id}")
    
    # Now add template-specific line items
    success = add_template_line_items_to_quote(quote_id, template_name, access_token)
    
    if success:
        print(f"🎉 Quote {quote_id} created with template '{template_name}' and all line items")
        return {
            "quote_id": quote_id,
            "template_name": template_name,
            "line_items_added": True,
            "cover_letter_added": bool(cover_letter),
            "appended_content_added": bool(appended_content),
            "url": quote_result.get("url")
        }
    else:
        print(f"⚠️ Quote {quote_id} created but some line items failed to add")
        return {
            "quote_id": quote_id,
            "template_name": template_name,
            "line_items_added": False,
            "cover_letter_added": bool(cover_letter),
            "appended_content_added": bool(appended_content),
            "url": quote_result.get("url")
        }

if __name__ == "__main__":
    # Test the mapping system
    print("🧪 Testing Template Line Items Mapping System")
    print("=" * 60)
    
    # Show all available templates
    templates = get_all_template_names()
    print(f"📋 Available templates: {', '.join(templates)}")
    
    # Test each template
    for template in templates:
        bundle = get_template_bundle(template)
        items = get_template_line_items(template)
        cover_letter = get_template_cover_letter(template)
        appended_content = get_template_appended_content(template)
        
        print(f"\n🎯 Template: {template}")
        print(f"   Line items: {len(items)}")
        print(f"   Cover letter: {'✅ Yes' if cover_letter else '❌ No'}")
        print(f"   Appended content: {'✅ Yes' if appended_content else '❌ No'}")
        
        for item in items:
            if "item_id" in item:
                print(f"   - {item['name']} (ID: {item['item_id']})")
            else:
                price = item.get('unit_price', 'No price')
                print(f"   - {item['name']}: ${price}")
