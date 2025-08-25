import requests
import os
from dotenv import load_dotenv
from utils.logger import logger
from quoter import update_quoter_sku
from category_mapper import get_quoter_category_from_pipedrive_id, get_verified_subcategory_hierarchy
from dynamic_category_manager import get_or_create_category_mapping, get_or_create_subcategory_mapping

load_dotenv()
API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

def update_or_create_products(products):
    """
    Update or create products in Pipedrive based on Quoter data.
    
    Args:
        products (list): List of product data from Quoter
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return
    
    # Pipedrive API authentication
    # Based on testing, this API token works with URL parameter method
    headers = {
        "Content-Type": "application/json"
    }
    
    # Use URL parameter method (Method 4 from testing)
    params = {"api_token": API_TOKEN}
    
    for product in products:
        try:
            # Pipedrive product mapping - using supplier_sku as unique identifier
            pipedrive_product = {
                "name": product.get("name", "Unknown Product"),
                "code": product.get("code", ""),  # Using 'code' instead of 'sku'
                "description": product.get("description", ""),
                "unit": "piece",
                "tax": 0,
                "active_flag": True,
                "visible_to": 3  # 3 = Entire company
                # Removed owner_id - let Pipedrive assign default owner
            }
            
            # Add price if available
            if product.get("price_decimal"):
                pipedrive_product["price"] = float(product.get("price_decimal", 0))
            
            # Add cost if available (Pipedrive stores cost in prices array)
            if product.get("cost_decimal"):
                pipedrive_product["cost"] = float(product.get("cost_decimal", 0))
            
            # Add category and subcategory if available (Pipedrive has separate fields)
            if product.get("category_id"):
                # Get the verified category mapping from Pipedrive ID
                category_info = get_quoter_category_from_pipedrive_id(int(product.get("category_id")))
                
                if category_info:
                    # Use dynamic category manager to get or create mappings
                    pipedrive_category_id = get_or_create_category_mapping(category_info["name"])
                    
                    if pipedrive_category_id:
                        pipedrive_product["category"] = pipedrive_category_id
                        logger.info(f"Mapped category '{category_info['name']}' to Pipedrive ID {pipedrive_category_id}")
                        
                        # Check if there are subcategories for this category
                        hierarchy = get_verified_subcategory_hierarchy()
                        if category_info["name"] in hierarchy and hierarchy[category_info["name"]]:
                            # For now, we'll leave subcategory empty as it needs business logic
                            # This can be enhanced based on your specific requirements
                            logger.info(f"Category '{category_info['name']}' has subcategories: {hierarchy[category_info['name']]}")
                    else:
                        logger.warning(f"No category mapping found for '{category_info['name']}'")
                else:
                    logger.warning(f"No category info found for Pipedrive ID {product.get('category_id')}")
            
            # Check if product exists by sku (which maps to Pipedrive ID)
            sku = product.get("sku")
            existing_product = None
            
            if sku:
                # Product has sku, check if it exists in Pipedrive
                existing_product = find_product_by_id(sku, headers, params)
                logger.info(f"Checking for existing product with sku: {sku}")
            else:
                # No sku, this is a new product
                logger.info(f"New product (no sku): {product.get('name')}")
            
            if existing_product:
                # Check if product needs updating by comparing fields
                needs_update = False
                update_reasons = []
                
                # Compare key fields
                if existing_product.get("name") != pipedrive_product.get("name"):
                    needs_update = True
                    update_reasons.append("name")
                
                if existing_product.get("code") != pipedrive_product.get("code"):
                    needs_update = True
                    update_reasons.append("code")
                
                if existing_product.get("description") != pipedrive_product.get("description"):
                    needs_update = True
                    update_reasons.append("description")
                
                if existing_product.get("price") != pipedrive_product.get("price"):
                    needs_update = True
                    update_reasons.append("price")
                
                if existing_product.get("cost") != pipedrive_product.get("cost"):
                    needs_update = True
                    update_reasons.append("cost")
                
                if existing_product.get("category") != pipedrive_product.get("category"):
                    needs_update = True
                    update_reasons.append("category")
                
                if existing_product.get("ae55145d60840de457ff9e785eba68f0b39ab777") != pipedrive_product.get("ae55145d60840de457ff9e785eba68f0b39ab777"):
                    needs_update = True
                    update_reasons.append("subcategory")
                
                if needs_update:
                    # Update existing product
                    product_id = existing_product["id"]
                    response = requests.put(
                        f"{BASE_URL}/products/{product_id}",
                        json=pipedrive_product,
                        headers=headers,
                        params=params
                    )
                    response.raise_for_status()
                    logger.info(f"Updated product: {pipedrive_product['name']} (ID: {product_id}) - Changes: {', '.join(update_reasons)}")
                else:
                    logger.info(f"No updates needed for: {pipedrive_product['name']} (ID: {existing_product['id']})")
            else:
                # Create new product
                response = requests.post(
                    f"{BASE_URL}/products",
                    json=pipedrive_product,
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                
                # Get the new product ID from the response
                new_product_data = response.json()
                new_product_id = new_product_data.get("data", {}).get("id")
                
                if new_product_id:
                    logger.info(f"Created product: {pipedrive_product['name']} (ID: {new_product_id})")
                    
                    # Update Quoter with the new Pipedrive ID
                    update_quoter_sku(product.get("id"), new_product_id)
                else:
                    logger.error(f"Failed to get new product ID for: {pipedrive_product['name']}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error syncing product {product.get('name', 'Unknown')}: {e}")

def find_product_by_id(product_id, headers, params):
    """
    Find a product in Pipedrive by its ID.
    
    Args:
        product_id (str): Product ID to search for
        headers (dict): Request headers
        params (dict): URL parameters with authentication
        
    Returns:
        dict: Product data if found, None otherwise
    """
    if not product_id:
        return None
        
    try:
        response = requests.get(
            f"{BASE_URL}/products/{product_id}",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data")
        elif response.status_code == 404:
            # Product not found
            return None
        else:
            logger.error(f"Error searching for product with ID {product_id}: {response.status_code}")
            return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching for product with ID {product_id}: {e}")
        return None

def update_quoter_supplier_sku(quoter_item_id, pipedrive_product_id):
    """
    Update Quoter item with the new Pipedrive product ID.
    
    Args:
        quoter_item_id (str): Quoter item ID
        pipedrive_product_id (str): Pipedrive product ID
    """
    # This would require a PATCH request to Quoter API
    # For now, just log the update that would be needed
    logger.info(f"Would update Quoter item {quoter_item_id} with supplier_sku: {pipedrive_product_id}")
    
    # TODO: Implement actual Quoter API update
    # This would require:
    # 1. OAuth access token
    # 2. PATCH request to https://api.quoter.com/v1/items/{quoter_item_id}
    # 3. Request body: {"supplier_sku": pipedrive_product_id} 

def get_sub_organizations_ready_for_quotes():
    """
    Get sub-organizations that are ready for quote creation.
    Searches ALL organizations with pagination, not just specific owners.
    
    Returns:
        list: List of organizations with HID-QBO-Status = "QBO-SubCust"
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return []
    
    headers = {"Content-Type": "application/json"}
    
    try:
        all_organizations = []
        page = 1
        limit = 100
        
        # Get all organizations with pagination
        while True:
            # Add pagination parameters
            params = {
                "api_token": API_TOKEN,
                "limit": limit,
                "start": (page - 1) * limit  # Pipedrive uses 'start' parameter
            }
            
            logger.info(f"Fetching organizations page {page} (start: {params['start']})")
            
            response = requests.get(
                f"{BASE_URL}/organizations",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                organizations = data.get("data", [])
                
                all_organizations.extend(organizations)
                
                # Debug: Check if we're getting unique organizations
                unique_ids = set(org.get('id') for org in all_organizations)
                logger.info(f"Retrieved {len(organizations)} organizations (page: {page}, total so far: {len(all_organizations)}, unique IDs: {len(unique_ids)})")
                
                # Check if we're getting the same organizations repeatedly
                if len(all_organizations) != len(unique_ids):
                    logger.warning(f"⚠️  Duplicate organizations detected! Total: {len(all_organizations)}, Unique: {len(unique_ids)}")
                    # Remove duplicates and continue
                    all_organizations = list({org.get('id'): org for org in all_organizations}.values())
                    logger.info(f"Removed duplicates, now have {len(all_organizations)} unique organizations")
                
                # Check if there are more organizations
                # If we got exactly the limit, there might be more
                if len(organizations) < limit:
                    logger.info(f"Got {len(organizations)} organizations (less than limit {limit}), stopping pagination")
                    break
                
                # Safety check: if we're getting the same organizations repeatedly, stop
                if len(all_organizations) > 5000:  # Allow more organizations
                    logger.warning(f"⚠️  Stopping pagination at {len(all_organizations)} organizations to prevent endless loop")
                    break
                    
                page += 1
            else:
                logger.error(f"❌ API request failed with status {response.status_code}: {response.text}")
                break
        
        # Filter for sub-organizations ready for quotes (any owner)
        ready_orgs = []
        for org in all_organizations:
            # Check if has the right status (QBO-SubCust) regardless of owner
            # HID-QBO-Status field key: 454a3767bce03a880b31d78a38c480d6870e0f1b
            # Note: Pipedrive returns custom field values as strings, so compare as strings
            if str(org.get("454a3767bce03a880b31d78a38c480d6870e0f1b")) == "289":  # 289 = QBO-SubCust
                # Also check if it has an associated deal ID
                if org.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e"):  # Deal_ID field
                    ready_orgs.append(org)
                    owner_name = org.get("owner_id", {}).get("name", "Unknown")
                    logger.debug(f"Found ready organization {org.get('id')} ({org.get('name')}) owned by {owner_name}")
        
        logger.info(f"✅ Successfully retrieved {len(all_organizations)} total organizations from Pipedrive")
        logger.info(f"Found {len(ready_orgs)} organizations ready for quote creation (all owners)")
        return ready_orgs
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error connecting to Pipedrive API: {e}")
        return []

def get_deal_by_id(deal_id):
    """
    Get deal information by ID.
    
    Args:
        deal_id (int): Deal ID
        
    Returns:
        dict: Deal data if found, None otherwise
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(
            f"{BASE_URL}/deals/{deal_id}",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data")
        elif response.status_code == 404:
            logger.warning(f"Deal {deal_id} not found")
            return None
        else:
            logger.error(f"Error getting deal {deal_id}: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting deal {deal_id}: {e}")
        return None

def get_person_by_id(person_id):
    """
    Get person/contact information by ID.
    
    Args:
        person_id (int): Person ID
        
    Returns:
        dict: Person data if found, None otherwise
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(
            f"{BASE_URL}/persons/{person_id}",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            person_data = data.get("data")
            
            # Debug logging to see what fields we get from Pipedrive
            if person_data:
                logger.info(f"🔍 DEBUG: Pipedrive person {person_id} fields:")
                logger.info(f"   Available keys: {list(person_data.keys())}")
                
                # Check for address-related fields
                address_fields = [key for key in person_data.keys() if 'address' in key.lower() or 'postal' in key.lower()]
                if address_fields:
                    logger.info(f"   Address-related fields: {address_fields}")
                    for field in address_fields:
                        logger.info(f"      {field}: {person_data.get(field)}")
                else:
                    logger.info(f"   No address-related fields found")
                
                # Check for city, state, zip fields
                location_fields = [key for key in person_data.keys() if any(loc in key.lower() for loc in ['city', 'state', 'zip', 'postal', 'locality', 'admin'])]
                if location_fields:
                    logger.info(f"   Location-related fields: {location_fields}")
                    for field in location_fields:
                        logger.info(f"      {field}: {person_data.get(field)}")
                else:
                    logger.info(f"   No location-related fields found")
            
            return person_data
        elif response.status_code == 404:
            logger.warning(f"Person {person_id} not found")
            return None
        else:
            logger.error(f"Error getting person {person_id}: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting person {person_id}: {e}")
        return None

def get_organization_by_id(org_id):
    """
    Get organization information by ID.
    
    Args:
        org_id (int): Organization ID
        
    Returns:
        dict: Organization data if found, None otherwise
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(
            f"{BASE_URL}/organizations/{org_id}",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            org_data = data.get("data")
            
            # Debug logging to see what fields we get from Pipedrive
            if org_data:
                logger.info(f"🔍 DEBUG: Pipedrive organization {org_id} fields:")
                logger.info(f"   Available keys: {list(org_data.keys())}")
                
                # Check for address-related fields
                address_fields = [key for key in org_data.keys() if 'address' in key.lower()]
                if address_fields:
                    logger.info(f"   Address-related fields: {address_fields}")
                    for field in address_fields:
                        logger.info(f"      {field}: {org_data.get(field)}")
                else:
                    logger.info(f"   No address-related fields found")
                
                # Check for city, state, zip fields
                location_fields = [key for key in org_data.keys() if any(loc in key.lower() for loc in ['city', 'state', 'zip', 'postal'])]
                if location_fields:
                    logger.info(f"   Location-related fields: {location_fields}")
                    for field in location_fields:
                        logger.info(f"      {field}: {org_data.get(field)}")
                else:
                    logger.info(f"   No location-related fields found")
            
            return org_data
        elif response.status_code == 404:
            logger.warning(f"Organization {org_id} not found")
            return None
        else:
            logger.error(f"Error getting organization {org_id}: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting organization {org_id}: {e}")
        return None 

def get_organization_by_name(org_name):
    """
    Get organization information by name.
    
    Args:
        org_name (str): Organization name to search for
        
    Returns:
        dict: Organization data if found, None otherwise
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        # Search for organization by name
        response = requests.get(
            f"{BASE_URL}/organizations/search",
            headers=headers,
            params={**params, "term": org_name}
        )
        
        if response.status_code == 200:
            data = response.json()
            organizations = data.get("data", {}).get("items", [])
            
            # Look for exact match first
            for org in organizations:
                if org.get("item", {}).get("name") == org_name:
                    logger.info(f"✅ Found organization by name: {org_name}")
                    return org.get("item")
            
            # If no exact match, return the first one (closest match)
            if organizations:
                closest_match = organizations[0].get("item", {})
                logger.info(f"📍 Using closest organization match: {closest_match.get('name')} for search term: {org_name}")
                return closest_match
            
            logger.warning(f"Organization '{org_name}' not found")
            return None
        else:
            logger.error(f"Error searching for organization '{org_name}': {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching for organization '{org_name}': {e}")
        return None

def update_deal_with_quote_info(deal_id, quote_id, quote_number, quote_amount, quote_status, contact_data):
    """
    Update Pipedrive deal with quote information when a quote is published.
    
    Args:
        deal_id (str): Deal ID from organization name (e.g., "2096")
        quote_id (str): Quoter quote ID
        quote_number (str): Quote number assigned by Quoter
        quote_amount (str): Total quote amount
        quote_status (str): Quote status (pending, published, etc.)
        contact_data (dict): Contact information from Quoter
        
    Returns:
        bool: True if update successful, False otherwise
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return False
    
    try:
        # Convert deal_id to integer for Pipedrive API
        deal_id_int = int(deal_id)
        
        # First, get the current deal to preserve the original title
        headers = {"Content-Type": "application/json"}
        params = {"api_token": API_TOKEN}
        
        # Get current deal info
        deal_response = requests.get(
            f"{BASE_URL}/deals/{deal_id_int}",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if deal_response.status_code != 200:
            logger.error(f"❌ Failed to get deal {deal_id_int}: {deal_response.status_code}")
            return False
            
        current_deal = deal_response.json().get("data", {})
        original_title = current_deal.get("title", "")
        
        # Prepare update data - preserve original title, only update value and status
        update_data = {
            "title": original_title,  # Keep original deal name
            "value": float(quote_amount.replace(',', '').replace('$', '')),
            "status": "presented" if quote_status == "pending" else "presented"
        }
        
        # Add quote info to custom fields instead of overwriting title
        # Note: You'll need to map these to your actual Pipedrive custom field IDs
        custom_fields = {}
        
        # Example custom field mappings (update these with your actual field IDs)
        # custom_fields["quote_number"] = quote_number
        # custom_fields["quote_id"] = quote_id
        # custom_fields["quote_status"] = quote_status
        
        if custom_fields:
            update_data.update(custom_fields)
        
        logger.info(f"Updating Pipedrive deal {deal_id_int} with quote data:")
        logger.info(f"   Title: {update_data['title']} (preserved)")
        logger.info(f"   Value: ${update_data['value']}")
        logger.info(f"   Status: {update_data['status']}")
        
        # Update the deal
        response = requests.put(
            f"{BASE_URL}/deals/{deal_id_int}",
            headers=headers,
            params=params,
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Successfully updated Pipedrive deal {deal_id_int}")
            
            # Now update the contact's address information
            if update_contact_address(contact_data):
                logger.info(f"✅ Successfully updated contact address information")
            else:
                logger.warning(f"⚠️ Failed to update contact address information")
            
            return True
        else:
            logger.error(f"❌ Failed to update deal {deal_id_int}: {response.status_code} - {response.text}")
            return False
            
    except ValueError as e:
        logger.error(f"❌ Invalid deal ID format: {deal_id} - {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error updating Pipedrive deal {deal_id}: {e}")
        return False

def update_contact_address(contact_data):
    """
    Update contact address information in Pipedrive.
    
    Args:
        contact_data (dict): Contact information from Quoter
        
    Returns:
        bool: True if update successful, False otherwise
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return False
    
    try:
        # Debug logging to see what data we're receiving
        logger.info(f"🔍 DEBUG: Received contact_data: {contact_data}")
        logger.info(f"🔍 DEBUG: contact_data type: {type(contact_data)}")
        logger.info(f"🔍 DEBUG: contact_data keys: {list(contact_data.keys()) if isinstance(contact_data, dict) else 'Not a dict'}")
        
        # Extract contact information
        first_name = contact_data.get('first_name', '')
        last_name = contact_data.get('last_name', '')
        email = contact_data.get('email_address', '')
        organization = contact_data.get('organization', '')
        
        logger.info(f"🔍 DEBUG: Extracted values - first_name: '{first_name}', last_name: '{last_name}', email: '{email}', organization: '{organization}'")
        
        if not email:
            logger.warning("No email address found in contact data")
            logger.warning(f"🔍 DEBUG: Available fields in contact_data: {list(contact_data.keys()) if isinstance(contact_data, dict) else 'Not a dict'}")
            return False
        
        # Search for the contact by email
        headers = {"Content-Type": "application/json"}
        params = {"api_token": API_TOKEN}
        
        search_response = requests.get(
            f"{BASE_URL}/persons/search",
            headers=headers,
            params={**params, "term": email},
            timeout=10
        )
        
        if search_response.status_code != 200:
            logger.error(f"❌ Failed to search for contact: {search_response.status_code}")
            return False
        
        search_results = search_response.json().get("data", {}).get("items", [])
        
        if not search_results:
            logger.warning(f"No contact found with email: {email}")
            return False
        
        # Get the first matching contact
        contact = search_results[0].get("item", {})
        contact_id = contact.get("id")
        
        if not contact_id:
            logger.error("No contact ID found in search results")
            return False
        
        # Prepare address update data
        addresses = contact_data.get('addresses', {})
        billing_address = addresses.get('billing', {})
        
        if not billing_address:
            logger.warning("No billing address found in contact data")
            return False
        
        # Build single address string (like Google Maps format)
        address_parts = []
        
        # Add street address
        if billing_address.get('line1'):
            address_parts.append(billing_address['line1'])
        if billing_address.get('line2'):
            address_parts.append(billing_address['line2'])
        
        # Add city, state, zip fields
        if billing_address.get('city'):
            address_parts.append(billing_address['city'])
        if billing_address.get('state', {}).get('code'):
            address_parts.append(billing_address['state']['code'])
        if billing_address.get('postal_code'):
            address_parts.append(billing_address['postal_code'])
        
        # Combine into single address string
        full_address = ", ".join(filter(None, address_parts))
        
        # Update contact with new address information - populate all individual fields for QuickBooks integration
        update_data = {
            "name": f"{first_name} {last_name}".strip(),
            "org_name": organization,
            "email": [{"value": email, "primary": True, "label": "work"}],
            "phone": [{"value": contact_data.get('telephone_numbers', {}).get('work', ''), "label": "work"}],
            # Populate all individual address fields for QuickBooks integration
            "postal_address": full_address,
            "postal_address_subpremise": billing_address.get('line2', ''),  # Apartment/suite number
            "postal_address_street_number": billing_address.get('line1', '').split()[0] if billing_address.get('line1') else '',
            "postal_address_route": ' '.join(billing_address.get('line1', '').split()[1:]) if billing_address.get('line1') else '',
            "postal_address_locality": billing_address.get('city', ''),
            "postal_address_admin_area_level_1": billing_address.get('state', {}).get('code', ''),
            "postal_address_postal_code": billing_address.get('postal_code', ''),
            "postal_address_country": billing_address.get('country', {}).get('code', '')
        }
        
        logger.info(f"Updating contact {contact_id} with address: {full_address}")
        
        # Update the contact
        update_response = requests.put(
            f"{BASE_URL}/persons/{contact_id}",
            headers=headers,
            params=params,
            json=update_data,
            timeout=10
        )
        
        if update_response.status_code == 200:
            logger.info(f"✅ Successfully updated contact {contact_id} address")
            return True
        else:
            logger.error(f"❌ Failed to update contact {contact_id}: {update_response.status_code} - {update_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating contact address: {e}")
        return False 

def update_organization_address(org_id, contact_data):
    """
    Update organization address fields in Pipedrive using address data from Quoter contact.
    
    Args:
        org_id (int): Organization ID in Pipedrive
        contact_data (dict): Contact data from Quoter with address information
        
    Returns:
        bool: True if update successful, False otherwise
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found in environment variables")
        return False
    
    try:
        # Extract address information from contact data
        addresses = contact_data.get('addresses', {})
        billing_address = addresses.get('billing', {})
        
        if not billing_address:
            logger.warning("⚠️ No billing address found in contact data")
            return False
        
        # Extract address components
        line1 = billing_address.get('line1', '')
        line2 = billing_address.get('line2', '')
        city = billing_address.get('city', '')
        state = billing_address.get('state', {})
        state_code = state.get('code', '') if isinstance(state, dict) else state
        postal_code = billing_address.get('postal_code', '')
        country = billing_address.get('country', {})
        country_code = country.get('code', '') if isinstance(country, dict) else country
        
        # Build full address string (Google Maps style)
        address_parts = []
        if line1:
            address_parts.append(line1)
        if line2:
            address_parts.append(line2)
        if city:
            address_parts.append(city)
        if state_code:
            address_parts.append(state_code)
        if postal_code:
            address_parts.append(postal_code)
        if country_code:
            address_parts.append(country_code)
        
        full_address = ', '.join(address_parts) if address_parts else ''
        
        # Prepare update data for organization
        update_data = {
            # Full address string
            "address": full_address,
            # Individual address components for QuickBooks integration
            "address_subpremise": line2 or None,  # Apartment/suite number
            "address_street_number": line1.split()[0] if line1 else None,
            "address_route": ' '.join(line1.split()[1:]) if line1 and len(line1.split()) > 1 else None,
            "address_locality": city or None,
            "address_admin_area_level_1": state_code or None,
            "address_postal_code": postal_code or None,
            "address_country": country_code or None
        }
        
        # Remove None values to avoid overwriting with empty data
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        logger.info(f"🔄 Updating organization {org_id} address:")
        logger.info(f"   Full Address: {full_address}")
        logger.info(f"   Individual Fields: {update_data}")
        
        # Log each field being updated with its value
        logger.info(f"🔍 DEBUG: Organization address update details:")
        logger.info(f"   Input data - line1: '{line1}', line2: '{line2}', city: '{city}', state: '{state_code}', postal: '{postal_code}', country: '{country_code}'")
        logger.info(f"   Pipedrive field mappings:")
        for field, value in update_data.items():
            logger.info(f"      {field}: '{value}'")
        
        # Log what we're NOT updating (None values)
        none_fields = [k for k, v in update_data.items() if v is None]
        if none_fields:
            logger.info(f"   Fields with None values (not updating): {none_fields}")
        
        logger.info(f"   Total fields to update: {len(update_data)}")
        logger.info(f"   Pipedrive API endpoint: {BASE_URL}/organizations/{org_id}")
        
        # Update the organization
        headers = {"Content-Type": "application/json"}
        params = {"api_token": API_TOKEN}
        
        logger.info(f"📡 Sending PUT request to Pipedrive API...")
        logger.info(f"   Headers: {headers}")
        logger.info(f"   Params: {params}")
        logger.info(f"   Request body: {update_data}")
        
        response = requests.put(
            f"{BASE_URL}/organizations/{org_id}",
            json=update_data,
            headers=headers,
            params=params
        )
        
        logger.info(f"📡 Pipedrive API response:")
        logger.info(f"   Status Code: {response.status_code}")
        logger.info(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code in [200, 201]:
            try:
                response_data = response.json()
                logger.info(f"   Response Body: {response_data}")
                
                # Check if the response contains the updated fields
                if 'data' in response_data:
                    updated_org = response_data['data']
                    logger.info(f"✅ Organization update response details:")
                    logger.info(f"   Updated Organization ID: {updated_org.get('id')}")
                    logger.info(f"   Updated Organization Name: {updated_org.get('name')}")
                    
                    # Log the address fields that were returned
                    address_fields_returned = {k: v for k, v in updated_org.items() if 'address' in k.lower()}
                    if address_fields_returned:
                        logger.info(f"   Address fields in response: {address_fields_returned}")
                    else:
                        logger.info(f"   No address fields found in response")
                        
            except Exception as e:
                logger.warning(f"⚠️ Could not parse response JSON: {e}")
                logger.info(f"   Raw response text: {response.text[:500]}")
            
            logger.info(f"✅ Successfully updated organization {org_id} address")
            return True
        else:
            logger.error(f"❌ Failed to update organization {org_id} address: {response.status_code}")
            logger.error(f"   Response text: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating organization {org_id} address: {e}")
        return False 