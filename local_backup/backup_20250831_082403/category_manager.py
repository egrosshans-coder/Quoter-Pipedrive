#!/usr/bin/env python3
"""
Consolidated Category Manager
Fetches real categories from Pipedrive API and provides clean mapping functions.
Replaces both category_mapper.py and dynamic_category_manager.py
"""

import requests
import os
from dotenv import load_dotenv
from utils.logger import logger
from quoter import get_access_token

load_dotenv()
API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

# Cache for categories to avoid repeated API calls
_categories_cache = None
_subcategories_cache = None

def get_pipedrive_categories():
    """
    Fetch all categories directly from Pipedrive API.
    Returns a dict of {category_name: category_id}
    """
    global _categories_cache
    
    if _categories_cache is not None:
        return _categories_cache
    
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return {}
    
    try:
        logger.info("🔍 Fetching categories from Pipedrive API...")
        
        # Get product fields to find the category field
        url = f"{BASE_URL}/productFields"
        params = {"api_token": API_TOKEN}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Find the category field
            category_field = None
            for field in data.get('data', []):
                if field.get('name') == 'Category':
                    category_field = field
                    break
            
            if category_field and 'options' in category_field:
                categories = {}
                for option in category_field['options']:
                    category_id = option.get('id')
                    category_name = option.get('label')
                    if category_id and category_name:
                        categories[category_name] = category_id
                
                _categories_cache = categories
                logger.info(f"✅ Retrieved {len(categories)} categories from Pipedrive")
                return categories
            else:
                logger.error("❌ Category field not found in Pipedrive")
                return {}
        else:
            logger.error(f"❌ API request failed: {response.status_code}")
            return {}
            
    except Exception as e:
        logger.error(f"❌ Error fetching Pipedrive categories: {e}")
        return {}

def get_subcategory_field_key():
    """
    Get the subcategory custom field key from Pipedrive.
    Returns the field key if found, None otherwise.
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    try:
        logger.info("🔍 Finding subcategory custom field key...")
        
        # Get product fields to find the subcategory custom field
        url = f"{BASE_URL}/productFields"
        params = {"api_token": API_TOKEN}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Find the subcategory custom field by name
            subcategory_field = None
            for field in data.get('data', []):
                if field.get('name') == 'Subcategory':
                    subcategory_field = field
                    break
            
            if subcategory_field:
                field_key = subcategory_field.get('key')
                logger.info(f"✅ Found subcategory field key: {field_key}")
                return field_key
            else:
                logger.error("❌ Subcategory field not found in Pipedrive")
                return None
        else:
            logger.error(f"❌ API request failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error finding subcategory field: {e}")
        return None

def get_category_mapping(category_name):
    """
    Get Pipedrive category ID for a category name.
    Returns the category ID if found, None otherwise.
    """
    categories = get_pipedrive_categories()
    category_id = categories.get(category_name)
    
    if category_id:
        logger.info(f"✅ Mapped category '{category_name}' to Pipedrive ID {category_id}")
    else:
        logger.warning(f"⚠️  No Pipedrive category found for '{category_name}'")
    
    return category_id

def get_subcategory_field_key():
    """
    Get the subcategory custom field key from Pipedrive.
    Returns the field key if found, None otherwise.
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    try:
        logger.info("🔍 Finding subcategory custom field key...")
        
        # Get product fields to find the subcategory custom field
        url = f"{BASE_URL}/productFields"
        params = {"api_token": API_TOKEN}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Find the subcategory custom field by name
            subcategory_field = None
            for field in data.get('data', []):
                if field.get('name') == 'Subcategory':
                    subcategory_field = field
                    break
            
            if subcategory_field:
                field_key = subcategory_field.get('key')
                logger.info(f"✅ Found subcategory field key: {field_key}")
                return field_key
            else:
                logger.error("❌ Subcategory field not found in Pipedrive")
                return None
        else:
            logger.error(f"❌ API request failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error finding subcategory field: {e}")
        return None

def get_subcategory_mapping(subcategory_name):
    """
    For subcategories, we return the field key since it's a text field.
    The subcategory_name will be sent as the text value.
    """
    field_key = get_subcategory_field_key()
    if field_key:
        logger.info(f"✅ Subcategory '{subcategory_name}' will be sent to field key: {field_key}")
        return field_key
    else:
        logger.warning(f"⚠️  Could not find subcategory field key")
        return None

