#!/usr/bin/env python3
"""
Working test script - completely self-contained
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("🚀 WORKING PIPEDRIVE CATEGORY TEST")
    print("=" * 50)
    
    # Get API token
    API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found")
        return
    
    # Get products with pagination
    all_products = []
    page = 0
    limit = 100
    
    while True:
        try:
            url = "https://api.pipedrive.com/v1/products"
            params = {
                "api_token": API_TOKEN,
                "limit": limit,
                "start": page * limit
            }
            
            response = requests.get(
                url, 
                headers={"Content-Type": "application/json"}, 
                params=params, 
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to fetch products: {response.status_code}")
                return
                
            data = response.json()
            products = data.get("data", [])
            
            if not products:
                break
                
            all_products.extend(products)
            page += 1
            
            print(f"📦 Retrieved {len(products)} products from page {page}")
            
        except Exception as e:
            print(f"❌ Error fetching products: {e}")
            break
    
    if not all_products:
        print("❌ No products found")
        return
        
    print(f"✅ Found {len(all_products)} products total")
    products = all_products
    
    # Define mapping directly in main function
    category_mapping = {
            28: "Hologram",
            29: "Service", 
            30: "Tanks",
            31: "Balloons",
            36: "LED Tubes/Floor/Panels",
            35: "Laser",
            38: "Projection",
            94: "Drones",
            32: "Robotics",
            34: "Spheres",
            43: "Wristbands/Lanyards/Orbs",
            40: "1-to-3 Splitter",
            41: "Drop",
            42: "FV",
            101: "Pyro",
            102: "Confetti/Streamers", 
            104: "Fog",
            109: "CO2",
            110: "Water",
            360: "Apparel",
            361: "Programming",
            362: "AI",
            396: "DJ"
    }
    
    # Count categories and build hierarchy
    category_counts = {}
    subcategory_counts = {}
    category_hierarchy = {}  # New: tracks which subcategories belong to which categories
    
    for product in products:
        # Main category
        if product.get("category"):
            category_id = int(product["category"])  # Convert string to int
            category_name = category_mapping.get(category_id, f"Unknown ID: {category_id}")
            category_counts[category_name] = category_counts.get(category_name, 0) + 1
            
            # Initialize category hierarchy if not exists
            if category_name not in category_hierarchy:
                category_hierarchy[category_name] = set()
        
        # Subcategory
        if product.get("ae55145d60840de457ff9e785eba68f0b39ab777"):
            subcategory = str(product["ae55145d60840de457ff9e785eba68f0b39ab777"])
            subcategory_counts[subcategory] = subcategory_counts.get(subcategory, 0) + 1
            
            # Add subcategory to the appropriate parent category
            if product.get("category"):
                category_id = int(product["category"])
                category_name = category_mapping.get(category_id, f"Unknown ID: {category_id}")
                category_hierarchy[category_name].add(subcategory)
    
    # Display results
    print(f"\n📊 CATEGORY BREAKDOWN:")
    print("-" * 30)
    for category, count in sorted(category_counts.items()):
        print(f"  {category}: {count} products")
    
    print(f"\n🔗 SUBCATEGORY BREAKDOWN:")
    print("-" * 30)
    for subcategory, count in sorted(subcategory_counts.items()):
        print(f"  {subcategory}: {count} products")
    
    print(f"\n🏗️  CATEGORY HIERARCHY (Categories with their Subcategories):")
    print("-" * 60)
    for category, subcategories in sorted(category_hierarchy.items()):
        if subcategories:
            print(f"  {category}:")
            for subcat in sorted(subcategories):
                count = subcategory_counts.get(subcat, 0)
                print(f"    • {subcat}: {count} products")
        else:
            print(f"  {category}: (no subcategories)")
    
    print(f"\n🎯 SUMMARY:")
    print(f"  Total Categories: {len(category_counts)}")
    print(f"  Total Subcategories: {len(subcategory_counts)}")
    print(f"  Total Products: {len(products)}")

if __name__ == "__main__":
    main()
