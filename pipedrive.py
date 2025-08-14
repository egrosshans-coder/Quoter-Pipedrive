import requests
import os
from dotenv import load_dotenv
from utils.logger import logger
from quoter import update_quoter_sku
from category_mapper import get_category_path
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
                # Get the full category path (e.g., "Tanks / 1-to-3 Splitter")
                full_category_path = get_category_path(product.get("category_id"))
                
                if full_category_path and " / " in full_category_path:
                    # Split the path into category and subcategory
                    category_parts = full_category_path.split(" / ", 1)
                    main_category = category_parts[0]
                    subcategory = category_parts[1]
                    
                    # Use dynamic category manager to get or create mappings
                    pipedrive_category_id = get_or_create_category_mapping(main_category)
                    pipedrive_subcategory_id = get_or_create_subcategory_mapping(subcategory)
                    
                    if pipedrive_category_id:
                        pipedrive_product["category"] = pipedrive_category_id
                        logger.info(f"Mapped main category '{main_category}' to Pipedrive ID {pipedrive_category_id}")
                    else:
                        logger.warning(f"No category mapping found for '{main_category}'")
                    
                    if pipedrive_subcategory_id:
                        # Use the custom field key for subcategory
                        pipedrive_product["ae55145d60840de457ff9e785eba68f0b39ab777"] = pipedrive_subcategory_id
                        logger.info(f"Mapped subcategory '{subcategory}' to Pipedrive ID {pipedrive_subcategory_id}")
                    else:
                        logger.warning(f"No subcategory mapping found for '{subcategory}'")
                        
                elif full_category_path:
                    # Single category (no subcategory)
                    pipedrive_category_id = get_or_create_category_mapping(full_category_path)
                    
                    if pipedrive_category_id:
                        pipedrive_product["category"] = pipedrive_category_id
                        logger.info(f"Mapped category '{full_category_path}' to Pipedrive ID {pipedrive_category_id}")
                    else:
                        logger.warning(f"No category mapping found for '{full_category_path}'")
                else:
                    logger.warning(f"Could not resolve category path for category_id: {product.get('category_id')}")
            
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
            return data.get("data")
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
            return data.get("data")
        elif response.status_code == 404:
            logger.warning(f"Organization {org_id} not found")
            return None
        else:
            logger.error(f"Error getting organization {org_id}: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting organization {org_id}: {e}")
        return None 