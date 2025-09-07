#!/usr/bin/env python3
"""
Complete Sync Runner
Runs Quoter → Pipedrive sync first, then Quoter → QBO sync
This ensures proper sequence and data consistency
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from utils.logger import logger

def run_command(command, description):
    """Run a command and return success status"""
    logger.info(f"🔄 {description}...")
    logger.info(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ {description} completed successfully")
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
            return True
        else:
            logger.error(f"❌ {description} failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ {description} failed with exception: {e}")
        return False

def main():
    """Run the complete sync workflow"""
    start_time = datetime.now()
    logger.info("🚀 Starting Complete Sync Workflow")
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Quoter → Pipedrive Sync
    logger.info("\n" + "="*60)
    logger.info("STEP 1: QUOTER → PIPEDRIVE SYNC")
    logger.info("="*60)
    
    pipedrive_success = run_command(
        "python sync_with_date_filter.py",
        "Quoter → Pipedrive sync"
    )
    
    if not pipedrive_success:
        logger.error("❌ Pipedrive sync failed. Stopping workflow.")
        sys.exit(1)
    
    # Wait a moment between syncs
    logger.info("⏳ Waiting 30 seconds before QBO sync...")
    time.sleep(30)
    
    # Step 2: Quoter → QBO Sync
    logger.info("\n" + "="*60)
    logger.info("STEP 2: QUOTER → QBO SYNC")
    logger.info("="*60)
    
    qbo_success = run_command(
        "python quoter_to_qbo_sync.py",
        "Quoter → QBO sync"
    )
    
    if not qbo_success:
        logger.error("❌ QBO sync failed.")
        sys.exit(1)
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("\n" + "="*60)
    logger.info("SYNC WORKFLOW COMPLETE")
    logger.info("="*60)
    logger.info(f"✅ Pipedrive sync: {'SUCCESS' if pipedrive_success else 'FAILED'}")
    logger.info(f"✅ QBO sync: {'SUCCESS' if qbo_success else 'FAILED'}")
    logger.info(f"⏱️  Total duration: {duration}")
    logger.info(f"🕐 Completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if pipedrive_success and qbo_success:
        logger.info("🎉 All syncs completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Some syncs failed. Check logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
