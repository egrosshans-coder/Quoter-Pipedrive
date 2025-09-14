#!/usr/bin/env python3
"""
Test script to see if we can update a quote's template after creation.
"""

import requests
import json
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token
from utils.logger import logger

def test_template_update():
    """
    Test if we can update a quote's template after creation using PATCH/PUT.
    """
    print("🧪 Testing Template Update After Quote Creation")
    print("=" * 60)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Use one of the test quotes we created
    test_quote_id = "quot_32Z1DVfFhhiW84OovuHT2TfN3bW"  # The Robotics one
    
    print(f"🔍 Testing template update on quote: {test_quote_id}")
    
    # Test different field names for template
    test_updates = [
        {"template_id": "tmpl_329qcsv6mx0upqqLkXFkEZZi92O"},  # Robotics
        {"template": "tmpl_329qcsv6mx0upqqLkXFkEZZi92O"},     # Alternative field name
        {"quote_template_id": "tmpl_329qcsv6mx0upqqLkXFkEZZi92O"},  # Another alternative
        {"template": {"id": "tmpl_329qcsv6mx0upqqLkXFkEZZi92O"}},  # Object format
    ]
    
    for i, update_data in enumerate(test_updates, 1):
        print(f"\n🔍 Test {i}: Trying to update template with:")
        print(f"   {json.dumps(update_data, indent=2)}")
        
        try:
            # Try PATCH request
            response = requests.patch(
                f"https://api.quoter.com/v1/quotes/{test_quote_id}",
                json=update_data,
                headers=headers,
                timeout=10
            )
            
            print(f"   PATCH Response: {response.status_code}")
            if response.status_code not in [200, 201, 204]:
                print(f"   Error: {response.text}")
            else:
                print(f"   ✅ Success! Template updated")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Also test PUT request
    print(f"\n🔍 Testing PUT request:")
    try:
        put_data = {
            "template_id": "tmpl_329qcsv6mx0upqqLkXFkEZZi92O"
        }
        
        response = requests.put(
            f"https://api.quoter.com/v1/quotes/{test_quote_id}",
            json=put_data,
            headers=headers,
            timeout=10
        )
        
        print(f"   PUT Response: {response.status_code}")
        if response.status_code not in [200, 201, 204]:
            print(f"   Error: {response.text}")
        else:
            print(f"   ✅ Success! Template updated")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n📊 SUMMARY:")
    print("=" * 60)
    print("Check the quote in Quoter to see if any of these update methods worked.")
    print("If none worked, we may need to use a different approach.")
    
    return True

if __name__ == "__main__":
    test_template_update()

