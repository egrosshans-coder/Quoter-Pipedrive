#!/usr/bin/env python3
"""
Sync Quoter templates to Pipedrive enum field
This script automatically adds new Quoter templates to the Pipedrive Quote Template enum field.
"""

import os
import sys
import requests
import json
from typing import List, Dict, Set
from quoter import get_access_token
import os

def get_quoter_templates(access_token: str) -> List[Dict]:
    """Get all templates from Quoter API"""
    url = "https://api.quoter.com/v1/quote_templates"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        print(f"❌ Error fetching Quoter templates: {e}")
        return []

def get_pipedrive_enum_options(api_token: str, field_id: str) -> List[Dict]:
    """Get current enum options from Pipedrive field"""
    url = f"https://api.pipedrive.com/v1/dealFields/{field_id}"
    params = {"api_token": api_token}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("options", [])
    except Exception as e:
        print(f"❌ Error fetching Pipedrive enum options: {e}")
        return []

def add_enum_option(api_token: str, field_id: str, label: str) -> bool:
    """Add a new option to Pipedrive enum field"""
    url = f"https://api.pipedrive.com/v1/dealFields/{field_id}/options"
    params = {"api_token": api_token}
    data = {"label": label}
    
    try:
        response = requests.post(url, params=params, json=data)
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            print(f"✅ Added enum option: {label}")
            return True
        else:
            error_msg = result.get("error", "Unknown error")
            if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                print(f"⚠️  Enum option already exists: {label}")
                return True  # Not an error, just already exists
            else:
                print(f"❌ Failed to add enum option: {label} - {error_msg}")
                return False
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print(f"⚠️  Enum option may already exist: {label}")
            return True  # Assume it already exists
        else:
            print(f"❌ HTTP error adding enum option '{label}': {e}")
            return False
    except Exception as e:
        print(f"❌ Error adding enum option '{label}': {e}")
        return False

def sync_templates_to_pipedrive():
    """Main sync function"""
    print("🔄 Syncing Quoter templates to Pipedrive enum field")
    print("=" * 60)
    
    # Get API tokens
    quoter_token = get_access_token()
    if not quoter_token:
        print("❌ Failed to get Quoter access token")
        return False
    
    pipedrive_token = os.getenv("PIPEDRIVE_API_TOKEN")
    if not pipedrive_token:
        print("❌ Failed to get Pipedrive API token from environment")
        return False
    
    # Field ID for Quote Template enum (use numeric ID, not the key)
    field_id = "90"
    
    # Get current state
    print("📋 Fetching current templates and enum options...")
    quoter_templates = get_quoter_templates(quoter_token)
    pipedrive_options = get_pipedrive_enum_options(pipedrive_token, field_id)
    
    if not quoter_templates:
        print("❌ No templates found in Quoter")
        return False
    
    if not pipedrive_options:
        print("❌ No enum options found in Pipedrive")
        return False
    
    # Extract template names and current enum labels
    quoter_names = {template.get("title", "") for template in quoter_templates}
    pipedrive_labels = {option.get("label", "") for option in pipedrive_options}
    
    print(f"📊 Found {len(quoter_templates)} templates in Quoter")
    print(f"📊 Found {len(pipedrive_options)} enum options in Pipedrive")
    print()
    
    # Find new templates that need to be added (case-insensitive comparison)
    quoter_names_lower = {name.lower() for name in quoter_names}
    pipedrive_labels_lower = {label.lower() for label in pipedrive_labels}
    
    # Find truly new templates (not just case differences)
    new_templates = set()
    for quoter_name in quoter_names:
        if quoter_name.lower() not in pipedrive_labels_lower:
            new_templates.add(quoter_name)
    
    removed_templates = pipedrive_labels - quoter_names
    
    print("🔍 Analysis:")
    print(f"   • New templates to add: {len(new_templates)}")
    print(f"   • Templates to remove: {len(removed_templates)}")
    print()
    
    if new_templates:
        print("➕ New templates found:")
        for template in sorted(new_templates):
            print(f"   • {template}")
        print()
        
        # Ask for confirmation
        response = input("Do you want to add these templates to Pipedrive? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            print("🔄 Adding new templates to Pipedrive...")
            success_count = 0
            for template in sorted(new_templates):
                if add_enum_option(pipedrive_token, field_id, template):
                    success_count += 1
            
            print(f"✅ Successfully added {success_count}/{len(new_templates)} new templates")
        else:
            print("❌ Sync cancelled by user")
    else:
        print("✅ No new templates to sync - everything is up to date!")
    
    if removed_templates:
        print()
        print("⚠️  Templates that exist in Pipedrive but not in Quoter:")
        for template in sorted(removed_templates):
            print(f"   • {template}")
        print("   (These won't be automatically removed for safety)")
    
    return True

if __name__ == "__main__":
    sync_templates_to_pipedrive()
