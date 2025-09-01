#!/usr/bin/env python3
"""
Get Pipedrive Categories - Direct API Call
Fetches only the main categories from Pipedrive, no subcategories or local mappings.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_pipedrive_categories():
    """Get categories directly from Pipedrive API."""
    
    # Get API token from environment
    api_token = os.getenv('PIPEDRIVE_API_TOKEN')
    if not api_token:
        print("❌ PIPEDRIVE_API_TOKEN not found in .env file")
        return
    
    # Pipedrive API endpoint for product fields
    url = f"https://api.pipedrive.com/v1/productFields?api_token={api_token}"
    
    try:
        print("🔍 Fetching categories from Pipedrive API...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Find the category field
            category_field = None
            for field in data.get('data', []):
                if field.get('name') == 'Category':
                    category_field = field
                    break
            
            if category_field and 'options' in category_field:
                print(f"\n📋 PIPEDRIVE CATEGORIES (Total: {len(category_field['options'])})")
                print("=" * 50)
                
                # Sort categories alphabetically
                categories = sorted(category_field['options'], key=lambda x: x.get('label', ''))
                
                for i, option in enumerate(categories, 1):
                    option_id = option.get('id', 'N/A')
                    option_label = option.get('label', 'Unknown')
                    print(f"{i:2d}. {option_label} (ID: {option_id})")
                
                print("=" * 50)
                print(f"✅ Retrieved {len(categories)} categories from Pipedrive")
                
            else:
                print("❌ Category field not found in Pipedrive")
                
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_pipedrive_categories()
