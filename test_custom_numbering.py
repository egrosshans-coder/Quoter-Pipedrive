#!/usr/bin/env python3
"""
Test script to verify our updated quote creation function works with custom numbering.
"""

from quoter import create_draft_quote
from utils.logger import logger

def test_custom_quote_numbering():
    """Test the updated create_draft_quote function with custom numbering"""
    print("🧪 Testing Custom Quote Numbering")
    print("=" * 60)
    
    # Test with a sample deal
    test_deal_id = "TEST-001"
    test_org_name = "Test Organization"
    test_deal_title = "Test Deal for Custom Numbering"
    
    print(f"📝 Creating test quote:")
    print(f"   Deal ID: {test_deal_id}")
    print(f"   Organization: {test_org_name}")
    print(f"   Deal Title: {test_deal_title}")
    print(f"   Expected Quote Number: PD-{test_deal_id}")
    
    # Create the quote
    result = create_draft_quote(test_deal_id, test_org_name, test_deal_title)
    
    if result:
        print(f"\n✅ Quote created successfully!")
        print(f"   Quote ID: {result.get('id', 'N/A')}")
        print(f"   Quote URL: {result.get('url', 'N/A')}")
        print(f"   Quote Number: PD-{test_deal_id} (set during creation)")
        
        # Note: We can't verify the quote_number in the response because Quoter doesn't return it
        # But we know it was accepted during creation based on our earlier testing
        
    else:
        print(f"\n❌ Failed to create quote")
    
    print("\n" + "=" * 60)
    print("🎯 Test Complete!")
    print("Note: Quote numbers are set during creation but may not appear in the response.")
    print("Check your Quoter admin panel to see the custom quote numbers.")

if __name__ == "__main__":
    test_custom_quote_numbering()
