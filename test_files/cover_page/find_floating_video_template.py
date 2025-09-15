#!/usr/bin/env python3
"""
Find the actual Floating Video template ID in Quoter
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token
import requests

def find_floating_video_template():
    print("🔍 FINDING FLOATING VIDEO TEMPLATE")
    print("=" * 40)
    
    access_token = get_access_token()
    if not access_token:
        print("❌ No access token")
        return
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    try:
        response = requests.get('https://api.quoter.com/v1/quote_templates', headers=headers)
        if response.status_code == 200:
            data = response.json()
            templates = data.get('data', [])
            
            print(f"📋 Found {len(templates)} templates:")
            print("-" * 40)
            
            floating_video_template = None
            
            for template in templates:
                template_id = template.get('id')
                template_name = template.get('name', 'Unknown')
                template_slug = template.get('slug', 'Unknown')
                
                print(f"ID: {template_id}")
                print(f"Name: {template_name}")
                print(f"Slug: {template_slug}")
                print("-" * 20)
                
                # Look for Floating Video template
                if ('floating' in template_name.lower() or 
                    'floating' in template_slug.lower() or
                    'video' in template_name.lower() or
                    'video' in template_slug.lower()):
                    floating_video_template = template
                    print("🎯 POTENTIAL FLOATING VIDEO TEMPLATE FOUND!")
            
            if floating_video_template:
                print(f"\n✅ FLOATING VIDEO TEMPLATE:")
                print(f"   ID: {floating_video_template.get('id')}")
                print(f"   Name: {floating_video_template.get('name')}")
                print(f"   Slug: {floating_video_template.get('slug')}")
                return floating_video_template.get('id')
            else:
                print(f"\n⚠️ No Floating Video template found!")
                print(f"   Available templates: {[t.get('name') for t in templates]}")
                return None
                
        else:
            print(f"❌ Failed to get templates: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    template_id = find_floating_video_template()
    if template_id:
        print(f"\n🎯 Use this template ID for Floating Video quotes: {template_id}")
    else:
        print(f"\n❌ No Floating Video template found")
