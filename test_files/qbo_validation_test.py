#!/usr/bin/env python3
"""
QBO Validation Test - Dry Run Mode
Validates data and checks for duplicates WITHOUT creating anything in QBO
"""

import os
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import logger

# Load environment variables
load_dotenv()

class QBOValidator:
    """QuickBooks Online validation client (read-only)"""
    
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
            
            logger.info("✅ Successfully refreshed QBO access token")
            return True
        else:
            logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
            return False
    
    def get_headers(self):
        """Get headers for QBO API requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_existing_items(self):
        """Get all existing items from QBO (READ ONLY)"""
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

def get_quoter_items_since(since_date):
    """Get items from Quoter modified since a specific date"""
    from quoter import get_access_token
    
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get Quoter OAuth access token")
        return []
    
    url = "https://api.quoter.com/v1/items"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    params = {}
    if since_date:
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
    """Convert Quoter item to QBO item format with validation"""
    # Get basic item info
    name = quoter_item.get('name', '')
    sku = quoter_item.get('sku', '')
    description = quoter_item.get('description', '')
    
    # Validate required fields
    if not name:
        return {"error": "Missing name", "item": quoter_item}
    
    # Get price and validate
    unit_price = quoter_item.get('price', 0)
    if not isinstance(unit_price, (int, float)) or unit_price < 0:
        unit_price = 0
    
    # Get cost information
    cost = quoter_item.get('cost', 0)
    if not isinstance(cost, (int, float)) or cost < 0:
        cost = 0
    
    # Get category info
    category = quoter_item.get('category', {})
    if isinstance(category, dict):
        category_name = category.get('name', '')
    else:
        category_name = str(category) if category else ''
    subcategory = quoter_item.get('subcategory', '')
    
    # Determine item type
    if sku and sku.startswith('SVC'):
        item_type = 'Service'
    elif category_name and 'equipment' in category_name.lower():
        item_type = 'Inventory'
    else:
        item_type = 'Service'
    
    # Build QBO item data
    qbo_item = {
        "Name": name,
        "Type": item_type,
        "UnitPrice": unit_price,
        "IncomeAccountRef": {
            "value": "250"
        }
    }
    
    # Add optional fields
    if description:
        qbo_item["Description"] = description
    
    if sku:
        qbo_item["Sku"] = sku
    
    if item_type == 'Inventory' and cost > 0:
        qbo_item["PurchaseCost"] = cost
        qbo_item["ExpenseAccountRef"] = {
            "value": "251"
        }
    
    # Add category info
    if category_name or subcategory:
        category_info = []
        if category_name:
            category_info.append(f"Category: {category_name}")
        if subcategory:
            category_info.append(f"Subcategory: {subcategory}")
        
        if category_info:
            if "Description" in qbo_item:
                qbo_item["Description"] += f" | {' | '.join(category_info)}"
            else:
                qbo_item["Description"] = " | ".join(category_info)
    
    return qbo_item

def find_existing_item(quoter_item, existing_items):
    """Find existing QBO item by multiple criteria"""
    name = quoter_item.get('name', '')
    sku = quoter_item.get('sku', '')
    
    matches = []
    
    # Match by SKU (most reliable)
    if sku:
        for item in existing_items:
            if item.get('Sku') == sku:
                matches.append(("SKU", item))
    
    # Match by exact name
    if name:
        for item in existing_items:
            if item.get('Name') == name:
                matches.append(("Name", item))
    
    # Fuzzy name matching
    if name:
        name_clean = name.strip().lower()
        for item in existing_items:
            item_name_clean = item.get('Name', '').strip().lower()
            if item_name_clean == name_clean and item not in [m[1] for m in matches]:
                matches.append(("Fuzzy Name", item))
    
    return matches

def validate_qbo_item(qbo_item):
    """Validate QBO item data before creation"""
    errors = []
    warnings = []
    
    # Check required fields
    if not qbo_item.get('Name'):
        errors.append("Missing Name")
    
    if not qbo_item.get('Type'):
        errors.append("Missing Type")
    
    if qbo_item.get('UnitPrice') is None:
        errors.append("Missing UnitPrice")
    
    # Check price validity
    unit_price = qbo_item.get('UnitPrice', 0)
    if not isinstance(unit_price, (int, float)) or unit_price < 0:
        errors.append(f"Invalid UnitPrice: {unit_price}")
    
    # Check SKU format
    sku = qbo_item.get('Sku', '')
    if sku and len(sku) > 50:
        warnings.append(f"SKU too long: {len(sku)} characters (max 50)")
    
    # Check name length
    name = qbo_item.get('Name', '')
    if len(name) > 100:
        warnings.append(f"Name too long: {len(name)} characters (max 100)")
    
    # Check description length
    description = qbo_item.get('Description', '')
    if len(description) > 1000:
        warnings.append(f"Description too long: {len(description)} characters (max 1000)")
    
    return errors, warnings

def run_validation_test():
    """Run comprehensive validation test (DRY RUN ONLY)"""
    logger.info("🔍 Starting QBO Validation Test (DRY RUN - NO CHANGES WILL BE MADE)")
    
    try:
        # Initialize QBO validator
        qbo = QBOValidator()
        
        # Get existing QBO items
        logger.info("Fetching existing QBO items...")
        existing_items = qbo.get_existing_items()
        
        # Get Quoter items
        logger.info("Fetching Quoter items...")
        quoter_items = get_quoter_items_since("2025-08-01T00:00:00.000Z")  # Get recent items
        
        if not quoter_items:
            logger.info("No Quoter items found")
            return
        
        # Validation results
        validation_results = {
            'total_quoter_items': len(quoter_items),
            'valid_items': 0,
            'invalid_items': 0,
            'duplicate_items': 0,
            'new_items': 0,
            'update_items': 0,
            'errors': [],
            'warnings': []
        }
        
        logger.info(f"\n📊 VALIDATION RESULTS:")
        logger.info(f"Quoter items to process: {len(quoter_items)}")
        logger.info(f"Existing QBO items: {len(existing_items)}")
        
        for i, quoter_item in enumerate(quoter_items, 1):
            item_name = quoter_item.get('name', f'Item {i}')
            logger.info(f"\n--- Processing Item {i}/{len(quoter_items)}: '{item_name}' ---")
            
            # Convert to QBO format
            qbo_item = convert_quoter_to_qbo_item(quoter_item)
            
            if 'error' in qbo_item:
                validation_results['invalid_items'] += 1
                validation_results['errors'].append(f"Item '{item_name}': {qbo_item['error']}")
                logger.error(f"❌ {qbo_item['error']}")
                continue
            
            # Validate QBO item
            errors, warnings = validate_qbo_item(qbo_item)
            
            if errors:
                validation_results['invalid_items'] += 1
                validation_results['errors'].extend([f"Item '{item_name}': {error}" for error in errors])
                logger.error(f"❌ Validation errors: {', '.join(errors)}")
                continue
            
            if warnings:
                validation_results['warnings'].extend([f"Item '{item_name}': {warning}" for warning in warnings])
                logger.warning(f"⚠️  Warnings: {', '.join(warnings)}")
            
            # Check for duplicates
            existing_matches = find_existing_item(quoter_item, existing_items)
            
            if existing_matches:
                validation_results['duplicate_items'] += 1
                validation_results['update_items'] += 1
                logger.info(f"🔄 Would UPDATE existing item:")
                for match_type, existing_item in existing_matches:
                    logger.info(f"   {match_type} match: '{existing_item.get('Name')}' (ID: {existing_item.get('Id')})")
                    logger.info(f"   Current QBO: Price=${existing_item.get('UnitPrice', 0)}, SKU={existing_item.get('Sku', 'N/A')}")
                    logger.info(f"   New data: Price=${qbo_item.get('UnitPrice', 0)}, SKU={qbo_item.get('Sku', 'N/A')}")
            else:
                validation_results['new_items'] += 1
                logger.info(f"➕ Would CREATE new item:")
                logger.info(f"   Name: {qbo_item.get('Name')}")
                logger.info(f"   Type: {qbo_item.get('Type')}")
                logger.info(f"   Price: ${qbo_item.get('UnitPrice', 0)}")
                logger.info(f"   SKU: {qbo_item.get('Sku', 'N/A')}")
                logger.info(f"   Description: {qbo_item.get('Description', 'N/A')[:100]}...")
            
            validation_results['valid_items'] += 1
        
        # Final summary
        logger.info(f"\n🎯 VALIDATION SUMMARY:")
        logger.info(f"✅ Valid items: {validation_results['valid_items']}")
        logger.info(f"❌ Invalid items: {validation_results['invalid_items']}")
        logger.info(f"🔄 Would update: {validation_results['update_items']}")
        logger.info(f"➕ Would create: {validation_results['new_items']}")
        logger.info(f"⚠️  Warnings: {len(validation_results['warnings'])}")
        logger.info(f"❌ Errors: {len(validation_results['errors'])}")
        
        if validation_results['errors']:
            logger.info(f"\n❌ ERRORS FOUND:")
            for error in validation_results['errors'][:10]:  # Show first 10 errors
                logger.info(f"   {error}")
            if len(validation_results['errors']) > 10:
                logger.info(f"   ... and {len(validation_results['errors']) - 10} more errors")
        
        if validation_results['warnings']:
            logger.info(f"\n⚠️  WARNINGS:")
            for warning in validation_results['warnings'][:10]:  # Show first 10 warnings
                logger.info(f"   {warning}")
            if len(validation_results['warnings']) > 10:
                logger.info(f"   ... and {len(validation_results['warnings']) - 10} more warnings")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        if validation_results['invalid_items'] > 0:
            logger.info("   ❌ Fix validation errors before running sync")
        if validation_results['duplicate_items'] > 0:
            logger.info("   🔄 Review duplicate detection logic")
        if validation_results['new_items'] > 0:
            logger.info("   ➕ New items look good for creation")
        
        if validation_results['invalid_items'] == 0 and validation_results['errors'] == 0:
            logger.info("   ✅ All items passed validation - ready for sync!")
        else:
            logger.info("   ⚠️  Fix issues before running actual sync")
        
    except Exception as e:
        logger.error(f"Validation test failed: {e}")

if __name__ == "__main__":
    run_validation_test()




