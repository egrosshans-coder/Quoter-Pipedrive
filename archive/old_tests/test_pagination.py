#!/usr/bin/env python3
"""
Test script to check pagination for sub-organizations
"""

from pipedrive import get_sub_organizations_ready_for_quotes
from utils.logger import logger
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def debug_pipedrive_response():
    """Debug the actual Pipedrive API response structure"""
    API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
    BASE_URL = "https://api.pipedrive.com/v1"
    
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found")
        return
    
    headers = {"Content-Type": "application/json"}
    params = {
        "api_token": API_TOKEN,
        "limit": 100,
        "start": 0
    }
    
    print("🔍 Debugging Pipedrive API response structure...")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/organizations",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response status: {response.status_code}")
            print(f"📊 Response keys: {list(data.keys())}")
            
            if 'data' in data:
                print(f"📋 Data array length: {len(data['data'])}")
            
            if 'additional_data' in data:
                print(f"🔧 Additional data keys: {list(data['additional_data'].keys())}")
                
                if 'pagination' in data['additional_data']:
                    pagination = data['additional_data']['pagination']
                    print(f"📄 Pagination keys: {list(pagination.keys())}")
                    print(f"📄 Pagination data: {pagination}")
            
            print("\n" + "=" * 60)
            print("🎯 Now testing our function...")
            print("=" * 60)
            
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    # First debug the API response
    debug_pipedrive_response()
    
    print('🧪 Testing pagination for sub-organizations...')
    print('=' * 50)

    # Test the updated function
    ready_orgs = get_sub_organizations_ready_for_quotes()

    print(f'\n🎯 Results:')
    print(f'Found {len(ready_orgs)} organizations ready for quotes')

    if ready_orgs:
        print('\n✅ Organizations ready for quotes:')
        for org in ready_orgs:
            print(f'  • ID: {org.get("id")}')
            print(f'    Name: {org.get("name")}')
            print(f'    Owner: {org.get("owner_id", {}).get("name", "Unknown")}')
            print(f'    Deal ID: {org.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")}')
            print(f'    HID-QBO-Status: {org.get("454a3767bce03a880b31d78a38c480d6870e0f1b")}')
            print()
    else:
        print('\n❌ No organizations found ready for quotes')
        print('This could mean:')
        print('  • No organizations have HID-QBO-Status = 289')
        print('  • No organizations have populated Deal_ID fields')
        print('  • The Pipedrive automation hasn\'t run yet')

if __name__ == "__main__":
    main()
