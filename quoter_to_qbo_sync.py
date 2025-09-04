#!/usr/bin/env python3
"""
Direct Quoter to QuickBooks Online Service Synchronization

This script creates services directly in QBO from Quoter, bypassing Pipedrive entirely.
This eliminates the need for manual CSV export/import and creates a clean sync path.
"""

import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
from quoter import get_quoter_products, get_access_token
from utils.logger import logger

load_dotenv()

class QuickBooksOnlineAPI:
    """QuickBooks Online API client for service management."""
    
    def __init__(self):
        self.base_url = "https://sandbox-quickbooks.api.intuit.com" if os.getenv('QBO_SANDBOX') == 'true' else "https://quickbooks.api.intuit.com"
        self.company_id = os.getenv('QBO_COMPANY_ID')
        if not self.company_id:
            logger.error("❌ QBO_COMPANY_ID not found in environment variables")
        self.access_token = None
        self.refresh_token = os.getenv('QBO_REFRESH_TOKEN')
        self.client_id = os.getenv('QBO_CLIENT_ID')
        self.client_secret = os.getenv('QBO_CLIENT_SECRET')
        
    def get_access_token(self):
        """Get OAuth access token for QBO API."""
        if not self.refresh_token:
            logger.error("❌ QBO_REFRESH_TOKEN not found in environment variables")
            return None
            
        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data, auth=(self.client_id, self.client_secret))
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            
            if self.access_token:
                logger.info("✅ Successfully obtained QBO access token")
                return self.access_token
            else:
                logger.error("❌ No access token in QBO response")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error getting QBO access token: {e}")
            return None
    
    def create_service(self, quoter_item):
        """Create a service in QuickBooks Online from Quoter item data."""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Map Quoter item to QBO service format
        qbo_service = self._map_quoter_to_qbo_service(quoter_item)
        
        url = f"{self.base_url}/v3/company/{self.company_id}/items"
        
        try:
            logger.info(f"📤 Creating QBO service: {qbo_service['Name']}")
            
            response = requests.post(url, json=qbo_service, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                item = result.get("QueryResponse", {}).get("Item", [{}])[0]
                logger.info(f"✅ Successfully created QBO service: {item.get('Name')} (ID: {item.get('Id')})")
                return item
            else:
                logger.error(f"❌ Failed to create QBO service: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error creating QBO service: {e}")
            return None
    
    def _map_quoter_to_qbo_service(self, quoter_item):
        """Map Quoter item data to QBO service format."""
        return {
            "Name": quoter_item.get("name", "Unnamed Service")[:100],  # QBO limit
            "Description": quoter_item.get("description", "")[:500],  # QBO limit
            "UnitPrice": float(quoter_item.get("price", 0)),
            "Type": "Service",  # Use Service instead of Inventory
            "IncomeAccountRef": {
                "value": os.getenv('QBO_INCOME_ACCOUNT_ID', '1')  # Default income account
            },
            "Taxable": True,
            "Active": True
        }
    
    def get_existing_items(self):
        """Get all existing items from QBO to check for duplicates."""
        if not self.access_token:
            if not self.get_access_token():
                return []
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        
        url = f"{self.base_url}/v3/company/{self.company_id}/items"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            items = result.get("QueryResponse", {}).get("Item", [])
            
            logger.info(f"📋 Found {len(items)} existing items in QBO")
            return items
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error getting QBO items: {e}")
            return []

def sync_quoter_to_qbo(since_date=None, force_sync=False):
    """
    Bulk sync ALL items from Quoter directly to QuickBooks Online as Services.
    
    This bypasses Quoter's quote-driven sync and creates all items in QBO upfront.
    Perfect for inventory management and having all items available immediately.
    
    Args:
        since_date (str, optional): ISO date string to filter items modified since this date
        force_sync (bool): If True, sync all items even if they exist in QBO
    """
    logger.info("=== BULK Quoter to QBO Service Synchronization ===")
    logger.info("🎯 This will sync ALL Quoter items to QBO as Services upfront (not quote-driven)")
    
    if since_date:
        logger.info(f"🕐 Syncing items modified since: {since_date}")
    else:
        logger.info("🕐 Syncing ALL items from Quoter to QBO as Services")
    
    # Initialize QBO API client
    qbo = QuickBooksOnlineAPI()
    
    # Get existing QBO items to avoid duplicates (unless force_sync)
    existing_items = []
    existing_names = set()
    
    if not force_sync:
        existing_items = qbo.get_existing_items()
        existing_names = {item.get("Name", "").lower() for item in existing_items}
        logger.info(f"📋 Found {len(existing_items)} existing items in QBO")
    
    # Get ALL items from Quoter
    quoter_items = get_quoter_products(since_date=since_date)
    
    if not quoter_items:
        logger.info("📭 No items found in Quoter to sync")
        return
    
    logger.info(f"📦 Found {len(quoter_items)} items in Quoter to sync")
    
    # Sync items to QBO
    synced_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, item in enumerate(quoter_items, 1):
        item_name = item.get("name", "")
        item_name_lower = item_name.lower()
        
        logger.info(f"🔄 Processing item {i}/{len(quoter_items)}: {item_name}")
        
        # Check if item already exists in QBO (unless force_sync)
        if not force_sync and item_name_lower in existing_names:
            logger.info(f"⏭️  Skipping existing item: {item_name}")
            skipped_count += 1
            continue
        
        # Create service in QBO
        qbo_item = qbo.create_service(item)
        if qbo_item:
            synced_count += 1
            logger.info(f"✅ Successfully synced: {item_name}")
        else:
            error_count += 1
            logger.error(f"❌ Failed to sync item: {item_name}")
    
    # Summary
    logger.info(f"\n🎉 BULK SYNC COMPLETE!")
    logger.info(f"   📦 Total items processed: {len(quoter_items)}")
    logger.info(f"   ✅ Successfully synced: {synced_count}")
    logger.info(f"   ⏭️  Skipped (existing): {skipped_count}")
    logger.info(f"   ❌ Errors: {error_count}")
    
    if synced_count > 0:
        logger.info(f"\n🎯 {synced_count} services are now available in QBO!")
        logger.info("   SyncQ can now detect these services and sync them to Pipedrive")
    
    return {
        "total": len(quoter_items),
        "synced": synced_count,
        "skipped": skipped_count,
        "errors": error_count
    }

def bulk_sync_all_items():
    """Bulk sync ALL items from Quoter to QBO as Services."""
    logger.info("🚀 Starting BULK sync of ALL Quoter items to QBO as Services")
    return sync_quoter_to_qbo(force_sync=False)

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--bulk":
            # Bulk sync all items
            logger.info("🔄 Running BULK sync of all items")
            bulk_sync_all_items()
        elif sys.argv[1] == "--force":
            # Force sync all items (even existing ones)
            logger.info("🔄 Running FORCE sync of all items")
            sync_quoter_to_qbo(force_sync=True)
        else:
            # Use command line argument as date
            since_date = sys.argv[1]
            logger.info(f"Using command line date: {since_date}")
            sync_quoter_to_qbo(since_date)
    else:
        # Default: bulk sync all items
        logger.info("🔄 Running BULK sync of all items (default)")
        bulk_sync_all_items()

if __name__ == "__main__":
    main()