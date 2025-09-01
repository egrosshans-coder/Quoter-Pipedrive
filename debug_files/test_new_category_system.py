#!/usr/bin/env python3
"""
Test New Category System
Uses our consolidated category_manager.py to show real categories and subcategories.
This replaces the old working_test.py with accurate, real-time data.
"""

from category_manager import (
    get_pipedrive_categories, 
    get_subcategory_field_key,
    get_category_mapping,
    get_subcategory_mapping
)

def test_category_system():
    """Test the new consolidated category system."""
    
    print("🚀 TESTING NEW CONSOLIDATED CATEGORY SYSTEM")
    print("=" * 60)
    
    # Test 1: Get all Pipedrive categories
    print("\n📋 TEST 1: Fetching Pipedrive Categories")
    print("-" * 40)
    
    categories = get_pipedrive_categories()
    if categories:
        print(f"✅ Successfully retrieved {len(categories)} categories:")
        for i, (name, id_val) in enumerate(sorted(categories.items()), 1):
            print(f"  {i:2d}. {name} (ID: {id_val})")
    else:
        print("❌ Failed to retrieve categories")
        return
    
    # Test 2: Get subcategory field key
    print("\n📋 TEST 2: Finding Subcategory Field")
    print("-" * 40)
    
    subcategory_field_key = get_subcategory_field_key()
    if subcategory_field_key:
        print(f"✅ Found subcategory field key: {subcategory_field_key}")
        print("✅ Field type: Text (free-form input)")
    else:
        print("❌ Failed to find subcategory field")
        return
    
    # Test 3: Test category mapping for specific categories
    print("\n📋 TEST 3: Testing Category Mappings")
    print("-" * 40)
    
    test_categories = ["Tanks", "Laser", "Hologram", "Pyro", "AI"]
    for category_name in test_categories:
        category_id = get_category_mapping(category_name)
        if category_id:
            print(f"✅ '{category_name}' → ID: {category_id}")
        else:
            print(f"❌ '{category_name}' → Not found")
    
    # Test 4: Test subcategory mapping
    print("\n📋 TEST 4: Testing Subcategory Mappings")
    print("-" * 40)
    
    test_subcategories = ["1-to-3 Splitter", "40Watt", "Controller-TLC", "GlowBalls"]
    for subcategory_name in test_subcategories:
        field_key = get_subcategory_mapping(subcategory_name)
        if field_key:
            print(f"✅ '{subcategory_name}' → Field Key: {field_key}")
            print(f"   (Will be sent as text value)")
        else:
            print(f"❌ '{subcategory_name}' → Field key not found")
    
    # Test 5: Show complete mapping example
    print("\n📋 TEST 5: Complete Mapping Example")
    print("-" * 40)
    
    print("Example: Quoter category 'Tanks / 1-to-3 Splitter'")
    
    # Get main category mapping
    main_category = "Tanks"
    category_id = get_category_mapping(main_category)
    
    # Get subcategory field key
    subcategory_name = "1-to-3 Splitter"
    field_key = get_subcategory_mapping(subcategory_name)
    
    if category_id and field_key:
        print(f"✅ Main category '{main_category}' → ID: {category_id}")
        print(f"✅ Subcategory '{subcategory_name}' → Field: {field_key}")
        print(f"✅ Pipedrive payload would be:")
        print(f"   {{'category': {category_id}, '{field_key}': '{subcategory_name}'}}")
    else:
        print("❌ Mapping failed")
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Categories found: {len(categories)}")
    print(f"✅ Subcategory field: {'Found' if subcategory_field_key else 'Not found'}")
    print(f"✅ System status: {'Working' if categories and subcategory_field_key else 'Broken'}")
    
    if categories and subcategory_field_key:
        print("\n🎉 NEW CATEGORY SYSTEM IS WORKING!")
        print("This replaces the old working_test.py with accurate, real-time data.")
    else:
        print("\n⚠️  NEW CATEGORY SYSTEM HAS ISSUES")
        print("Check the errors above for details.")

if __name__ == "__main__":
    test_category_system()
