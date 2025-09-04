#!/usr/bin/env python3
"""
Find the custom field ID for the "Quote Template" field in Pipedrive Deal's "Quoter" section.
This script searches through all deal custom fields to locate the field.
"""

import requests
import json
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipedrive import API_TOKEN, BASE_URL
from utils.logger import logger

def find_quoter_template_field():
    """
    Find the custom field ID for the "Quote Template" field.
    """
    print("🔍 Searching for 'Quote Template' custom field in Pipedrive...")
    print("=" * 60)
    
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    try:
        # Get all deal custom fields
        url = f"{BASE_URL}/dealFields"
        params = {"api_token": API_TOKEN}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            fields = data.get("data", [])
            
            print(f"📋 Found {len(fields)} deal custom fields")
            print()
            
            # Search for fields related to "Quoter" or "Quote Template"
            quoter_fields = []
            template_fields = []
            
            for field in fields:
                field_name = field.get("name", "")
                field_key = field.get("key", "")
                field_id = field.get("id", "")
                field_type = field.get("field_type", "")
                
                # Look for Quoter-related fields
                if "quoter" in field_name.lower() or "quoter" in field_key.lower():
                    quoter_fields.append({
                        "id": field_id,
                        "name": field_name,
                        "key": field_key,
                        "type": field_type
                    })
                
                # Look for Template-related fields
                if "template" in field_name.lower() or "template" in field_key.lower():
                    template_fields.append({
                        "id": field_id,
                        "name": field_name,
                        "key": field_key,
                        "type": field_type
                    })
                
                # Show all fields for debugging
                print(f"📋 Field: {field_name}")
                print(f"   ID: {field_id}")
                print(f"   Key: {field_key}")
                print(f"   Type: {field_type}")
                print()
            
            # Report findings
            print("=" * 60)
            print("🎯 QUOTER-RELATED FIELDS:")
            if quoter_fields:
                for field in quoter_fields:
                    print(f"   ✅ {field['name']} (ID: {field['id']}, Key: {field['key']})")
            else:
                print("   ❌ No Quoter-related fields found")
            
            print()
            print("🎯 TEMPLATE-RELATED FIELDS:")
            if template_fields:
                for field in template_fields:
                    print(f"   ✅ {field['name']} (ID: {field['id']}, Key: {field['key']})")
            else:
                print("   ❌ No Template-related fields found")
            
            # If we found the Quote Template field, return its details
            for field in template_fields:
                if "quote template" in field['name'].lower():
                    print()
                    print("🎉 FOUND QUOTE TEMPLATE FIELD!")
                    print(f"   Field Name: {field['name']}")
                    print(f"   Field ID: {field['id']}")
                    print(f"   Field Key: {field['key']}")
                    print(f"   Field Type: {field['type']}")
                    return field
            
            print()
            print("💡 INSTRUCTIONS:")
            print("   1. Create the 'Quote Template' field in Pipedrive Deal")
            print("   2. Place it in the 'Quoter' section")
            print("   3. Make it a dropdown with template options:")
            print("      - test")
            print("      - Managed Service Proposal - Example Only")
            print("      - Tank Delivery")
            print("      - LED Wristbands")
            print("   4. Run this script again to find the field ID")
            
            return None
            
        else:
            print(f"❌ Failed to fetch deal fields: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error searching for fields: {e}")
        return None

def main():
    """
    Main function to find the Quote Template field.
    """
    try:
        field_info = find_quoter_template_field()
        if field_info:
            print(f"\n🎉 Field found! Use ID: {field_info['id']}")
        else:
            print(f"\n⚠️  Field not found. Please create it first.")
    except Exception as e:
        print(f"❌ Script failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
