#!/usr/bin/env python3
"""
Simple test to verify the simplified contact search logic.
"""

from quoter import create_or_find_contact_in_quoter

def test_simple_contact_search():
    """Test the simplified contact search logic."""
    
    print("🧪 Testing Simplified Contact Search")
    print("=" * 40)
    print("Goal: Email match = use existing, no match = create new")
    print()
    
    # Test 1: Robert Lee (should find existing)
    print("🎯 Test 1: Robert Lee (existing contact)")
    print("-" * 30)
    
    contact_id_1 = create_or_find_contact_in_quoter(
        contact_name="Robert Lee",
        contact_email="robert.lee@blueowl.com",
        organization_name="Blue Owl Capital"
    )
    
    print(f"Result: {contact_id_1}")
    print()
    
    # Test 2: Robert Lee again (should find same existing)
    print("🎯 Test 2: Robert Lee again (should reuse)")
    print("-" * 30)
    
    contact_id_2 = create_or_find_contact_in_quoter(
        contact_name="Robert Lee",
        contact_email="robert.lee@blueowl.com",
        organization_name="Blue Owl Capital"
    )
    
    print(f"Result: {contact_id_2}")
    print()
    
    # Test 3: New person (should create new)
    print("🎯 Test 3: New Person (should create new)")
    print("-" * 30)
    
    contact_id_3 = create_or_find_contact_in_quoter(
        contact_name="Jane Doe",
        contact_email="jane.doe@newcompany.com",
        organization_name="New Company"
    )
    
    print(f"Result: {contact_id_3}")
    print()
    
    # Summary
    print("📊 Summary:")
    print(f"   Test 1: {contact_id_1}")
    print(f"   Test 2: {contact_id_2}")
    print(f"   Test 3: {contact_id_3}")
    print()
    
    if contact_id_1 == contact_id_2:
        print("✅ SUCCESS: Same contact reused")
    else:
        print("❌ ISSUE: Different contacts for same person")
    
    if contact_id_3 and contact_id_3 != contact_id_1:
        print("✅ SUCCESS: New contact created for new person")
    else:
        print("❌ ISSUE: New contact not created or same as existing")

if __name__ == "__main__":
    test_simple_contact_search()
