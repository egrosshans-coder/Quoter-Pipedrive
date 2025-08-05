#!/usr/bin/env python3
"""
Quoter-Pipedrive Sync with Date Filtering

This script syncs only items that have been modified since a specified date,
making the sync process much more efficient for regular updates.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from quoter import get_quoter_products
from pipedrive import update_or_create_products
from utils.logger import logger

load_dotenv()

def sync_since_date(since_date=None):
    """
    Sync Quoter products to Pipedrive with date filtering.
    
    Args:
        since_date (str, optional): ISO date string (YYYY-MM-DD) to filter items 
                                   modified since this date. If None, gets all items.
    """
    logger.info("=== Quoter-Pipedrive Sync with Date Filtering ===")
    
    if since_date:
        logger.info(f"🕐 Syncing items modified since: {since_date}")
    else:
        logger.info("🕐 Syncing all items (no date filter)")
    
    # Get products from Quoter with date filtering
    products = get_quoter_products(since_date=since_date)
    
    if not products:
        logger.info("📭 No products found to sync")
        return
    
    logger.info(f"📦 Found {len(products)} products to sync")
    
    # Sync to Pipedrive
    update_or_create_products(products)
    
    logger.info("✅ Sync complete!")

def get_last_sync_date():
    """
    Get the last sync date from a file or return a default date.
    """
    last_sync_file = "last_sync_date.txt"
    
    if os.path.exists(last_sync_file):
        try:
            with open(last_sync_file, 'r') as f:
                date_str = f.read().strip()
                return date_str
        except Exception as e:
            logger.warning(f"Could not read last sync date: {e}")
    
    # Default to 7 days ago if no last sync date
    default_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    logger.info(f"Using default date (7 days ago): {default_date}")
    return default_date

def save_sync_date():
    """
    Save the current date as the last sync date.
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    try:
        with open("last_sync_date.txt", 'w') as f:
            f.write(current_date)
        logger.info(f"💾 Saved sync date: {current_date}")
    except Exception as e:
        logger.error(f"Could not save sync date: {e}")

def main():
    """
    Main function to handle command line arguments and run sync.
    """
    if len(sys.argv) > 1:
        # Use command line argument as date
        since_date = sys.argv[1]
        logger.info(f"Using command line date: {since_date}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--last":
        # Use last sync date
        since_date = get_last_sync_date()
        logger.info(f"Using last sync date: {since_date}")
    else:
        # Use last sync date by default
        since_date = get_last_sync_date()
        logger.info(f"Using last sync date: {since_date}")
    
    # Run the sync
    sync_since_date(since_date)
    
    # Save the current date as the new last sync date
    save_sync_date()

if __name__ == "__main__":
    main() 