def get_category_path_from_item(item_data):
    """
    Get the complete category path from item data by querying the Categories API.
    Returns "Parent / Child" format or just the category name.
    """
    category_id = item_data.get('category_id')
    if not category_id:
        logger.warning("No category_id found in item data")
        return None
    
    try:
        access_token = get_access_token()
        if not access_token:
            logger.error("Failed to get OAuth token for category lookup")
            return None
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Query the Categories API to get the full hierarchy
        url = f"https://api.quoter.com/v1/categories/{category_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            category_data = response.json()
            current_category_name = category_data.get('name', 'Unknown')
            parent_category = category_data.get('parent_category')
            
            if parent_category:
                # Return full path: "Parent / Child"
                full_path = f"{parent_category} / {current_category_name}"
                logger.info(f"🔍 Found category hierarchy: {full_path}")
                return full_path
            else:
                # No parent, this is a main category
                logger.info(f"🔍 Category '{current_category_name}' is a main category (no parent)")
                return current_category_name
                
        else:
            logger.warning(f"Could not get category details for {category_id}: {response.status_code}")
            # Fallback to item's category field if Categories API fails
            fallback_category = item_data.get('category')
            if fallback_category:
                logger.info(f"🔍 Using fallback category from item data: {fallback_category}")
                return fallback_category
            return None
            
    except Exception as e:
        logger.error(f"Error getting category path: {e}")
        # Fallback to item's category field if API call fails
        fallback_category = item_data.get('category')
        if fallback_category:
            logger.info(f"🔍 Using fallback category from item data: {fallback_category}")
            return fallback_category
        return None

def get_category_path(quoter_category_id):
    """
    Get the full category path from Quoter category ID.
    This function is kept for backward compatibility but the Items API approach is better.
    """
    logger.warning("⚠️  Using deprecated category ID lookup - prefer get_category_path_from_item()")
    
    try:
        access_token = get_access_token()
        if not access_token:
            logger.error("Failed to get OAuth token for category lookup")
            return None
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Get category details from Quoter
        url = f"https://api.quoter.com/v1/categories/{quoter_category_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            category_data = response.json()
            current_category_name = category_data.get('name', 'Unknown')
            
            # Check if it has a parent category
            if category_data.get('parent_id'):
                # Get parent category name
                parent_response = requests.get(
                    f"https://api.quoter.com/v1/categories/{category_data['parent_id']}", 
                    headers=headers, 
                    timeout=10
                )
                
                if parent_response.status_code == 200:
                    parent_data = parent_response.json()
                    parent_name = parent_data.get('name', 'Unknown')
                    
                    # Return full path: "Parent / Child"
                    full_path = f"{parent_name} / {current_category_name}"
                    logger.info(f"🔍 Found category hierarchy: {full_path}")
                    return full_path
                else:
                    logger.warning(f"Could not get parent category details: {parent_response.status_code}")
            
            # No parent found, this is a main category
            logger.info(f"🔍 Category '{current_category_name}' is a main category (no parent)")
            return current_category_name
            
        else:
            logger.warning(f"Could not get category details for {quoter_category_id}: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting category path: {e}")
        return None

def print_current_categories():
    """Print current categories and subcategory field info for debugging."""
    print("\n📋 CURRENT PIPEDRIVE CATEGORIES:")
    print("=" * 50)
    
    categories = get_pipedrive_categories()
    for name, id_val in sorted(categories.items()):
        print(f"• {name} (ID: {id_val})")
    
    print(f"\n📋 SUBCATEGORY FIELD INFO:")
    print("=" * 50)
    
    subcategory_field_key = get_subcategory_field_key()
    if subcategory_field_key:
        print(f"• Subcategory field key: {subcategory_field_key}")
        print(f"• Field type: Text (free-form input)")
    else:
        print("• Subcategory field not found")
    
    print(f"\n📊 SUMMARY:")
    print(f"  Categories: {len(categories)}")
    print(f"  Subcategory field: {'Found' if subcategory_field_key else 'Not found'}")

if __name__ == "__main__":
    print_current_categories()
