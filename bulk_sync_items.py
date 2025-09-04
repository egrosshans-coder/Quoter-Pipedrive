#!/usr/bin/env python3
"""
Bulk Item Sync Script

This script syncs ALL items from Quoter to QuickBooks Online in one go.
Perfect for initial setup or when you add many new items to Quoter.

Usage:
    python bulk_sync_items.py          # Sync all items (skip existing)
    python bulk_sync_items.py --force  # Sync all items (overwrite existing)
"""

import sys
import os
from dotenv import load_dotenv
from quoter_to_qbo_sync import bulk_sync_all_items, sync_quoter_to_qbo
from utils.logger import logger

load_dotenv()

def main():
    """Main function for bulk item synchronization."""
    logger.info("🎯 BULK ITEM SYNC: Quoter → QuickBooks Online")
    logger.info("=" * 60)
    
    # Check if force sync is requested
    force_sync = "--force" in sys.argv
    
    if force_sync:
        logger.info("⚠️  FORCE SYNC MODE: Will sync all items (may create duplicates)")
        logger.info("   This will attempt to sync items even if they exist in QBO")
    else:
        logger.info("🔄 NORMAL SYNC MODE: Will skip items that already exist in QBO")
    
    # Confirm before proceeding
    if not force_sync:
        response = input("\n🤔 Do you want to proceed with bulk sync? (y/N): ")
        if response.lower() != 'y':
            logger.info("❌ Bulk sync cancelled by user")
            return
    
    try:
        # Run the bulk sync
        if force_sync:
            result = sync_quoter_to_qbo(force_sync=True)
        else:
            result = bulk_sync_all_items()
        
        if result:
            logger.info("\n🎉 BULK SYNC COMPLETED SUCCESSFULLY!")
            logger.info(f"   📦 Total items: {result['total']}")
            logger.info(f"   ✅ Synced: {result['synced']}")
            logger.info(f"   ⏭️  Skipped: {result['skipped']}")
            logger.info(f"   ❌ Errors: {result['errors']}")
            
            if result['synced'] > 0:
                logger.info(f"\n🎯 {result['synced']} items are now available in QBO!")
                logger.info("   Next steps:")
                logger.info("   1. Check QBO to verify items were created")
                logger.info("   2. SyncQ should detect these items and sync to Pipedrive")
                logger.info("   3. Your items are now available for quotes and invoicing")
        else:
            logger.error("❌ Bulk sync failed or returned no results")
            
    except Exception as e:
        logger.error(f"❌ Bulk sync failed with error: {e}")
        logger.error("   Check your QBO configuration and try again")

if __name__ == "__main__":
    main()
