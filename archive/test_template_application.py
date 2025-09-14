#!/usr/bin/env python3
"""
Test script to see if Quoter API actually applies templates during quote creation.
"""

import requests
import json
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token, create_or_find_contact_in_quoter
from utils.logger import logger

def test_template_application():
    """
    Test if different template_id values actually result in different templates being applied.
    """
    print("🧪 Testing Template Application in Quoter API")
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
    
    # Get a test contact
    contact_id = create_or_find_contact_in_quoter(
        contact_name="Test Contact",
        contact_email="test@example.com",
        organization_name="Test Org"
    )
    
    if not contact_id:
        print("❌ Failed to create test contact")
        return False
    
    print(f"✅ Using test contact: {contact_id}")
    
    # Test with different templates
    test_templates = [
        ("Basic", "tmpl_30O6JTDIbApan1B5gh9hF2w1tfL"),
        ("Robotics", "tmpl_329qcsv6mx0upqqLkXFkEZZi92O"),
        ("Tank Delivery", "tmpl_31vLnIjRObApRldxGd7V3LSuEd8")
    ]
    
    created_quotes = []
    
    for template_name, template_id in test_templates:
        print(f"\n🔍 Testing template: {template_name} (ID: {template_id})")
        
        quote_data = {
            "contact_id": contact_id,
            "template_id": template_id,
            "currency_abbr": "USD",
            "name": f"Test Quote - {template_name}"
        }
        
        print(f"📤 Sending quote data:")
        print(f"   {json.dumps(quote_data, indent=2)}")
        
        try:
            response = requests.post(
                "https://api.quoter.com/v1/quotes",
                json=quote_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                quote_id = data.get("id")
                
                if quote_id:
                    print(f"✅ Quote created: {quote_id}")
                    print(f"   URL: {data.get('url', 'N/A')}")
                    
                    # Store for comparison
                    created_quotes.append({
                        "template_name": template_name,
                        "template_id": template_id,
                        "quote_id": quote_id,
                        "quote_data": data
                    })
                else:
                    print(f"❌ No quote ID in response")
            else:
                print(f"❌ Failed to create quote: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating quote: {e}")
    
    # Now let's check what templates were actually applied
    print(f"\n🔍 Checking what templates were actually applied...")
    print("=" * 60)
    
    for quote in created_quotes:
        quote_id = quote["quote_id"]
        template_name = quote["template_name"]
        
        print(f"\n📋 Checking quote {quote_id} (should be {template_name}):")
        
        try:
            # Get the quote details to see what template is actually applied
            response = requests.get(
                f"https://api.quoter.com/v1/quotes/{quote_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                quote_details = response.json()
                
                # Look for template information in the response
                template_info = quote_details.get("template", {})
                template_title = template_info.get("title", "Unknown")
                template_id_actual = template_info.get("id", "Unknown")
                
                print(f"   Expected: {template_name}")
                print(f"   Actual:   {template_title}")
                print(f"   Template ID: {template_id_actual}")
                
                if template_title == template_name:
                    print(f"   ✅ Template applied correctly!")
                else:
                    print(f"   ❌ Template NOT applied correctly!")
                    
            else:
                print(f"   ❌ Failed to get quote details: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error getting quote details: {e}")
    
    print(f"\n📊 SUMMARY:")
    print("=" * 60)
    print("Check the quotes in Quoter to see if they actually have different templates.")
    print("If they all look the same, then the template_id field is being ignored.")
    
    return True

if __name__ == "__main__":
    test_template_application()

