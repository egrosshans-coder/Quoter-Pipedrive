#!/usr/bin/env python3
"""
Find orphaned items in Quoter that no longer have matches in Pipedrive.

This script identifies items that exist in Quoter but don't have corresponding
products in Pipedrive (likely duplicates that were removed from Pipedrive).
"""

import os
import requests
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

# API Configuration
PIPEDRIVE_API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
CLIENT_ID = os.getenv("QUOTER_API_KEY")
CLIENT_SECRET = os.getenv("QUOTER_CLIENT_SECRET")

def get_access_token():
    """Get OAuth access token from Quoter API."""
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.error("CLIENT_ID or CLIENT_SECRET not found in environment variables")
        return None
    
    auth_url = "https://api.quoter.com/v1/auth/oauth/authorize"
    auth_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    
    try:
        logger.info("Getting OAuth access token from Quoter...")
        response = requests.post(auth_url, json=auth_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            if access_token:
                logger.info("✅ Successfully obtained OAuth access token")
                return access_token
            else:
                logger.error("❌ No access_token in response")
                return None
        else:
            logger.error(f"❌ OAuth authentication failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error getting OAuth token: {e}")
        return None

def get_pipedrive_products():
    """Fetch all products from Pipedrive."""
    if not PIPEDRIVE_API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return []
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": PIPEDRIVE_API_TOKEN}
    
    try:
        all_products = []
        page = 1
        limit = 100
        
        while True:
            params.update({
                "limit": limit,
                "start": (page - 1) * limit
            })
            
            logger.info(f"Fetching Pipedrive products page {page}")
            
            response = requests.get(
                f"https://tlciscreative.pipedrive.com/v1/products",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", [])
                
                if not products:
                    break
                    
                all_products.extend(products)
                logger.info(f"Retrieved {len(products)} products (page {page})")
                page += 1
            else:
                logger.error(f"Error fetching Pipedrive products: {response.status_code}")
                break
                
        logger.info(f"Total Pipedrive products retrieved: {len(all_products)}")
        return all_products
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Pipedrive API: {e}")
        return []

def get_quoter_items():
    """Fetch all items from Quoter."""
    access_token = get_access_token()
    if not access_token:
        return []
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        all_items = []
        page = 1
        limit = 100
        
        while True:
            params = {
                "limit": limit,
                "page": page
            }
            
            logger.info(f"Fetching Quoter items page {page}")
            
            response = requests.get(
                "https://api.quoter.com/v1/items",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                
                if not items:
                    break
                    
                all_items.extend(items)
                logger.info(f"Retrieved {len(items)} items (page {page})")
                page += 1
            else:
                logger.error(f"Error fetching Quoter items: {response.status_code}")
                break
                
        logger.info(f"Total Quoter items retrieved: {len(all_items)}")
        return all_items
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Quoter API: {e}")
        return []

def find_orphaned_items():
    """Find items in Quoter that don't have matches in Pipedrive."""
    logger.info("🔍 Finding orphaned Quoter items...")
    
    # Get data from both systems
    pipedrive_products = get_pipedrive_products()
    quoter_items = get_quoter_items()
    
    if not pipedrive_products or not quoter_items:
        logger.error("❌ Failed to fetch data from one or both systems")
        return
    
    # Create lookup set of Pipedrive product codes
    pipedrive_codes = set()
    for product in pipedrive_products:
        code = product.get("code")
        if code and code.strip():
            pipedrive_codes.add(code.strip())
    
    logger.info(f"Created Pipedrive codes lookup with {len(pipedrive_codes)} codes")
    
    # Find orphaned items in Quoter
    orphaned_items = []
    for item in quoter_items:
        code = item.get("code")
        if code and code.strip():
            code = code.strip()
            if code not in pipedrive_codes:
                orphaned_items.append(item)
    
    logger.info(f"Found {len(orphaned_items)} orphaned items in Quoter")
    
    # Display orphaned items
    if orphaned_items:
        print("\n" + "="*80)
        print("🚨 ORPHANED ITEMS IN QUOTER (No match in Pipedrive)")
        print("="*80)
        
        for i, item in enumerate(orphaned_items, 1):
            item_id = item.get("id", "Unknown ID")
            name = item.get("name", "Unknown Name")
            code = item.get("code", "No Code")
            category = item.get("category", {})
            if isinstance(category, dict):
                category_name = category.get("name", "No Category")
            else:
                category_name = str(category) if category else "No Category"
            
            print(f"\n{i}. {name}")
            print(f"   ID: {item_id}")
            print(f"   Code: {code}")
            print(f"   Category: {category_name}")
            print(f"   Status: {'Active' if item.get('active', True) else 'Inactive'}")
            
            # Show additional details if available
            if item.get("description"):
                desc = item.get("description", "")[:100]
                print(f"   Description: {desc}{'...' if len(item.get('description', '')) > 100 else ''}")
            
            if item.get("price"):
                print(f"   Price: ${item.get('price', 0):.2f}")
        
        print("\n" + "="*80)
        print(f"📊 SUMMARY: {len(orphaned_items)} orphaned items found")
        print("="*80)
        
        # Save to file for reference
        with open("orphaned_quoter_items.txt", "w") as f:
            f.write("ORPHANED ITEMS IN QUOTER (No match in Pipedrive)\n")
            f.write("="*60 + "\n\n")
            
            for i, item in enumerate(orphaned_items, 1):
                f.write(f"{i}. {item.get('name', 'Unknown Name')}\n")
                f.write(f"   ID: {item.get('id', 'Unknown ID')}\n")
                f.write(f"   Code: {item.get('code', 'No Code')}\n")
                category = item.get('category', {})
                if isinstance(category, dict):
                    category_name = category.get('name', 'No Category')
                else:
                    category_name = str(category) if category else 'No Category'
                f.write(f"   Category: {category_name}\n")
                f.write(f"   Status: {'Active' if item.get('active', True) else 'Inactive'}\n")
                if item.get("description"):
                    f.write(f"   Description: {item.get('description', '')}\n")
                if item.get("price"):
                    f.write(f"   Price: ${item.get('price', 0):.2f}\n")
                f.write("\n")
        
        print(f"💾 Details saved to: orphaned_quoter_items.txt")
        
    else:
        print("\n✅ No orphaned items found! All Quoter items have matches in Pipedrive.")

if __name__ == "__main__":
    find_orphaned_items()
