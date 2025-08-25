#!/usr/bin/env python3
"""
Update Category Mappings - Start from Quoter and map to Pipedrive
"""

import requests
import os
from dotenv import load_dotenv
from category_mapper import get_all_categories

load_dotenv()

def get_pipedrive_categories_and_subcategories():
    """Fetch all unique categories and subcategories from Pipedrive products with pagination."""
    API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
    BASE_URL = "https://api.pipedrive.com/v1"
    
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found")
        return {}, {}
    
    categories = {}
    subcategories = {}
    
    try:
        all_products = []
        start = 0
        limit = 100
        
        # Pagination loop to get ALL products
        while True:
            url = f"{BASE_URL}/products"
            params = {
                "api_token": API_TOKEN,
                "start": start,
                "limit": limit
            }
            
            response = requests.get(url, headers={"Content-Type": "application/json"}, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", [])
                has_more = data.get("has_more", False)
                total_count = data.get("total_count", 0)
                
                all_products.extend(products)
                print(f"📊 Fetched {len(products)} products (start: {start}, total so far: {len(all_products)})")
                
                if not has_more or len(products) == 0 or len(all_products) >= total_count:
                    break
                
                start += limit
            else:
                print(f"❌ Failed to fetch Pipedrive products: {response.status_code}")
                break
        
        print(f"📊 Total products fetched: {len(all_products)}")
        
        # Process all products to extract categories and subcategories
        for product in all_products:
            # Main category
            if product.get('category'):
                cat_id = product['category']
                if cat_id not in categories:
                    categories[cat_id] = set()
                # Store product names to help identify what this category contains
                categories[cat_id].add(product.get('name', 'Unknown'))
            
            # Subcategory
            subcat_field = "ae55145d60840de457ff9e785eba68f0b39ab777"
            if product.get(subcat_field):
                subcat_name = str(product[subcat_field])
                if subcat_name not in subcategories:
                    subcategories[subcat_name] = set()
                subcategories[subcat_name].add(product.get('name', 'Unknown'))
        
        print(f"📋 Found {len(categories)} unique category IDs in Pipedrive")
        print(f"📋 Found {len(subcategories)} unique subcategories in Pipedrive")
        
    except Exception as e:
        print(f"❌ Error fetching Pipedrive products: {e}")
        return {}, {}
    
    return categories, subcategories

def analyze_quoter_categories():
    """Analyze Quoter categories and suggest mappings."""
    print("\n🔍 **Analyzing Quoter Categories**")
    print("=" * 60)
    
    quoter_categories = get_all_categories()
    if not quoter_categories:
        print("❌ No categories found in Quoter")
        return
    
    print(f"📊 Found {len(quoter_categories)} categories in Quoter")
    
    # Group by main categories and subcategories
    main_categories = {}
    subcategories = {}
    
    for category in quoter_categories:
        category_name = category.get('name')
        category_id = category.get('id')
        parent_category = category.get('parent_category')
        
        if parent_category:
            # This is a subcategory
            if parent_category not in subcategories:
                subcategories[parent_category] = []
            subcategories[parent_category].append({
                'id': category_id,
                'name': category_name
            })
        else:
            # This is a main category
            main_categories[category_name] = category_id
    
    print(f"\n📋 **Main Categories ({len(main_categories)}):**")
    for name, cat_id in main_categories.items():
        print(f"  • {name} (ID: {cat_id})")
    
    print(f"\n📋 **Subcategories by Parent ({len(subcategories)}):**")
    for parent, subs in subcategories.items():
        print(f"  • {parent}:")
        for sub in subs:
            print(f"    - {sub['name']} (ID: {sub['id']})")
    
    return main_categories, subcategories

def suggest_mappings(main_categories, subcategories, pipedrive_cats, pipedrive_subcats):
    """Suggest mappings between Quoter and Pipedrive categories."""
    print("\n�� **Suggested Category Mappings**")
    print("=" * 60)
    
    print("\n📝 **Main Categories to Add to Mapping Table:**")
    print("manual_mappings = {")
    
    # Suggest mappings for main categories
    for quoter_name in main_categories.keys():
        # Look for potential matches in Pipedrive
        best_match = None
        best_score = 0
        
        for pipedrive_id, product_names in pipedrive_cats.items():
            # Simple matching logic - look for category names in product names
            for product_name in product_names:
                if quoter_name.lower() in product_name.lower():
                    score = len(quoter_name) / len(product_name)  # Simple scoring
                    if score > best_score:
                        best_score = score
                        best_match = pipedrive_id
        
        if best_match and best_score > 0.3:  # Threshold for matching
            print(f'    "{quoter_name}": {best_match},  # Suggested from Pipedrive products')
        else:
            print(f'    "{quoter_name}": None,  # No clear match found')
    
    print("}")
    
    print("\n📝 **Subcategories to Add to Mapping Table:**")
    print("manual_mappings = {")
    
    # Suggest mappings for subcategories
    for parent, subs in subcategories.items():
        for sub in subs:
            sub_name = sub['name']
            best_match = None
            
            # Look for exact matches in Pipedrive subcategories
            if sub_name in pipedrive_subcats:
                # Find the most common Pipedrive ID for this subcategory
                pipedrive_ids = list(pipedrive_subcats[sub_name])
                if pipedrive_ids:
                    best_match = pipedrive_ids[0]  # Use first one for now
            
            if best_match:
                print(f'    "{sub_name}": {best_match},  # Matches Pipedrive subcategory')
            else:
                print(f'    "{sub_name}": None,  # No clear match found')
    
    print("}")

def main():
    """Main function to update category mappings."""
    print("🔄 **Category Mapping Update Tool**")
    print("=" * 60)
    print("Starting from Quoter categories and mapping to Pipedrive...")
    
    # Get Pipedrive categories
    pipedrive_cats, pipedrive_subcats = get_pipedrive_categories_and_subcategories()
    
    # Analyze Quoter categories
    main_categories, subcategories = analyze_quoter_categories()
    
    # Suggest mappings
    suggest_mappings(main_categories, subcategories, pipedrive_cats, pipedrive_subcats)
    
    print("\n" + "=" * 60)
    print("🎯 **Next Steps:**")
    print("1. Review the suggested mappings above")
    print("2. Update the manual_mappings in dynamic_category_manager.py")
    print("3. Test the updated mappings")
    print("4. Import your CSV to Quoter")

if __name__ == "__main__":
    main()
