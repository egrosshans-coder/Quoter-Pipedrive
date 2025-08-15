#!/usr/bin/env python3
"""
Deep dive into Quoter's Pipedrive integration to understand how to properly create quotes.
"""

from quoter import get_access_token
import requests
import json

def deep_dive_pipedrive():
    """Deep dive into Pipedrive integration"""
    print("🔍 Deep Dive into Quoter's Pipedrive Integration")
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
    
    # 1. Examine Pipedrive contacts
    print("📋 1. Examining Pipedrive Contacts")
    print("-" * 40)
    
    try:
        response = requests.get(
            f"{base_url}/contacts",
            headers=headers,
            params={"source": "pipedrive"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            contacts = data.get("data", [])
            print(f"✅ Found {len(contacts)} Pipedrive contacts")
            
            for i, contact in enumerate(contacts):
                print(f"\n   Contact {i+1}:")
                print(f"   📋 All fields:")
                for key, value in contact.items():
                    print(f"      {key}: {value}")
                    
        else:
            print(f"❌ Failed to get Pipedrive contacts: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting Pipedrive contacts: {e}")
    
    print("\n" + "=" * 60)
    
    # 2. Examine quotes with Pipedrive data
    print("📋 2. Examining Quotes with Pipedrive Data")
    print("-" * 40)
    
    try:
        response = requests.get(
            f"{base_url}/quotes",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get("data", [])
            print(f"✅ Found {len(quotes)} quotes")
            
            # Find quotes with pipedrive_deal_id
            pipedrive_quotes = [q for q in quotes if q.get("pipedrive_deal_id")]
            print(f"🎯 Found {len(pipedrive_quotes)} quotes with Pipedrive deal IDs")
            
            if pipedrive_quotes:
                print(f"\n   First Pipedrive quote details:")
                quote = pipedrive_quotes[0]
                print(f"   📋 All fields:")
                for key, value in quote.items():
                    print(f"      {key}: {value}")
                    
                # Show the pipedrive_deal_id specifically
                deal_id = quote.get("pipedrive_deal_id")
                print(f"\n   🎯 Pipedrive Deal ID: {deal_id}")
                
                # Check if this matches our test deal (2096)
                if deal_id == "2096":
                    print(f"   🎉 This is OUR test quote!")
                else:
                    print(f"   📝 This is a different Pipedrive deal")
                    
        else:
            print(f"❌ Failed to get quotes: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting quotes: {e}")
    
    print("\n" + "=" * 60)
    
    # 3. Test creating a quote with proper Pipedrive data
    print("📋 3. Testing Quote Creation with Pipedrive Data")
    print("-" * 40)
    
    # Get required fields first
    try:
        # Get a contact
        response = requests.get(
            f"{base_url}/contacts",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            contacts = data.get("data", [])
            if contacts:
                contact = contacts[0]
                contact_id = contact.get("id")
                print(f"✅ Using contact ID: {contact_id}")
                
                # Get a template
                response = requests.get(
                    f"{base_url}/quote_templates",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    templates = data.get("data", [])
                    if templates:
                        template = templates[0]
                        template_id = template.get("id")
                        print(f"✅ Using template ID: {template_id}")
                        
                        # Now test creating a quote with pipedrive_deal_id
                        print(f"\n   🧪 Testing quote creation with Pipedrive data...")
                        
                        quote_data = {
                            "contact_id": contact_id,
                            "template_id": template_id,
                            "currency_abbr": "USD",
                            "title": "Test Quote with Pipedrive Integration",
                            "pipedrive_deal_id": "TEST-2096",  # Test deal ID
                            "custom_number": "PD-TEST-2096"  # Custom quote number
                        }
                        
                        print(f"   📋 Quote data:")
                        for key, value in quote_data.items():
                            print(f"      {key}: {value}")
                        
                        # Try to create the quote
                        response = requests.post(
                            f"{base_url}/quotes",
                            headers=headers,
                            json=quote_data,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            print(f"\n   ✅ Quote created successfully!")
                            print(f"   🎯 Quote ID: {data.get('id', 'N/A')}")
                            print(f"   🎯 Pipedrive Deal ID: {data.get('pipedrive_deal_id', 'N/A')}")
                            print(f"   🎯 Custom Number: {data.get('custom_number', 'N/A')}")
                            
                            # Show all response data
                            print(f"   📋 Full response:")
                            for key, value in data.items():
                                print(f"      {key}: {value}")
                                
                        elif response.status_code == 422:
                            data = response.json()
                            print(f"\n   ❌ Validation error: {response.status_code}")
                            print(f"   📋 Error details:")
                            for key, value in data.items():
                                print(f"      {key}: {value}")
                        else:
                            print(f"\n   ❌ Failed to create quote: {response.status_code}")
                            print(f"   📋 Response: {response.text}")
                            
                    else:
                        print(f"❌ No templates found")
                else:
                    print(f"❌ Failed to get templates: {response.status_code}")
            else:
                print(f"❌ No contacts found")
        else:
            print(f"❌ Failed to get contacts: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing quote creation: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Deep Dive Complete!")
    print("Check the output above to understand the Pipedrive integration structure.")

if __name__ == "__main__":
    deep_dive_pipedrive()
