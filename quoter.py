import requests
import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()
CLIENT_ID = os.getenv("QUOTER_API_KEY")  # Your Client ID
CLIENT_SECRET = os.getenv("QUOTER_CLIENT_SECRET")  # Your Client Secret

def get_access_token():
    """
    Get OAuth access token from Quoter API.
    
    Based on Quoter API documentation: https://docs.quoter.com/api
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        logger.error("CLIENT_ID or CLIENT_SECRET not found in environment variables")
        return None
    
    auth_url = "https://api.quoter.com/v1/auth/oauth/authorize"
    auth_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    
    try:
        logger.info("Getting OAuth access token from Quoter...")
        response = requests.post(auth_url, json=auth_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("access_token")
            if access_token:
                logger.info("✅ Successfully obtained OAuth access token")
                return access_token
            else:
                logger.error("❌ No access_token in response")
                return None
        else:
            logger.error(f"❌ OAuth authentication failed: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error getting OAuth token: {e}")
        return None

def get_quoter_products(since_date=None):
    """
    Fetch products/items from Quoter API with optional date filtering.
    
    Based on Quoter API documentation: https://docs.quoter.com/api
    
    Args:
        since_date (str, optional): ISO date string (YYYY-MM-DD) to filter items 
                                   modified since this date. If None, gets all items.
    
    Returns:
        list: List of product data from Quoter
    """
    # First get OAuth access token
    access_token = get_access_token()
    if not access_token:
        return []
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # According to Quoter API docs, the correct endpoint is /items
    endpoint = "https://api.quoter.com/v1/items"
    
    try:
        if since_date:
            logger.info(f"Fetching items from Quoter API modified since {since_date}: {endpoint}")
        else:
            logger.info(f"Fetching all items from Quoter API: {endpoint}")
        
        all_items = []
        page = 1
        limit = 100
        
        # Get all items with pagination using page parameter
        while True:
            # Add pagination parameters
            params = {
                "limit": limit,
                "page": page
            }
            
            # Add date filter if specified
            if since_date:
                # Convert date to ISO 8601 format (e.g., "2025-08-04" -> "2025-08-04T00:00:00.000Z")
                if 'T' not in since_date:
                    since_date = f"{since_date}T00:00:00.000Z"
                params["modified_at[gt]"] = since_date
            
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", [])
                has_more = data.get("has_more", False)
                total_count = data.get("total_count", 0)
                
                all_items.extend(items)
                
                logger.info(f"Retrieved {len(items)} items (page: {page}, total so far: {len(all_items)}/{total_count})")
                
                # Check if there are more items
                if not has_more or len(items) == 0:
                    break
                
                # Safety check: if we're getting the same items repeatedly, stop
                if len(all_items) > total_count * 2:
                    logger.warning(f"⚠️  Stopping pagination to prevent endless loop. Got {len(all_items)} items but total_count is {total_count}")
                    break
                    
                page += 1
            else:
                logger.error(f"❌ API request failed with status {response.status_code}: {response.text}")
                break
        
        # Remove duplicates based on item ID
        unique_items = []
        seen_ids = set()
        
        for item in all_items:
            item_id = item.get('id')
            if item_id and item_id not in seen_ids:
                unique_items.append(item)
                seen_ids.add(item_id)
            elif not item_id:
                # If no ID, use name as fallback
                item_name = item.get('name', '')
                if item_name not in seen_ids:
                    unique_items.append(item)
                    seen_ids.add(item_name)
        
        logger.info(f"✅ Successfully retrieved {len(unique_items)} unique items from Quoter (removed {len(all_items) - len(unique_items)} duplicates)")
        return unique_items
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error connecting to Quoter API: {e}")
        return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error connecting to Quoter API: {e}")
        return [] 

def update_quoter_sku(quoter_item_id, pipedrive_product_id):
    """
    Update Quoter item with the new Pipedrive product ID.

    Args:
        quoter_item_id (str): Quoter item ID
        pipedrive_product_id (str): Pipedrive product ID
    """
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth token for Quoter update")
        return False

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Update data
    update_data = {
        "sku": str(pipedrive_product_id)
    }
    
    try:
        logger.info(f"Updating Quoter item {quoter_item_id} with supplier_sku: {pipedrive_product_id}")
        
        response = requests.patch(
            f"https://api.quoter.com/v1/items/{quoter_item_id}",
            json=update_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Successfully updated Quoter item {quoter_item_id}")
            return True
        else:
            logger.error(f"❌ Failed to update Quoter item {quoter_item_id}: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error updating Quoter item {quoter_item_id}: {e}")
        return False 

def get_quote_required_fields(access_token):
    """
    Get the required fields for quote creation (template and currency only).
    Contact ID is now created separately for each quote.
    
    Args:
        access_token (str): OAuth access token
        
    Returns:
        dict: Required fields (template_id, currency_abbr) or None
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get first available template
    try:
        response = requests.get(
            "https://api.quoter.com/v1/quote_templates",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get("data", [])
            if templates:
                # Look for the "test" template first
                preferred_template = None
                fallback_template = None
                
                for template in templates:
                    title = template.get("title", "")
                    if title == "test":  # Prioritize the "test" template
                        preferred_template = template
                        break
                    elif title and "Managed Service Proposal" in title:  # Use as fallback
                        fallback_template = template
                
                # Use preferred template, fallback, or first available
                if preferred_template:
                    template_id = preferred_template.get("id")
                    logger.info(f"Found preferred template: {preferred_template.get('title')} (ID: {template_id})")
                elif fallback_template:
                    template_id = fallback_template.get("id")
                    logger.info(f"Using fallback template: {fallback_template.get('title')} (ID: {template_id})")
                else:
                    template_id = templates[0].get("id")
                    logger.info(f"Using first available template: {templates[0].get('title', 'N/A')} (ID: {template_id})")
            else:
                logger.error("No templates found")
                return None
        else:
            logger.error(f"Failed to get templates: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return None
    
    return {
        "template_id": template_id,
        "currency_abbr": "USD"  # Default currency
    }

def create_draft_quote_with_contact(deal_id, organization_name, deal_title, 
                                   contact_name, contact_email=None, contact_phone=None, 
                                   pipedrive_contact_id=None):
    """
    Create a draft quote in Quoter with enhanced contact information.
    
    Args:
        deal_id (str): Pipedrive deal ID
        organization_name (str): Organization name
        deal_title (str): Deal title
        contact_name (str): Primary contact name
        contact_email (str, optional): Primary contact email
        contact_phone (str, optional): Primary contact phone
        pipedrive_contact_id (str, optional): Pipedrive person ID
        
    Returns:
        dict: Quote data if created successfully, None otherwise
    """
    # First get OAuth access token
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth token for quote creation")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Get required fields for quote creation
    required_fields = get_quote_required_fields(access_token)
    if not required_fields:
        logger.error("Failed to get required fields for quote creation")
        return None
    
    # Get a default contact ID (Quoter will replace this with actual Pipedrive contact)
    default_contact_id = get_default_contact_id(access_token)
    if not default_contact_id:
        logger.error("Failed to get default contact ID")
        return None
    
    # Prepare quote data with the actual contact and enhanced information
    quote_data = {
        "contact_id": default_contact_id,  # Use the actual contact, not generic
        "template_id": required_fields["template_id"],
        "currency_abbr": required_fields["currency_abbr"],
        "title": f"Quote for {organization_name} - {deal_title}",
        "quote_number": f"PD-{deal_id}",
        "pipedrive_deal_id": str(deal_id),  # This field triggers Quoter's Pipedrive integration
        "organization_name": organization_name  # Include organization name
    }
    
    try:
        logger.info(f"Creating enhanced draft quote for deal {deal_id}")
        logger.info(f"Organization: {organization_name}")
        logger.info(f"Contact: {contact_name}")
        logger.info(f"Quote number: PD-{deal_id}")
        
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json=quote_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            quote_id = data.get("id")
            
            if quote_id:
                logger.info(f"✅ Successfully created enhanced draft quote {quote_id}")
                logger.info(f"   Quote number: PD-{deal_id}")
                logger.info(f"   Organization: {organization_name}")
                logger.info(f"   Contact: {contact_name}")
                logger.info(f"   URL: {data.get('url', 'N/A')}")
                return data
            else:
                logger.error(f"❌ No quote ID in response: {data}")
                return None
        else:
            logger.error(f"❌ Failed to create quote: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error creating enhanced quote: {e}")
        return None

def get_default_contact_id(access_token):
    """
    Get a default contact ID from Quoter for quote creation.
    Quoter will replace this with the actual Pipedrive contact after creation.
    
    Args:
        access_token (str): OAuth access token
        
    Returns:
        str: Default contact ID if found, None otherwise
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
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
                logger.info(f"Using default contact ID: {contact_id}")
                return contact_id
            else:
                logger.error("No contacts found in Quoter")
                return None
        else:
            logger.error(f"Failed to get contacts: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting default contact: {e}")
        return None

def create_quote_from_pipedrive_org(organization_data):
    """
    Create a quote in Quoter using native Pipedrive integration.
    This function extracts deal ID from org name, gets contact info, and creates the quote.
    
    Args:
        organization_data (dict): Organization data from Pipedrive
        
    Returns:
        dict: Quote data if created successfully, None otherwise
    """
    from pipedrive import get_deal_by_id
    
    org_name = organization_data.get("name", "")
    org_id = organization_data.get("id")
    
    if not org_name:
        logger.error(f"Organization {org_id} has no name")
        return None
    
    # Extract deal ID from org name (last 4 digits after the dash)
    # Format: "CompanyName-1234" -> deal_id = "1234"
    if "-" in org_name:
        deal_id = org_name.split("-")[-1]
        try:
            # Validate it's a number
            int(deal_id)
        except ValueError:
            logger.error(f"Could not extract valid deal ID from org name: {org_name}")
            return None
    else:
        logger.error(f"Organization name format invalid (expected 'CompanyName-1234'): {org_name}")
        return None
    
    logger.info(f"Extracted deal ID '{deal_id}' from organization name '{org_name}'")
    
    # Get deal information from Pipedrive
    deal_data = get_deal_by_id(deal_id)
    if not deal_data:
        logger.error(f"Could not find deal {deal_id} for organization {org_name}")
        return None
    
    deal_title = deal_data.get("title", f"Deal {deal_id}")
    logger.info(f"Found deal: {deal_title}")
    
    # Get contact information from the deal
    person_data = deal_data.get("person_id", {})
    if not person_data:
        logger.error(f"No contact found in deal {deal_id}")
        return None
    
    # Handle both single contact and multiple contacts
    if isinstance(person_data, list):
        contacts = person_data
    else:
        contacts = [person_data]
    
    if not contacts:
        logger.error(f"No valid contacts found in deal {deal_id}")
        return None
    
    # Use the first contact (primary contact)
    primary_contact = contacts[0]
    contact_name = primary_contact.get("name", "Unknown Contact")
    contact_id = primary_contact.get("value")  # This is the Pipedrive person ID
    
    # Extract email and phone from contact data
    email = None
    phone = None
    
    if primary_contact.get("email"):
        email_data = primary_contact["email"]
        if isinstance(email_data, list) and email_data:
            # Find primary email or use first one
            for email_item in email_data:
                if email_item.get("primary", False) or not email:
                    email = email_item.get("value")
    
    if primary_contact.get("phone"):
        phone_data = primary_contact["phone"]
        if isinstance(phone_data, list) and phone_data:
            # Find primary phone or use first one
            for phone_item in phone_data:
                if phone_item.get("primary", False) or not phone:
                    phone = phone_item.get("value")
    
    logger.info(f"Primary contact: {contact_name} (ID: {contact_id})")
    if email:
        logger.info(f"Contact email: {email}")
    if phone:
        logger.info(f"Contact phone: {phone}")
    
    # Now create the quote using native Quoter-Pipedrive integration
    return create_draft_quote_with_contact(
        deal_id=deal_id,
        organization_name=org_name,
        deal_title=deal_title,
        contact_name=contact_name,
        contact_email=email,
        contact_phone=phone,
        pipedrive_contact_id=contact_id
    ) 