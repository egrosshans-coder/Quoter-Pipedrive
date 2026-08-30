import requests
import os
import json
from dotenv import load_dotenv
from utils.logger import logger

# Import the enhanced template mapping system

load_dotenv()
CLIENT_ID = os.getenv("QUOTER_API_KEY")  # Your Client ID
CLIENT_SECRET = os.getenv("QUOTER_CLIENT_SECRET")  # Your Client Secret

def get_template_name_from_id(template_id, access_token):
    """
    Get template name from template ID for bundle mapping
    
    Args:
        template_id (str): Quoter template ID
        access_token (str): Quoter API access token
        
    Returns:
        str: Template name/slug or None if not found
    """
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    try:
        response = requests.get('https://api.quoter.com/v1/quote_templates', headers=headers)
        if response.status_code == 200:
            data = response.json()
            templates = data.get('data', [])
            
            for template in templates:
                if template.get('id') == template_id:
                    # Try to get slug or name for mapping
                    template_slug = template.get('slug', '').lower().replace('-', '_')
                    template_name = template.get('name', '').lower().replace(' ', '-')
                    
                    # Map to our bundle names
                    if 'floating' in template_slug or 'floating' in template_name:
                        return 'floating-video'
                    elif 'led' in template_slug or 'wristband' in template_slug:
                        return 'led-wristbands'
                    
                    logger.info(f"📋 Template found: {template.get('name')} (ID: {template_id})")
                    return template_slug or template_name
            
            logger.warning(f"⚠️ Template ID {template_id} not found in templates list")
            return None
        else:
            logger.warning(f"⚠️ Failed to get templates: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"❌ Error getting template name: {e}")
        return None

def find_item_id_by_sku(sku, access_token):
    """
    Find Quoter item ID by item code (cross-system SKU)
    
    Args:
        sku (str): Item code (cross-system SKU like HG-FV-Graph-001)
        access_token (str): Quoter API access token
        
    Returns:
        str: Item ID or None if not found
    """
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Search for item by code (cross-system SKU) with pagination
    page = 1
    while page <= 5:  # Check first 5 pages
        search_params = {'search': sku, 'page': page, 'limit': 100}
        response = requests.get('https://api.quoter.com/v1/items', headers=headers, params=search_params)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('data', [])
            
            for item in items:
                # Search by 'code' field (cross-system SKU), not 'sku' field (internal ID)
                if item.get('code') == sku:
                    logger.info(f"✅ Found item by code: {item.get('name')} (ID: {item.get('id')}, Code: {item.get('code')})")
                    return item.get('id')
            
            if len(items) == 0:
                break
            page += 1
        else:
            logger.error(f"❌ Error searching for item {sku}: {response.status_code}")
            break
    
    logger.warning(f"⚠️ Item with code {sku} not found")
    return None

def generate_sequential_quote_number(deal_id):
    """
    Generate the quote number in the decided TLC scheme: dealID-YYYYMMDD.

    The deal ID is zero-padded to 5 digits and the date is the creation date in
    Pacific time (e.g. "03010-20260715"). This is deterministic - no account-wide
    quote scan and no sequence suffix (sequence-based numbering was rejected because
    the deal ID + creation date already sort correctly and never mutate).

    Quoter-native versioning (parent_quote_id) handles revisions, so revisions keep
    the parent's number; this function is only for the original quote.

    Args:
        deal_id (str or int): The deal ID from Pipedrive

    Returns:
        str: Formatted quote number (e.g., "03010-20260715")
    """
    # Zero-pad the deal ID to 5 digits (deal 3010 -> "03010")
    try:
        padded_deal_id = f"{int(str(deal_id).strip()):05d}"
    except (ValueError, TypeError):
        padded_deal_id = str(deal_id).strip()
        logger.warning(f"⚠️ Deal ID '{deal_id}' is not numeric; using it unpadded in quote number")

    # Creation date in Pacific time (America/Los_Angeles), non-mutable context
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        date_str = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y%m%d")
    except Exception as e:
        # Fallback to system local date if zoneinfo/tz data is unavailable
        logger.warning(f"⚠️ Could not resolve Pacific timezone ({e}); using local date")
        date_str = datetime.now().strftime("%Y%m%d")

    quote_number = f"{padded_deal_id}-{date_str}"
    logger.info(f"🎯 Generated quote number: {quote_number} for deal {deal_id}")
    return quote_number

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

def _fetch_items_with_date_filter(endpoint, headers, filter_type, filter_value):
    """
    Fetch items from Quoter API with a specific date filter.
    
    Args:
        endpoint (str): API endpoint URL
        headers (dict): Request headers
        filter_type (str): Filter type (e.g., "created_at[gt]", "modified_at[gt]")
        filter_value (str): Filter value (ISO date string)
    
    Returns:
        list: List of items from the API
    """
    all_items = []
    page = 1
    limit = 100
    
    while True:
        params = {
            "limit": limit,
            "page": page
        }
        
        if filter_type and filter_value:
            params[filter_type] = filter_value
        
        try:
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
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching items: {e}")
            break
    
    return all_items

def _combine_and_deduplicate_items(created_items, modified_items):
    """
    Combine two lists of items and remove duplicates.
    
    Args:
        created_items (list): Items created since date
        modified_items (list): Items modified since date
    
    Returns:
        list: Combined unique items
    """
    all_items = created_items + modified_items
    
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
    
    logger.info(f"Combined {len(created_items)} created + {len(modified_items)} modified = {len(unique_items)} unique items")
    return unique_items

def get_quoter_products(since_date=None):
    """
    Fetch products/items from Quoter API with optional date filtering.
    
    Based on Quoter API documentation: https://docs.quoter.com/api
    
    Args:
        since_date (str, optional): ISO date string (YYYY-MM-DD) to filter items 
                                   created or modified since this date. If None, gets all items.
    
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
            logger.info(f"Fetching items from Quoter API created or modified since {since_date}: {endpoint}")
        else:
            logger.info(f"Fetching all items from Quoter API: {endpoint}")
        
        all_items = []
        
        if since_date:
            # Ensure date is in ISO 8601 format
            if 'T' not in since_date:
                # Old date-only format, convert to datetime
                since_date = f"{since_date}T00:00:00.000Z"
            elif not since_date.endswith('Z'):
                # Add timezone if missing
                since_date = f"{since_date}Z"
            
            # Get items created since the date
            created_items = _fetch_items_with_date_filter(endpoint, headers, "created_at[gt]", since_date)
            logger.info(f"Found {len(created_items)} items created since {since_date}")
            
            # Get items modified since the date
            modified_items = _fetch_items_with_date_filter(endpoint, headers, "modified_at[gt]", since_date)
            logger.info(f"Found {len(modified_items)} items modified since {since_date}")
            
            # Combine and deduplicate items
            all_items = _combine_and_deduplicate_items(created_items, modified_items)
            logger.info(f"Combined total: {len(all_items)} unique items")
        else:
            # Get all items without date filtering
            all_items = _fetch_items_with_date_filter(endpoint, headers, None, None)
        
        logger.info(f"✅ Successfully retrieved {len(all_items)} items from Quoter")
        return all_items
            
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

def create_or_find_contact_in_quoter(contact_name, contact_email=None, contact_phone=None, contact_mobile=None, pipedrive_contact_id=None, organization_name=None,
                                    billing_address=None, billing_address2=None, billing_city=None, billing_region_iso=None,
                                    billing_postal_code=None, billing_country_iso=None):
    """
    Create a new contact in Quoter or find existing one based on email and organization.
    
    Args:
        contact_name (str): Contact name
        contact_email (str, optional): Contact email
        contact_phone (str, optional): Contact phone
        pipedrive_contact_id (str, optional): Pipedrive person ID
        organization_name (str, optional): Organization name for better matching
        contact_mobile (str, optional): Mobile phone number
        billing_address (str, optional): Street line 1
        billing_address2 (str, optional): Street line 2 / suite
        billing_city (str, optional): City
        billing_region_iso (str, optional): State/region code
        billing_postal_code (str, optional): Zip/postal code
        billing_country_iso (str, optional): Country code (e.g. US)
        
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
        last_name = name_parts[1] if len(name_parts) > 1 else "Contact"  # Fallback for Quoter API requirement
        
        # Create contact with all required fields
        contact_data = {
            "first_name": first_name,
            "last_name": last_name,
            "organization": organization_name or "",
            "billing_country_iso": billing_country_iso or "US"
        }
        
        # Add email if available
        if contact_email:
            contact_data["email"] = contact_email
        
        # Add phone if available (use work_phone per Quoter API)
        if contact_phone:
            contact_data["work_phone"] = contact_phone
            logger.info(f"✅ Added work_phone: {contact_phone!r}")
        # Add mobile phone if available
        if contact_mobile:
            contact_data["mobile_phone"] = contact_mobile
            logger.info(f"✅ Added mobile_phone: {contact_mobile!r}")
        
        # Add Pipedrive reference if available
        if pipedrive_contact_id:
            contact_data["pipedrive_contact_id"] = str(pipedrive_contact_id)
        
        # Add billing address from webhook/Pipedrive if provided
        logger.info(f"🔍 Creating contact with address params: billing_address={billing_address!r}, billing_city={billing_city!r}, billing_state={billing_region_iso!r}, billing_postal={billing_postal_code!r}")
        if billing_address:
            contact_data["billing_address"] = billing_address
            logger.info(f"✅ Added billing_address: {billing_address!r}")
        if billing_address2:
            contact_data["billing_address2"] = billing_address2
            logger.info(f"✅ Added billing_address2: {billing_address2!r}")
        if billing_city:
            contact_data["billing_city"] = billing_city
            logger.info(f"✅ Added billing_city: {billing_city!r}")
        if billing_region_iso:
            contact_data["billing_region_iso"] = billing_region_iso
            logger.info(f"✅ Added billing_region_iso: {billing_region_iso!r}")
        if billing_postal_code:
            contact_data["billing_postal_code"] = billing_postal_code
            logger.info(f"✅ Added billing_postal_code: {billing_postal_code!r}")
        if billing_country_iso:
            contact_data["billing_country_iso"] = billing_country_iso
            logger.info(f"✅ Added billing_country_iso: {billing_country_iso!r}")
        # Mirror to shipping for now
        if billing_address:
            contact_data["shipping_address"] = billing_address
        if billing_address2:
            contact_data["shipping_address2"] = billing_address2
        if billing_city:
            contact_data["shipping_city"] = billing_city
        if billing_region_iso:
            contact_data["shipping_region_iso"] = billing_region_iso
        if billing_postal_code:
            contact_data["shipping_postal_code"] = billing_postal_code
        if billing_country_iso:
            contact_data["shipping_country_iso"] = billing_country_iso
        
        logger.info(f"Creating new contact in Quoter: {contact_name}")
        logger.info(f"🔍 Full contact_data being sent to Quoter API: {json.dumps(contact_data, indent=2)}")
        
        response = requests.post(
            "https://api.quoter.com/v1/contacts",
            json=contact_data,
            headers=headers,
            timeout=10
        )
        
        logger.info(f"🔍 Quoter API response status: {response.status_code}")
        if response.status_code not in (200, 201):
            logger.error(f"🔍 Quoter API response body: {response.text}")
        
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
        last_name = name_parts[1] if len(name_parts) > 1 else "Contact"  # Fallback for Quoter API requirement
        
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
                # Look for the "Basic" template first, then "Managed Service Proposal" as fallback
                preferred_template = None
                fallback_template = None
                
                for template in templates:
                    title = template.get("title", "")
                    if title == "Basic":  # Look for exact "Basic" template first
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
