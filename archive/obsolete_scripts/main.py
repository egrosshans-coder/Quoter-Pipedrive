#!/usr/bin/env python3
"""
Quoter Sync - Main entry point
Synchronizes products/items between Quoter and Pipedrive APIs.
"""

from quoter import get_quoter_products
from pipedrive import update_or_create_products
from utils.logger import logger

def main():
    """
    Main function that orchestrates the sync process.
    """
    logger.info("Starting Quoter ↔ Pipedrive sync...")
    
    try:
        # Step 1: Fetch products from Quoter
        logger.info("Fetching products from Quoter...")
        quoter_products = get_quoter_products()
        
        if not quoter_products:
            logger.warning("No products found in Quoter or error occurred")
            return
        
        # Step 2: Sync products to Pipedrive
        logger.info("Syncing products to Pipedrive...")
        update_or_create_products(quoter_products)
        
        logger.info("Sync completed successfully!")
        
    except Exception as e:
        logger.error(f"Sync failed with error: {e}")
        raise

if __name__ == "__main__":
    main() 