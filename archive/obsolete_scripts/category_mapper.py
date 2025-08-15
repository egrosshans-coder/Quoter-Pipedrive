#!/usr/bin/env python3
"""
Category mapping utilities for Quoter to Pipedrive sync
"""

import requests
import os
from dotenv import load_dotenv
from utils.logger import logger
from quoter import get_access_token

load_dotenv()

# Cache for categories to avoid repeated API calls
_categories_cache = None

def get_all_categories():
    """Fetch all categories from Quoter API with caching."""
    global _categories_cache
    
    if _categories_cache is not None:
        return _categories_cache
    
    access_token = get_access_token()
    if not access_token:
        return []
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    endpoint = "https://api.quoter.com/v1/categories"
    
    try:
        all_categories = []
        offset = 0
        limit = 100
        
        while True:
            params = {
                "limit": limit,
                "offset": offset
            }
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get("data", [])
                has_more = data.get("has_more", False)
                total_count = data.get("total_count", 0)
                
                all_categories.extend(categories)
                
                if not has_more or len(categories) == 0 or len(all_categories) >= total_count:
                    break
                
                offset += limit
            else:
                logger.error(f"❌ API request failed with status {response.status_code}: {response.text}")
                break
        
        logger.info(f"✅ Successfully retrieved {len(all_categories)} total categories from Quoter")
        _categories_cache = all_categories
        return all_categories
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error connecting to Quoter API: {e}")
        return []

def get_category_path(category_id):
    """Get the full category path (Parent / Child) for a given category ID."""
    categories = get_all_categories()
    
    if not categories:
        return None
    
    # Find the category by ID
    target_category = None
    for category in categories:
        if category['id'] == category_id:
            target_category = category
            break
    
    if not target_category:
        logger.warning(f"Category with ID {category_id} not found")
        return None
    
    # If it has a parent, build the full path
    if target_category.get('parent_category'):
        return f"{target_category['parent_category']} / {target_category['name']}"
    else:
        return target_category['name']

def get_category_by_name(category_name):
    """Find a category by name (case-insensitive)."""
    categories = get_all_categories()
    
    if not categories:
        return None
    
    for category in categories:
        if category['name'].lower() == category_name.lower():
            return category
    
    return None

def test_category_mapping():
    """Test the category mapping functionality."""
    logger.info("=== Testing Category Mapping ===")
    
    # Test with known categories
    test_cases = [
        "cat_30LNfhXf8MdwLYlqsvoBNDGfPNV",  # 1-to-3 Splitter
        "cat_30LNfgV7gCwhQydirKD1KhNrS00",  # Drop
    ]
    
    for category_id in test_cases:
        path = get_category_path(category_id)
        logger.info(f"Category ID {category_id}: {path}")
    
    # Test finding categories by name
    test_names = [
        "Tanks",
        "Balloons", 
        "1-to-3 Splitter",
        "Drop"
    ]
    
    logger.info("\n=== Testing Category Lookup by Name ===")
    for name in test_names:
        category = get_category_by_name(name)
        if category:
            logger.info(f"Found '{name}': ID={category['id']}, Parent={category.get('parent_category')}")
        else:
            logger.warning(f"Category '{name}' not found")

if __name__ == "__main__":
    test_category_mapping() 