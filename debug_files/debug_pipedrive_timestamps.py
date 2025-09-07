#!/usr/bin/env python3
"""
Debug Pipedrive timestamp format to fix datetime comparison
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def debug_pipedrive_timestamps():
    """Check Pipedrive timestamp format"""
    pipedrive_token = os.getenv("PIPEDRIVE_API_TOKEN")
    if not pipedrive_token:
        print("❌ No Pipedrive token")
        return
    
    url = "https://api.pipedrive.com/v1/products"
    params = {"api_token": pipedrive_token, "limit": 5}
    
    response = requests.get(url, params=params, timeout=30)
    if response.status_code != 200:
        print(f"❌ Failed to fetch: {response.status_code}")
        return
    
    data = response.json()
    products = data.get("data", [])
    
    print(f"📊 Found {len(products)} products")
    print("=" * 50)
    
    for i, product in enumerate(products[:3]):
        print(f"Product {i+1}:")
        print(f"  Name: {product.get('name', 'N/A')}")
        print(f"  ID: {product.get('id', 'N/A')}")
        print(f"  add_time: {product.get('add_time', 'N/A')}")
        print(f"  update_time: {product.get('update_time', 'N/A')}")
        print(f"  add_time type: {type(product.get('add_time'))}")
        print(f"  update_time type: {type(product.get('update_time'))}")
        print()

if __name__ == "__main__":
    debug_pipedrive_timestamps()
