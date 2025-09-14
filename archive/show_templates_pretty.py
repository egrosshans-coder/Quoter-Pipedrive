#!/usr/bin/env python3
"""
Pretty display of Quoter templates in columned format
"""

import requests
import os
from quoter import get_access_token

def show_templates_pretty():
    """Display templates in a pretty columned format"""
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print('❌ Failed to get access token')
        return False

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    print('🔍 Fetching quote templates from Quoter API...')
    r = requests.get('https://api.quoter.com/v1/quote_templates', headers=headers)

    if r.status_code == 200:
        data = r.json()
        templates = data.get('data', [])
        
        print(f'\n📋 Found {len(templates)} templates:')
        print('=' * 130)
        
        # Header row
        header = f"{'Template Name':<25} {'Template ID':<35} {'Slug':<20} {'Created':<12} {'Modified':<12}"
        print(header)
        print('-' * 130)
        
        # Template rows
        for template in templates:
            name = template.get('title', 'N/A')
            template_id = template.get('id', 'N/A')
            slug = template.get('slug', 'N/A')
            created = template.get('created_at', 'N/A')[:10] if template.get('created_at') else 'N/A'
            modified = template.get('modified_at', 'N/A')[:10] if template.get('modified_at') else 'N/A'
            
            row = f"{name:<25} {template_id:<35} {slug:<20} {created:<12} {modified:<12}"
            print(row)
        
        print('-' * 130)
        print(f'Total: {len(templates)} templates')
        
        # Show template mapping status
        print(f'\n🎯 Template Mapping Status:')
        print('=' * 50)
        
        # Check which templates have mappings
        from template_mapping import get_all_template_names
        mapped_templates = get_all_template_names()
        
        for template in templates:
            name = template.get('title', 'N/A')
            status = '✅ Mapped' if name in mapped_templates else '❌ Not Mapped'
            print(f"{name:<25} {status}")
            
        print(f'\n📊 Mapping Summary:')
        mapped_count = sum(1 for template in templates if template.get('title') in mapped_templates)
        total_count = len(templates)
        print(f"   Mapped: {mapped_count}/{total_count} templates")
        print(f"   Unmapped: {total_count - mapped_count}/{total_count} templates")
        
        return True
    else:
        print(f'❌ Error: {r.status_code} - {r.text}')
        return False

if __name__ == "__main__":
    show_templates_pretty()

