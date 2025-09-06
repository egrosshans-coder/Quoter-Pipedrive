#!/usr/bin/env python3
"""
Direct sync from Quoter to QuickBooks Online
"""
import os
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import logger

# Load environment variables
load_dotenv()

class QBOClient:
    """QuickBooks Online API client"""
    
    def __init__(self):
        self.client_id = os.getenv('QBO_CLIENT_ID')
        self.client_secret = os.getenv('QBO_CLIENT_SECRET')
        self.company_id = os.getenv('QBO_COMPANY_ID')
        self.access_token = os.getenv('QBO_ACCESS_TOKEN')
        self.refresh_token = os.getenv('QBO_REFRESH_TOKEN')
        
        if not all([self.client_id, self.client_secret, self.company_id]):
            raise ValueError("Missing QBO credentials in .env file")
    
    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False
        
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        logger.info("Refreshing QBO access token...")
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = result.get('access_token')
            if result.get('refresh_token'):
                self.refresh_token = result.get('refresh_token')
            
            # Save new tokens to .env file
            self._save_tokens_to_env()
            
            logger.info("✅ Successfully refreshed QBO access token")
            return True
        else:
            error_data = response.json() if response.text else {}
            error_type = error_data.get('error', 'unknown')
            
            if error_type == 'invalid_grant':
                logger.error("❌ Refresh token has expired. You need to get new tokens from Google Scripts.")
                logger.error("🔧 Steps to fix:")
                logger.error("   1. Go to your Google Scripts project")
                logger.error("   2. Run the forceRefreshToken() function")
                logger.error("   3. Copy the new access token")
                logger.error("   4. Update QBO_ACCESS_TOKEN in .env file")
                logger.error("   5. Update QBO_REFRESH_TOKEN in .env file if provided")
            else:
                logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
            return False
    
    def _save_tokens_to_env(self):
        """Save updated tokens to .env file"""
        try:
            # Read current .env file
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # Update or add token lines
            token_lines = {
                'QBO_ACCESS_TOKEN': self.access_token,
                'QBO_REFRESH_TOKEN': self.refresh_token
            }
            
            # Update existing lines or add new ones
            updated_lines = []
            found_keys = set()
            
            for line in lines:
                line_stripped = line.strip()
                if '=' in line_stripped:
                    key = line_stripped.split('=')[0].strip()
                    if key in token_lines:
                        updated_lines.append(f"{key}={token_lines[key]}\n")
                        found_keys.add(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Add any missing keys
            for key, value in token_lines.items():
                if key not in found_keys:
                    updated_lines.append(f"{key}={value}\n")
            
            # Write back to file
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
            
            logger.info("✅ Updated tokens in .env file")
            
        except Exception as e:
            logger.error(f"Failed to save tokens to .env: {e}")
    
    def get_headers(self):
        """Get headers for QBO API requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_existing_items(self):
        """Get all existing items from QBO"""
        url = f"https://quickbooks.api.intuit.com/v3/company/{self.company_id}/query"
        headers = self.get_headers()
        
        query = "SELECT * FROM Item"
        params = {'query': query}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 401:
                # Token expired, try to refresh
                logger.info("Access token expired, refreshing...")
                if self.refresh_access_token():
                    headers = self.get_headers()
                    response = requests.get(url, headers=headers, params=params)
                else:
                    raise Exception("Cannot refresh access token")
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('QueryResponse', {}).get('Item', [])
                logger.info(f"Found {len(items)} existing QBO items")
                return items
            else:
                logger.error(f"Failed to fetch QBO items: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching QBO items: {e}")
            return []
    
    def create_item(self, item_data):
        """Create a new item in QBO"""
        url = f"https://quickbooks.api.intuit.com/v3/company/{self.company_id}/item"
        headers = self.get_headers()
        
        response = requests.post(url, headers=headers, json=item_data)
        
        if response.status_code == 401:
            # Token expired, try to refresh
            logger.info("Access token expired, refreshing...")
            if self.refresh_access_token():
                headers = self.get_headers()
                response = requests.post(url, headers=headers, json=item_data)
            else:
                raise Exception("Cannot refresh access token")
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            # Parse create response correctly
            item = data.get('Item', {})
            logger.info(f"✅ Created QBO item: {item.get('Name', 'Unknown')} (ID: {item.get('Id', 'Unknown')})")
            return item
        else:
            logger.error(f"Failed to create QBO item: {response.status_code} - {response.text}")
            return None
    
    def update_item(self, item_id, item_data):
        """Update an existing item in QBO"""
        url = f"https://quickbooks.api.intuit.com/v3/company/{self.company_id}/item"
        headers = self.get_headers()
        
        # Add the item ID to the data
        item_data['Id'] = item_id
        
        response = requests.post(url, headers=headers, json=item_data)
        
        if response.status_code == 401:
            # Token expired, try to refresh
            logger.info("Access token expired, refreshing...")
            if self.refresh_access_token():
                headers = self.get_headers()
                response = requests.post(url, headers=headers, json=item_data)
            else:
                raise Exception("Cannot refresh access token")
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            # Parse update response correctly
            item = data.get('Item', {})
            logger.info(f"✅ Updated QBO item: {item.get('Name', 'Unknown')} (ID: {item.get('Id', 'Unknown')})")
            return item
        else:
            logger.error(f"Failed to update QBO item: {response.status_code} - {response.text}")
            return None

def get_quoter_items_since(since_date):
    """Get items from Quoter modified since a specific date"""
    # Get Quoter API credentials
    quoter_token = os.getenv('QUOTER_API_TOKEN')
    if not quoter_token:
        logger.error("Missing QUOTER_API_TOKEN in .env")
        return []
    
    # Quoter API endpoint
    url = "https://api.quoter.com/v1/items"
    headers = {
        "Authorization": f"Bearer {quoter_token}",
        "Content-Type": "application/json"
    }
    
    # Build date filter
    params = {}
    if since_date:
        # Ensure date is in ISO 8601 format
        if 'T' not in since_date:
            since_date = f"{since_date}T00:00:00.000Z"
        elif not since_date.endswith('Z'):
            since_date = f"{since_date}Z"
        
        params['modified_at[gt]'] = since_date
    
    logger.info(f"Fetching items from Quoter modified since {since_date}...")
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch Quoter items: {response.status_code} - {response.text}")
        return []
    
    data = response.json()
    items = data.get('data', [])
    logger.info(f"Found {len(items)} items from Quoter")
    return items

def convert_quoter_to_qbo_item(quoter_item):
    """Convert Quoter item to QBO item format"""
    # Get basic item info
    name = quoter_item.get('name', '')
    sku = quoter_item.get('sku', '')
    description = quoter_item.get('description', '')
    
    # Validate required fields
    if not name:
        logger.warning("Skipping item with no name")
        return None
    
    # Get price and validate
    unit_price = quoter_item.get('price', 0)
    if not isinstance(unit_price, (int, float)) or unit_price < 0:
        logger.warning(f"Invalid price for item '{name}': {unit_price}, using 0")
        unit_price = 0
    
    # Get category info (for reference only)
    category = quoter_item.get('category', {})
    category_name = category.get('name', '') if category else ''
    subcategory = quoter_item.get('subcategory', '')
    
    # Determine item type based on SKU
    if sku and sku.startswith('SVC'):
        item_type = 'Service'
    else:
        item_type = 'Service'  # Use Service for all items (QBO limitation)
    
    # Build QBO item data
    qbo_item = {
        "Name": name,
        "Type": item_type,
        "UnitPrice": unit_price,
        "IncomeAccountRef": {
            "value": "250"  # Consulting Income account
        }
    }
    
    # Add description if available
    if description:
        qbo_item["Description"] = description
    
    # Add SKU if available
    if sku:
        qbo_item["Sku"] = sku
    
    # Note: Category handling removed - QBO categories need to be created first
    # and referenced by ID, not name. This would require additional API calls.
    
    return qbo_item

def get_last_sync_date():
    """Get the last sync date from a file or return a default date."""
    last_sync_file = "last_quoter_qbo_sync_date.txt"
    
    if os.path.exists(last_sync_file):
        try:
            with open(last_sync_file, 'r') as f:
                date_str = f.read().strip()
                return date_str
        except Exception as e:
            logger.error(f"Error reading last sync date: {e}")
    
    # Return a date from 7 days ago as default
    from datetime import datetime, timedelta
    default_date = datetime.now() - timedelta(days=7)
    return default_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def save_sync_date():
    """Save the current datetime as the last sync date."""
    last_sync_file = "last_quoter_qbo_sync_date.txt"
    
    try:
        current_time = datetime.now()
        date_str = current_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        with open(last_sync_file, 'w') as f:
            f.write(date_str)
        
        logger.info(f"Saved sync date: {date_str}")
    except Exception as e:
        logger.error(f"Error saving sync date: {e}")

def sync_quoter_to_qbo():
    """Main sync function: Quoter → QBO"""
    logger.info("🚀 Starting Quoter → QBO sync...")
    
    try:
        # Initialize QBO client
        qbo = QBOClient()
        
        # Get last sync date
        last_sync_date = get_last_sync_date()
        logger.info(f"🕐 Syncing items modified since: {last_sync_date}")
        
        # Get existing QBO items
        logger.info("Fetching existing QBO items...")
        existing_items = qbo.get_existing_items()
        existing_by_name = {item.get('Name'): item for item in existing_items if item.get('Name')}
        logger.info(f"Found {len(existing_by_name)} existing QBO items by name")
        
        # Get Quoter items to sync
        quoter_items = get_quoter_items_since(last_sync_date)
        
        if not quoter_items:
            logger.info("No items to sync")
            return
        
        # Process each item
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for item in quoter_items:
            try:
                # Convert to QBO format
                qbo_item = convert_quoter_to_qbo_item(item)
                
                # Skip if conversion failed
                if not qbo_item:
                    continue
                
                # Check if item already exists by name
                item_name = qbo_item.get('Name')
                logger.info(f"Processing item: '{item_name}'")
                
                if item_name in existing_by_name:
                    # Update existing item
                    existing_item = existing_by_name[item_name]
                    item_id = existing_item.get('Id')
                    
                    logger.info(f"Updating existing QBO item: {item_name}")
                    result = qbo.update_item(item_id, qbo_item)
                    
                    if result:
                        updated_count += 1
                    else:
                        error_count += 1
                else:
                    # Create new item
                    logger.info(f"Creating new QBO item: {item_name}")
                    result = qbo.create_item(qbo_item)
                    
                    if result:
                        created_count += 1
                        # Add to existing items cache
                        existing_by_name[item_name] = result
                    else:
                        error_count += 1
                        
            except Exception as e:
                logger.error(f"Error processing item '{item.get('name', 'Unknown')}': {e}")
                error_count += 1
        
        # Save sync date
        save_sync_date()
        
        # Summary
        logger.info(f"📊 Sync Summary:")
        logger.info(f"   Created: {created_count}")
        logger.info(f"   Updated: {updated_count}")
        logger.info(f"   Errors: {error_count}")
        logger.info(f"   Total processed: {len(quoter_items)}")
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")

if __name__ == "__main__":
    sync_quoter_to_qbo()