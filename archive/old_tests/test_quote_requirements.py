#!/usr/bin/env python3
"""
Test script to get required fields for quote creation and test quote numbering.
"""

from quoter import get_access_token
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_required_fields():
    """Get the required fields for quote creation"""
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Getting Required Fields for Quote Creation")
    print("=" * 60)
    
    # Get contacts (for contact_id)
    try:
        response = requests.get(
            "https://api.quoter.com/v1/contacts",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            contacts = data.get("data", [])
            if contacts:
                contact_id = contacts[0].get("id")
                print(f"✅ Found contact: ID {contact_id}")
            else:
                print("❌ No contacts found")
                return None
        else:
            print(f"❌ Failed to get contacts: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting contacts: {e}")
        return None
    
    # Try different template endpoints
    template_id = None
    template_endpoints = [
        "https://api.quoter.com/v1/templates",
        "https://api.quoter.com/v1/quote_templates",
        "https://api.quoter.com/v1/quote-templates"
    ]
    
    for endpoint in template_endpoints:
        try:
            print(f"🔍 Trying template endpoint: {endpoint}")
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                templates = data.get("data", [])
                if templates:
                    template_id = templates[0].get("id")
                    print(f"✅ Found template: ID {template_id} from {endpoint}")
                    break
                else:
                    print(f"⚠️  No templates found in {endpoint}")
            else:
                print(f"⚠️  Endpoint {endpoint} returned {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Error with {endpoint}: {e}")
    
    if not template_id:
        print("❌ Could not find any templates. Trying to create quote without template...")
        # We'll try to create a quote without template_id to see what happens
    
    # Default currency
    currency_abbr = "USD"
    print(f"✅ Using currency: {currency_abbr}")
    
    return {
        "contact_id": contact_id,
        "template_id": template_id,
        "currency_abbr": currency_abbr
    }

def test_quote_creation_with_required_fields(required_fields):
    """Test quote creation with required fields and custom numbering"""
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🧪 Testing Quote Creation with Required Fields")
    print("=" * 60)
    
    # Test different field combinations
    test_cases = []
    
    # Basic required fields
    basic_data = {
        "contact_id": required_fields["contact_id"],
        "currency_abbr": required_fields["currency_abbr"]
    }
    
    # Add template_id if we have it
    if required_fields["template_id"]:
        basic_data["template_id"] = required_fields["template_id"]
    
    test_cases.append({
        "name": "Required fields only",
        "data": basic_data
    })
    
    # Test with quote_number
    test_cases.append({
        "name": "With quote_number field",
        "data": {**basic_data, "quote_number": "PD-TEST-001"}
    })
    
    # Test with title
    test_cases.append({
        "name": "With title and custom fields",
        "data": {**basic_data, "title": "Test Quote - Custom Number", "quote_number": "PD-TEST-002"}
    })
    
    created_quotes = []
    
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
                
                created_quotes.append(quote_id)
                
                # Try to modify the quote after creation
                if quote_id:
                    test_quote_modification(quote_id, access_token)
                
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
    
    return created_quotes

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

def cleanup_test_quotes(quote_ids, access_token):
    """Clean up test quotes"""
    if not quote_ids:
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🗑️  Cleaning up {len(quote_ids)} test quotes...")
    
    for quote_id in quote_ids:
        try:
            response = requests.delete(
                f"https://api.quoter.com/v1/quotes/{quote_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Deleted quote {quote_id}")
            else:
                print(f"❌ Failed to delete quote {quote_id}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error deleting quote {quote_id}: {e}")

def main():
    print("🔍 Quote Requirements and Numbering Research Tool")
    print("=" * 60)
    
    # Step 1: Get required fields
    required_fields = get_required_fields()
    if not required_fields:
        print("❌ Could not get required fields. Exiting.")
        return
    
    # Step 2: Test quote creation with required fields
    created_quotes = test_quote_creation_with_required_fields(required_fields)
    
    # Step 3: Clean up test quotes
    if created_quotes:
        access_token = get_access_token()
        if access_token:
            cleanup_test_quotes(created_quotes, access_token)
    
    print("\n🎯 Research Complete!")
    print("Check the output above to see what fields are supported for quote numbering.")

if __name__ == "__main__":
    main()
