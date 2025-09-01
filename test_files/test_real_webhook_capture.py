#!/usr/bin/env python3
"""
Test script to help capture and analyze real webhook data.
This will help us identify why the email field is missing in the actual webhook.
"""
import os
import sys
import json
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger

load_dotenv()

def analyze_webhook_data_structure():
    """Analyze the webhook data structure to identify email field issues."""
    logger.info("🔍 Analyzing Webhook Data Structure for Email Field Issues")
    logger.info("=" * 70)
    
    # Based on the actual webhook logs, let's analyze what might be different
    logger.info("📋 Analysis of the email field issue:")
    logger.info("")
    
    logger.info("🔍 What we know works:")
    logger.info("   1. ✅ Direct call to update_contact_address() - WORKS")
    logger.info("   2. ✅ Simulated webhook data structure - WORKS") 
    logger.info("   3. ✅ URL-encoded parsing logic - WORKS")
    logger.info("   4. ✅ Email field extraction from parsed data - WORKS")
    logger.info("")
    
    logger.info("🔍 What we know doesn't work:")
    logger.info("   1. ❌ Real webhook processing - FAILS with 'No email address found'")
    logger.info("")
    
    logger.info("🔍 Possible causes:")
    logger.info("   1. 📝 Real webhook data has different structure than our simulation")
    logger.info("   2. 📝 Email field name is different in real data")
    logger.info("   3. 📝 Email field is nested differently in real data")
    logger.info("   4. 📝 Real data is missing the email field entirely")
    logger.info("   5. 📝 Data corruption during webhook transmission")
    logger.info("")
    
    logger.info("🔍 Next steps to debug:")
    logger.info("   1. 📊 Check Render logs for the next real webhook")
    logger.info("   2. 📊 Look for the debug messages we added:")
    logger.info("      - '🔍 DEBUG: Raw person data from quote:'")
    logger.info("      - '🔍 DEBUG: Constructed contact_data:'")
    logger.info("      - '🔍 DEBUG: About to call update_deal_with_quote_info with contact_data:'")
    logger.info("   3. 📊 Compare real data structure with our simulation")
    logger.info("")
    
    logger.info("🔍 To trigger a real webhook:")
    logger.info("   1. 📝 Publish a quote in Quoter")
    logger.info("   2. 📝 Check Render logs at: https://quoter-webhook-server.onrender.com")
    logger.info("   3. 📝 Look for the debug output")
    logger.info("")
    
    logger.info("🔍 Alternative debugging approach:")
    logger.info("   1. 📝 Check if Quoter webhook format changed")
    logger.info("   2. 📝 Verify webhook endpoint configuration in Quoter")
    logger.info("   3. 📝 Test with a different quote/contact")
    logger.info("")
    
    logger.info("🎯 The debug logging we added should reveal the exact issue!")
    logger.info("=" * 70)

def show_debug_logging_help():
    """Show help for interpreting the debug logs."""
    logger.info("📖 Debug Logging Help")
    logger.info("=" * 50)
    
    logger.info("When you publish a quote, look for these log messages:")
    logger.info("")
    logger.info("🔍 DEBUG: Raw person data from quote: {...}")
    logger.info("   This shows the exact data Quoter sent")
    logger.info("")
    logger.info("🔍 DEBUG: Constructed contact_data: {...}")
    logger.info("   This shows what we extracted from the person data")
    logger.info("")
    logger.info("🔍 DEBUG: About to call update_deal_with_quote_info with contact_data: {...}")
    logger.info("   This shows what we're passing to the Pipedrive function")
    logger.info("")
    logger.info("🔍 DEBUG: Received contact_data: {...}")
    logger.info("   This shows what the Pipedrive function receives")
    logger.info("")
    logger.info("🔍 DEBUG: Extracted values - email: '...'")
    logger.info("   This shows if the email was found or not")
    logger.info("")
    logger.info("Compare these with our test results to find the mismatch!")

if __name__ == "__main__":
    analyze_webhook_data_structure()
    print("\n")
    show_debug_logging_help()
