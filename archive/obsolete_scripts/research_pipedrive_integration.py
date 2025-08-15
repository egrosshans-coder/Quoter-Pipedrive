#!/usr/bin/env python3
"""
Research script to explore Quoter API endpoints for Pipedrive integration.
This will help us find the proper way to create quotes using Pipedrive contacts and deals.
"""

from quoter import get_access_token
import requests
import json

def research_pipedrive_integration():
    """Research Quoter API endpoints for Pipedrive integration"""
    print("🔍 Researching Quoter API for Pipedrive Integration")
    print("=" * 60)
    
    # Get OAuth token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth access token")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://api.quoter.com/v1"
    
    # List of endpoints to research
    endpoints_to_test = [
        # Core endpoints
        "/contacts",
        "/organizations", 
        "/quotes",
        "/quote_templates",
        
        # Pipedrive-specific endpoints (hypothetical)
        "/pipedrive/contacts",
        "/pipedrive/deals",
        "/pipedrive/organizations",
        "/integrations/pipedrive",
        
        # Alternative naming patterns
        "/external_contacts",
        "/external_deals",
        "/external_organizations",
        "/sync/pipedrive",
        
        # Quote creation with external data
        "/quotes/create_with_pipedrive",
        "/quotes/create_from_deal",
        "/quotes/create_from_contact"
    ]
    
    print("📋 Testing potential Pipedrive integration endpoints...")
    print()
    
    working_endpoints = []
    
    for endpoint in endpoints_to_test:
        full_url = f"{base_url}{endpoint}"
        print(f"🔍 Testing: {endpoint}")
        
        try:
            response = requests.get(full_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 200 OK - Found endpoint!")
                
                # Check if it contains Pipedrive-related data
                response_text = json.dumps(data, indent=2)
                if "pipedrive" in response_text.lower():
                    print(f"   🎯 Contains Pipedrive data!")
                
                # Show structure
                if isinstance(data, dict):
                    keys = list(data.keys())
                    print(f"   📋 Response keys: {keys[:5]}{'...' if len(keys) > 5 else ''}")
                    
                    # Check for data array
                    if "data" in data and isinstance(data["data"], list):
                        print(f"   📊 Data count: {len(data['data'])}")
                        if data["data"]:
                            first_item = data["data"][0]
                            if isinstance(first_item, dict):
                                item_keys = list(first_item.keys())
                                print(f"   🔑 First item keys: {item_keys[:5]}{'...' if len(item_keys) > 5 else ''}")
                
                working_endpoints.append(endpoint)
                print()
                
            elif response.status_code == 404:
                print(f"   ❌ 404 Not Found")
            elif response.status_code == 403:
                print(f"   ⚠️  403 Forbidden (might exist but no access)")
            else:
                print(f"   ⚠️  {response.status_code} - {response.text[:100]}{'...' if len(response.text) > 100 else ''}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
    
    # Now test specific Pipedrive integration scenarios
    print("🎯 Testing Pipedrive Integration Scenarios")
    print("=" * 60)
    
    # Test 1: Can we search for Pipedrive contacts?
    print("📋 Test 1: Searching for Pipedrive contacts...")
    try:
        # Try to get contacts with Pipedrive filter
        response = requests.get(
            f"{base_url}/contacts",
            headers=headers,
            params={"source": "pipedrive"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Found contacts with Pipedrive source filter")
            contacts = data.get("data", [])
            print(f"   📊 Contact count: {len(contacts)}")
            
            # Look for Pipedrive-related fields
            if contacts:
                first_contact = contacts[0]
                contact_keys = list(first_contact.keys())
                pipedrive_fields = [k for k in contact_keys if "pipedrive" in k.lower()]
                if pipedrive_fields:
                    print(f"   🎯 Pipedrive fields found: {pipedrive_fields}")
                    
        else:
            print(f"   ❌ Pipedrive source filter not supported: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing Pipedrive source filter: {e}")
    
    print()
    
    # Test 2: Can we create quotes with Pipedrive deal IDs?
    print("📋 Test 2: Testing quote creation with Pipedrive data...")
    try:
        # Try to get quote creation schema
        response = requests.get(
            f"{base_url}/quotes",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get("data", [])
            if quotes:
                first_quote = quotes[0]
                quote_keys = list(first_quote.keys())
                
                # Look for Pipedrive-related fields
                pipedrive_fields = [k for k in quote_keys if "pipedrive" in k.lower()]
                if pipedrive_fields:
                    print(f"   🎯 Pipedrive fields in quotes: {pipedrive_fields}")
                else:
                    print(f"   ⚠️  No Pipedrive fields found in quotes")
                    
                # Show all fields for reference
                print(f"   📋 All quote fields: {quote_keys}")
                
        else:
            print(f"   ❌ Could not get quotes: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing quote creation: {e}")
    
    print()
    
    # Summary
    print("📊 Research Summary")
    print("=" * 60)
    print(f"✅ Working endpoints found: {len(working_endpoints)}")
    for endpoint in working_endpoints:
        print(f"   - {endpoint}")
    
    print()
    print("🎯 Next Steps:")
    print("1. Review the working endpoints above")
    print("2. Check if any contain Pipedrive integration data")
    print("3. Test quote creation with Pipedrive contact/deal IDs")
    print("4. Look for API documentation on Pipedrive integration")

if __name__ == "__main__":
    research_pipedrive_integration()
