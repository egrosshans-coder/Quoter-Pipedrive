#!/usr/bin/env python3
"""
Add Instructional Line Item to Quote Template

This script adds a line item to the quote template with step-by-step instructions
for users to complete the draft quote and link it to Pipedrive.
"""

from quoter import get_access_token
import requests
import json

def add_instructional_line_item():
    """
    Add a line item with step-by-step instructions to the quote template.
    """
    print("📝 Adding Instructional Line Item to Quote Template")
    print("=" * 60)
    
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return False
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Template ID for the "test" template
    template_id = "tmpl_30O6JTDIbApan1B5gh9hF2w1tfL"
    
    # Step-by-step instructions for users
    instructions = """STEP-BY-STEP INSTRUCTIONS TO COMPLETE DRAFT QUOTE:

1. ORGANIZATION LINKING:
   • Go to the Organization field
   • Backspace/delete until the Pipedrive dropdown appears
   • Select the correct Pipedrive organization from the dropdown
   • This links the quote to the Pipedrive organization

2. DEAL/OPPORTUNITY LINKING:
   • In the Deal/Opportunity section, click the dropdown
   • Choose the correct deal from the list
   • This links the quote to the specific Pipedrive deal

3. OPTIONAL: ADD LINE ITEMS
   • Add any required products or services
   • Set quantities and prices as needed

4. PUBLISH QUOTE:
   • Review all information
   • Click "Publish" to finalize the quote

Note: The contact information has been automatically populated from Pipedrive."""
    
    # Line item data for the instructions
    line_item_data = {
        "template_id": template_id,
        "name": "📋 COMPLETION INSTRUCTIONS - READ BEFORE PUBLISHING",
        "description": instructions,
        "quantity": 1,
        "unit_price": 0.00,  # Free item - just for instructions
        "tax_rate": 0.00,
        "sort_order": 1  # Place at the top
    }
    
    try:
        print(f"📋 Adding instructional line item to template: {template_id}")
        print(f"📝 Instructions length: {len(instructions)} characters")
        
        # Add the line item to the template
        response = requests.post(
            "https://api.quoter.com/v1/quote_template_items",
            json=line_item_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            line_item_id = data.get("id")
            
            if line_item_id:
                print("✅ Successfully added instructional line item!")
                print(f"   Line Item ID: {line_item_id}")
                print(f"   Template: {template_id}")
                print(f"   Name: {line_item_data['name']}")
                print()
                print("📋 Instructions added to template:")
                print("-" * 40)
                print(instructions)
                print("-" * 40)
                print()
                print("🎯 Next steps:")
                print("   1. Check the template in Quoter UI")
                print("   2. Verify the instructional line item appears")
                print("   3. Test creating a new quote with this template")
                print("   4. Users will now see step-by-step completion guide")
                
                return True
            else:
                print("❌ No line item ID in response")
                print(f"Response: {data}")
                return False
        else:
            print(f"❌ Failed to add line item: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error adding line item: {e}")
        return False

def main():
    """
    Main function to add the instructional line item.
    """
    try:
        success = add_instructional_line_item()
        if success:
            print("\n🎉 Instructional line item successfully added to template!")
        else:
            print("\n❌ Failed to add instructional line item")
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
