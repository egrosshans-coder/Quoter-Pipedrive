#!/usr/bin/env python3
"""
Debug Quoter Categories
Make direct API calls to examine the actual category structure and check for errors.
"""

import requests
from quoter import get_access_token

def debug_quoter_categories():
    """Debug Quoter category structure directly."""
    
    print("🔍 DEBUGGING QUOTER CATEGORIES")
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
    
    # Test 1: Get all categories
    print("\n📋 TEST 1: Get All Categories")
    print("-" * 30)
    
    try:
        url = "https://api.quoter.com/v1/categories"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            categories = data.get('data', [])
            print(f"✅ Retrieved {len(categories)} categories")
            
            # Show first few categories with their structure
            for i, cat in enumerate(categories[:5]):
                print(f"\nCategory {i+1}:")
                print(f"  ID: {cat.get('id')}")
                print(f"  Name: {cat.get('name')}")
                print(f"  Parent ID: {cat.get('parent_id')}")
                print(f"  Has Parent: {'Yes' if cat.get('parent_id') else 'No'}")
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Examine specific category IDs from our sync
    print("\n📋 TEST 2: Examine Specific Categories")
    print("-" * 30)
    
    test_categories = [
        'cat_30TrYJTJbanER6ieH156VNnwIiH',  # 40Watt
        'cat_30LNfhXf8MdwLYlqsvoBNDGfPNV',  # 1-to-3 Splitter
        'cat_30LNfiSTr07Irp5zsWDYHhMv5Rx',  # Controller-Xylo
        'cat_30LNfo0NKrVSVacvryFJm1j3FSg',  # Controller-TLC
        'cat_30LNflAUVPZ0yqrw2Tb60lLVtMr'   # GlowBalls
    ]
    
    for cat_id in test_categories:
        print(f"\n🔍 Examining: {cat_id}")
        try:
            url = f"https://api.quoter.com/v1/categories/{cat_id}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                cat_data = response.json()
                print(f"  Name: {cat_data.get('name')}")
                print(f"  Parent ID: {cat_data.get('parent_id')}")
                print(f"  Has Parent: {'Yes' if cat_data.get('parent_id') else 'No'}")
                
                # If it has a parent, get parent details
                if cat_data.get('parent_id'):
                    parent_response = requests.get(
                        f"https://api.quoter.com/v1/categories/{cat_data['parent_id']}", 
                        headers=headers, 
                        timeout=10
                    )
                    if parent_response.status_code == 200:
                        parent_data = parent_response.json()
                        print(f"  Parent Name: {parent_data.get('name')}")
                        print(f"  Full Path: {parent_data.get('name')} / {cat_data.get('name')}")
                    else:
                        print(f"  ❌ Could not get parent details: {parent_response.status_code}")
                else:
                    print(f"  Full Path: {cat_data.get('name')} (main category)")
            else:
                print(f"  ❌ API request failed: {response.status_code}")
                print(f"  Response: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Test 3: Check for any API errors or issues
    print("\n📋 TEST 3: Check for API Issues")
    print("-" * 30)
    
    try:
        # Try to get categories with different parameters
        url = "https://api.quoter.com/v1/categories"
        params = {"limit": 100, "offset": 0}
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            print(f"✅ Total categories available: {total}")
            
            # Check for any error fields in response
            if 'errors' in data:
                print(f"⚠️  API returned errors: {data['errors']}")
            if 'warnings' in data:
                print(f"⚠️  API returned warnings: {data['warnings']}")
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_quoter_categories()
