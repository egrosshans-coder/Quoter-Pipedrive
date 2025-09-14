#!/usr/bin/env python3
"""
Enhanced Template Mapping System
Based on webhook data analysis for comprehensive quote creation
"""

import requests

# Bundle 1: Template-Specific (Hardware + Labor) - Reduced Items
TEMPLATE_BUNDLES = {
    "floating-video": {
        "name": "Floating Video",
        "items": [
            # FV Category - Using ACTUAL Quoter Item Codes with simple categories (like Bundle 2)
            {"sku": "HG-FV-Graph-001", "name": "FV-Standard Graphics Pkg", "type": "FV-Graphics", "price": 500.00},
            {"sku": "HG-FV-Graph-002", "name": "FV-Advanced Graphics Pkg", "type": "FV-Graphics", "price": 1500.00},
            {"sku": "HG-FV-Graph-003", "name": "FV-Ultimate Graphics Pkg", "type": "FV-Graphics", "price": 3000.00},
            {"sku": "HG-FVH-L30-001", "name": "FV-30 Fan Holographic", "type": "FV", "price": 2500.00},
            {"sku": "HG-FVH-M22-001", "name": "FV-22 Fan Holographic", "type": "FV", "price": 2000.00},
            {"sku": "HG-FVV-100-001", "name": "FV-40in-100 Fan Holographic", "type": "FV", "price": 3000.00},
            {"sku": "HG-FVV-150-001", "name": "FV-5FT-150 Fan Holographic", "type": "FV", "price": 4000.00},
            {"sku": "HG-FVV-180-001", "name": "FV-6FT-180 Fan Holographic", "type": "FV", "price": 6000.00},
            {"sku": "HG-FVV-MBOX-001", "name": "FVV-MasterBox", "type": "FV", "price": 1000.00},
            {"sku": "HG-FVH-MBOX-001", "name": "FV-MasterBox", "type": "FV", "price": 1000.00},
            {"sku": "HG-FVH-HH-001", "name": "FV-HoloHuman", "type": "FV", "price": 10000.00},
            {"sku": "HG-FVH-HH-002", "name": "FV-HoloHuman-Case", "type": "FV", "price": 2000.00},
            
            # Labor for this template
            {"sku": "SVC-LAB-001", "name": "Labor/Technician for Setup, Test and Strike", "type": "Labor", "price": 950.00}
        ]
    },
    "led-wristbands": {
        "name": "LED Wristbands",
        "items": [
            # LED wristband hardware items (to be populated from webhook data)
            {"sku": "LED-WBX-MK4-001", "name": "Xylo 8-LED Wristband", "type": "LED"},
            {"sku": "LED-WBX-CTX", "name": "Controller-Xylobands-Wristbands/Lanyards", "type": "LED"},
            {"sku": "LED-WBE-HTX", "name": "Remote Control for Wristbands/Lanyards", "type": "LED"},
            {"sku": "LED-WBE-LPAD", "name": "Launchpad for Wristbands/Lanyards", "type": "LED"},
            {"sku": "LED-WBE-LAP", "name": "Laptop for Wristbands/Lanyards", "type": "LED"},
            
            # Labor for this template
            {"sku": "SVC-LAB-001", "name": "Labor/Technician for Setup, Test and Strike", "type": "Labor"}
        ]
    }
}

# Bundle 2: Universal (T&E + Shipping) - Complete list from interface
UNIVERSAL_BUNDLE = {
    "name": "Travel & Shipping",
    "items": [
        {"sku": "SHP-S&H-001", "name": "Shipping & Handling", "type": "Shipping", "price": 150.00},
        {"sku": "T&E-BUY-OUT", "name": "T&E - accommodations Buyout", "type": "Buyout", "price": 500.00},
        {"sku": "T&E-BAG-001", "name": "T&E-Baggage fees", "type": "Baggage", "price": 100.00},
        {"sku": "T&E-FLY-001", "name": "T&E-Flights", "type": "Flights", "price": 800.00},
        {"sku": "T&E-GND-001", "name": "T&E-Ground transportation", "type": "Ground", "price": 200.00},
        {"sku": "T&E-MLS-001", "name": "T&E-Meals", "type": "Meals", "price": 150.00},
        {"sku": "T&E-PRK-001", "name": "T&E-Parking", "type": "Parking", "price": 50.00},
        {"sku": "T&E-PER-DIM", "name": "T&E-Per Diem", "type": "PerDiem", "price": 95.00},
        {"sku": "T&E-RMS-001", "name": "T&E-Rooms", "type": "Rooms", "price": 400.00}
    ]
}

