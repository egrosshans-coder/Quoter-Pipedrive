#!/usr/bin/env python3
"""
Get enum options for the Quote Template field in Pipedrive.
This will show us the numeric values and their corresponding text labels.
"""

import requests
import json
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipedrive import API_TOKEN, BASE_URL
from utils.logger import logger

def get_enum_options(field_id):
    """
    Get enum options for a specific field in Pipedrive.
    
    Args:
        field_id (str): The field ID to get options for
        
    Returns:
        dict: Enum options mapping
    """
    print(f"🔍 Getting enum options for field ID: {field_id}")
    print("=" * 60)
    
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    try:
        # Get field details including enum options
        url = f"{BASE_URL}/dealFields/{field_id}"
        params = {"api_token": API_TOKEN}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            field_data = data.get("data", {})
            
            print(f"📋 Field Name: {field_data.get('name', 'Unknown')}")
            print(f"📋 Field Type: {field_data.get('field_type', 'Unknown')}")
            print(f"📋 Field Key: {field_data.get('key', 'Unknown')}")
            print()
            
            # Get enum options
            options = field_data.get("options", [])
            if options:
                print(f"🎯 ENUM OPTIONS ({len(options)} found):")
                print()
                
                enum_mapping = {}
                for option in options:
                    option_id = option.get("id")
                    option_label = option.get("label", "Unknown")
                    enum_mapping[option_id] = option_label
                    
                    print(f"   {option_id}: {option_label}")
                
                print()
                print("📝 ENUM MAPPING (for code):")
                print("enum_mapping = {")
                for option_id, option_label in enum_mapping.items():
                    print(f"    {option_id}: '{option_label}',")
                print("}")
                
                return enum_mapping
            else:
                print("❌ No enum options found for this field")
                return None
                
        else:
            print(f"❌ Failed to fetch field details: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting enum options: {e}")
        return None

def main():
    """
    Main function to get Quote Template enum options.
    """
    # Quote Template field ID
    field_id = "90"
    
    try:
        enum_mapping = get_enum_options(field_id)
        if enum_mapping:
            print(f"\n🎉 Successfully retrieved {len(enum_mapping)} enum options!")
            print("Use these mappings in your template selection logic.")
        else:
            print(f"\n⚠️  Failed to retrieve enum options.")
    except Exception as e:
        print(f"❌ Script failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
