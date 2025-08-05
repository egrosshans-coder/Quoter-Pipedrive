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