def find_item_details_by_sku(sku, access_token):
    """
    Find Quoter item details by Item Code (cross-system SKU)
    
    Args:
        sku: Item Code (cross-system identifier)
        access_token: Quoter API token
    """
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

    page = 1
    while page <= 5:
        search_params = {'search': sku, 'page': page, 'limit': 100}
        response = requests.get('https://api.quoter.com/v1/items', headers=headers, params=search_params)

        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])

            for item in items:
                if item.get('code') == sku:  # Use 'code' field, not 'sku'
                    return {
                        'id': item.get('id'),
                        'name': item.get('name'),
                        'code': item.get('code'),
                        'price': float(item.get('base_price', 0)),
                        'category': item.get('category', 'Unknown')
                    }

            if len(items) == 0:
                break
            page += 1

    return None

def get_template_line_items(template_name, access_token=None):
    """
    Get all items for a template with real Quoter pricing
    
    Args:
        template_name (str): Template identifier (e.g., 'floating-video')
        access_token (str): Quoter API access token for fetching real prices
        
    Returns:
        list: All items for the template with real pricing from Quoter
    """
    items = []
    
    # Add template-specific bundle
    if template_name in TEMPLATE_BUNDLES:
        template_items = TEMPLATE_BUNDLES[template_name]["items"].copy()
        
        # Fetch real pricing for each item if access token provided
        if access_token:
            for item in template_items:
                item_details = find_item_details_by_sku(item['sku'], access_token)
                if item_details:
                    item['id'] = item_details['id']
                    item['price'] = item_details['price']
                    item['real_name'] = item_details['name']
                    print(f"✅ Found {item_details['name']} - ${item_details['price']:,.2f} (Code: {item['sku']})")
                else:
                    item['id'] = None
                    item['price'] = item.get('price', 100.00)  # Fallback price
                    print(f"⚠️ Item not found in Quoter: {item['sku']} - using fallback ${item['price']:,.2f}")
        
        items.extend(template_items)
        print(f"✅ Added {len(template_items)} items from {TEMPLATE_BUNDLES[template_name]['name']} template")
    else:
        print(f"⚠️ Template '{template_name}' not found in TEMPLATE_BUNDLES")
    
    # Always add universal bundle
    universal_items = UNIVERSAL_BUNDLE["items"].copy()
    
    # Fetch real pricing for universal items if access token provided
    if access_token:
        for item in universal_items:
            item_details = find_item_details_by_sku(item['sku'], access_token)
            if item_details:
                item['id'] = item_details['id']
                item['price'] = item_details['price']
                item['real_name'] = item_details['name']
                print(f"✅ Found {item_details['name']} - ${item_details['price']:,.2f}")
            else:
                item['id'] = None
                item['price'] = item.get('price', 100.00)  # Fallback price
                print(f"⚠️ Item not found in Quoter: {item['sku']} - using fallback ${item['price']:,.2f}")
    
    items.extend(universal_items)
    print(f"✅ Added {len(universal_items)} universal items")
    
    return items

def get_template_info(template_name):
    """
    Get template information
    
    Args:
        template_name (str): Template identifier
        
    Returns:
        dict: Template information or None if not found
    """
    return TEMPLATE_BUNDLES.get(template_name)

