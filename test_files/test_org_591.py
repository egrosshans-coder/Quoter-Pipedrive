#!/usr/bin/env python3
"""
Quick test to retrieve organization data from Pipedrive for organization ID 591
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

def test_org_591():
    """Test retrieving organization 591 data from Pipedrive"""
    
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in environment variables")
        return
    
    org_id = 591
    
    print(f"🧪 Testing Pipedrive API for Organization ID: {org_id}")
    print("=" * 60)
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        print(f"📡 Fetching organization data from Pipedrive...")
        response = requests.get(
            f"{BASE_URL}/organizations/{org_id}",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            org_data = data.get("data")
            
            if org_data:
                print(f"✅ Got organization data:")
                print(f"   Name: {org_data.get('name', 'Unknown')}")
                print(f"   ID: {org_data.get('id')}")
                
                print(f"\n🔍 Available keys:")
                print(f"   {list(org_data.keys())}")
                
                # Check for address-related fields
                address_fields = [key for key in org_data.keys() if 'address' in key.lower()]
                if address_fields:
                    print(f"\n🏠 Address-related fields:")
                    for field in address_fields:
                        value = org_data.get(field)
                        print(f"   {field}: {value}")
                else:
                    print(f"\n❌ No address-related fields found")
                
                # Check for city, state, zip fields
                location_fields = [key for key in org_data.keys() if any(loc in key.lower() for loc in ['city', 'state', 'zip', 'postal', 'locality', 'admin'])]
                if location_fields:
                    print(f"\n📍 Location-related fields:")
                    for field in location_fields:
                        value = org_data.get(field)
                        print(f"   {field}: {value}")
                else:
                    print(f"\n❌ No location-related fields found")
                
                # Show specific fields we're mapping
                print(f"\n🎯 Fields we're mapping in our code:")
                mapping_fields = [
                    'address', 'address_subpremise', 'address_street_number', 
                    'address_route', 'address_locality', 'address_admin_area_level_1',
                    'address_postal_code', 'address_country'
                ]
                
                for field in mapping_fields:
                    value = org_data.get(field)
                    if value:
                        print(f"   ✅ {field}: {value}")
                    else:
                        print(f"   ❌ {field}: NOT SET")
                        
            else:
                print(f"❌ No organization data found")
                
        elif response.status_code == 404:
            print(f"❌ Organization {org_id} not found")
        else:
            print(f"❌ Error getting organization {org_id}: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting organization {org_id}: {e}")

if __name__ == "__main__":
    test_org_591()
