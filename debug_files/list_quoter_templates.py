#!/usr/bin/env python3
"""
List all available Quoter templates
This script fetches and displays all quote templates available in the Quoter system.
"""

import requests
import json
import sys
import os

# Add the parent directory to the path so we can import quoter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quoter import get_access_token
from utils.logger import logger

def list_all_templates():
    """
    Fetch and display all available quote templates from Quoter.
    """
    print("🔍 Fetching all available Quoter templates...")
    print("=" * 60)
    
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Fetch all templates
        response = requests.get(
            "https://api.quoter.com/v1/quote_templates",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get("data", [])
            
            if not templates:
                print("❌ No templates found in Quoter")
                return False
            
            print(f"✅ Found {len(templates)} templates:")
            print()
            
            # Display each template with details
            for i, template in enumerate(templates, 1):
                template_id = template.get("id", "N/A")
                title = template.get("title", "N/A")
                description = template.get("description", "")
                created_at = template.get("created_at", "N/A")
                updated_at = template.get("updated_at", "N/A")
                
                print(f"📋 Template {i}:")
                print(f"   ID: {template_id}")
                print(f"   Title: {title}")
                if description:
                    print(f"   Description: {description}")
                print(f"   Created: {created_at}")
                print(f"   Updated: {updated_at}")
                
                # Show any additional fields
                other_fields = {k: v for k, v in template.items() 
                              if k not in ['id', 'title', 'description', 'created_at', 'updated_at']}
                if other_fields:
                    print(f"   Other fields: {json.dumps(other_fields, indent=6)}")
                
                print()
            
            # Summary
            print("=" * 60)
            print("📊 TEMPLATE SUMMARY:")
            print(f"   Total templates: {len(templates)}")
            
            # Group by common patterns
            titles = [t.get("title", "") for t in templates]
            print(f"   Template titles: {', '.join(titles)}")
            
            # Check for current hard-coded preferences
            test_templates = [t for t in templates if "test" in t.get("title", "").lower()]
            managed_templates = [t for t in templates if "managed" in t.get("title", "").lower()]
            
            print()
            print("🎯 CURRENT HARD-CODED PREFERENCES:")
            if test_templates:
                print(f"   ✅ 'test' templates found: {len(test_templates)}")
                for t in test_templates:
                    print(f"      - {t.get('title')} (ID: {t.get('id')})")
            else:
                print("   ❌ No 'test' templates found")
            
            if managed_templates:
                print(f"   ✅ 'Managed Service' templates found: {len(managed_templates)}")
                for t in managed_templates:
                    print(f"      - {t.get('title')} (ID: {t.get('id')})")
            else:
                print("   ❌ No 'Managed Service' templates found")
            
            return True
            
        else:
            print(f"❌ Failed to fetch templates: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching templates: {e}")
        return False

def main():
    """
    Main function to list all Quoter templates.
    """
    try:
        success = list_all_templates()
        if success:
            print("\n🎉 Template listing completed successfully!")
        else:
            print("\n❌ Template listing failed!")
    except Exception as e:
        print(f"❌ Script failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
