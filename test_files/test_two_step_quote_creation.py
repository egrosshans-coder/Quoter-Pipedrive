#!/usr/bin/env python3
"""
Test Two-Step Quote Creation Workflow

This script demonstrates the correct Quoter API workflow:
1. Create draft quote (POST /v1/quotes)
2. Add instructional line item (POST /v1/line_items)
"""

from quoter import get_access_token
import requests
import json

def test_two_step_quote_creation():
    """
    Test the correct two-step quote creation workflow.
    """
    print("🧪 Testing Two-Step Quote Creation Workflow")
    print("=" * 60)
    print("Goal: Create quote then add instructional line item")
    print()
    
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Step 1: Create the draft quote
    print("📝 STEP 1: Creating draft quote...")
    print("-" * 40)
    
    # Get a contact ID first
    contacts_response = requests.get('https://api.quoter.com/v1/contacts', headers=headers)
    if contacts_response.status_code != 200:
        print(f"❌ Failed to get contacts: {contacts_response.status_code}")
        return False
    
    contacts_data = contacts_response.json()
    if not contacts_data.get('data'):
        print("❌ No contacts found")
        return False
    
    contact_id = contacts_data['data'][0]['id']
    print(f"📞 Using contact ID: {contact_id}")
    
    # Get template ID
    template_response = requests.get('https://api.quoter.com/v1/quote_templates', headers=headers)
    if template_response.status_code != 200:
        print(f"❌ Failed to get templates: {template_response.status_code}")
        return False
    
    template_data = template_response.json()
    if not template_data.get('data'):
        print("❌ No templates found")
        return False
    
    # Look for "test" template
    template_id = None
    for template in template_data['data']:
        if template.get('title') == 'test':
            template_id = template['id']
            break
    
    if not template_id:
        print("❌ 'test' template not found")
        return False
    
    print(f"📋 Using template ID: {template_id}")
    
    # Create the quote (without items)
    quote_data = {
        "contact_id": contact_id,
        "template_id": template_id,
        "currency_abbr": "USD",
        "name": "Two-Step API Test Quote"
    }
    
    print(f"📤 Creating quote with data: {json.dumps(quote_data, indent=2)}")
    
    create_response = requests.post('https://api.quoter.com/v1/quotes', 
                                  headers=headers, json=quote_data)
    
    if create_response.status_code not in [200, 201]:
        print(f"❌ Failed to create quote: {create_response.status_code}")
        print(f"   Error: {create_response.text[:200]}")
        return False
    
    quote_result = create_response.json()
    quote_id = quote_result.get('id')
    
    if not quote_id:
        print("❌ No quote ID in response")
        return False
    
    print(f"✅ SUCCESS! Draft quote created:")
    print(f"   Quote ID: {quote_id}")
    print(f"   Name: {quote_result.get('name', 'N/A')}")
    print(f"   URL: {quote_result.get('url', 'N/A')}")
    print()
    
    # Step 2: Add the existing instructional line item
    print("📋 STEP 2: Adding existing instructional line item...")
    print("-" * 40)
    
    # Use the existing instructional item from Quoter
    existing_item_id = "item_31IIdw4C1GHIwU05yhnZ2B88S2B"
    print(f"📋 Using existing instructional item: {existing_item_id}")
    
    # Get the full item details to include description
    item_response = requests.get(f'https://api.quoter.com/v1/items/{existing_item_id}', headers=headers)
    if item_response.status_code == 200:
        item_data = item_response.json()
        item_name = item_data.get('name', '01-Draft Quote-Instructions (delete before sending quote)')
        item_category = item_data.get('category', 'DJ')
        item_description = item_data.get('description', '')
        
        print(f"📋 Retrieved item details:")
        print(f"   Name: {item_name}")
        print(f"   Category: {item_category}")
        print(f"   Description length: {len(item_description)} characters")
        print()
        
        line_item_data = {
            "quote_id": quote_id,
            "item_id": existing_item_id,  # Reference existing item
            "name": item_name,  # Include name from existing item
            "category": item_category,  # Include category from existing item
            "description": item_description,  # Include full description from existing item
            "quantity": 1,
            "unit_price": 1.00  # Include unit cost from existing item
        }
    else:
        print(f"❌ Failed to get item details: {item_response.status_code}")
        return False
    
    print(f"📤 Adding line item with data: {json.dumps(line_item_data, indent=2)}")
    
    line_item_response = requests.post('https://api.quoter.com/v1/line_items', 
                                     headers=headers, json=line_item_data)
    
    if line_item_response.status_code not in [200, 201]:
        print(f"❌ Failed to add line item: {line_item_response.status_code}")
        print(f"   Error: {line_item_response.text[:200]}")
        return False
    
    line_item_result = line_item_response.json()
    line_item_id = line_item_result.get('id')
    
    if not line_item_id:
        print("❌ No line item ID in response")
        return False
    
    print(f"✅ SUCCESS! Instructional line item added:")
    print(f"   Line Item ID: {line_item_id}")
    print(f"   Name: {line_item_result.get('name', 'N/A')}")
    print()
    
    # Final result
    print("🎉 TWO-STEP WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📋 Final Quote: {quote_result.get('url', 'N/A')}")
    print(f"📝 Instructional Item: {line_item_result.get('name', 'N/A')}")
    print()
    print("🔍 Next steps:")
    print("   1. Check the quote in Quoter UI")
    print("   2. Verify the instructional line item is visible")
    print("   3. Confirm this is the correct workflow")
    
    return True

if __name__ == "__main__":
    test_two_step_quote_creation()
