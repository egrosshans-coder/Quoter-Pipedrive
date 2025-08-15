#!/usr/bin/env python3
"""
Simplified Quote Creator - Using Quoter's Native Pipedrive Integration
"""

import os
import json
import requests
from dotenv import load_dotenv
from quoter import get_access_token
from pipedrive import get_deal_by_id, get_organization_by_id
from utils.logger import logger

load_dotenv()

def is_organization_ready_for_quote(organization):
    """
    Check if organization meets all requirements for quote creation.
    Works for any owner, not just Maurice.
    
    Args:
        organization (dict): Organization data from Pipedrive
        
    Returns:
        bool: True if ready for quote creation, False otherwise
    """
    # Check HID-QBO-Status (must be QBO-SubCust)
    hid_status = organization.get("454a3767bce03a880b31d78a38c480d6870e0f1b")
    if hid_status != 289:  # 289 = QBO-SubCust
        logger.debug(f"Organization {organization.get('id')} not ready for quotes (status: {hid_status})")
        return False
    
    # Check Deal_ID field
    deal_id = organization.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")
    if not deal_id:
        logger.debug(f"Organization {organization.get('id')} has no associated deal ID")
        return False
    
    # Check QBO integration fields (optional but recommended)
    qbo_subcust_id = organization.get("4024")  # QuickBooks Id : SyncQ
    qbo_cust_id = organization.get("4024")  # QuickBooks Id : SyncQ
    
    if not qbo_subcust_id or not qbo_cust_id:
        logger.warning(f"Organization {organization.get('id')} missing QBO integration fields")
        # Continue anyway - these are optional for quote creation
    
    owner_name = organization.get("owner_id", {}).get("name", "Unknown")
    logger.info(f"Organization {organization.get('id')} ({organization.get('name')}) ready for quote creation (owner: {owner_name})")
    return True

def create_quote_from_pipedrive_deal(deal_id, organization_id=None):
    """
    Create a quote in Quoter using Pipedrive deal ID.
    Leverages Quoter's native Pipedrive integration.
    
    Args:
        deal_id (str): Pipedrive deal ID
        organization_id (str, optional): Pipedrive organization ID
        
    Returns:
        dict: Quote data if created successfully, None otherwise
    """
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth token for quote creation")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get deal information from Pipedrive
    deal_data = get_deal_by_id(deal_id)
    if not deal_data:
        logger.error(f"Could not find deal {deal_id} in Pipedrive")
        return None
    
    # Get organization information if provided
    organization_data = None
    if organization_id:
        organization_data = get_organization_by_id(organization_id)
    
    # Prepare quote data using Quoter's native integration
    quote_data = {
        "title": f"Quote for {deal_data.get('title', f'Deal {deal_id}')}",
        "status": "draft",
        "pipedrive_deal_id": str(deal_id),
        "pipedrive_organization_id": str(organization_id) if organization_id else None,
        # Let Quoter handle the Pipedrive integration automatically
        "use_pipedrive_integration": True
    }
    
    try:
        logger.info(f"Creating quote for Pipedrive deal {deal_id} using native integration")
        
        # Use Quoter's API to create quote with Pipedrive integration
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json=quote_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            quote = data.get("data", {})
            quote_id = quote.get("id")
            
            if quote_id:
                logger.info(f"✅ Successfully created quote {quote_id} for Pipedrive deal {deal_id}")
                logger.info(f"📋 Quote will be associated with Pipedrive deal automatically")
                return quote
            else:
                logger.error(f"❌ No quote ID in response: {data}")
                return None
        else:
            logger.error(f"❌ Failed to create quote: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error creating quote: {e}")
        return None

def check_existing_quote_for_deal(deal_id):
    """
    Check if a quote already exists for the given Pipedrive deal ID.
    
    Args:
        deal_id (str): Pipedrive deal ID
        
    Returns:
        dict: Existing quote data if found, None otherwise
    """
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth token for quote check")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Search for quotes with the given Pipedrive deal ID
        response = requests.get(
            f"https://api.quoter.com/v1/quotes?pipedrive_deal_id={deal_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get("data", [])
            
            if quotes:
                existing_quote = quotes[0]  # Get the first (most recent) quote
                logger.info(f"Found existing quote {existing_quote.get('id')} for deal {deal_id}")
                return existing_quote
            else:
                logger.debug(f"No existing quote found for deal {deal_id}")
                return None
        else:
            logger.error(f"Failed to check for existing quotes: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking for existing quotes: {e}")
        return None

def create_quote_for_sub_organization(organization_id):
    """
    Create a quote for a sub-organization that's ready for quotes.
    Uses Quoter's native Pipedrive integration.
    Prevents duplicate quote creation by checking for existing quotes for the deal.
    
    Args:
        organization_id (str): Pipedrive organization ID
        
    Returns:
        dict: Quote data if created successfully, None otherwise
    """
    # Get organization information
    organization_data = get_organization_by_id(organization_id)
    if not organization_data:
        logger.error(f"Could not find organization {organization_id}")
        return None
    
    # Validate organization is ready for quote creation
    if not is_organization_ready_for_quote(organization_data):
        logger.error(f"Organization {organization_id} not ready for quote creation")
        return None
    
    # Get the associated deal ID
    deal_id = organization_data.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")  # Deal_ID field
    if not deal_id:
        logger.error(f"Organization {organization_id} has no associated deal ID")
        return None
    
    # Check for existing quote for this deal (prevent duplicates)
    existing_quote = check_existing_quote_for_deal(deal_id)
    if existing_quote:
        quote_id = existing_quote.get("id")
        logger.info(f"⚠️ Quote already exists for deal {deal_id}: {quote_id}")
        logger.info(f"📋 Skipping quote creation to prevent duplicates")
        return existing_quote
    
    logger.info(f"Creating new quote for organization {organization_id} (deal {deal_id})")
    
    # Create quote using Pipedrive integration
    quote_data = create_quote_from_pipedrive_deal(deal_id, organization_id)
    
    if quote_data:
        quote_id = quote_data.get("id")
        logger.info(f"✅ Successfully created new quote {quote_id} for sub-organization {organization_id}")
        return quote_data
    else:
        logger.error(f"❌ Failed to create quote for sub-organization {organization_id}")
        return None

def main():
    """
    Main function for simplified quote creation.
    """
    logger.info("🚀 Starting Simplified Quote Creator...")
    
    try:
        # Check environment variables
        if not os.getenv("QUOTER_API_KEY") or not os.getenv("QUOTER_CLIENT_SECRET"):
            logger.error("Missing Quoter API credentials")
            return
        
        if not os.getenv("PIPEDRIVE_API_TOKEN"):
            logger.error("Missing Pipedrive API token")
            return
        
        # Example usage - replace with actual organization ID
        organization_id = input("Enter organization ID to create quote for: ")
        
        if organization_id:
            quote_data = create_quote_for_sub_organization(organization_id)
            if quote_data:
                logger.info(f"✅ Quote creation completed successfully!")
                logger.info(f"📋 Quote ID: {quote_data.get('id')}")
                logger.info(f"🔗 Check Quoter interface to see the created quote")
            else:
                logger.error("❌ Quote creation failed")
        else:
            logger.error("No organization ID provided")
        
    except Exception as e:
        logger.error(f"❌ Simplified Quote Creator failed: {e}")
        raise

if __name__ == "__main__":
    main()
