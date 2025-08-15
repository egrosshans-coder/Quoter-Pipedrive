#!/usr/bin/env python3
"""
Debug script to examine specific organizations and see why they're not ready for quotes.
"""

from pipedrive import get_sub_organizations_ready_for_quotes
from utils.logger import logger
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def examine_organization(org_id):
    """Examine a specific organization to see its fields and status"""
    API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
    BASE_URL = "https://api.pipedrive.com/v1"
    
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found")
        return
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(
            f"{BASE_URL}/organizations/{org_id}",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            org = data.get("data", {})
            
            print(f"\n🔍 Organization Details for ID: {org_id}")
            print("=" * 60)
            print(f"Name: {org.get('name', 'N/A')}")
            print(f"Owner: {org.get('owner_id', {}).get('name', 'N/A')}")
            
            # Check the key fields we need
            print(f"\n📋 Key Fields:")
            print(f"  HID-QBO-Status (454a3767bce03a880b31d78a38c480d6870e0f1b): {org.get('454a3767bce03a880b31d78a38c480d6870e0f1b', 'NOT SET')}")
            print(f"  Deal_ID (15034cf07d05ceb15f0a89dcbdcc4f596348584e): {org.get('15034cf07d05ceb15f0a89dcbdcc4f596348584e', 'NOT SET')}")
            print(f"  Parent_Org_ID (6b4253304d94302a6f387ce6bde138a6dad48026): {org.get('6b4253304d94302a6f387ce6bde138a6dad48026', 'NOT SET')}")
            
            # Check if it's a sub-organization by name pattern
            org_name = org.get('name', '')
            if '-' in org_name and org_name.split('-')[-1].isdigit():
                print(f"  📝 Name pattern: SUB-ORGANIZATION (matches 'parent-####' format)")
            else:
                print(f"  📝 Name pattern: REGULAR ORGANIZATION")
            
            # Show all custom fields
            print(f"\n🔧 All Custom Fields:")
            for key, value in org.items():
                if key.startswith('4') or key.startswith('6') or key.startswith('1'):  # Custom field IDs
                    print(f"  {key}: {value}")
            
            # Check if it meets our criteria
            print(f"\n✅ Quote Readiness Check:")
            has_status = org.get('454a3767bce03a880b31d78a38c480d6870e0f1b') == 289
            has_deal_id = org.get('15034cf07d05ceb15f0a89dcbdcc4f596348584e')
            
            print(f"  HID-QBO-Status = 289 (QBO-SubCust): {'✅ YES' if has_status else '❌ NO'}")
            print(f"  Has Deal_ID: {'✅ YES' if has_deal_id else '❌ NO'}")
            print(f"  Ready for quotes: {'✅ YES' if (has_status and has_deal_id) else '❌ NO'}")
            
            # Debug the actual values
            print(f"\n🔍 Debug Values:")
            status_value = org.get('454a3767bce03a880b31d78a38c480d6870e0f1b')
            deal_id_value = org.get('15034cf07d05ceb15f0a89dcbdcc4f596348584e')
            print(f"  HID-QBO-Status value: {status_value} (type: {type(status_value)})")
            print(f"  Deal_ID value: {deal_id_value} (type: {type(deal_id_value)})")
            print(f"  Comparison: {status_value} == 289 = {status_value == 289}")
            
        else:
            print(f"❌ Failed to get organization {org_id}: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def examine_sample_organizations():
    """Examine a few sample organizations to understand the data"""
    API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
    BASE_URL = "https://api.pipedrive.com/v1"
    
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found")
        return
    
    headers = {"Content-Type": "application/json"}
    params = {
        "api_token": API_TOKEN,
        "limit": 5  # Just get 5 organizations to examine
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/organizations",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            organizations = data.get("data", [])
            
            print(f"🔍 Examining {len(organizations)} sample organizations...")
            print("=" * 60)
            
            for i, org in enumerate(organizations, 1):
                org_id = org.get('id')
                org_name = org.get('name', 'N/A')
                print(f"\n{i}. Organization ID: {org_id}, Name: {org_name}")
                examine_organization(org_id)
                
        else:
            print(f"❌ Failed to get organizations: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🔍 Organization Debug Tool")
    print("=" * 60)
    
    # Option 1: Examine specific organization by ID
    org_id = input("Enter organization ID to examine (or press Enter to examine sample organizations): ").strip()
    
    if org_id:
        examine_organization(org_id)
    else:
        # Option 2: Examine sample organizations
        examine_sample_organizations()

if __name__ == "__main__":
    main()
