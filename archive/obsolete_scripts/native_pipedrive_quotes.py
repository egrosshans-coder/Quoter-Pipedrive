#!/usr/bin/env python3
"""
Native Pipedrive Integration for Quote Creation
Uses Quoter's built-in Pipedrive integration to create quotes properly.
"""

from pipedrive import get_sub_organizations_ready_for_quotes, get_organization_by_id, get_deal_by_id
from quoter import get_access_token, get_quote_required_fields
import requests
import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

def find_pipedrive_contact_in_quoter(organization_name, deal_id):
    """
    Search Quoter for a Pipedrive contact that matches the organization.
    
    Args:
        organization_name (str): Name of the organization (e.g., "Blue Owl Capital-2096")
        deal_id (str): Pipedrive deal ID
    
    Returns:
        dict: Contact data if found, None otherwise
    """
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth access token")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Search for Pipedrive contacts
    try:
        response = requests.get(
            "https://api.quoter.com/v1/contacts",
            headers=headers,
            params={"source": "pipedrive"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            contacts = data.get("data", [])
            
            logger.info(f"Found {len(contacts)} Pipedrive contacts in Quoter")
            
            # Look for a contact that matches our organization
            # Strategy: Look for contacts with matching organization name or deal ID
            for contact in contacts:
                contact_org = contact.get("organization", "")
                contact_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                
                # Check if organization name contains the contact's organization
                if contact_org and contact_org.lower() in organization_name.lower():
                    logger.info(f"✅ Found matching contact: {contact_name} ({contact_org})")
                    return contact
                
                # Check if contact name appears in organization name
                if contact_name and contact_name.lower() in organization_name.lower():
                    logger.info(f"✅ Found matching contact: {contact_name} ({contact_org})")
                    return contact
            
            logger.warning(f"❌ No matching Pipedrive contact found for: {organization_name}")
            return None
            
        else:
            logger.error(f"Failed to get Pipedrive contacts: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error searching for Pipedrive contacts: {e}")
        return None

def create_quote_with_pipedrive_contact(deal_id, organization_name, deal_title, contact_id):
    """
    Create a quote using a specific Pipedrive contact ID.
    
    Args:
        deal_id (str): Pipedrive deal ID
        organization_name (str): Organization name
        deal_title (str): Deal title
        contact_id (str): Quoter contact ID
    
    Returns:
        dict: Quote data if created, None otherwise
    """
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth access token")
        return None
    
    # Get required fields for quote creation
    required_fields = get_quote_required_fields(access_token)
    if not required_fields:
        logger.error("Failed to get required fields for quote creation")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Prepare quote data using the specific contact ID
    quote_data = {
        "contact_id": contact_id,  # Use the Pipedrive contact ID
        "template_id": required_fields["template_id"],
        "currency_abbr": required_fields["currency_abbr"],
        "title": deal_title or f"Quote for {organization_name} - Deal {deal_id}",
        "pipedrive_deal_id": str(deal_id),  # Link to Pipedrive deal
        "custom_number": f"PD-{deal_id}"  # Custom quote number
    }
    
    logger.info(f"Creating quote with Pipedrive contact: {contact_id}")
    logger.info(f"Quote data: {quote_data}")
    
    try:
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            headers=headers,
            json=quote_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Quote created successfully!")
            logger.info(f"   Quote ID: {data.get('id', 'N/A')}")
            logger.info(f"   Pipedrive Deal ID: {data.get('pipedrive_deal_id', 'N/A')}")
            logger.info(f"   Custom Number: {data.get('custom_number', 'N/A')}")
            logger.info(f"   URL: {data.get('url', 'N/A')}")
            return data
            
        elif response.status_code == 422:
            data = response.json()
            logger.error(f"❌ Validation error: {response.status_code}")
            logger.error(f"   Error details: {data}")
            return None
        else:
            logger.error(f"❌ Failed to create quote: {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating quote: {e}")
        return None

def process_ready_organizations_with_pipedrive():
    """
    Process organizations ready for quotes using native Pipedrive integration.
    """
    print("🎯 Processing Organizations with Native Pipedrive Integration")
    print("=" * 60)
    
    # Get organizations ready for quotes
    print("📋 Step 1: Getting organizations ready for quotes...")
    ready_orgs = get_sub_organizations_ready_for_quotes()
    
    if not ready_orgs:
        print("❌ No organizations ready for quotes")
        return
    
    print(f"✅ Found {len(ready_orgs)} organizations ready for quotes")
    print()
    
    # Process each organization
    successful_quotes = 0
    failed_quotes = 0
    no_contact_found = 0
    
    for i, org in enumerate(ready_orgs[:5]):  # Process first 5 for testing
        org_id = org.get("id")
        org_name = org.get("name", "Unknown")
        deal_id = org.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")  # Deal_ID custom field
        
        print(f"📋 Processing organization {i+1}/{min(5, len(ready_orgs))}: {org_name}")
        print(f"   Organization ID: {org_id}")
        print(f"   Deal ID: {deal_id}")
        
        if not deal_id:
            print(f"   ❌ No Deal ID found, skipping")
            failed_quotes += 1
            continue
        
        # Get deal details
        deal = get_deal_by_id(deal_id)
        if deal:
            deal_title = deal.get("title", f"Deal {deal_id}")
            print(f"   Deal Title: {deal_title}")
        else:
            deal_title = f"Deal {deal_id}"
            print(f"   Deal Title: Unknown (using default)")
        
        # Step 2: Find matching Pipedrive contact in Quoter
        print(f"   🔍 Searching for Pipedrive contact...")
        contact = find_pipedrive_contact_in_quoter(org_name, deal_id)
        
        if not contact:
            print(f"   ❌ No Pipedrive contact found, skipping")
            no_contact_found += 1
            continue
        
        contact_id = contact.get("id")
        contact_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        print(f"   ✅ Found contact: {contact_name} (ID: {contact_id})")
        
        # Step 3: Create quote using the Pipedrive contact
        print(f"   📝 Creating quote...")
        result = create_quote_with_pipedrive_contact(deal_id, org_name, deal_title, contact_id)
        
        if result:
            print(f"   🎉 Quote created successfully!")
            successful_quotes += 1
        else:
            print(f"   ❌ Failed to create quote")
            failed_quotes += 1
        
        print()
    
    # Summary
    print("📊 Processing Summary")
    print("=" * 60)
    print(f"✅ Successful quotes: {successful_quotes}")
    print(f"❌ Failed quotes: {failed_quotes}")
    print(f"⚠️  No contact found: {no_contact_found}")
    print(f"📋 Total processed: {min(5, len(ready_orgs))}")
    
    if successful_quotes > 0:
        print(f"\n🎯 Success! Created {successful_quotes} quotes using native Pipedrive integration.")
        print("Check your Quoter admin panel to see the properly linked quotes!")
    else:
        print(f"\n❌ No quotes were created successfully.")
        print("This suggests we need to investigate the Pipedrive contact matching logic.")

if __name__ == "__main__":
    process_ready_organizations_with_pipedrive()

