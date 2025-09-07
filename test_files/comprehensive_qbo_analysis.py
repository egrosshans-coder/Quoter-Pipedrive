#!/usr/bin/env python3
"""
Comprehensive QBO analysis combining all clues:
1. Parent Category (from ParentRef)
2. Category (from Name when SubItem=True and Level=1)
3. Item Name (from Name when Level=2+)
4. Fully Qualified Name (complete hierarchy path)
"""

import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

def comprehensive_qbo_analysis():
    """Comprehensive analysis using all QBO structure clues"""
    from quoter_to_qbo_sync import QBOClient
    
    # Initialize QBO client
    qbo = QBOClient()
    
    logger.info("🔍 Comprehensive QBO Analysis - Combining All Clues...")
    
    # Get all QBO items
    all_items = qbo.get_existing_items()
    
    if not all_items:
        logger.error("No QBO items found!")
        return
    
    # Build complete hierarchy map
    hierarchy_map = {}
    parent_categories = {}
    sub_categories = {}
    actual_items = {}
    
    # First pass: identify parent categories
    for item in all_items:
        item_id = item.get('Id')
        name = item.get('Name', '')
        fully_qualified = item.get('FullyQualifiedName', '')
        sub_item = item.get('SubItem', False)
        level = item.get('Level', 0)
        
        if not sub_item:
            # This is a parent category
            parent_categories[item_id] = {
                'name': name,
                'fully_qualified': fully_qualified,
                'level': level,
                'type': item.get('Type', ''),
                'active': item.get('Active', True)
            }
    
    # Second pass: identify sub-categories and actual items
    for item in all_items:
        item_id = item.get('Id')
        name = item.get('Name', '')
        fully_qualified = item.get('FullyQualifiedName', '')
        sub_item = item.get('SubItem', False)
        level = item.get('Level', 0)
        parent_ref = item.get('ParentRef', {})
        parent_id = parent_ref.get('value') if parent_ref else None
        
        if sub_item and level == 1:
            # This is a sub-category
            parent_name = parent_categories.get(parent_id, {}).get('name', 'Unknown Parent')
            sub_categories[item_id] = {
                'name': name,
                'fully_qualified': fully_qualified,
                'parent_id': parent_id,
                'parent_name': parent_name,
                'level': level,
                'type': item.get('Type', ''),
                'active': item.get('Active', True)
            }
        elif sub_item and level >= 2:
            # This is an actual item
            parent_name = "Unknown Parent"
            grandparent_name = "Unknown Grandparent"
            
            # Find parent (sub-category)
            if parent_id in sub_categories:
                parent_name = sub_categories[parent_id]['name']
                grandparent_id = sub_categories[parent_id]['parent_id']
                if grandparent_id in parent_categories:
                    grandparent_name = parent_categories[grandparent_id]['name']
            
            actual_items[item_id] = {
                'name': name,
                'fully_qualified': fully_qualified,
                'parent_id': parent_id,
                'parent_name': parent_name,
                'grandparent_id': grandparent_id if parent_id in sub_categories else None,
                'grandparent_name': grandparent_name,
                'level': level,
                'type': item.get('Type', ''),
                'active': item.get('Active', True),
                'price': item.get('UnitPrice'),
                'description': item.get('Description', ''),
                'taxable': item.get('Taxable', False)
            }
    
    # Display comprehensive analysis
    logger.info(f"📊 Comprehensive QBO Structure Analysis:")
    logger.info(f"Total Items: {len(all_items)}")
    logger.info(f"Parent Categories: {len(parent_categories)}")
    logger.info(f"Sub Categories: {len(sub_categories)}")
    logger.info(f"Actual Items: {len(actual_items)}")
    
    # Show parent categories
    logger.info(f"\n🏷️  Parent Categories:")
    for item_id, data in sorted(parent_categories.items(), key=lambda x: x[1]['name']):
        logger.info(f"  {data['name']} (ID: {item_id})")
        logger.info(f"    Fully Qualified: {data['fully_qualified']}")
        logger.info(f"    Type: {data['type']}, Active: {data['active']}")
    
    # Show sub-categories grouped by parent
    logger.info(f"\n📁 Sub Categories by Parent:")
    for parent_id, parent_data in sorted(parent_categories.items(), key=lambda x: x[1]['name']):
        logger.info(f"\n{parent_data['name']} (Parent Category):")
        
        # Find sub-categories under this parent
        sub_cats_under_parent = [sc for sc in sub_categories.values() if sc['parent_id'] == parent_id]
        
        for sub_cat in sorted(sub_cats_under_parent, key=lambda x: x['name']):
            logger.info(f"  └── {sub_cat['name']} (ID: {item_id})")
            logger.info(f"      Fully Qualified: {sub_cat['fully_qualified']}")
            logger.info(f"      Type: {sub_cat['type']}, Active: {sub_cat['active']}")
    
    # Show actual items grouped by hierarchy
    logger.info(f"\n🛍️  Actual Items by Hierarchy:")
    for parent_id, parent_data in sorted(parent_categories.items(), key=lambda x: x[1]['name']):
        logger.info(f"\n{parent_data['name']} (Parent Category):")
        
        # Find sub-categories under this parent
        sub_cats_under_parent = [sc for sc in sub_categories.values() if sc['parent_id'] == parent_id]
        
        for sub_cat in sorted(sub_cats_under_parent, key=lambda x: x['name']):
            logger.info(f"  └── {sub_cat['name']} (Sub Category):")
            
            # Find actual items under this sub-category
            items_under_sub_cat = [ai for ai in actual_items.values() if ai['parent_id'] == sub_cat['parent_id']]
            
            for item in sorted(items_under_sub_cat, key=lambda x: x['name']):
                price_str = f"${item['price']}" if item['price'] is not None else "No Price"
                logger.info(f"      • {item['name']} - {price_str}")
                logger.info(f"        Fully Qualified: {item['fully_qualified']}")
                logger.info(f"        Type: {item['type']}, Active: {item['active']}")
                if item['description']:
                    desc = item['description'][:100] + "..." if len(item['description']) > 100 else item['description']
                    logger.info(f"        Description: {desc}")
    
    # Count sellable items
    sellable_items = [item for item in actual_items.values() if item['price'] is not None]
    logger.info(f"\n💰 Sellable Items Summary:")
    logger.info(f"Total Sellable Items: {len(sellable_items)}")
    
    # Show sellable items with complete hierarchy
    logger.info(f"\n💵 Sellable Items with Complete Hierarchy:")
    for item in sorted(sellable_items, key=lambda x: x['fully_qualified']):
        price_str = f"${item['price']}" if item['price'] is not None else "No Price"
        logger.info(f"  {item['fully_qualified']} - {price_str}")
    
    # Now compare with Quoter structure
    logger.info(f"\n🔄 Comparing with Quoter Structure...")
    
    try:
        from quoter import get_access_token
        quoter_token = get_access_token()
        
        quoter_items = []
        page = 1
        per_page = 100
        
        while True:
            url = f"https://api.quoter.com/v1/items"
            headers = {
                'Authorization': f'Bearer {quoter_token}',
                'Content-Type': 'application/json'
            }
            params = {
                'page': page,
                'per_page': per_page
            }
            
            response = qbo.session.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('data', [])
                quoter_items.extend(items)
                
                if not data.get('has_more', False):
                    break
                page += 1
            else:
                logger.error(f"Failed to fetch Quoter items: {response.status_code}")
                break
        
        logger.info(f"Quoter Items: {len(quoter_items)}")
        
        # Show Quoter items with their categories
        logger.info(f"\n📋 Quoter Items with Categories:")
        for i, item in enumerate(quoter_items[:15], 1):
            category = item.get('category', {})
            if isinstance(category, dict):
                category_name = category.get('name', 'No Category')
            else:
                category_name = str(category) if category else 'No Category'
            
            code = item.get('code', 'No Code')
            price = item.get('price_decimal', 'No Price')
            
            logger.info(f"  {i:2d}. {item.get('name')}")
            logger.info(f"      Category: {category_name}, Code: {code}, Price: ${price}")
        
        # Final comparison
        logger.info(f"\n📊 Final Comparison:")
        logger.info(f"QBO Total Items: {len(all_items)}")
        logger.info(f"QBO Parent Categories: {len(parent_categories)}")
        logger.info(f"QBO Sub Categories: {len(sub_categories)}")
        logger.info(f"QBO Actual Items: {len(actual_items)}")
        logger.info(f"QBO Sellable Items: {len(sellable_items)}")
        logger.info(f"Quoter Items: {len(quoter_items)}")
        
        # Check for matches between sellable QBO items and Quoter items
        qbo_sellable_names = {item['name'].lower() for item in sellable_items}
        quoter_item_names = {item.get('name', '').lower() for item in quoter_items}
        
        matches = qbo_sellable_names.intersection(quoter_item_names)
        logger.info(f"Exact name matches between QBO sellable items and Quoter: {len(matches)}")
        
        if matches:
            logger.info(f"Sample matches: {list(matches)[:10]}")
        
    except Exception as e:
        logger.error(f"Error comparing with Quoter: {e}")

if __name__ == "__main__":
    comprehensive_qbo_analysis()




