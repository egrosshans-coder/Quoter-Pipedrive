#!/usr/bin/env python3
"""
Debug what products are being detected as "new"
"""

import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def debug_new_products():
    """Show exactly what products are detected as new"""
    
    # Get last sync date
    try:
        with open("last_sync_date.txt", "r") as f:
            last_sync_str = f.read().strip()
            last_sync_date = datetime.fromisoformat(last_sync_str.replace('Z', '+00:00'))
            print(f"📅 Last sync date: {last_sync_date}")
    except Exception as e:
        print(f"❌ Error reading last sync date: {e}")
        return
    
    # Get Pipedrive products
    pipedrive_token = os.getenv("PIPEDRIVE_API_TOKEN")
    if not pipedrive_token:
        print("❌ No Pipedrive token")
        return
    
    url = "https://api.pipedrive.com/v1/products"
    params = {"api_token": pipedrive_token, "limit": 100}
    
    response = requests.get(url, params=params, timeout=30)
    if response.status_code != 200:
        print(f"❌ Failed to fetch: {response.status_code}")
        return
    
    data = response.json()
    products = data.get("data", [])
    
    print(f"📊 Checking {len(products)} Pipedrive products...")
    print("=" * 60)
    
    new_products = []
    
    for product in products:
        add_time = product.get("add_time")
        update_time = product.get("update_time")
        
        is_new = False
        reason = ""
        
        if add_time:
            product_added = datetime.strptime(add_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            if product_added >= last_sync_date:
                is_new = True
                reason = f"Added: {add_time}"
        
        if update_time and not is_new:
            product_updated = datetime.strptime(update_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            if product_updated >= last_sync_date:
                is_new = True
                reason = f"Updated: {update_time}"
        
        if is_new:
            new_products.append({
                'product': product,
                'reason': reason
            })
            print(f"🆕 NEW: {product.get('name', 'Unknown')} (ID: {product.get('id')})")
            print(f"   Reason: {reason}")
            print(f"   Last sync: {last_sync_date}")
            print()
    
    print(f"📊 Total new products found: {len(new_products)}")
    
    if len(new_products) == 0:
        print("✅ No products were created or updated since last sync")
    else:
        print(f"❌ Found {len(new_products)} products that appear to be 'new'")

if __name__ == "__main__":
    debug_new_products()