def verify_bundle_against_quoter(template_name, access_token):
    """
    Verify stored bundle data against current Quoter items
    
    Args:
        template_name (str): Template identifier
        access_token (str): Quoter API access token
        
    Returns:
        dict: Verification results with changes detected
    """
    print(f"🔍 Verifying {template_name} bundle against Quoter...")
    
    # Get all items from bundle
    all_items = get_template_line_items(template_name, access_token)
    
    verification_results = {
        "template_name": template_name,
        "total_items": len(all_items),
        "items_verified": 0,
        "items_changed": [],
        "items_not_found": [],
        "items_unchanged": []
    }
    
    for item in all_items:
        sku = item['sku']
        stored_name = item['name']
        stored_price = item['price']
        stored_type = item['type']
        
        # Try to find item in Quoter
        item_details = find_item_details_by_sku(sku, access_token)
        
        if item_details:
            quoter_name = item_details['name']
            quoter_price = item_details['price']
            quoter_category = item_details['category']
            
            verification_results["items_verified"] += 1
            
            # Check for changes
            changes = []
            if stored_name != quoter_name:
                changes.append(f"name: '{stored_name}' → '{quoter_name}'")
            if abs(stored_price - quoter_price) > 0.01:  # Allow for rounding
                changes.append(f"price: ${stored_price:,.2f} → ${quoter_price:,.2f}")
            if stored_type != quoter_category:
                changes.append(f"type: '{stored_type}' → '{quoter_category}'")
            
            if changes:
                verification_results["items_changed"].append({
                    "sku": sku,
                    "changes": changes,
                    "stored": {"name": stored_name, "price": stored_price, "type": stored_type},
                    "quoter": {"name": quoter_name, "price": quoter_price, "category": quoter_category}
                })
                print(f"⚠️  {sku}: {', '.join(changes)}")
            else:
                verification_results["items_unchanged"].append(sku)
                print(f"✅ {sku}: No changes detected")
        else:
            verification_results["items_not_found"].append({
                "sku": sku,
                "stored": {"name": stored_name, "price": stored_price, "type": stored_type}
            })
            print(f"❌ {sku}: Item not found in Quoter")
    
    return verification_results

def update_bundle_from_quoter(template_name, access_token, dry_run=True):
    """
    Update stored bundle data with current Quoter information
    
    Args:
        template_name (str): Template identifier
        access_token (str): Quoter API access token
        dry_run (bool): If True, only show what would be updated
        
    Returns:
        dict: Update results
    """
    print(f"🔄 {'[DRY RUN] ' if dry_run else ''}Updating {template_name} bundle from Quoter...")
    
    verification = verify_bundle_against_quoter(template_name, access_token)
    
    if dry_run:
        print(f"\n📊 DRY RUN RESULTS:")
        print(f"   Items to update: {len(verification['items_changed'])}")
        print(f"   Items not found: {len(verification['items_not_found'])}")
        print(f"   Items unchanged: {len(verification['items_unchanged'])}")
        
        if verification['items_changed']:
            print(f"\n🔄 Items that would be updated:")
            for item in verification['items_changed']:
                print(f"   {item['sku']}: {', '.join(item['changes'])}")
        
        return verification
    
    else:
        print(f"\n⚠️  LIVE UPDATE MODE - This would modify the stored bundle!")
        print(f"   Run with dry_run=True first to preview changes.")
        return verification

def get_available_templates():
    """
    Get list of available templates
    
    Returns:
        list: Available template names
    """
    return list(TEMPLATE_BUNDLES.keys())

def get_item_by_sku(sku, template_name=None):
    """
    Find an item by SKU across all bundles
    
    Args:
        sku (str): Item SKU code
        template_name (str, optional): Specific template to search
        
    Returns:
        dict: Item information or None if not found
    """
    # Search in template bundles
    if template_name and template_name in TEMPLATE_BUNDLES:
        for item in TEMPLATE_BUNDLES[template_name]["items"]:
            if item["sku"] == sku:
                return item
    
    # Search in all template bundles
    for template_name, template_data in TEMPLATE_BUNDLES.items():
        for item in template_data["items"]:
            if item["sku"] == sku:
                return item
    
    # Search in universal bundle
    for item in UNIVERSAL_BUNDLE["items"]:
        if item["sku"] == sku:
            return item
    
    return None

# Test function
if __name__ == "__main__":
    print("🧪 Testing Enhanced Template Mapping System")
    print("=" * 50)
    
    # Test available templates
    templates = get_available_templates()
    print(f"📋 Available templates: {templates}")
    
    # Test floating video template
    if "floating-video" in templates:
        items = get_template_line_items("floating-video")
        print(f"\n🎯 Floating Video Template:")
        print(f"   Total items: {len(items)}")
        
        # Group by type
        types = {}
        for item in items:
            item_type = item["type"]
            if item_type not in types:
                types[item_type] = []
            types[item_type].append(item["name"])
        
        print(f"   Items by type:")
        for item_type, names in types.items():
            print(f"     {item_type}: {len(names)} items")
    
    print("\n✅ Template mapping system ready!")
