#!/usr/bin/env python3
"""
Test script to explore quote numbering options in Quoter API.
"""

from quoter import get_access_token
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_quote_creation_fields():
    """Test what fields are supported during quote creation"""
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Test different field combinations
    test_cases = [
        {
            "name": "Basic fields only",
            "data": {
                "title": "Test Quote - Basic",
                "status": "draft"
            }
        },
        {
            "name": "With quote_number field",
            "data": {
                "title": "Test Quote - With Number",
                "status": "draft",
                "quote_number": "PD-TEST-001"
            }
        },
        {
            "name": "With custom fields",
            "data": {
                "title": "Test Quote - Custom Fields",
                "status": "draft",
                "quote_number": "PD-TEST-002",
                "pipedrive_deal_id": "TEST-001",
                "organization_name": "Test Organization"
            }
        }
    ]
    
    print("🧪 Testing Quote Creation Fields")
    print("=" * 60)
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        print(f"Data: {test_case['data']}")
        
        try:
            response = requests.post(
                "https://api.quoter.com/v1/quotes",
                json=test_case['data'],
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                quote = data.get("data", {})
                quote_id = quote.get("id")
                quote_number = quote.get("quote_number", "NOT SET")
                
                print(f"✅ Success! Quote ID: {quote_id}")
                print(f"   Quote Number: {quote_number}")
                print(f"   Response: {data}")
                
                # Try to modify the quote after creation
                if quote_id:
                    test_quote_modification(quote_id, access_token)
                
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)

def test_quote_modification(quote_id, access_token):
    """Test if we can modify a quote after creation"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔧 Testing quote modification for ID: {quote_id}")
    
    # Test updating quote number
    update_data = {
        "quote_number": f"PD-MODIFIED-{quote_id}"
    }
    
    try:
        response = requests.patch(
            f"https://api.quoter.com/v1/quotes/{quote_id}",
            json=update_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Quote modified successfully!")
            print(f"   Updated data: {data}")
        else:
            print(f"❌ Failed to modify quote: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error modifying quote: {e}")

def test_quote_schema():
    """Test what fields are available in the quote schema"""
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("\n🔍 Testing Quote Schema")
    print("=" * 60)
    
    # Try to get quote schema or create a minimal quote to see what fields are returned
    try:
        # Create a minimal quote first
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json={"title": "Schema Test", "status": "draft"},
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            quote = data.get("data", {})
            
            print(f"✅ Created test quote: {quote.get('id')}")
            print(f"\n📋 Available fields in quote response:")
            for key, value in quote.items():
                print(f"  {key}: {value} (type: {type(value)})")
            
            # Clean up - delete the test quote
            quote_id = quote.get('id')
            if quote_id:
                delete_response = requests.delete(
                    f"https://api.quoter.com/v1/quotes/{quote_id}",
                    headers=headers,
                    timeout=10
                )
                if delete_response.status_code == 200:
                    print(f"\n🗑️  Cleaned up test quote {quote_id}")
                else:
                    print(f"\n⚠️  Could not clean up test quote {quote_id}")
                    
        else:
            print(f"❌ Failed to create test quote: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🔍 Quote Numbering Research Tool")
    print("=" * 60)
    
    # Test 1: Quote creation with different fields
    test_quote_creation_fields()
    
    # Test 2: Quote schema exploration
    test_quote_schema()
    
    print("\n🎯 Research Complete!")
    print("Check the output above to see what fields are supported.")

if __name__ == "__main__":
    main()
