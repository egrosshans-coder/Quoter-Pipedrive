#!/usr/bin/env python3
"""
Dynamic Category Manager - Makes Quoter the source of truth for Pipedrive categories
"""

import requests
import os
from dotenv import load_dotenv
from utils.logger import logger
from quoter import get_access_token

load_dotenv()
API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

# Cache for category mappings to avoid repeated API calls
_category_cache = {}

def get_pipedrive_categories():
    """Fetch all existing categories from Pipedrive."""
    headers = {
        "Content-Type": "application/json"
    }
    params = {"api_token": API_TOKEN}
    
    try:
        # Try to get categories from Pipedrive
        # Note: Pipedrive doesn't have a standard categories endpoint for products
        # We'll need to infer from existing products
        url = f"{BASE_URL}/products"
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('data', [])
            
            # Extract unique categories from existing products
            categories = set()
            for product in products:
                if product.get('category'):
                    categories.add(product['category'])
            
            logger.info(f"Found {len(categories)} existing categories in Pipedrive: {list(categories)}")
            return list(categories)
        else:
            logger.warning(f"Could not fetch Pipedrive categories: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Pipedrive categories: {e}")
        return []

def create_pipedrive_category(category_name):
    """
    Create a new category in Pipedrive.
    Note: This is a placeholder - Pipedrive doesn't have a standard API for creating product categories.
    """
    logger.warning(f"⚠️  Pipedrive doesn't have a standard API for creating product categories")
    logger.info(f"📝 You'll need to manually create category '{category_name}' in Pipedrive")
    logger.info(f"📝 Then update the mapping in pipedrive.py")
    
    # For now, return None - user needs to create manually
    return None

def get_or_create_category_mapping(quoter_category_name):
    """
    Get or create a category mapping for Quoter category.
    Returns the Pipedrive category ID.
    """
    # Check cache first
    if quoter_category_name in _category_cache:
        return _category_cache[quoter_category_name]
    
    # Check if we have a manual mapping
    manual_mappings = {
        "Tanks": 30,
        "Balloons": 31,
        "Hologram": 28,
        "Service": 29,
        # Add more as needed
    }
    
    if quoter_category_name in manual_mappings:
        pipedrive_id = manual_mappings[quoter_category_name]
        _category_cache[quoter_category_name] = pipedrive_id
        logger.info(f"✅ Found existing mapping: '{quoter_category_name}' → Pipedrive ID {pipedrive_id}")
        return pipedrive_id
    
    # Check if category exists in Pipedrive
    existing_categories = get_pipedrive_categories()
    
    # For now, we can't automatically create categories in Pipedrive
    # So we'll log a warning and return None
    logger.warning(f"❌ No mapping found for category '{quoter_category_name}'")
    logger.info(f"📝 Please add mapping in pipedrive.py or create category in Pipedrive")
    
    return None

def get_or_create_subcategory_mapping(quoter_subcategory_name):
    """
    Get or create a subcategory mapping for Quoter subcategory.
    Returns the Pipedrive subcategory ID.
    """
    # Check cache first
    if quoter_subcategory_name in _category_cache:
        return _category_cache[quoter_subcategory_name]
    
    # Check if we have a manual mapping
    manual_mappings = {
        "1-to-3 Splitter": 40,
        "Drop": 41,
        "FV": 42,
        # Add more as needed
    }
    
    if quoter_subcategory_name in manual_mappings:
        pipedrive_id = manual_mappings[quoter_subcategory_name]
        _category_cache[quoter_subcategory_name] = pipedrive_id
        logger.info(f"✅ Found existing mapping: '{quoter_subcategory_name}' → Pipedrive ID {pipedrive_id}")
        return pipedrive_id
    
    # For now, we can't automatically create subcategories in Pipedrive
    # So we'll log a warning and return None
    logger.warning(f"❌ No mapping found for subcategory '{quoter_subcategory_name}'")
    logger.info(f"📝 Please add mapping in pipedrive.py or create subcategory in Pipedrive")
    
    return None

def sync_categories_from_quoter():
    """
    Sync all categories from Quoter to ensure Pipedrive has all necessary categories.
    """
    logger.info("=== Syncing Categories from Quoter to Pipedrive ===")
    
    # Get all categories from Quoter
    from category_mapper import get_all_categories
    quoter_categories = get_all_categories()
    
    if not quoter_categories:
        logger.error("No categories found in Quoter")
        return
    
    logger.info(f"Found {len(quoter_categories)} categories in Quoter")
    
    # Process each category
    for category in quoter_categories:
        category_name = category.get('name')
        category_id = category.get('id')
        parent_category = category.get('parent_category')
        
        if parent_category:
            # This is a subcategory
            logger.info(f"Processing subcategory: '{category_name}' (Parent: '{parent_category}')")
            get_or_create_subcategory_mapping(category_name)
        else:
            # This is a main category
            logger.info(f"Processing main category: '{category_name}'")
            get_or_create_category_mapping(category_name)
    
    logger.info("=== Category Sync Complete ===")

def test_dynamic_category_manager():
    """Test the dynamic category manager."""
    logger.info("=== Testing Dynamic Category Manager ===")
    
    # Test with known categories
    test_categories = ["Tanks", "Balloons", "NewCategory", "Hologram"]
    
    for category in test_categories:
        result = get_or_create_category_mapping(category)
        if result:
            logger.info(f"✅ Category '{category}' mapped to ID: {result}")
        else:
            logger.info(f"❌ Category '{category}' needs manual mapping")
    
    # Test with known subcategories
    test_subcategories = ["1-to-3 Splitter", "Drop", "NewSubcategory", "FV"]
    
    for subcategory in test_subcategories:
        result = get_or_create_subcategory_mapping(subcategory)
        if result:
            logger.info(f"✅ Subcategory '{subcategory}' mapped to ID: {result}")
        else:
            logger.info(f"❌ Subcategory '{subcategory}' needs manual mapping")

if __name__ == "__main__":
    test_dynamic_category_manager()
    # sync_categories_from_quoter() 