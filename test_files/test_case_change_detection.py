#!/usr/bin/env python3
"""
Test case change detection logic
This simulates what would happen if you changed case in Quoter templates
"""

def test_case_change_detection():
    """Simulate case change detection"""
    print("🧪 Testing Case Change Detection")
    print("=" * 50)
    
    # Simulate current Pipedrive enum options
    pipedrive_labels = {
        "Balloons",
        "Basic", 
        "Co2/smoke/upright foggers",
        "Confetti/Streamers",
        "Fireworks/pyro/fire",
        "Floating Video",
        "LED Lanyards",
        "LED Wristbands",
        "Low level fog",
        "Robotics",
        "Tank Delivery"
    }
    
    # Simulate Quoter templates with case changes
    quoter_names = {
        "BALLOONS",  # Changed case
        "Basic",
        "Co2/smoke/upright foggers", 
        "Confetti/streamers",  # Changed case
        "Fireworks/pyro/fire",
        "Floating Video",
        "LED Lanyards",
        "LED Wristbands", 
        "Low level fog",
        "Robotics",
        "Tank Delivery"
    }
    
    print("📋 Current Pipedrive labels:")
    for label in sorted(pipedrive_labels):
        print(f"   • {label}")
    
    print(f"\n📋 Quoter templates (with case changes):")
    for name in sorted(quoter_names):
        print(f"   • {name}")
    
    print(f"\n🔍 Detection Analysis:")
    
    # Smart detection logic
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
                print(f"➕ New template: '{quoter_name}'")
    
    # Calculate removed templates (excluding those that were renamed)
    renamed_old_names = set(renamed_templates.keys())
    removed_templates = pipedrive_labels - quoter_names - renamed_old_names
    
    print(f"\n📊 Summary:")
    print(f"   • New templates: {len(new_templates)}")
    print(f"   • Renamed templates: {len(renamed_templates)}")
    print(f"   • Removed templates: {len(removed_templates)}")
    
    if renamed_templates:
        print(f"\n🔄 What the system would do:")
        for old_name, new_name in renamed_templates.items():
            print(f"   • Update Pipedrive: '{old_name}' → '{new_name}'")
    
    if new_templates:
        print(f"\n➕ What the system would do:")
        for template in new_templates:
            print(f"   • Add to Pipedrive: '{template}'")
    
    if removed_templates:
        print(f"\n⚠️  What the system would report (but not remove):")
        for template in removed_templates:
            print(f"   • Template in Pipedrive but not Quoter: '{template}'")
    
    print(f"\n✅ Result: System would automatically fix {len(renamed_templates)} case changes!")

if __name__ == "__main__":
    test_case_change_detection()
