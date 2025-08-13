#!/usr/bin/env python3
"""
Test script to test the improved contact search logic and see if it prevents
duplicate contact creation.
"""

from quoter import create_or_find_contact_in_quoter

def test_improved_contact_search():
    """Test the improved contact search logic."""
    
    print("🧪 Testing Improved Contact Search")
    print("=" * 50)
    print("Goal: Test if improved search prevents duplicate contacts")
    print()
    
    # Test case 1: Robert Lee at Blue Owl Capital (should find existing)
    print("🎯 Test Case 1: Robert Lee at Blue Owl Capital")
    print("-" * 40)
    
    contact_id_1 = create_or_find_contact_in_quoter(
        contact_name="Robert Lee",
        contact_email="robert.lee@blueowl.com",
        organization_name="Blue Owl Capital"
    )
    
    print(f"Result: {contact_id_1}")
    print()
    
    # Test case 2: Robert Lee at Blue Owl Capital-2096 (should find existing)
    print("🎯 Test Case 2: Robert Lee at Blue Owl Capital-2096")
    print("-" * 40)
    
    contact_id_2 = create_or_find_contact_in_quoter(
        contact_name="Robert Lee",
        contact_email="robert.lee@blueowl.com",
        organization_name="Blue Owl Capital-2096"
    )
    
    print(f"Result: {contact_id_2}")
    print()
    
    # Test case 3: Robert Lee at different org (should find existing but warn)
    print("🎯 Test Case 3: Robert Lee at Different Org")
    print("-" * 40)
    
    contact_id_3 = create_or_find_contact_in_quoter(
        contact_name="Robert Lee",
        contact_email="robert.lee@blueowl.com",
        organization_name="Different Company"
    )
    
    print(f"Result: {contact_id_3}")
    print()
    
    # Test case 4: New person (should create new contact)
    print("🎯 Test Case 4: New Person")
    print("-" * 40)
    
    contact_id_4 = create_or_find_contact_in_quoter(
        contact_name="John Smith",
        contact_email="john.smith@newcompany.com",
        organization_name="New Company"
    )
    
    print(f"Result: {contact_id_4}")
    print()
    
    # Summary
    print("📊 Summary:")
    print(f"   Test 1 (Blue Owl Capital): {contact_id_1}")
    print(f"   Test 2 (Blue Owl Capital-2096): {contact_id_2}")
    print(f"   Test 3 (Different Org): {contact_id_3}")
    print(f"   Test 4 (New Person): {contact_id_4}")
    print()
    
    if contact_id_1 == contact_id_2:
        print("✅ SUCCESS: Same contact reused for Blue Owl Capital variants")
    else:
        print("❌ ISSUE: Different contacts for same person")
    
    if contact_id_1 == contact_id_3:
        print("✅ SUCCESS: Same contact reused even with different org")
    else:
        print("❌ ISSUE: Different contacts for same person with different org")
    
    if contact_id_4 and contact_id_4 != contact_id_1:
        print("✅ SUCCESS: New contact created for new person")
    else:
        print("❌ ISSUE: New contact not created or same as existing")

if __name__ == "__main__":
    test_improved_contact_search()
