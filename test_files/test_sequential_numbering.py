#!/usr/bin/env python3
"""
Test script for sequential quote numbering functionality.
Tests the generate_sequential_quote_number function with various deal IDs.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import generate_sequential_quote_number
from utils.logger import logger

load_dotenv()

def test_sequential_numbering():
    """Test the sequential quote numbering function with various deal IDs."""
    
    logger.info("🧪 Testing Sequential Quote Numbering Function")
    logger.info("=" * 50)
    
    # Test cases with different deal ID formats
    test_cases = [
        "2096",      # 4 digits
        "123",       # 3 digits  
        "4567",      # 4 digits
        "12345",     # 5 digits
        "1",         # 1 digit
        "99999",     # 5 digits
        "0",         # Edge case
        "100000"     # 6 digits (edge case)
    ]
    
    for deal_id in test_cases:
        try:
            logger.info(f"\n📋 Testing Deal ID: {deal_id}")
            quote_number = generate_sequential_quote_number(deal_id)
            logger.info(f"   ✅ Generated: {quote_number}")
            
            # Validate format
            if "-" in quote_number and len(quote_number.split("-")[0]) == 5:
                logger.info(f"   ✅ Format: Valid xxxxx-yy format")
            else:
                logger.warning(f"   ⚠️ Format: Unexpected format")
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info("🎯 Sequential Numbering Test Complete!")

if __name__ == "__main__":
    test_sequential_numbering()
