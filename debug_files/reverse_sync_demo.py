#!/usr/bin/env python3
"""
Reverse Sync Demo - Pipedrive → Quoter
Shows the exact logic for updating Quoter categories from Pipedrive corrections.
"""

import requests
import os
from dotenv import load_dotenv
from utils.logger import logger
from quoter import get_access_token

load_dotenv()
PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
PIPEDRIVE_BASE_URL = "https://api.pipedrive.com/v1"
QUOTER_BASE_URL = "https://api.quoter.com/v1"

def get_pipedrive_products_with_categories():
    """
    Get all products from Pipedrive with their corrected categories.
    This is what you've been fixing manually in Pipedrive.
    """
    print("🔍 STEP 1: Getting corrected categories from Pipedrive")
    print("=" * 60)
    
    # Get all products from Pipedrive
    url = f"{PIPEDRIVE_BASE_URL}/products"
    params = {"api_token": PIPEDRIVE_API_TOKEN, "limit": 5}  # Just 5 for demo
    
    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        print(f"❌ Failed to get Pipedrive products: {response.status_code}")
        return []
    
    products = response.json().get("data", [])
    
    print(f"📦 Found {len(products)} products in Pipedrive")
    print()
    
    for product in products:
        name = product.get("name", "Unknown")
        category = product.get("category", "No Category")
        
        # Get the subcategory from the custom field
        subcategory = "No Subcategory"
        for field in product.get("custom_fields", []):
            if field.get("name") == "Subcategory":
                subcategory = field.get("value", "No Subcategory")
                break
        
        print(f"📋 Product: {name}")
        print(f"   Main Category: {category}")
        print(f"   Subcategory: {subcategory}")
        print()
    
    return products

def get_quoter_category_structure():
    """
    Get the category structure from Quoter to understand the mapping.
    """
    print("🔍 STEP 2: Understanding Quoter Category Structure")
    print("=" * 60)
    
    access_token = get_access_token()
    if not access_token:
        print("❌ Could not get Quoter access token")
        return {}
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get a few categories to show the structure
    url = f"{QUOTER_BASE_URL}/categories"
    params = {"limit": 10}
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    if response.status_code != 200:
        print(f"❌ Failed to get Quoter categories: {response.status_code}")
        return {}
    
    categories = response.json().get("data", [])
    
    print(f"📋 Found {len(categories)} categories in Quoter")
    print()
    
    for category in categories[:5]:  # Show first 5
        cat_id = category.get("id")
        cat_name = category.get("name", "Unknown")
        parent_id = category.get("parent_id")
        parent_name = category.get("parent_category")
        
        print(f"📁 Category ID: {cat_id}")
        print(f"   Name: {cat_name}")
        print(f"   Parent ID: {parent_id}")
        print(f"   Parent Name: {parent_name}")
        print()
    
    return categories

def demonstrate_mapping_logic():
    """
    Show exactly how the mapping will work.
    """
    print("🔍 STEP 3: Category Mapping Logic")
    print("=" * 60)
    
    print("📋 MAPPING RULES:")
    print()
    print("1. Pipedrive 'category' field → Quoter 'parent_category'")
    print("2. Pipedrive 'subcategory' field → Quoter 'category' (specific category ID)")
    print()
    print("🔄 EXAMPLE MAPPING:")
    print()
    print("Pipedrive Product:")
    print("   Main Category: 'HOLOGRAM'")
    print("   Subcategory: 'Hologram / FV'")
    print()
    print("Quoter Mapping:")
    print("   Find category with name 'Hologram / FV'")
    print("   Ensure it's under parent 'HOLOGRAM'")
    print("   Use that category ID to update the Quoter product")
    print()
    print("📝 WHAT THE SCRIPT WILL DO:")
    print("1. Read all 249 products from Pipedrive")
    print("2. For each product, get its corrected category/subcategory")
    print("3. Find the matching Quoter category ID")
    print("4. Update the Quoter product with the correct category_id")
    print("5. Log all changes for verification")

def show_quoter_update_example():
    """
    Show an example of how we'll update a Quoter product.
    """
    print("🔍 STEP 4: Quoter Update Example")
    print("=" * 60)
    
    print("📝 QUOTER PRODUCT UPDATE:")
    print()
    print("Current Quoter product:")
    print("   category_id: 'cat_30LNfhXf8MdwLYlqsvoBNDGfPNV'")
    print("   name: 'Hologram Projector'")
    print()
    print("After Pipedrive correction:")
    print("   category_id: 'cat_NEW_CORRECT_ID'  # Updated from Pipedrive")
    print("   name: 'Hologram Projector'  # Unchanged")
    print()
    print("🔄 The script will:")
    print("   - Keep all other fields unchanged")
    print("   - Only update the category_id field")
    print("   - Ensure the new category matches Pipedrive's corrected data")

if __name__ == "__main__":
    print("🚀 REVERSE SYNC DEMO: Pipedrive → Quoter")
    print("=" * 60)
    print()
    
    # Step 1: Show Pipedrive data
    pipedrive_products = get_pipedrive_products_with_categories()
    
    print()
    
    # Step 2: Show Quoter structure
    quoter_categories = get_quoter_category_structure()
    
    print()
    
    # Step 3: Show mapping logic
    demonstrate_mapping_logic()
    
    print()
    
    # Step 4: Show update example
    show_quoter_update_example()
    
    print()
    print("✅ This is exactly what the reverse sync script will do!")
    print("   Ready to create the actual implementation?")
