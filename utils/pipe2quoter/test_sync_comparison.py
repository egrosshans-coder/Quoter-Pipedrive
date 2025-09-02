#!/usr/bin/env python3
"""
Test script for Pipedrive to Quoter sync comparison logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sync_pipedrive_to_quoter import compare_items

def test_comparison():
    """Test the comparison logic with sample data."""
    
    print("🧪 Testing Pipedrive to Quoter Comparison Logic")
    print("=" * 50)
    
    # Mock Quoter categories for testing
    quoter_categories = {
        "Lighting / LED": "cat_123",
        "Audio / Speakers": "cat_456", 
        "Video / Projectors": "cat_789",
        "Lighting": "cat_parent_123"
    }
    
    # Test case 1: Name change
    print("\n1. Testing name change:")
    pipedrive_product = {
        "name": "Updated Product Name",
        "code": "TEST001",
        "category_name": "Lighting / LED"
    }
    quoter_item = {
        "name": "Old Product Name",
        "code": "TEST001",
        "category_id": "cat_123"
    }
    
    changes = compare_items(pipedrive_product, quoter_item, quoter_categories)
    print(f"   Changes detected: {changes}")
    
    # Test case 2: Code change
    print("\n2. Testing code change:")
    pipedrive_product = {
        "name": "Same Product Name",
        "code": "TEST002",
        "category_name": "Lighting / LED"
    }
    quoter_item = {
        "name": "Same Product Name",
        "code": "TEST001",
        "category_id": "cat_123"
    }
    
    changes = compare_items(pipedrive_product, quoter_item, quoter_categories)
    print(f"   Changes detected: {changes}")
    
    # Test case 3: Category change (Parent/Child format)
    print("\n3. Testing category change (Parent/Child):")
    pipedrive_product = {
        "name": "Same Product Name",
        "code": "TEST001",
        "category_name": "Audio / Speakers"
    }
    quoter_item = {
        "name": "Same Product Name",
        "code": "TEST001",
        "category_id": "cat_123"
    }
    
    changes = compare_items(pipedrive_product, quoter_item, quoter_categories)
    print(f"   Changes detected: {changes}")
    
    # Test case 4: Category not found in Quoter
    print("\n4. Testing category not found:")
    pipedrive_product = {
        "name": "Same Product Name",
        "code": "TEST001",
        "category_name": "Unknown / Category"
    }
    quoter_item = {
        "name": "Same Product Name",
        "code": "TEST001",
        "category_id": "cat_123"
    }
    
    changes = compare_items(pipedrive_product, quoter_item, quoter_categories)
    print(f"   Changes detected: {changes}")
    
    # Test case 5: No changes
    print("\n5. Testing no changes:")
    pipedrive_product = {
        "name": "Same Product Name",
        "code": "TEST001",
        "category_name": "Lighting / LED"
    }
    quoter_item = {
        "name": "Same Product Name",
        "code": "TEST001",
        "category_id": "cat_123"
    }
    
    changes = compare_items(pipedrive_product, quoter_item, quoter_categories)
    print(f"   Changes detected: {changes}")
    
    print("\n" + "=" * 50)
    print("🎯 Comparison logic test complete!")
    print("\nKey improvements:")
    print("• Handles Quoter's parent/child category schema")
    print("• Maps 'Parent / Child' format to category IDs")
    print("• Warns about categories not found in Quoter")
    print("• Properly compares category IDs instead of names")

if __name__ == "__main__":
    test_comparison()
