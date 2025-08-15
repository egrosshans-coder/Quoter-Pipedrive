#!/usr/bin/env python3
"""
CSV Reader for Quoter Export - Processes the CSV file and converts to API format
"""

import csv
import os
from utils.logger import logger

def read_quoter_csv(csv_path="test_files/export.csv"):
    """
    Read the Quoter CSV export and convert to the format expected by our sync system.
    
    Returns:
        list: List of items in the format expected by pipedrive.py
    """
    logger.info(f"=== Reading Quoter CSV: {csv_path} ===")
    
    if not os.path.exists(csv_path):
        logger.error(f"❌ CSV file not found: {csv_path}")
        return []
    
    items = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
                try:
                    # Skip empty rows
                    if not row.get('*Item Name', '').strip():
                        continue
                    
                    # Convert CSV row to our expected format
                    item = {
                        'id': f"csv_item_{row_num}",  # Generate a unique ID
                        'name': row.get('*Item Name', '').strip(),
                        'code': row.get('Code', '').strip(),
                        'description': row.get('Description', '').strip(),
                        'category': row.get('*Category', '').strip(),
                        'subcategory': row.get('Subcategory', '').strip(),
                        'price_decimal': float(row.get('*USD Price (e.g. 1000.00)', 0)) if row.get('*USD Price (e.g. 1000.00)', '').strip() else 0,
                        'cost_decimal': float(row.get('USD Cost (in dollars or percentage)', 0)) if row.get('USD Cost (in dollars or percentage)', '').strip() else 0,
                        'sku': row.get('Supplier SKU', '').strip(),
                        'manufacturer': row.get('Manufacturer', '').strip(),
                        'supplier': row.get('Supplier', '').strip(),
                        'weight': float(row.get('Weight (e.g. 5.0 - default is 0)', 0)) if row.get('Weight (e.g. 5.0 - default is 0)', '').strip() else 0,
                        'pricing_type': row.get('Pricing Type (enter Flat Fee or Fixed Per Unit - default is Fixed Per Unit),', '').strip(),
                        'cost_type': row.get('USD Cost Type (enter dollars or percent - default is dollars)', '').strip(),
                        'recurring': row.get('Recurring (enter No/Monthly/Quarterly/Annually - default is No)', '').strip(),
                        'allow_decimal': row.get('Allow Decimal Quantities (enter Yes or No - default is No)', '').strip(),
                        'taxable': row.get('Taxable Item (enter Yes or No - default is Yes)', '').strip(),
                    }
                    
                    # Create category_id based on category and subcategory
                    if item['category'] and item['subcategory']:
                        item['category_id'] = f"{item['category']} / {item['subcategory']}"
                    elif item['category']:
                        item['category_id'] = item['category']
                    else:
                        item['category_id'] = None
                    
                    items.append(item)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing row {row_num}: {e}")
                    continue
            
            logger.info(f"✅ Successfully processed {len(items)} items from CSV")
            
            # Show sample items
            logger.info(f"\n=== Sample Items (first 5) ===")
            for i, item in enumerate(items[:5]):
                logger.info(f"{i+1}. {item['name']} (Category: {item['category']}, Price: ${item['price_decimal']})")
            
            return items
            
    except Exception as e:
        logger.error(f"❌ Error reading CSV file: {e}")
        return []

def test_csv_reader():
    """Test the CSV reader."""
    logger.info("=== Testing CSV Reader ===")
    
    items = read_quoter_csv()
    
    if items:
        logger.info(f"\n=== Summary ===")
        logger.info(f"📦 Total items: {len(items)}")
        
        # Count by category
        categories = {}
        for item in items:
            cat = item.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        logger.info(f"📁 Categories found:")
        for cat, count in sorted(categories.items()):
            logger.info(f"  • {cat}: {count} items")
        
        # Check items with SKU
        items_with_sku = [item for item in items if item.get('sku')]
        logger.info(f"🏷️  Items with SKU: {len(items_with_sku)}")
        logger.info(f"🏷️  Items without SKU: {len(items) - len(items_with_sku)}")
        
        return items
    else:
        logger.error("❌ No items found in CSV")
        return []

if __name__ == "__main__":
    test_csv_reader() 