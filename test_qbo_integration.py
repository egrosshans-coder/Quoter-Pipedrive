#!/usr/bin/env python3
"""
Test script for Quoter to QBO direct integration.

This script tests the connection and basic functionality of the QBO integration.
"""

import os
import sys
from dotenv import load_dotenv
from quoter_to_qbo_sync import QuickBooksOnlineAPI
from quoter import get_quoter_products
from utils.logger import logger

load_dotenv()

def test_qbo_connection():
    """Test QBO API connection and authentication."""
    logger.info("=== Testing QBO Connection ===")
    
    qbo = QuickBooksOnlineAPI()
    
    # Test access token
    if qbo.get_access_token():
        logger.info("✅ QBO access token obtained successfully")
    else:
        logger.error("❌ Failed to get QBO access token")
        return False
    
    # Test getting existing items
    existing_items = qbo.get_existing_items()
    if existing_items is not None:
        logger.info(f"✅ Successfully retrieved {len(existing_items)} existing items from QBO")
        return True
    else:
        logger.error("❌ Failed to retrieve items from QBO")
        return False

def test_quoter_connection():
    """Test Quoter API connection."""
    logger.info("=== Testing Quoter Connection ===")
    
    # Test getting items from Quoter
    items = get_quoter_products()
    if items:
        logger.info(f"✅ Successfully retrieved {len(items)} items from Quoter")
        return True
    else:
        logger.error("❌ Failed to retrieve items from Quoter")
        return False

def test_item_mapping():
    """Test mapping Quoter item to QBO format."""
    logger.info("=== Testing Item Mapping ===")
    
    # Sample Quoter item
    sample_quoter_item = {
        "id": "test_item_123",
        "name": "Test Item",
        "description": "This is a test item for QBO integration",
        "price": 99.99,
        "cost": 50.00,
        "category": "Test Category"
    }
    
    qbo = QuickBooksOnlineAPI()
    qbo_item = qbo._map_quoter_to_qbo_item(sample_quoter_item)
    
    logger.info(f"✅ Mapped Quoter item to QBO format:")
    logger.info(f"   Name: {qbo_item['Name']}")
    logger.info(f"   Description: {qbo_item['Description']}")
    logger.info(f"   Unit Price: {qbo_item['UnitPrice']}")
    logger.info(f"   Purchase Cost: {qbo_item['PurchaseCost']}")
    
    return True

def main():
    """Run all tests."""
    logger.info("🧪 Starting QBO Integration Tests")
    
    tests = [
        ("Quoter Connection", test_quoter_connection),
        ("QBO Connection", test_qbo_connection),
        ("Item Mapping", test_item_mapping)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n=== Test Results Summary ===")
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        logger.info("🎉 All tests passed! QBO integration is ready.")
    else:
        logger.error("⚠️  Some tests failed. Check configuration and try again.")

if __name__ == "__main__":
    main()
