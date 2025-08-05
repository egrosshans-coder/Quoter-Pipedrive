#!/usr/bin/env python3
"""
Automated Scheduler for Quoter Sync
Runs syncs on a schedule and logs results
"""

import schedule
import time
import os
from datetime import datetime
from sync_with_date_filter import sync_since_date, get_last_sync_date
from utils.logger import logger

def run_scheduled_sync():
    """Run the sync with date filtering and log the results."""
    logger.info("=== Starting Scheduled Sync (Date Filtered) ===")
    logger.info(f"🕐 Sync started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Get the last sync date and sync only items modified since then
        last_sync_date = get_last_sync_date()
        logger.info(f"📅 Syncing items modified since: {last_sync_date}")
        
        sync_since_date(last_sync_date)
        logger.info("✅ Scheduled sync completed successfully")
        
        # Log to a separate sync log file
        with open("sync_log.txt", "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Sync completed successfully (since {last_sync_date})\n")
            
    except Exception as e:
        logger.error(f"❌ Scheduled sync failed: {e}")
        
        # Log errors to sync log file
        with open("sync_log.txt", "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Sync failed: {e}\n")

def setup_scheduler():
    """Set up the scheduler with different sync intervals."""
    logger.info("=== Setting up Automated Scheduler ===")
    
    # Schedule syncs at different intervals
    schedule.every().day.at("09:00").do(run_scheduled_sync)  # Daily at 9 AM
    schedule.every().day.at("17:00").do(run_scheduled_sync)  # Daily at 5 PM
    schedule.every().hour.do(run_scheduled_sync)             # Every hour (for testing)
    
    logger.info("✅ Scheduler configured:")
    logger.info("  📅 Daily syncs at 9:00 AM and 5:00 PM")
    logger.info("  ⏰ Hourly syncs (for testing)")
    logger.info("  📝 Logs saved to sync_log.txt")
    
    return schedule

def run_scheduler():
    """Run the scheduler continuously."""
    logger.info("=== Starting Scheduler ===")
    logger.info("🔄 Scheduler is running... Press Ctrl+C to stop")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def main():
    """Main function to start the scheduler."""
    logger.info("=== Quoter Sync Scheduler ===")
    
    # Set up the scheduler
    scheduler = setup_scheduler()
    
    # Run the scheduler
    run_scheduler()

if __name__ == "__main__":
    main() 