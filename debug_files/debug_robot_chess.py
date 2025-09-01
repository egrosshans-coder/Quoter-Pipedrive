#!/usr/bin/env python3
"""
Debug Robot Chess Update
Update the Robot Chess item (SKU 481) in Pipedrive to debug the price field mapping issue.
"""

import os
import requests
from dotenv import load_dotenv
from quoter import get_quoter_products
from pipedrive import get_category_mapping, get_subcategory_mapping
from utils.logger import logger

load_dotenv()

# Pipedrive configuration
API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

def debug_robot_chess_update():
    """
    Debug updating the Robot Chess item (SKU 481) in Pipedrive.
    """
    print("🔍 DEBUGGING ROBOT CHESS UPDATE (SKU 481)")
    print("=" * 50)
    
    # Get the specific Robot Chess item from Quoter
    print("📡 Fetching Robot Chess item from Quoter...")
    products = get_quoter_products(limit=100)  # Get more to find SKU 481
    
    if not products:
        print("❌ No products found")
        return
    
    # Find the Robot Chess item
    robot_chess = None
    for product in products:
        if product.get('sku') == 481:
            robot_chess = product
            break
    
    if not robot_chess:
        print("❌ Robot Chess item (SKU 481) not found")
        return
    
    print(f"✅ Found Robot Chess: {robot_chess.get('name')}")
    print(f"   SKU: {robot_chess.get('sku')}")
    print(f"   Price: {robot_chess.get('price_decimal')}")
    print(f"   Cost: {robot_chess.get('cost_decimal')}")
    print(f"   Category: {robot_chess.get('category')}")
    
    # Build the Pipedrive payload exactly like the main function does
    print("\n🔧 BUILDING PIPEDRIVE PAYLOAD:")
    print("-" * 40)
    
    pipedrive_product = {
        "name": robot_chess.get("name", "Unknown Product"),
        "code": robot_chess.get("code", ""),
        "description": robot_chess.get("description", ""),
        "unit": "piece",
        "tax": 0,
        "active_flag": True,
        "visible_to": 3
    }
    
    print(f"✅ Basic fields: {list(pipedrive_product.keys())}")
    
    # Add price if available
    if robot_chess.get("price_decimal"):
        pipedrive_product["price"] = float(robot_chess.get("price_decimal", 0))
        print(f"✅ Added price: {pipedrive_product['price']}")
    else:
        print("❌ No price_decimal found")
    
    # Add cost if available
    if robot_chess.get("cost_decimal"):
        pipedrive_product["cost"] = float(robot_chess.get("cost_decimal", 0))
        print(f"✅ Added cost: {pipedrive_product['cost']}")
    else:
        print("❌ No cost_decimal found")
    
    # Add category mapping
    if robot_chess.get("category_id"):
        print(f"🔍 Processing category: {robot_chess.get('category')}")
        
        # For this debug, just use the category name directly
        category_name = robot_chess.get("category")
        if category_name:
            pipedrive_category_id = get_category_mapping(category_name)
            if pipedrive_category_id:
                pipedrive_product["category"] = pipedrive_category_id
                print(f"✅ Mapped category '{category_name}' to Pipedrive ID {pipedrive_category_id}")
            else:
                print(f"❌ No category mapping found for '{category_name}'")
    
    print(f"\n📋 FINAL PAYLOAD:")
    print("-" * 40)
    for key, value in pipedrive_product.items():
        print(f"   {key}: {value}")
    
    # Now try to update the existing product in Pipedrive
    print(f"\n🔄 UPDATING PIPEDRIVE PRODUCT:")
    print("-" * 40)
    
    # The SKU in Quoter is the product ID in Pipedrive
    pipedrive_product_id = robot_chess.get("sku")  # Should be 481
    print(f"   Pipedrive Product ID: {pipedrive_product_id}")
    
    if not pipedrive_product_id:
        print("❌ No SKU found - cannot update")
        return
    
    # Make the update request
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    print(f"   API Endpoint: {BASE_URL}/products/{pipedrive_product_id}")
    print(f"   Request Method: PUT")
    print(f"   Headers: {headers}")
    print(f"   Params: {params}")
    
    try:
        print(f"\n📡 Sending update request...")
        response = requests.put(
            f"{BASE_URL}/products/{pipedrive_product_id}",
            json=pipedrive_product,
            headers=headers,
            params=params,
            timeout=10
        )
        
        print(f"📡 Response received:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"✅ Update successful!")
            
            # Get the updated product to verify the changes
            print(f"\n🔍 VERIFYING UPDATED PRODUCT:")
            print("-" * 40)
            
            get_response = requests.get(
                f"{BASE_URL}/products/{pipedrive_product_id}",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if get_response.status_code == 200:
                updated_data = get_response.json().get("data", {})
                print(f"✅ Retrieved updated product:")
                print(f"   Name: {updated_data.get('name')}")
                print(f"   Code: {updated_data.get('code')}")
                print(f"   Price: {updated_data.get('price')}")
                print(f"   Cost: {updated_data.get('cost')}")
                print(f"   Category: {updated_data.get('category')}")
                
                # Check if price was actually set
                if updated_data.get('price'):
                    print(f"✅ PRICE FIELD SUCCESSFULLY UPDATED: {updated_data.get('price')}")
                else:
                    print(f"❌ PRICE FIELD STILL MISSING after update")
                    
            else:
                print(f"❌ Could not retrieve updated product: {get_response.status_code}")
                
        else:
            print(f"❌ Update failed: {response.status_code}")
            print(f"   Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during update: {e}")

if __name__ == "__main__":
    debug_robot_chess_update()
