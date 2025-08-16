#!/usr/bin/env python3
"""
Test script to retrieve a deal's current name from Pipedrive.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Pipedrive configuration
API_TOKEN = os.getenv('PIPEDRIVE_API_TOKEN')
BASE_URL = "https://api.pipedrive.com/v1"

def get_deal_name(deal_id):
    """
    Retrieve a deal's current name from Pipedrive.
    
    Args:
        deal_id (str): Deal ID (e.g., "2096")
        
    Returns:
        str: Deal name if found, None otherwise
    """
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    try:
        deal_id_int = int(deal_id)
        
        headers = {"Content-Type": "application/json"}
        params = {"api_token": API_TOKEN}
        
        print(f"🔍 Retrieving deal {deal_id_int} from Pipedrive...")
        
        response = requests.get(
            f"{BASE_URL}/deals/{deal_id_int}",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            deal_data = data.get("data", {})
            
            if deal_data:
                deal_name = deal_data.get("title", "No title")
                deal_value = deal_data.get("value", "No value")
                deal_status = deal_data.get("status", "No status")
                
                print(f"✅ Deal {deal_id_int} found:")
                print(f"   Name: {deal_name}")
                print(f"   Value: ${deal_value}")
                print(f"   Status: {deal_status}")
                
                return deal_name
            else:
                print(f"❌ No deal data found for ID {deal_id_int}")
                return None
                
        elif response.status_code == 404:
            print(f"❌ Deal {deal_id_int} not found")
            return None
        else:
            print(f"❌ Error getting deal {deal_id_int}: {response.status_code} - {response.text}")
            return None
            
    except ValueError as e:
        print(f"❌ Invalid deal ID format: {deal_id} - {e}")
        return None
    except Exception as e:
        print(f"❌ Error retrieving deal {deal_id}: {e}")
        return None

if __name__ == "__main__":
    # Test with deal ID 2096
    deal_id = "2096"
    print(f"🧪 Testing deal name retrieval for deal {deal_id}")
    print("=" * 50)
    
    deal_name = get_deal_name(deal_id)
    
    if deal_name:
        print(f"\n🎯 Original deal name: '{deal_name}'")
        print("This name will be preserved when updating the deal.")
    else:
        print(f"\n❌ Could not retrieve deal name for {deal_id}")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
