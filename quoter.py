import requests
import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()
CLIENT_ID = os.getenv("QUOTER_API_KEY")  # Your Client ID
CLIENT_SECRET = os.getenv("QUOTER_CLIENT_SECRET")  # Your Client Secret

def generate_sequential_quote_number(deal_id):
    """
    Generate sequential quote number in xxxxx-yy format with leading zeros.
    
    Args:
        deal_id (str or int): The deal ID from Pipedrive
        
    Returns:
        str: Formatted quote number (e.g., "02096-01", "02096-02")
    """
    try:
        # Convert deal_id to integer and pad with leading zeros to 5 digits
        deal_id_int = int(str(deal_id))
        padded_deal_id = f"{deal_id_int:05d}"
        
        # Get access token for API calls
        access_token = get_access_token()
        if not access_token:
            logger.warning(f"⚠️ Could not get access token, using fallback numbering for deal {deal_id}")
            return f"{padded_deal_id}-01"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Query existing quotes to find the next sequence number
        # We'll search for quotes that contain the deal ID in their name or number
        endpoint = "https://api.quoter.com/v1/quotes"
        
        # Search for existing quotes related to this deal
        # We'll use a broader search to find any quotes that might be related
        search_params = {
            "limit": 100,  # Get more quotes to ensure we don't miss any
            "page": 1
        }
        
        existing_quotes = []
        page = 1
        
        while True:
            search_params["page"] = page
            response = requests.get(endpoint, headers=headers, params=search_params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Could not fetch quotes page {page}, using fallback numbering")
                break
                
            data = response.json()
            quotes = data.get("data", [])
            
            if not quotes:
                break
                
            # Filter quotes that might be related to this deal
            for quote in quotes:
                quote_name = quote.get("name", "")
                quote_number = quote.get("number", "")
                
                # Check if this quote is related to our deal
                # Look for deal ID in quote name or number
                if (str(deal_id) in quote_name or 
                    str(deal_id) in quote_number or
                    padded_deal_id in quote_name or
                    padded_deal_id in quote_number):
                    existing_quotes.append(quote)
            
            # Check if we've reached the end
            if len(quotes) < 100:
                break
                
            page += 1
        
        # Find the highest sequence number for this deal
        max_sequence = 0
        for quote in existing_quotes:
            quote_name = quote.get("name", "")
            quote_number = quote.get("number", "")
            
            # Look for existing xxxxx-yy pattern
            import re
            pattern = rf"{padded_deal_id}-(\d{{2}})"
            match = re.search(pattern, quote_name) or re.search(pattern, quote_number)
            
            if match:
                sequence = int(match.group(1))
                max_sequence = max(max_sequence, sequence)
        
        # Generate next sequence number
        next_sequence = max_sequence + 1
        quote_number = f"{padded_deal_id}-{next_sequence:02d}"
        
        logger.info(f"🎯 Generated quote number: {quote_number} for deal {deal_id}")
        logger.info(f"   Found {len(existing_quotes)} existing quotes, max sequence: {max_sequence}")
        
        return quote_number
        
    except Exception as e:
        logger.error(f"❌ Error generating quote number for deal {deal_id}: {e}")
        # Fallback to basic format
        try:
            deal_id_int = int(str(deal_id))
            padded_deal_id = f"{deal_id_int:05d}"
            return f"{padded_deal_id}-01"
        except:
            return f"DEAL-{deal_id}-01"

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

def create_or_find_contact_in_quoter(contact_name, contact_email=None, contact_phone=None, pipedrive_contact_id=None, organization_name=None):
    """
    Create a new contact in Quoter or find existing one based on email and organization.
    
    Args:
        contact_name (str): Contact name
        contact_email (str, optional): Contact email
        contact_phone (str, optional): Contact phone
        pipedrive_contact_id (str, optional): Pipedrive person ID
        organization_name (str, optional): Organization name for better matching
        
    Returns:
        str: Contact ID if created/found, None otherwise
    """
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth token for contact creation")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # First, try to find existing contact by email
    if contact_email:
        try:
            response = requests.get(
                "https://api.quoter.com/v1/contacts",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                contacts = data.get("data", [])
                
                # Look for existing contact with matching email
                for contact in contacts:
                    contact_emails = contact.get("email", [])
                    if isinstance(contact_emails, list):
                        for email_item in contact_emails:
                            if email_item.get("value") == contact_email:
                                logger.info(f"✅ Found existing contact: {contact.get('first_name')} {contact.get('last_name')} "
                                          f"(ID: {contact.get('id')}) - reusing existing contact")
                                return contact.get("id")
                    elif isinstance(contact_emails, str) and contact_emails == contact_email:
                        logger.info(f"✅ Found existing contact: {contact.get('first_name')} {contact.get('last_name')} "
                                  f"(ID: {contact.get('id')}) - reusing existing contact")
                        return contact.get("id")
                
                logger.info(f"📧 No existing contact found with email {contact_email} - will create new one")
                    
        except Exception as e:
            logger.warning(f"Error searching for existing contact: {e}")
    
    # If no existing contact found, create a new one
    try:
        # Parse first and last name from contact_name
        name_parts = contact_name.split(" ", 1)
        first_name = name_parts[0] if name_parts else contact_name
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Create contact with all required fields
        contact_data = {
            "first_name": first_name,
            "last_name": last_name,
            "organization": organization_name,  # Use the organization name from the quote
            "billing_country_iso": "US"  # Default to US for now
        }
        
        # Add email if available
        if contact_email:
            contact_data["email"] = contact_email
        
        # Add phone if available
        if contact_phone:
            contact_data["phone"] = contact_phone
        
        # Add Pipedrive reference if available
        if pipedrive_contact_id:
            contact_data["pipedrive_contact_id"] = str(pipedrive_contact_id)
        
        logger.info(f"Creating new contact in Quoter: {contact_name}")
        
        response = requests.post(
            "https://api.quoter.com/v1/contacts",
            json=contact_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            contact_id = data.get("id")
            
            if contact_id:
                logger.info(f"✅ Successfully created contact {contact_id} in Quoter")
                return contact_id
            else:
                logger.error(f"❌ No contact ID in response: {data}")
                return None
        else:
            logger.error(f"❌ Failed to create contact: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error creating contact: {e}")
        return None

def create_comprehensive_contact_from_pipedrive(pipedrive_contact_data, pipedrive_org_data):
    """
    Create or find a contact in Quoter with comprehensive data mapping from Pipedrive.
    
    This function extracts ALL available data from Pipedrive and maps it to standard
    Quoter contact fields, creating rich, complete contact information.
    
    Args:
        pipedrive_contact_data (dict): Person data from Pipedrive
        pipedrive_org_data (dict): Organization data from Pipedrive
        
    Returns:
        str: Contact ID if created/found, None otherwise
    """
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth token for comprehensive contact creation")
        return None
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Extract contact information
    contact_name = pipedrive_contact_data.get("name", "Unknown Contact")
    contact_email = None
    contact_phone = None
    contact_mobile = None
    
    # Extract email (handle both list and direct formats)
    emails = pipedrive_contact_data.get("email", [])
    if isinstance(emails, list):
        for email_item in emails:
            if email_item.get("primary", False):
                contact_email = email_item.get("value")
                break
        if not contact_email and emails:
            contact_email = emails[0].get("value")
    elif isinstance(emails, str):
        contact_email = emails
    
    # Extract phone numbers (handle both list and direct formats)
    phones = pipedrive_contact_data.get("phone", [])
    if isinstance(phones, list):
        for phone_item in phones:
            if phone_item.get("label") == "work":
                contact_phone = phone_item.get("value")
            elif phone_item.get("label") == "mobile":
                contact_mobile = phone_item.get("value")
        if not contact_phone and phones:
            contact_phone = phones[0].get("value")
    elif isinstance(phones, str):
        contact_phone = phones
    
    # Extract organization information
    org_name = pipedrive_org_data.get("name", "")
    org_website = pipedrive_org_data.get("website", "")
    
    # Extract address information from organization
    org_address = pipedrive_org_data.get("address", "")
    org_address2 = pipedrive_org_data.get("address2", "")
    org_city = pipedrive_org_data.get("city", "")
    org_state = pipedrive_org_data.get("state", "")
    org_zip = pipedrive_org_data.get("postal_code", "") or pipedrive_org_data.get("zip", "")
    org_country = pipedrive_org_data.get("country", "US")  # Default to US
    
    # Extract organization contact information
    org_phone = pipedrive_org_data.get("phone", "")
    org_email = pipedrive_org_data.get("email", "")
    
    # First, try to find existing contact by email
    if contact_email:
        try:
            response = requests.get(
                "https://api.quoter.com/v1/contacts",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                contacts = data.get("data", [])
                
                # Look for existing contact with matching email
                for contact in contacts:
                    contact_emails = contact.get('email', [])
                    if isinstance(contact_emails, list):
                        for email_item in contact_emails:
                            if email_item.get('value') == contact_email:
                                logger.info(f"✅ Found existing contact: {contact.get('first_name')} {contact.get('last_name')} "
                                          f"(ID: {contact.get('id')}) - reusing existing contact")
                                return contact.get("id")
                    elif isinstance(contact_emails, str) and contact_emails == contact_email:
                        logger.info(f"✅ Found existing contact: {contact.get('first_name')} {contact.get('last_name')} "
                                  f"(ID: {contact.get('id')}) - reusing existing contact")
                        return contact.get("id")
                
                logger.info(f"📧 No existing contact found with email {contact_email} - will create new one with comprehensive data")
                    
        except Exception as e:
            logger.warning(f"Error searching for existing contact: {e}")
    
    # If no existing contact found, create a new one with comprehensive data
    try:
        # Parse first and last name from contact_name
        name_parts = contact_name.split(" ", 1)
        first_name = name_parts[0] if name_parts else contact_name
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Create comprehensive contact data using standard Quoter fields
        contact_data = {
            "first_name": first_name,
            "last_name": last_name,
            "organization": org_name,
            "billing_country_iso": org_country,
            "shipping_country_iso": org_country,
        }
        
        # Add job title if available (Pipedrive title field = job title)
        contact_title = pipedrive_contact_data.get("title", "")
        if contact_title:
            contact_data["title"] = contact_title
            logger.info(f"   Job Title: {contact_title}")
        
        # Add email if available
        if contact_email:
            contact_data["email"] = contact_email
        
        # Add phone information
        if contact_phone:
            contact_data["work_phone"] = contact_phone
        if contact_mobile:
            contact_data["mobile_phone"] = contact_mobile
        elif contact_phone:  # Use work phone as mobile if no mobile specified
            contact_data["mobile_phone"] = contact_phone
        
        # Add website if available
        if org_website:
            contact_data["website"] = org_website
        
        # Add organization contact information if available
        if org_phone:
            contact_data["work_phone"] = org_phone  # Use org phone as work phone if no contact phone
        if org_email:
            contact_data["email"] = org_email  # Use org email if no contact email
        
        # Add comprehensive billing address from organization data
        if org_address:
            contact_data["billing_address"] = org_address
        if org_address2:
            contact_data["billing_address2"] = org_address2
        if org_city:
            contact_data["billing_city"] = org_city
        if org_state:
            contact_data["billing_region_iso"] = org_state
        if org_zip:
            contact_data["billing_postal_code"] = org_zip
        if org_country:
            contact_data["billing_country_iso"] = org_country
        
        # Add comprehensive shipping address from organization data (same as billing for now)
        if org_address:
            contact_data["shipping_address"] = org_address
        if org_address2:
            contact_data["shipping_address2"] = org_address2
        if org_city:
            contact_data["shipping_city"] = org_city
        if org_state:
            contact_data["shipping_region_iso"] = org_state
        if org_zip:
            contact_data["shipping_postal_code"] = org_zip
        if org_country:
            contact_data["shipping_country_iso"] = org_country
        
        # Add shipping contact details
        if contact_email:
            contact_data["shipping_email"] = contact_email
        if first_name:
            contact_data["shipping_first_name"] = first_name
        if last_name:
            contact_data["shipping_last_name"] = last_name
        if org_name:
            contact_data["shipping_organization"] = org_name
        if contact_phone:
            contact_data["shipping_phone"] = contact_phone
        
        # Add shipping label
        if first_name and last_name:
            contact_data["shipping_label"] = f"Ship to {first_name} {last_name}"
        
        logger.info(f"Creating comprehensive contact in Quoter: {contact_name}")
        logger.info(f"   Organization: {org_name}")
        logger.info(f"   Email: {contact_email or org_email}")
        logger.info(f"   Phone: {contact_phone or org_phone}")
        logger.info(f"   Address: {org_address}, {org_city}, {org_state} {org_zip}")
        logger.info(f"   Website: {org_website}")
        logger.info(f"   Country: {org_country}")
        logger.info(f"   Total fields to map: {len(contact_data)}")
        
        response = requests.post(
            "https://api.quoter.com/v1/contacts",
            json=contact_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            contact_id = data.get("id")
            
            if contact_id:
                logger.info(f"✅ Successfully created comprehensive contact {contact_id} in Quoter")
                logger.info(f"   Mapped {len(contact_data)} fields from Pipedrive")
                return contact_id
            else:
                logger.error(f"❌ No contact ID in response: {data}")
                return None
        else:
            logger.error(f"❌ Failed to create comprehensive contact: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error creating comprehensive contact: {e}")
        return None

def create_quote_from_pipedrive_org(organization_data):
    """
    Create a quote in Quoter using native Pipedrive integration.
    This function uses the Deal_ID custom field to get deal info and create the quote.
    
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
    
    # Get deal ID from the custom field (much more reliable than parsing org name)
    # Custom field key: 15034cf07d05ceb15f0a89dcbdcc4f596348584e
    deal_id = organization_data.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")
    
    if not deal_id:
        logger.error(f"Organization {org_id} has no Deal_ID custom field")
        return None
    
    logger.info(f"Found deal ID '{deal_id}' from custom field for organization '{org_name}'")
    
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
    
    # Get clean organization name (without deal ID suffix) for display
    # Look for parent organization or clean the current name
    clean_org_name = org_name
    if "-" in org_name:
        clean_org_name = org_name.split("-")[0].strip()
    
    logger.info(f"Using clean organization name: '{clean_org_name}'")
    
    # Now create the quote using native Quoter-Pipedrive integration
    return create_draft_quote_with_contact(
        deal_id=deal_id,
        organization_name=clean_org_name,
        deal_title=deal_title,
        contact_name=contact_name,
        contact_email=email,
        contact_phone=phone,
        pipedrive_contact_id=contact_id
    )

def create_draft_quote_with_contact(deal_id, organization_name, deal_title, 
                                   contact_name, contact_email=None, contact_phone=None, 
                                   pipedrive_contact_id=None):
    """
    Create a draft quote in Quoter that will automatically pull Pipedrive data.
    Quoter handles the contact/org/deal population after quote creation.
    
    Args:
        deal_id (str): Pipedrive deal ID
        organization_name (str): Organization name
        deal_title (str): Deal title
        contact_name (str): Primary contact name (for logging only)
        contact_email (str, optional): Primary contact email (for logging only)
        contact_phone (str, optional): Primary contact phone (for logging only)
        pipedrive_contact_id (str, optional): Pipedrive person ID (for logging only)
        
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
    
    # Get required fields for quote creation (template and currency)
    required_fields = get_quote_required_fields(access_token)
    if not required_fields:
        logger.error("Failed to get required fields for quote creation")
        return None
    
    # Get a default contact ID (Quoter will replace this with actual Pipedrive contact)
    default_contact_id = get_default_contact_id(access_token)
    if not default_contact_id:
        logger.error("Failed to get default contact ID")
        return None
    
    # Create or find the contact in Quoter first
    logger.info(f"Creating/finding contact in Quoter: {contact_name}")
    contact_id = create_or_find_contact_in_quoter(
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        pipedrive_contact_id=pipedrive_contact_id,
        organization_name=organization_name
    )
    
    if not contact_id:
        logger.error("Failed to create/find contact in Quoter")
        return None
    
    logger.info(f"✅ Using contact ID: {contact_id}")
    
    # Prepare quote data with the real contact and organization data
    quote_data = {
        "contact_id": contact_id,  # Use the real contact, not a default placeholder
        "template_id": required_fields["template_id"],
        "currency_abbr": required_fields["currency_abbr"],
        "pipedrive_deal_id": str(deal_id),  # Include Pipedrive deal ID
        "name": f"Quote for {organization_name}",  # Use the clean organization name passed in
        "status": "draft"
    }
    
    try:
        logger.info(f"Creating draft quote for deal {deal_id}")
        logger.info(f"Organization: {organization_name}")
        logger.info(f"Contact: {contact_name}")
        logger.info("Note: Quoter will automatically populate contact/org/deal info from Pipedrive")
        
        logger.info(f"📤 Sending API request to Quoter:")
        logger.info(f"   URL: https://api.quoter.com/v1/quotes")
        logger.info(f"   Headers: {headers}")
        logger.info(f"   Data: {quote_data}")
        
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json=quote_data,
            headers=headers,
            timeout=10
        )
        
        logger.info(f"📥 API Response:")
        logger.info(f"   Status: {response.status_code}")
        logger.info(f"   Response: {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            quote_id = data.get("id")
            
            if quote_id:
                logger.info(f"✅ Successfully created draft quote {quote_id}")
                logger.info(f"   Pipedrive deal ID: {deal_id}")
                logger.info(f"   Organization: {organization_name}")
                logger.info(f"   Title: Quote for {organization_name} - Deal {deal_id}")
                logger.info(f"   Quoter should now pull Pipedrive data automatically")
                logger.info(f"   URL: {data.get('url', 'N/A')}")
                return data
            else:
                logger.error(f"❌ No quote ID in response: {data}")
                return None
        else:
            logger.error(f"❌ Failed to create quote: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error creating quote: {e}")
        return None

def update_quote_after_creation(quote_id, deal_id, organization_name, contact_name):
    """
    Update a quote after creation with the correct merge fields and Pipedrive data.
    
    Args:
        quote_id (str): The quote ID returned from creation
        deal_id (str): Pipedrive deal ID
        organization_name (str): Organization name
        contact_name (str): Contact name
        
    Returns:
        bool: True if update successful, False otherwise
    """
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth token for quote update")
        return False

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Update data with merge fields
    update_data = {
        "quote_number": f"##PD-{deal_id}##",  # Use merge field format
        "organization_name": organization_name,
        "contact_name": contact_name
    }
    
    try:
        logger.info(f"Updating quote {quote_id} with merge fields:")
        logger.info(f"   Quote number: ##PD-{deal_id}##")
        logger.info(f"   Organization: {organization_name}")
        logger.info(f"   Contact: {contact_name}")
        
        response = requests.patch(
            f"https://api.quoter.com/v1/quotes/{quote_id}",
            json=update_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Successfully updated quote {quote_id}")
            return True
        else:
            logger.error(f"❌ Failed to update quote {quote_id}: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error updating quote {quote_id}: {e}")
        return False

def create_draft_quote(deal_id, organization_name, deal_title=None):
    """
    Create a draft quote in Quoter for the given deal and organization.
    
    Args:
        deal_id (str): Pipedrive deal ID
        organization_name (str): Organization name
        deal_title (str, optional): Deal title
        
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
    
    # Prepare quote data (quote number will be assigned by Quoter after publication)
    quote_data = {
        "contact_id": default_contact_id,  # Use the created contact
        "template_id": required_fields["template_id"],
        "currency_abbr": required_fields["currency_abbr"],
        "title": deal_title or f"Quote for {organization_name} - Deal {deal_id}",
        "pipedrive_deal_id": str(deal_id),
        "organization_name": organization_name
    }
    
    try:
        logger.info(f"Creating draft quote for deal {deal_id} and organization {organization_name}")
        
        response = requests.post(
            "https://api.quoter.com/v1/quotes",
            json=quote_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            quote_id = data.get("id")  # Direct ID access based on our testing
            
            if quote_id:
                logger.info(f"✅ Successfully created draft quote {quote_id} for deal {deal_id}")
                logger.info(f"   URL: {data.get('url', 'N/A')}")
                return data
            else:
                logger.error(f"❌ No quote ID in response: {data}")
                return None
        else:
            logger.error(f"❌ Failed to create quote: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error creating quote: {e}")
        return None

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
    
    # Get specific template by name (prefer "Managed Service Proposal" over "test")
    try:
        response = requests.get(
            "https://api.quoter.com/v1/quote_templates",  # Correct endpoint we discovered
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get("data", [])
            if templates:
                # Look for the "test" template first, then "Managed Service Proposal" as fallback
                preferred_template = None
                fallback_template = None
                
                for template in templates:
                    title = template.get("title", "")
                    if title == "test":  # Look for exact "test" template first
                        preferred_template = template
                        break
                    elif "Managed Service Proposal" in title:  # Use as fallback
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

def create_comprehensive_quote_from_pipedrive(organization_data):
    """
    Create a comprehensive draft quote in Quoter with maximum data mapping from Pipedrive.
    
    This function extracts ALL available data from Pipedrive and creates a rich draft quote
    that includes comprehensive contact information and organization details.
    
    Args:
        organization_data (dict): Organization data from Pipedrive
        
    Returns:
        dict: Quote data if created successfully, None otherwise
    """
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get OAuth token for comprehensive quote creation")
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
    
    # Extract organization information
    org_name = organization_data.get("name", "Unknown Organization")
    org_id = organization_data.get("id")
    
    # Extract deal ID from custom field
    deal_id = organization_data.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")
    if not deal_id:
        logger.error(f"❌ No deal ID found in organization {org_id}")
        return None
    
    logger.info(f"🎯 Creating comprehensive quote for organization: {org_name}")
    logger.info(f"   Organization ID: {org_id}")
    logger.info(f"   Deal ID: {deal_id}")
    
    # Get deal information from Pipedrive
    from pipedrive import get_deal_by_id
    deal_data = get_deal_by_id(deal_id)
    if not deal_data:
        logger.error(f"❌ Failed to get deal {deal_id} from Pipedrive")
        return None
    
    logger.info(f"📋 Deal found: {deal_data.get('title', 'Unknown Deal')}")
    
    # Extract person/contact information from deal
    person_data = deal_data.get("person_id", {})
    if not person_data:
        logger.error(f"❌ No person data found in deal {deal_id}")
        return None
    
    # Handle both list and direct person data formats
    if isinstance(person_data, list):
        if person_data:
            primary_contact = person_data[0]
        else:
            logger.error(f"❌ Empty person list in deal {deal_id}")
            return None
    else:
        primary_contact = person_data
    
    contact_id = primary_contact.get("value")
    if not contact_id:
        logger.error(f"❌ No contact ID found in person data")
        return None
    
    # Get full person data from Pipedrive
    from pipedrive import get_person_by_id
    contact_data = get_person_by_id(contact_id)
    if not contact_data:
        logger.error(f"❌ Failed to get person {contact_id} from Pipedrive")
        return None
    
    logger.info(f"👤 Contact found: {contact_data.get('name', 'Unknown Contact')}")
    
    # Create comprehensive contact in Quoter
    contact_id = create_comprehensive_contact_from_pipedrive(
        contact_data, 
        organization_data
    )
    
    if not contact_id:
        logger.error("❌ Failed to create comprehensive contact in Quoter")
        return None
    
    logger.info(f"✅ Contact created/updated in Quoter: {contact_id}")
    
    # Prepare comprehensive quote data (quote number will be assigned by Quoter after publication)
    quote_data = {
        "contact_id": contact_id,
        "template_id": required_fields["template_id"],
        "currency_abbr": required_fields["currency_abbr"],
        "name": f"Quote for {org_name}"
    }
    
    try:
        logger.info(f"📝 Creating comprehensive draft quote...")
        logger.info(f"   Template: {required_fields['template_id']}")
        logger.info(f"   Currency: {required_fields['currency_abbr']}")
        logger.info(f"   Contact: {contact_id}")
        
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
                logger.info(f"🎉 SUCCESS! Comprehensive draft quote created:")
                logger.info(f"   Quote ID: {quote_id}")
                logger.info(f"   Name: {data.get('name', 'N/A')}")
                logger.info(f"   URL: {data.get('url', 'N/A')}")
                logger.info(f"   Contact ID: {contact_id}")
                
                # Step 2: Add the existing instructional line item
                logger.info(f"📋 Adding instructional line item to quote...")
                
                # Use the existing instructional item from Quoter
                existing_item_id = "item_31IIdw4C1GHIwU05yhnZ2B88S2B"
                
                # Get the full item details to include description and pricing
                item_response = requests.get(f'https://api.quoter.com/v1/items/{existing_item_id}', headers=headers)
                if item_response.status_code == 200:
                    item_data = item_response.json()
                    item_name = item_data.get('name', '01-Draft Quote-Instructions (delete before sending quote)')
                    item_category = item_data.get('category', 'DJ')
                    item_description = item_data.get('description', '')
                    
                    logger.info(f"📋 Retrieved instructional item details:")
                    logger.info(f"   Name: {item_name}")
                    logger.info(f"   Category: {item_category}")
                    logger.info(f"   Description length: {len(item_description)} characters")
                    
                    # Add the instructional line item
                    line_item_data = {
                        "quote_id": quote_id,
                        "item_id": existing_item_id,
                        "name": item_name,
                        "category": item_category,
                        "description": item_description,
                        "quantity": 1,
                        "unit_price": 1.00
                    }
                    
                    line_item_response = requests.post('https://api.quoter.com/v1/line_items', 
                                                    headers=headers, json=line_item_data)
                    
                    if line_item_response.status_code in [200, 201]:
                        line_item_result = line_item_response.json()
                        line_item_id = line_item_result.get('id')
                        logger.info(f"✅ Instructional line item added successfully:")
                        logger.info(f"   Line Item ID: {line_item_id}")
                        logger.info(f"   Name: {item_name}")
                    else:
                        logger.warning(f"⚠️ Failed to add instructional line item: {line_item_response.status_code}")
                        logger.warning(f"   Error: {line_item_response.text[:200]}")
                else:
                    logger.warning(f"⚠️ Failed to get instructional item details: {item_response.status_code}")
                
                logger.info(f"📊 Quote created with comprehensive contact data and instructional line item")
                logger.info(f"   Sales rep can now use Quoter's native dropdowns to link person/org/deal")
                
                return data
            else:
                logger.error(f"❌ No quote ID in response: {data}")
                return None
        else:
            logger.error(f"❌ Failed to create comprehensive quote: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error creating comprehensive quote: {e}")
        return None 

 