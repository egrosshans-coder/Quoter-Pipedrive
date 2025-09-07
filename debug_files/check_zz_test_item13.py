#!/usr/bin/env python3
"""
Check if zz-test item13 exists in all three systems
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_quoter():
    """Check if zz-test item13 exists in Quoter"""
    print("🔍 Checking Quoter...")
    try:
        from quoter import get_quoter_products
        products = get_quoter_products()
        
        found = False
        for product in products:
            if "zz-test item13" in product.get("name", "").lower():
                print(f"✅ Found in Quoter:")
                print(f"   Name: {product.get('name')}")
                print(f"   Code: {product.get('code')}")
                print(f"   Price: {product.get('price')}")
                print(f"   Category: {product.get('category')}")
                print(f"   Created: {product.get('created_at')}")
                print(f"   Updated: {product.get('updated_at')}")
                found = True
                break
        
        if not found:
            print("❌ Not found in Quoter")
            
    except Exception as e:
        print(f"❌ Error checking Quoter: {e}")

def check_pipedrive():
    """Check if zz-test item13 exists in Pipedrive"""
    print("\n🔍 Checking Pipedrive...")
    try:
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
        
        found = False
        for product in products:
            if "zz-test item13" in product.get("name", "").lower():
                print(f"✅ Found in Pipedrive:")
                print(f"   Name: {product.get('name')}")
                print(f"   ID: {product.get('id')}")
                print(f"   Code: {product.get('code')}")
                print(f"   Price: {product.get('price')}")
                print(f"   Category: {product.get('category')}")
                print(f"   Added: {product.get('add_time')}")
                print(f"   Updated: {product.get('update_time')}")
                
                # Check custom fields
                custom_fields = product.get("custom_fields", [])
                for field in custom_fields:
                    if field.get("name") == "Subcategory":
                        print(f"   Subcategory: {field.get('value')}")
                    elif field.get("name") == "QBO-Category:Subcategory":
                        print(f"   QBO-Category:Subcategory: {field.get('value')}")
                
                found = True
                break
        
        if not found:
            print("❌ Not found in Pipedrive")
            
    except Exception as e:
        print(f"❌ Error checking Pipedrive: {e}")

def check_qbo():
    """Check if zz-test item13 exists in QuickBooks"""
    print("\n🔍 Checking QuickBooks...")
    try:
        # This would need proper QBO OAuth implementation
        print("⚠️ QBO checking not implemented yet")
        print("❌ Cannot check QuickBooks without OAuth setup")
        
    except Exception as e:
        print(f"❌ Error checking QBO: {e}")

def main():
    print("🔍 Searching for 'zz-test item13' in all three systems...")
    print("=" * 60)
    
    check_quoter()
    check_pipedrive()
    check_qbo()
    
    print("\n" + "=" * 60)
    print("✅ Search completed")

if __name__ == "__main__":
    main()
