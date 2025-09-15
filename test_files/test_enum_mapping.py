#!/usr/bin/env python3
"""
Test Enum Mapping for Quote Template Field
Tests all enum values to ensure they map correctly to template names.
"""

import sys
import os

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from template_selection_logic import get_template_from_pipedrive_field
from quoter import get_access_token
from utils.logger import logger

def test_enum_mapping():
    """
    Test all enum values for the Quote Template field.
    """
    print("🧪 Testing Enum Mapping for Quote Template Field")
    print("=" * 60)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return False
    
    # Test all enum values
    enum_tests = [
        (441, "Basic"),
        (442, "Confetti/Streamers"),
        (443, "LED Lanyards"),
        (444, "LED Wristbands"),
        (451, "Balloons"),
        (452, "Co2/smoke/upright foggers"),
        (453, "Fireworks/pyro/fire"),
        (454, "Floating Video"),
        (455, "Low level fog"),
        (456, "Tank Delivery"),
        (457, "Robotics"),
    ]
    
    template_field_id = "42ab0c919271cb24f3587f0b01ea2af166019c8d"
    
    print(f"📋 Testing {len(enum_tests)} enum values...")
    print()
    
    success_count = 0
    
    for enum_value, expected_name in enum_tests:
        print(f"🔍 Testing enum {enum_value} -> '{expected_name}'")
        
        # Create mock deal data with the enum value
        deal_data = {
            "id": 9999,
            "title": "Test Deal",
            template_field_id: enum_value
        }
        
        # Test the template selection
        template_id = get_template_from_pipedrive_field(deal_data, access_token, template_field_id)
        
        if template_id:
            print(f"   ✅ Success: {enum_value} -> {expected_name} -> {template_id}")
            success_count += 1
        else:
            print(f"   ❌ Failed: {enum_value} -> {expected_name}")
        
        print()
    
    print("=" * 60)
    print(f"📊 Results: {success_count}/{len(enum_tests)} enum values mapped successfully")
    
    if success_count == len(enum_tests):
        print("🎉 All enum values mapped correctly!")
        return True
    else:
        print("⚠️  Some enum values failed to map")
        return False

def test_unknown_enum():
    """
    Test handling of unknown enum values.
    """
    print("\n" + "=" * 60)
    print("🧪 Testing Unknown Enum Value Handling")
    print("=" * 60)
    
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return False
    
    template_field_id = "42ab0c919271cb24f3587f0b01ea2af166019c8d"
    
    # Test with unknown enum value
    deal_data = {
        "id": 9999,
        "title": "Test Deal",
        template_field_id: 999  # Unknown enum value
    }
    
    print(f"🔍 Testing unknown enum value: 999")
    
    template_id = get_template_from_pipedrive_field(deal_data, access_token, template_field_id)
    
    if template_id is None:
        print("   ✅ Success: Unknown enum value handled correctly (returned None)")
        return True
    else:
        print(f"   ❌ Failed: Unknown enum value returned template ID: {template_id}")
        return False

def test_no_template_selected():
    """
    Test handling when no template is selected (None value).
    """
    print("\n" + "=" * 60)
    print("🧪 Testing No Template Selected Handling")
    print("=" * 60)
    
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return False
    
    template_field_id = "42ab0c919271cb24f3587f0b01ea2af166019c8d"
    
    # Test with no template selected
    deal_data = {
        "id": 9999,
        "title": "Test Deal",
        template_field_id: None  # No template selected
    }
    
    print(f"🔍 Testing no template selected (None)")
    
    template_id = get_template_from_pipedrive_field(deal_data, access_token, template_field_id)
    
    if template_id is None:
        print("   ✅ Success: No template selected handled correctly (returned None)")
        return True
    else:
        print(f"   ❌ Failed: No template selected returned template ID: {template_id}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Enum Mapping Tests")
    print("=" * 60)
    
    # Test 1: All valid enum values
    success1 = test_enum_mapping()
    
    # Test 2: Unknown enum value
    success2 = test_unknown_enum()
    
    # Test 3: No template selected
    success3 = test_no_template_selected()
    
    print("\n" + "=" * 60)
    print("📊 Final Test Results")
    print("=" * 60)
    print(f"Valid Enum Mapping: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Unknown Enum Handling: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"No Template Handling: {'✅ PASS' if success3 else '❌ FAIL'}")
    
    if success1 and success2 and success3:
        print("\n🎉 All enum mapping tests passed!")
    else:
        print("\n⚠️  Some enum mapping tests failed.")
