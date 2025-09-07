#!/usr/bin/env python3
"""
List All Available Templates in Quoter
This will help us see what templates are actually available and match them with our enum values.
"""

import requests
import json
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quoter import get_access_token
from utils.logger import logger

def list_all_templates():
    """
    List all available templates in Quoter with their IDs and names.
    """
    print("🔍 Listing All Available Templates in Quoter")
    print("=" * 60)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "https://api.quoter.com/v1/quote_templates",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get("data", [])
            
            print(f"📋 Found {len(templates)} templates in Quoter:")
            print()
            
            # Group templates by category for better organization
            template_categories = {
                "LED Products": [],
                "Event Services": [],
                "Technology": [],
                "Other": []
            }
            
            for template in templates:
                template_id = template.get("id", "Unknown")
                template_name = template.get("title", "Unknown")
                template_created = template.get("created_at", "Unknown")
                
                # Categorize templates
                if any(keyword in template_name.lower() for keyword in ["led", "wristband", "lanyard"]):
                    template_categories["LED Products"].append((template_id, template_name, template_created))
                elif any(keyword in template_name.lower() for keyword in ["confetti", "streamer", "tank", "delivery", "event"]):
                    template_categories["Event Services"].append((template_id, template_name, template_created))
                elif any(keyword in template_name.lower() for keyword in ["robot", "robotic", "ai", "automation", "tech"]):
                    template_categories["Technology"].append((template_id, template_name, template_created))
                else:
                    template_categories["Other"].append((template_id, template_name, template_created))
            
            # Display templates by category
            for category, templates_list in template_categories.items():
                if templates_list:
                    print(f"🎯 {category} ({len(templates_list)} templates):")
                    for template_id, template_name, template_created in templates_list:
                        print(f"   • {template_name}")
                        print(f"     ID: {template_id}")
                        print(f"     Created: {template_created}")
                        print()
            
            # Show all templates in a simple list for easy reference
            print("=" * 60)
            print("📋 ALL TEMPLATES (Simple List):")
            print("=" * 60)
            for i, template in enumerate(templates, 1):
                template_id = template.get("id", "Unknown")
                template_name = template.get("title", "Unknown")
                print(f"{i:2d}. {template_name} (ID: {template_id})")
            
            return templates
            
        else:
            print(f"❌ Failed to fetch templates: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching templates: {e}")
        return None

def match_enum_to_templates():
    """
    Try to match our enum values to available templates.
    """
    print("\n" + "=" * 60)
    print("🎯 Matching Enum Values to Available Templates")
    print("=" * 60)
    
    templates = list_all_templates()
    if not templates:
        return
    
    # Our enum mapping
    enum_mapping = {
        441: 'Basic',
        442: 'Confetti/Streamers',
        443: 'LED Lanyards',
        444: 'LED Wristbands',
        451: 'Balloons',
        452: 'Co2/smoke/upright foggers',
        453: 'Fireworks/pyro/fire',
        454: 'Floating Video',
        455: 'Low level fog',
        456: 'Tank Delivery',
        457: 'Robotics',
    }
    
    print("🔍 Checking for matches:")
    print()
    
    for enum_value, template_name in enum_mapping.items():
        print(f"Enum {enum_value} -> '{template_name}':")
        
        # Look for exact matches
        exact_matches = [t for t in templates if t.get("title", "").lower() == template_name.lower()]
        if exact_matches:
            for match in exact_matches:
                print(f"   ✅ EXACT MATCH: {match.get('title')} (ID: {match.get('id')})")
        else:
            print(f"   ❌ No exact match found")
            
            # Look for partial matches
            partial_matches = []
            for template in templates:
                template_title = template.get("title", "").lower()
                if any(word in template_title for word in template_name.lower().split()):
                    partial_matches.append(template)
            
            if partial_matches:
                print(f"   🔍 Partial matches:")
                for match in partial_matches:
                    print(f"      • {match.get('title')} (ID: {match.get('id')})")
            else:
                print(f"   ❌ No partial matches found")
        
        print()

if __name__ == "__main__":
    print("🚀 Starting Template Analysis")
    print("=" * 60)
    
    # List all templates
    templates = list_all_templates()
    
    # Match enum values to templates
    match_enum_to_templates()
    
    print("✅ Template analysis complete!")
