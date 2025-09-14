#!/usr/bin/env python3
"""
Complete test script to create a draft quote with "Basic" template.
This includes proper person data and organization setup.
"""

import sys
import os
import json

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import create_comprehensive_quote_from_pipedrive

def test_basic_template_quote_complete():
    """
    Test creating a quote with the "Basic" template using complete data.
    """
    print("🧪 Testing Basic Template Quote Creation (Complete)")
    print("=" * 60)
    
    # Mock organization data (simulating Pipedrive webhook)
    organization_data = {
        "id": "9999",
        "name": "Test-Basic-Template-9999",
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": "9999"  # Deal ID field
    }
    
    # Mock deal data with "Basic" template selected (enum value 441)
    # Include person data to make quote creation work
    deal_data = {
        "id": "9999",
        "title": "Test Basic Template Deal",
        "15034cf07d05ceb15f0a89dcbdcc4f596348584e": "9999",  # Deal ID field
        "42ab0c919271cb24f3587f0b01ea2af166019c8d": "441",   # Template field - Basic template
        "person_id": {
            "value": "12345",
            "name": "John Test"
        },
        "person_data": {
            "id": "12345",
            "name": "John Test",
            "email": "john.test@example.com",
            "phone": "555-123-4567",
            "organization": {
                "id": "9999",
                "name": "Test-Basic-Template-9999"
            }
        }
    }
    
    print(f"📋 Organization: {organization_data['name']}")
    print(f"📋 Deal: {deal_data['title']}")
    print(f"📋 Template: Basic (enum: 441)")
    print(f"📋 Person: {deal_data['person_data']['name']}")
    print(f"📋 Email: {deal_data['person_data']['email']}")
    print()
    
    try:
        # Create the quote using the same function the webhook uses
        quote_data = create_comprehensive_quote_from_pipedrive(organization_data, deal_data)
        
        if quote_data:
            print("✅ Quote created successfully!")
            print(f"   Quote ID: {quote_data.get('id')}")
            print(f"   Quote Name: {quote_data.get('name', 'N/A')}")
            print(f"   Quote Number: {quote_data.get('number', 'N/A')}")
            print(f"   Template ID: {quote_data.get('template_id', 'N/A')}")
            print(f"   Contact ID: {quote_data.get('person', {}).get('public_id', 'N/A')}")
            print()
            print("🎯 Check Quoter to see if the Basic template was applied!")
            print("   The quote should have:")
            print("   ✅ Basic template cover page")
            print("   ✅ Basic template cover letter")
            print("   ✅ Basic template terms & conditions")
            print("   ❌ No line items (need to be added manually)")
            return True
        else:
            print("❌ Quote creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating quote: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Complete Basic Template Quote Test")
    print()
    
    success = test_basic_template_quote_complete()
    
    if success:
        print("🎉 Test succeeded!")
        print("Check Quoter to see if the Basic template was applied to the quote.")
    else:
        print("❌ Test failed")

