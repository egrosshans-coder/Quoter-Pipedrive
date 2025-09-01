#!/usr/bin/env python3
"""
Debug Raw Category Reading
Examine the raw API response to see if categories are combined strings like "Hologram / FV".
"""

import requests
import json
from quoter import get_access_token

def debug_raw_category():
    """Debug raw category reading from API."""
    
    print("🔍 DEBUGGING RAW CATEGORY READING")
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
            
            # Examine each item's raw category data
            for i, item in enumerate(items, 1):
                print(f"\n📦 ITEM {i}: {item.get('name', 'N/A')}")
                print("-" * 50)
                
                # Look for the specific item we saw in the screenshot
                if "FV-30 Fan Holographic" in item.get('name', ''):
                    print("🎯 FOUND THE ITEM FROM SCREENSHOT!")
                
                # Raw category field examination
                category = item.get('category')
                category_id = item.get('category_id')
                
                print(f"  Raw category field: '{category}'")
                print(f"  Raw category_id field: '{category_id}'")
                
                # Check if category contains "/" (combined format)
                if category and "/" in str(category):
                    print(f"  🔍 CONTAINS SLASH: '{category}'")
                    parts = str(category).split(" / ")
                    print(f"  📋 Parsed parts: {parts}")
                    if len(parts) == 2:
                        print(f"    Main category: '{parts[0].strip()}'")
                        print(f"    Subcategory: '{parts[1].strip()}'")
                else:
                    print(f"  📋 No slash found - single category: '{category}'")
                
                # Check for any other fields that might contain category info
                print(f"\n  🔍 SEARCHING FOR CATEGORY DATA:")
                
                # Look for any field containing "hologram" or "fv"
                for key, value in item.items():
                    if value and isinstance(value, str):
                        if 'hologram' in value.lower() or 'fv' in value.lower():
                            print(f"    {key}: '{value}'")
                
                # Check if category_id maps to a different structure
                if category_id:
                    print(f"\n  🔍 EXAMINING CATEGORY ID: {category_id}")
                    
                    # Try to get category details from categories endpoint
                    cat_url = f"https://api.quoter.com/v1/categories/{category_id}"
                    cat_response = requests.get(cat_url, headers=headers, timeout=10)
                    
                    if cat_response.status_code == 200:
                        cat_data = cat_response.json()
                        print(f"    Category API response: {json.dumps(cat_data, indent=2)}")
                    else:
                        print(f"    ❌ Category API failed: {cat_response.status_code}")
                
                print("-" * 50)
                
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_raw_category()
