#!/usr/bin/env python3
"""
Pipedrive to Quoter Sync Script

This script compares Pipedrive products with Quoter items and syncs changes back to Quoter.
Focuses on: names, categories, and product codes (skips income/expense accounts for now).
"""

import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

# API Configuration
PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
CLIENT_ID = os.getenv("QUOTER_API_KEY")  # Note: .env uses QUOTER_API_KEY
CLIENT_SECRET = os.getenv("QUOTER_CLIENT_SECRET")
PIPEDRIVE_BASE_URL = "https://api.pipedrive.com/v1"
QUOTER_BASE_URL = "https://api.quoter.com/v1"

def get_access_token():
    """
    Get OAuth access token from Quoter API.
    
    Based on Quoter API documentation: https://docs.quoter.com/api
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.error("CLIENT_ID or CLIENT_SECRET not found in environment variables")
        return None
    
    auth_url = "https://api.quoter.com/v1/auth/oauth/authorize"
    auth_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    
    try:
        logger.info("Getting OAuth access token from Quoter...")
        response = requests.post(auth_url, json=auth_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            if access_token:
                logger.info("✅ Successfully obtained OAuth access token")
                return access_token
            else:
                logger.error("❌ No access_token in response")
                return None
        else:
            logger.error(f"❌ OAuth authentication failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error getting OAuth token: {e}")
        return None

def get_pipedrive_products():
    """
    Fetch all products from Pipedrive.
    
    Returns:
        list: List of Pipedrive products
    """
    if not PIPEDRIVE_API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return []
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": PIPEDRIVE_API_TOKEN}
    
    try:
        all_products = []
        page = 1
        limit = 100
        
        while True:
            params.update({
                "limit": limit,
                "start": (page - 1) * limit
            })
            
            logger.info(f"Fetching Pipedrive products page {page}")
            
            response = requests.get(
                f"{PIPEDRIVE_BASE_URL}/products",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", [])
                
                if not products:
                    break
                    
                all_products.extend(products)
                logger.info(f"Retrieved {len(products)} products (page {page})")
                
                if len(products) < limit:
                    break
                    
                page += 1
            else:
                logger.error(f"Error fetching Pipedrive products: {response.status_code}")
                break
        
        logger.info(f"Total Pipedrive products retrieved: {len(all_products)}")
        return all_products
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Pipedrive API: {e}")
        return []

def get_quoter_items():
    """
    Fetch all items from Quoter.
    
    Returns:
        list: List of Quoter items
    """
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        return []
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        all_items = []
        page = 1
        limit = 100
        
        while True:
            params = {
                "page": page,
                "limit": limit
            }
            
            logger.info(f"Fetching Quoter items page {page}")
            
            response = requests.get(
                "https://api.quoter.com/v1/items",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                
                if not items:
                    break
                    
                all_items.extend(items)
                logger.info(f"Retrieved {len(items)} items (page {page})")
                
                if len(items) < limit:
                    break
                    
                page += 1
            else:
                logger.error(f"Error fetching Quoter items: {response.status_code}")
                break
        
        logger.info(f"Total Quoter items retrieved: {len(all_items)}")
        return all_items
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Quoter API: {e}")
        return []

def find_matching_items(pipedrive_products, quoter_items):
    """
    Find matching items between Pipedrive and Quoter based on product codes.
    
    Args:
        pipedrive_products (list): List of Pipedrive products
        quoter_items (list): List of Quoter items
        
    Returns:
        list: List of tuples (pipedrive_product, quoter_item) for matches
    """
    matches = []
    
    # Create a lookup dictionary for Quoter items by code
    quoter_lookup = {}
    for item in quoter_items:
        code = item.get("code")
        if code and code.strip():
            quoter_lookup[code.strip()] = item
    
    logger.info(f"Created Quoter lookup with {len(quoter_lookup)} items")
    
    # Find matches
    for product in pipedrive_products:
        product_code = product.get("code", "").strip()
        if product_code and product_code in quoter_lookup:
            quoter_item = quoter_lookup[product_code]
            matches.append((product, quoter_item))
            logger.debug(f"Found match: {product_code} - {product.get('name')} <-> {quoter_item.get('name')}")
    
    logger.info(f"Found {len(matches)} matching items between Pipedrive and Quoter")
    return matches

def get_quoter_categories():
    """
    Fetch all categories from Quoter to build a lookup table.
    
    Returns:
        dict: Dictionary mapping category names to IDs
    """
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        return {}
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info("Fetching Quoter categories...")
        
        response = requests.get(
            "https://api.quoter.com/v1/categories",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            categories = data.get("data", [])
            
            # Build lookup table: "Parent / Child" -> category_id
            category_lookup = {}
            for category in categories:
                category_id = category.get("id")
                category_name = category.get("name", "")
                parent_name = category.get("parent", {}).get("name", "") if category.get("parent") else ""
                
                if parent_name and category_name:
                    # Parent / Child format
                    full_name = f"{parent_name} / {category_name}"
                    category_lookup[full_name] = category_id
                    logger.debug(f"Mapped category: '{full_name}' -> {category_id}")
                elif category_name:
                    # Just parent category
                    category_lookup[category_name] = category_id
                    logger.debug(f"Mapped category: '{category_name}' -> {category_id}")
            
            logger.info(f"Created Quoter category lookup with {len(category_lookup)} categories")
            return category_lookup
        else:
            logger.error(f"Error fetching Quoter categories: {response.status_code}")
            return {}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Quoter categories API: {e}")
        return {}

def compare_items(pipedrive_product, quoter_item, quoter_categories):
    """
    Compare a Pipedrive product with a Quoter item and identify changes.
    
    Args:
        pipedrive_product (dict): Pipedrive product data
        quoter_item (dict): Quoter item data
        quoter_categories (dict): Quoter category lookup table
        
    Returns:
        dict: Changes that need to be synced to Quoter
    """
    changes = {}
    
    # Compare names
    pipedrive_name = pipedrive_product.get("name", "").strip()
    quoter_name = quoter_item.get("name", "").strip()
    
    if pipedrive_name != quoter_name:
        changes["name"] = {
            "old": quoter_name,
            "new": pipedrive_name
        }
        logger.info(f"Name change detected: '{quoter_name}' -> '{pipedrive_name}'")
    
    # Compare codes
    pipedrive_code = pipedrive_product.get("code", "").strip()
    quoter_code = quoter_item.get("code", "").strip()
    
    if pipedrive_code != quoter_code:
        changes["code"] = {
            "old": quoter_code,
            "new": pipedrive_code
        }
        logger.info(f"Code change detected: '{quoter_code}' -> '{pipedrive_code}'")
    
    # Compare categories - handle Quoter's parent/child schema
    pipedrive_category_name = pipedrive_product.get("category_name", "").strip()
    quoter_category_id = quoter_item.get("category_id", "")
    
    if pipedrive_category_name:
        # Look up the category ID in Quoter
        quoter_category_id_for_name = quoter_categories.get(pipedrive_category_name)
        
        if quoter_category_id_for_name and str(quoter_category_id_for_name) != str(quoter_category_id):
            changes["category_id"] = {
                "old": quoter_category_id,
                "new": quoter_category_id_for_name,
                "category_name": pipedrive_category_name
            }
            logger.info(f"Category change detected: '{quoter_category_id}' -> '{quoter_category_id_for_name}' ('{pipedrive_category_name}')")
        elif not quoter_category_id_for_name:
            logger.warning(f"Category '{pipedrive_category_name}' not found in Quoter categories")
    
    return changes

def update_quoter_item(quoter_item_id, changes):
    """
    Update a Quoter item with the specified changes.
    
    Args:
        quoter_item_id (str): Quoter item ID
        changes (dict): Changes to apply
        
    Returns:
        bool: True if update successful, False otherwise
    """
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Prepare update data
    update_data = {}
    for field, change in changes.items():
        update_data[field] = change["new"]
    
    try:
        logger.info(f"Updating Quoter item {quoter_item_id} with changes: {update_data}")
        
        response = requests.patch(
            f"https://api.quoter.com/v1/items/{quoter_item_id}",
            headers=headers,
            json=update_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Successfully updated Quoter item {quoter_item_id}")
            return True
        else:
            logger.error(f"❌ Failed to update Quoter item {quoter_item_id}: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error updating Quoter item {quoter_item_id}: {e}")
        return False

def main():
    """
    Main function to sync Pipedrive changes back to Quoter.
    """
    logger.info("🔄 Starting Pipedrive to Quoter sync...")
    
    # Get data from both systems
    logger.info("📥 Fetching data from Pipedrive...")
    pipedrive_products = get_pipedrive_products()
    
    logger.info("📥 Fetching data from Quoter...")
    quoter_items = get_quoter_items()
    
    if not pipedrive_products or not quoter_items:
        logger.error("❌ Failed to fetch data from one or both systems")
        return
    
    # Get Quoter categories for proper mapping
    logger.info("📂 Fetching Quoter categories...")
    quoter_categories = get_quoter_categories()
    
    # Find matching items
    logger.info("🔍 Finding matching items...")
    matches = find_matching_items(pipedrive_products, quoter_items)
    
    if not matches:
        logger.warning("⚠️ No matching items found between Pipedrive and Quoter")
        return
    
    # Compare and update items
    logger.info("🔄 Comparing items and applying changes...")
    
    updated_count = 0
    error_count = 0
    
    for pipedrive_product, quoter_item in matches:
        quoter_item_id = quoter_item.get("id")
        if not quoter_item_id:
            logger.warning(f"⚠️ Quoter item missing ID: {quoter_item.get('name')}")
            continue
        
        # Compare items (pass quoter_categories for proper category mapping)
        changes = compare_items(pipedrive_product, quoter_item, quoter_categories)
        
        if changes:
            logger.info(f"📝 Changes found for {quoter_item.get('name')} (ID: {quoter_item_id}):")
            for field, change in changes.items():
                if field == "category_id" and "category_name" in change:
                    logger.info(f"   {field}: '{change['old']}' -> '{change['new']}' ('{change['category_name']}')")
                else:
                    logger.info(f"   {field}: '{change['old']}' -> '{change['new']}'")
            
            # Update Quoter item
            if update_quoter_item(quoter_item_id, changes):
                updated_count += 1
            else:
                error_count += 1
        else:
            logger.debug(f"✅ No changes needed for {quoter_item.get('name')} (ID: {quoter_item_id})")
    
    # Summary
    logger.info("🎉 Sync completed!")
    logger.info(f"📊 Summary:")
    logger.info(f"   Total matches: {len(matches)}")
    logger.info(f"   Items updated: {updated_count}")
    logger.info(f"   Errors: {error_count}")
    logger.info(f"   No changes needed: {len(matches) - updated_count - error_count}")

if __name__ == "__main__":
    main()
