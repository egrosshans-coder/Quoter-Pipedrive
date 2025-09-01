#!/usr/bin/env python3
"""
Fetch Items Debug
Fetch 5 items from Quoter API and examine the category field structure.
"""

import requests
import json
from quoter import get_access_token

def fetch_items_debug():
    """Fetch 5 items and examine category fields."""
    
    print("🔍 FETCHING 5 ITEMS FROM QUOTER API")
    print("=" * 50)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Fetch items from Quoter API
        url = "https://api.quoter.com/v1/items"
        params = {"limit": 5, "offset": 0}
        
        print("📡 Making API request to Quoter...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])
            
            print(f"✅ Retrieved {len(items)} items from API")
            print(f"📊 Total available: {data.get('total', 'Unknown')}")
            
            # Examine each item's category field
            for i, item in enumerate(items, 1):
                print(f"\n📦 ITEM {i}:")
                print("-" * 30)
                
                # Basic item info
                print(f"  Name: {item.get('name', 'N/A')}")
                print(f"  SKU: {item.get('sku', 'N/A')}")
                print(f"  Code: {item.get('code', 'N/A')}")
                
                # Category fields - examine ALL category-related fields
                print(f"\n  🔍 CATEGORY FIELDS:")
                print(f"    category: {item.get('category', 'N/A')}")
                print(f"    category_id: {item.get('category_id', 'N/A')}")
                
                # Look for any other category-related fields
                category_fields = {k: v for k, v in item.items() if 'categor' in k.lower()}
                if category_fields:
                    print(f"    Other category fields: {category_fields}")
                
                # Look for subcategory fields
                subcategory_fields = {k: v for k, v in item.items() if 'subcategor' in k.lower()}
                if subcategory_fields:
                    print(f"    Subcategory fields: {subcategory_fields}")
                
                # Show all fields for debugging
                print(f"\n  📋 ALL FIELDS:")
                for key, value in item.items():
                    if key not in ['name', 'sku', 'code', 'category', 'category_id']:
                        print(f"    {key}: {value}")
                
                print("-" * 50)
                
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fetch_items_debug()
