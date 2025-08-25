#!/usr/bin/env python3
"""
Retrieve Pipedrive Categories and Subcategories
This script queries the Pipedrive API to get the current category structure
and identify missing links in the category mapping.
"""

import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Pipedrive API configuration
PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

def get_pipedrive_products():
    """Get all products from Pipedrive to analyze categories and subcategories"""
    if not PIPEDRIVE_API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in environment variables")
        return []
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": PIPEDRIVE_API_TOKEN}
    
    all_products = []
    page = 0
    limit = 100
    
    while True:
        params.update({
            "limit": limit,
            "start": page * limit
        })
        
        try:
            response = requests.get(
                f"{BASE_URL}/products",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            products = data.get("data", [])
            
            if not products:
                break
                
            all_products.extend(products)
            page += 1
            
            print(f"📦 Retrieved {len(products)} products from page {page}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error retrieving products: {e}")
            break
    
    return all_products

def analyze_categories(products):
    """Analyze the categories and subcategories from products"""
    categories = {}
    subcategories = {}
    
    for product in products:
        # Main category
        if product.get("category"):
            category_id = int(product["category"])
            category_name = product.get("category_name", f"Category {category_id}")
            categories[category_id] = category_name
            
        # Subcategory (custom field)
        if product.get("ae55145d60840de457ff9e785eba68f0b39ab777"):
            subcategory = str(product["ae55145d60840de457ff9e785eba68f0b39ab777"])
            subcategories[subcategory] = subcategories.get(subcategory, 0) + 1
    
    return categories, subcategories

def get_product_fields():
    """Get product fields to understand the category structure"""
    if not PIPEDRIVE_API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in environment variables")
        return []
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": PIPEDRIVE_API_TOKEN}
    
    try:
        response = requests.get(
            f"{BASE_URL}/productFields",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        return data.get("data", [])
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error retrieving product fields: {e}")
        return []

def main():
    print("🔍 Retrieving Pipedrive category structure...")
    print("=" * 50)
    
    # Get all products
    products = get_pipedrive_products()
    print(f"\n📊 Total products retrieved: {len(products)}")
    
    if not products:
        print("❌ No products found")
        return
    
    # Analyze categories and subcategories
    categories, subcategories = analyze_categories(products)
    
    print(f"\n🏷️  CATEGORIES found in Pipedrive:")
    print("-" * 30)
    for cat_id, cat_name in sorted(categories.items()):
        print(f"  {cat_id}: {cat_name}")
    
    print(f"\n📋 SUBCATEGORIES found in Pipedrive:")
    print("-" * 30)
    for subcat, count in sorted(subcategories.items()):
        print(f"  {subcat}: {count} products")
    
    # Get product fields
    print(f"\n🔧 PRODUCT FIELDS:")
    print("-" * 30)
    fields = get_product_fields()
    for field in fields:
        if field.get("field_type") == "enum":
            print(f"  {field.get('name')}: {field.get('field_type')}")
            options = field.get('options', [])
            if options:
                print(f"    Options: {opt.get('label') for opt in options}")
    
    # Save results to file
    results = {
        "categories": categories,
        "subcategories": subcategories,
        "product_fields": fields,
        "total_products": len(products)
    }
    
    with open("pipedrive_category_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: pipedrive_category_analysis.json")
    print(f"\n🎯 Next steps:")
    print(f"  1. Compare with current mapping in category_mapper.py")
    print(f"  2. Identify missing categories/subcategories")
    print(f"  3. Update the mapping table")

if __name__ == "__main__":
    main()
