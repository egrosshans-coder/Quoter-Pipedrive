#!/usr/bin/env python3
"""
Automatic template sync with webhook integration
This script can be run periodically to keep Pipedrive enum field in sync with Quoter templates.
"""

import os
import sys
import requests
import json
import time
from typing import List, Dict, Set, Optional
from quoter import get_access_token
import os

class TemplateSyncer:
    def __init__(self):
        self.quoter_token = None
        self.pipedrive_token = None
        self.field_id = "90"  # Use numeric field ID, not the key
        
    def initialize_tokens(self) -> bool:
        """Initialize API tokens"""
        print("🔑 Initializing API tokens...")
        
        self.quoter_token = get_access_token()
        if not self.quoter_token:
            print("❌ Failed to get Quoter access token")
            return False
        
        self.pipedrive_token = os.getenv("PIPEDRIVE_API_TOKEN")
        if not self.pipedrive_token:
            print("❌ Failed to get Pipedrive API token from environment")
            return False
        
        print("✅ API tokens initialized successfully")
        return True
    
    def get_quoter_templates(self) -> List[Dict]:
        """Get all templates from Quoter API"""
        url = "https://api.quoter.com/v1/quote_templates"
        headers = {
            "Authorization": f"Bearer {self.quoter_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except requests.exceptions.Timeout:
            print("⏰ Timeout fetching Quoter templates")
            return []
        except Exception as e:
            print(f"❌ Error fetching Quoter templates: {e}")
            return []
    
    def get_pipedrive_enum_options(self) -> List[Dict]:
        """Get current enum options from Pipedrive field"""
        url = f"https://api.pipedrive.com/v1/dealFields/{self.field_id}"
        params = {"api_token": self.pipedrive_token}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("options", [])
        except requests.exceptions.Timeout:
            print("⏰ Timeout fetching Pipedrive enum options")
            return []
        except Exception as e:
            print(f"❌ Error fetching Pipedrive enum options: {e}")
            return []
    
    def add_enum_option(self, label: str) -> bool:
        """Add a new option to Pipedrive enum field"""
        url = f"https://api.pipedrive.com/v1/dealFields/{self.field_id}/options"
        params = {"api_token": self.pipedrive_token}
        data = {"label": label}
        
        try:
            response = requests.post(url, params=params, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                print(f"✅ Added enum option: {label}")
                return True
            else:
                print(f"❌ Failed to add enum option: {label} - {result.get('error', 'Unknown error')}")
                return False
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout adding enum option: {label}")
            return False
        except Exception as e:
            print(f"❌ Error adding enum option '{label}': {e}")
            return False
    
    def update_enum_option(self, old_label: str, new_label: str) -> bool:
        """Update an existing enum option in Pipedrive by updating the entire field"""
        # Get all current options
        options = self.get_pipedrive_enum_options()
        if not options:
            print(f"❌ Could not get current options")
            return False
        
        # Find and update the specific option
        updated_options = []
        found = False
        
        for option in options:
            if option.get("label") == old_label:
                # Update this option
                updated_option = option.copy()
                updated_option["label"] = new_label
                updated_options.append(updated_option)
                found = True
                print(f"🔄 Updating option: '{old_label}' → '{new_label}'")
            else:
                # Keep other options unchanged
                updated_options.append(option)
        
        if not found:
            print(f"❌ Could not find option '{old_label}' to update")
            return False
        
        # Update the entire field with all options
        url = f"https://api.pipedrive.com/v1/dealFields/{self.field_id}"
        params = {"api_token": self.pipedrive_token}
        data = {"options": updated_options}
        
        try:
            response = requests.put(url, params=params, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("success"):
                print(f"✅ Updated enum option: '{old_label}' → '{new_label}'")
                return True
            else:
                error_msg = result.get("error", "Unknown error")
                print(f"❌ Failed to update enum option: '{old_label}' → '{new_label}' - {error_msg}")
                return False
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout updating enum option: '{old_label}' → '{new_label}'")
            return False
        except Exception as e:
            print(f"❌ Error updating enum option '{old_label}' → '{new_label}': {e}")
            return False
    
    def sync_templates(self, auto_mode: bool = False) -> Dict:
        """Sync templates between Quoter and Pipedrive"""
        print("🔄 Starting template sync...")
        print("=" * 50)
        
        # Get current state
        print("📋 Fetching current state...")
        quoter_templates = self.get_quoter_templates()
        pipedrive_options = self.get_pipedrive_enum_options()
        
        if not quoter_templates:
            print("❌ No templates found in Quoter")
            return {"success": False, "error": "No Quoter templates"}
        
        if not pipedrive_options:
            print("❌ No enum options found in Pipedrive")
            return {"success": False, "error": "No Pipedrive enum options"}
        
        # Extract names and create mapping
        quoter_names = {template.get("title", "") for template in quoter_templates}
        pipedrive_labels = {option.get("label", "") for option in pipedrive_options}
        
        print(f"📊 Quoter templates: {len(quoter_templates)}")
        print(f"📊 Pipedrive options: {len(pipedrive_options)}")
        
        # Smart detection: Find new vs renamed templates
        new_templates = set()
        renamed_templates = {}
        
        # Check each Quoter template
        for quoter_name in quoter_names:
            if quoter_name not in pipedrive_labels:
                # Check if this might be a rename (case-insensitive)
                quoter_lower = quoter_name.lower()
                possible_rename = None
                
                for pipedrive_label in pipedrive_labels:
                    if pipedrive_label.lower() == quoter_lower:
                        possible_rename = pipedrive_label
                        break
                
                if possible_rename:
                    # This is likely a rename (case difference)
                    renamed_templates[possible_rename] = quoter_name
                    print(f"🔄 Detected rename: '{possible_rename}' → '{quoter_name}'")
                else:
                    # This is a new template
                    new_templates.add(quoter_name)
        
        # Calculate removed templates (excluding those that were renamed)
        renamed_old_names = set(renamed_templates.keys())
        removed_templates = pipedrive_labels - quoter_names - renamed_old_names
        
        result = {
            "success": True,
            "quoter_count": len(quoter_templates),
            "pipedrive_count": len(pipedrive_options),
            "new_templates": list(new_templates),
            "renamed_templates": renamed_templates,
            "removed_templates": list(removed_templates),
            "added_count": 0,
            "renamed_count": 0,
            "errors": []
        }
        
        if renamed_templates:
            print(f"\n🔄 Found {len(renamed_templates)} renamed templates:")
            for old_name, new_name in renamed_templates.items():
                print(f"   • '{old_name}' → '{new_name}'")
            
            if not auto_mode:
                response = input(f"\nUpdate these {len(renamed_templates)} template names in Pipedrive? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("❌ Sync cancelled by user")
                    result["success"] = False
                    return result
            
            print(f"\n🔄 Updating {len(renamed_templates)} template names...")
            for old_name, new_name in renamed_templates.items():
                if self.update_enum_option(old_name, new_name):
                    result["renamed_count"] += 1
                else:
                    result["errors"].append(f"Failed to rename: {old_name} → {new_name}")
        
        if new_templates:
            print(f"\n➕ Found {len(new_templates)} new templates:")
            for template in sorted(new_templates):
                print(f"   • {template}")
            
            if not auto_mode:
                response = input(f"\nAdd these {len(new_templates)} templates to Pipedrive? (y/N): ").strip().lower()
                if response not in ['y', 'yes']:
                    print("❌ Sync cancelled by user")
                    result["success"] = False
                    return result
            
            print(f"\n🔄 Adding {len(new_templates)} new templates...")
            for template in sorted(new_templates):
                if self.add_enum_option(template):
                    result["added_count"] += 1
                else:
                    result["errors"].append(f"Failed to add: {template}")
        
        if not new_templates and not renamed_templates:
            print("✅ No new or renamed templates to sync - everything is up to date!")
        
        if removed_templates:
            print(f"\n⚠️  {len(removed_templates)} templates in Pipedrive but not in Quoter:")
            for template in sorted(removed_templates):
                print(f"   • {template}")
            print("   (These won't be automatically removed for safety)")
        
        return result
    
    def run_auto_sync(self, interval_minutes: int = 60):
        """Run automatic sync every interval_minutes"""
        print(f"🤖 Starting auto-sync every {interval_minutes} minutes...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                print(f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')} - Running sync...")
                result = self.sync_templates(auto_mode=True)
                
                if result["success"]:
                    print(f"✅ Sync completed: {result['added_count']} templates added")
                else:
                    print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")
                
                print(f"⏳ Waiting {interval_minutes} minutes until next sync...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n🛑 Auto-sync stopped by user")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync Quoter templates to Pipedrive enum field")
    parser.add_argument("--auto", action="store_true", help="Run in auto mode (no user prompts)")
    parser.add_argument("--interval", type=int, default=60, help="Auto-sync interval in minutes (default: 60)")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon with auto-sync")
    
    args = parser.parse_args()
    
    syncer = TemplateSyncer()
    
    if not syncer.initialize_tokens():
        sys.exit(1)
    
    if args.daemon:
        syncer.run_auto_sync(args.interval)
    else:
        result = syncer.sync_templates(auto_mode=args.auto)
        if result["success"]:
            print(f"\n🎉 Sync completed successfully!")
            if result["added_count"] > 0:
                print(f"   Added {result['added_count']} new templates")
        else:
            print(f"\n❌ Sync failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

if __name__ == "__main__":
    main()
