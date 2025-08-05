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