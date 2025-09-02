#!/usr/bin/env python3
"""
Find the Pipedrive item that doesn't have a match in Quoter.

This will identify which item exists in Pipedrive but is missing from Quoter.
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

def find_missing_item():
    """Find the Pipedrive item that doesn't have a match in Quoter."""
    logger.info("🔍 Finding missing Quoter item...")
    
    # Get data from both systems
    pipedrive_products = get_pipedrive_products()
    quoter_items = get_quoter_items()
    
    if not pipedrive_products or not quoter_items:
        logger.error("❌ Failed to fetch data from one or both systems")
        return
    
    # Create lookup set of Quoter codes
    quoter_codes = set()
    for item in quoter_items:
        code = item.get("code")
        if code and code.strip():
            quoter_codes.add(code.strip())
    
    logger.info(f"Created Quoter codes lookup with {len(quoter_codes)} codes")
    
    # Find missing items in Pipedrive
    missing_items = []
    for product in pipedrive_products:
        code = product.get("code")
        if code and code.strip():
            code = code.strip()
            if code not in quoter_codes:
                missing_items.append(product)
    
    logger.info(f"Found {len(missing_items)} Pipedrive items missing from Quoter")
    
    # Display missing items
    if missing_items:
        print("\n" + "="*80)
        print("🚨 PIPEDRIVE ITEMS MISSING FROM QUOTER")
        print("="*80)
        
        for i, product in enumerate(missing_items, 1):
            product_id = product.get("id", "Unknown ID")
            name = product.get("name", "Unknown Name")
            code = product.get("code", "No Code")
            category = product.get("category", "No Category")
            active = product.get("active_flag", False)
            
            print(f"\n{i}. {name}")
            print(f"   ID: {product_id}")
            print(f"   Code: {code}")
            print(f"   Category: {category}")
            print(f"   Active: {active}")
            
            # Show additional details if available
            if product.get("description"):
                desc = product.get("description", "")[:100]
                print(f"   Description: {desc}{'...' if len(product.get('description', '')) > 100 else ''}")
            
            if product.get("prices"):
                price_data = product.get("prices", [{}])[0]
                if price_data.get("price"):
                    print(f"   Price: ${price_data.get('price', 0)/100:.2f}")
        
        print("\n" + "="*80)
        print(f"📊 SUMMARY: {len(missing_items)} Pipedrive items missing from Quoter")
        print("="*80)
        
    else:
        print("\n✅ No missing items found! All Pipedrive items have matches in Quoter.")

if __name__ == "__main__":
    find_missing_item()
