#!/usr/bin/env python3
"""
Check Pipedrive products for missing 4 required fields:
1. CatSub (QBO-Category:Subcategory)
2. QBO Item Type
3. Product/Service
4. Sync to QuickBooks
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "https://api.pipedrive.com/v1"
API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")

# Field keys (from pipedrive.py)
CATSUB_FIELD_KEY = "9c636133839b978b686bbc952fbd5dc41d5cd087"
QBO_ITEMTYPE_FIELD_KEY = "ae55145d60840de457ff9e785eba68f0b39ab777"
PRODUCT_SERVICE_FIELD_KEY = "98ec4970ff4f9f9cc17926d27675eee823a4eb86"
SYNC_FIELD_KEY = "98ec4970ff4f9f9cc17926d27675eee823a4eb86"

def get_all_products():
    """Get all products from Pipedrive with pagination"""
    all_products = []
    start = 0
    limit = 100
    
    while True:
        url = f"{BASE_URL}/products"
        params = {
            "api_token": API_TOKEN,
            "start": start,
            "limit": limit
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error fetching products: {response.status_code}")
            break
            
        data = response.json()
        products = data.get("data", [])
        
        if not products:
            break
            
        all_products.extend(products)
        
        # Check if there are more pages
        pagination = data.get("additional_data", {}).get("pagination", {})
        if not pagination.get("more_items_in_collection", False):
            break
            
        start = pagination.get("next_start", start + limit)
    
    return all_products

def check_4_fields():
    """Check which products are missing the 4 required fields"""
    print("🔍 Checking Pipedrive products for 4 required fields...")
    
    products = get_all_products()
    print(f"📊 Total products found: {len(products)}")
    
    # Track missing fields
    missing_catsub = []
    missing_qbo_itemtype = []
    missing_product_service = []
    missing_sync = []
    
    complete_products = 0
    
    for product in products:
        product_id = product.get("id")
        name = product.get("name", "Unknown")
        
        # Check each field
        has_catsub = bool(product.get(CATSUB_FIELD_KEY))
        has_qbo_itemtype = bool(product.get(QBO_ITEMTYPE_FIELD_KEY))
        has_product_service = bool(product.get(PRODUCT_SERVICE_FIELD_KEY))
        has_sync = bool(product.get(SYNC_FIELD_KEY))
        
        # Track missing fields
        if not has_catsub:
            missing_catsub.append(f"ID {product_id}: {name}")
        if not has_qbo_itemtype:
            missing_qbo_itemtype.append(f"ID {product_id}: {name}")
        if not has_product_service:
            missing_product_service.append(f"ID {product_id}: {name}")
        if not has_sync:
            missing_sync.append(f"ID {product_id}: {name}")
        
        # Count complete products
        if has_catsub and has_qbo_itemtype and has_product_service and has_sync:
            complete_products += 1
    
    # Report results
    print(f"\n📈 COMPLETENESS REPORT:")
    print(f"✅ Complete products (all 4 fields): {complete_products}/{len(products)} ({complete_products/len(products)*100:.1f}%)")
    print(f"❌ Missing CatSub: {len(missing_catsub)}")
    print(f"❌ Missing QBO Item Type: {len(missing_qbo_itemtype)}")
    print(f"❌ Missing Product/Service: {len(missing_product_service)}")
    print(f"❌ Missing Sync: {len(missing_sync)}")
    
    # Show details for missing fields
    if missing_catsub:
        print(f"\n🔍 Products missing CatSub ({len(missing_catsub)}):")
        for item in missing_catsub[:10]:  # Show first 10
            print(f"  - {item}")
        if len(missing_catsub) > 10:
            print(f"  ... and {len(missing_catsub) - 10} more")
    
    if missing_qbo_itemtype:
        print(f"\n🔍 Products missing QBO Item Type ({len(missing_qbo_itemtype)}):")
        for item in missing_qbo_itemtype[:10]:
            print(f"  - {item}")
        if len(missing_qbo_itemtype) > 10:
            print(f"  ... and {len(missing_qbo_itemtype) - 10} more")
    
    if missing_product_service:
        print(f"\n🔍 Products missing Product/Service ({len(missing_product_service)}):")
        for item in missing_product_service[:10]:
            print(f"  - {item}")
        if len(missing_product_service) > 10:
            print(f"  ... and {len(missing_product_service) - 10} more")
    
    if missing_sync:
        print(f"\n🔍 Products missing Sync ({len(missing_sync)}):")
        for item in missing_sync[:10]:
            print(f"  - {item}")
        if len(missing_sync) > 10:
            print(f"  ... and {len(missing_sync) - 10} more")
    
    # Recommendation
    total_missing = len(missing_catsub) + len(missing_qbo_itemtype) + len(missing_product_service) + len(missing_sync)
    if total_missing > 0:
        print(f"\n💡 RECOMMENDATION:")
        print(f"   {total_missing} products are missing required fields.")
        print(f"   Consider running the backfill script to fix missing CatSub fields.")
    else:
        print(f"\n✅ ALL PRODUCTS HAVE ALL 4 REQUIRED FIELDS!")
        print(f"   The backfill workflow may not be needed.")

if __name__ == "__main__":
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in environment variables")
        exit(1)
    
    check_4_fields()
