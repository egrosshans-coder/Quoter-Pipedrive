#!/usr/bin/env python3
"""
Script to retrieve all categories from Quoter API with pagination support.
This will get all 118 categories instead of just the first 100.
"""

import requests
import os
from dotenv import load_dotenv
import json

def get_access_token():
    """Get OAuth access token from Quoter API."""
    load_dotenv()
    client_id = os.getenv('QUOTER_API_KEY')
    client_secret = os.getenv('QUOTER_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ CLIENT_ID or CLIENT_SECRET not found in environment variables")
        return None
    
    auth_url = 'https://api.quoter.com/v1/auth/oauth/authorize'
    auth_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    
    try:
        print("🔐 Getting OAuth access token...")
        response = requests.post(auth_url, json=auth_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get('access_token')
            if access_token:
                print("✅ Successfully obtained OAuth access token")
                return access_token
            else:
                print("❌ No access_token in response")
                return None
        else:
            print(f"❌ OAuth authentication failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting OAuth token: {e}")
        return None

def get_all_categories():
    """Retrieve all categories from Quoter API with pagination."""
    access_token = get_access_token()
    if not access_token:
        return []
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    endpoint = 'https://api.quoter.com/v1/categories'
    all_categories = []
    page = 1
    limit = 100  # Maximum items per page
    
    print(f"\n📋 Retrieving all categories from Quoter API...")
    print(f"🔗 Endpoint: {endpoint}")
    print(f"📄 Page size: {limit}")
    
    while True:
        print(f"\n📄 Fetching page {page}...")
        
        params = {
            'limit': limit,
            'page': page
        }
        
        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get('data', [])
                has_more = data.get('has_more', False)
                total_count = data.get('total_count', 0)
                
                print(f"   ✅ Retrieved {len(categories)} categories")
                print(f"   📊 Total so far: {len(all_categories) + len(categories)}/{total_count}")
                print(f"   🔄 Has more pages: {has_more}")
                
                all_categories.extend(categories)
                
                # Check if we've reached the end
                if not has_more or len(categories) < limit:
                    print(f"\n🎯 Reached end of categories")
                    break
                
                page += 1
                
            else:
                print(f"❌ Error on page {page}: {response.status_code} - {response.text}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching page {page}: {e}")
            break
    
    return all_categories

def analyze_categories(categories):
    """Analyze and display category information."""
    if not categories:
        print("❌ No categories to analyze")
        return
    
    print(f"\n📊 CATEGORY ANALYSIS")
    print(f"=" * 50)
    print(f"Total Categories: {len(categories)}")
    
    # Count top-level categories (no parent)
    top_level = [cat for cat in categories if not cat.get('parent_category_id')]
    print(f"Top-level Categories: {len(top_level)}")
    
    # Count subcategories (with parent)
    subcategories = [cat for cat in categories if cat.get('parent_category_id')]
    print(f"Subcategories: {len(subcategories)}")
    
    # Group by parent category
    parent_groups = {}
    for cat in categories:
        parent = cat.get('parent_category', 'No Parent')
        if parent not in parent_groups:
            parent_groups[parent] = []
        parent_groups[parent].append(cat)
    
    print(f"\n🏗️  CATEGORY HIERARCHY")
    print(f"=" * 50)
    
    # Display top-level categories first
    for cat in top_level:
        print(f"\n📁 {cat['name']} (ID: {cat['id']})")
        parent_name = cat['name']
        if parent_name in parent_groups:
            for subcat in parent_groups[parent_name]:
                print(f"   └── {subcat['name']} (ID: {subcat['id']})")
    
    # Display categories with no subcategories
    for cat in top_level:
        if cat['name'] not in parent_groups:
            print(f"\n📁 {cat['name']} (ID: {cat['id']}) - No subcategories")

def save_categories_to_file(categories, filename='quoter_categories.json'):
    """Save categories to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(categories, f, indent=2)
        print(f"\n💾 Categories saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving to file: {e}")

def main():
    """Main function to retrieve and analyze all categories."""
    print("🚀 QUOTER CATEGORY RETRIEVAL WITH PAGINATION")
    print("=" * 60)
    
    # Get all categories
    categories = get_all_categories()
    
    if categories:
        print(f"\n✅ Successfully retrieved {len(categories)} categories!")
        
        # Analyze categories
        analyze_categories(categories)
        
        # Save to file
        save_categories_to_file(categories)
        
        # Display first few categories as sample
        print(f"\n📋 SAMPLE CATEGORIES (first 10):")
        print(f"=" * 50)
        for i, cat in enumerate(categories[:10]):
            parent_info = f" → {cat['parent_category']}" if cat.get('parent_category') else ""
            print(f"{i+1:2d}. {cat['name']}{parent_info}")
            print(f"     ID: {cat['id']}")
        
        if len(categories) > 10:
            print(f"\n... and {len(categories) - 10} more categories")
            
    else:
        print("❌ Failed to retrieve categories")

if __name__ == "__main__":
    main()
