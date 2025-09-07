#!/usr/bin/env python3
"""
Check for template changes - used by GitHub Actions
"""

import sys
import os
sys.path.append(".")

from auto_sync_templates import TemplateSyncer

def main():
    syncer = TemplateSyncer()
    if not syncer.initialize_tokens():
        print("❌ Failed to initialize tokens")
        sys.exit(1)
    
    # Get current state
    quoter_templates = syncer.get_quoter_templates()
    pipedrive_options = syncer.get_pipedrive_enum_options()
    
    if not quoter_templates or not pipedrive_options:
        print("❌ Could not fetch templates or options")
        sys.exit(1)
    
    # Extract names
    quoter_names = {template.get("title", "") for template in quoter_templates}
    pipedrive_labels = {option.get("label", "") for option in pipedrive_options}
    
    # Check for differences
    new_templates = quoter_names - pipedrive_labels
    renamed_templates = {}
    
    # Check for renames (case-insensitive)
    for quoter_name in quoter_names:
        if quoter_name not in pipedrive_labels:
            quoter_lower = quoter_name.lower()
            for pipedrive_label in pipedrive_labels:
                if pipedrive_label.lower() == quoter_lower:
                    renamed_templates[pipedrive_label] = quoter_name
                    break
    
    has_changes = len(new_templates) > 0 or len(renamed_templates) > 0
    
    print(f"📊 New templates: {len(new_templates)}")
    print(f"📊 Renamed templates: {len(renamed_templates)}")
    print(f"📊 Has changes: {has_changes}")
    
    if has_changes:
        print("✅ Changes detected - sync will run")
        # Write to GitHub output
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"), "a") as f:
            f.write("has_changes=true\n")
    else:
        print("⏭️  No changes detected - skipping sync")
        # Write to GitHub output
        with open(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"), "a") as f:
            f.write("has_changes=false\n")

if __name__ == "__main__":
    main()
