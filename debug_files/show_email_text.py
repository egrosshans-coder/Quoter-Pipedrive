#!/usr/bin/env python3
"""
Show email notification details in plain text format
"""

import os
from dotenv import load_dotenv
from detailed_sync_notification import DetailedSyncNotifier

load_dotenv()

def show_email_text():
    """Show email notification details in plain text"""
    print("📧 Daily Sync Report - Plain Text Format")
    print("=" * 60)
    
    # Show current last sync date
    try:
        with open("last_sync_date.txt", "r") as f:
            last_sync = f.read().strip()
            print(f"📅 Last sync date: {last_sync}")
    except:
        print("⚠️ Could not read last_sync_date.txt")
    
    print()
    
    # Create notifier and add sample data
    notifier = DetailedSyncNotifier()
    
    # Add sample Quoter items
    notifier.add_quoter_item({
        "name": "LED Balloon Arch",
        "code": "LED-ARCH-001",
        "price": 125.00,
        "category": "Balloons",
        "subcategory": "LED Balloons",
        "supplier_sku": "SUP-001"
    })
    
    notifier.add_quoter_item({
        "name": "Confetti Cannon",
        "code": "CONF-CAN-002",
        "price": 45.50,
        "category": "Confetti",
        "subcategory": "Cannons",
        "supplier_sku": "SUP-002"
    })
    
    # Add sample Pipedrive products
    notifier.add_pipedrive_product({
        "id": "12345",
        "name": "LED Balloon Arch",
        "code": "LED-ARCH-001",
        "price": 125.00,
        "category": "Balloons",
        "subcategory": "LED Balloons",
        "qbo_category_subcategory": "Balloons:LED Balloons",
        "quickbooks_id": "QBO-001"
    })
    
    notifier.add_pipedrive_product({
        "id": "12346",
        "name": "Confetti Cannon",
        "code": "CONF-CAN-002",
        "price": 45.50,
        "category": "Confetti",
        "subcategory": "Cannons",
        "qbo_category_subcategory": "Confetti:Cannons",
        "quickbooks_id": "QBO-002"
    })
    
    # Add sample QBO items
    notifier.add_qbo_item({
        "name": "LED Balloon Arch",
        "item_type": "Service",
        "sku": "LED-ARCH-001",
        "category": "Balloons",
        "price": 125.00
    })
    
    notifier.add_qbo_item({
        "name": "Confetti Cannon",
        "item_type": "Service",
        "sku": "CONF-CAN-002",
        "category": "Confetti",
        "price": 45.50
    })
    
    # Add sample error
    notifier.add_error("Failed to sync product LED-ARCH-001 to QBO", "QBO Sync")
    
    # Display summary
    print("📊 SUMMARY:")
    print(f"   New Quoter Items: {len(notifier.quoter_new_items)}")
    print(f"   New Pipedrive Products: {len(notifier.pipedrive_new_products)}")
    print(f"   New QuickBooks Items: {len(notifier.qbo_new_items)}")
    print(f"   Errors: {len(notifier.sync_errors)}")
    print()
    
    # Display Quoter items
    if notifier.quoter_new_items:
        print("🆕 NEW ITEMS ADDED TO QUOTER:")
        print("-" * 40)
        for item in notifier.quoter_new_items:
            print(f"Product Name: {item['name']}")
            print(f"Code: {item['code']}")
            print(f"Price: ${item['price']:.2f}")
            print(f"Category: {item['category']}")
            print(f"Subcategory: {item['subcategory']}")
            print(f"Supplier SKU: {item['supplier_sku']}")
            print(f"Added At: {item['added_at']}")
            print()
    
    # Display Pipedrive products
    if notifier.pipedrive_new_products:
        print("🆕 NEW PRODUCTS ADDED TO PIPEDRIVE:")
        print("-" * 40)
        for product in notifier.pipedrive_new_products:
            print(f"Product ID: {product['id']}")
            print(f"Name: {product['name']}")
            print(f"Code: {product['code']}")
            print(f"Price: ${product['price']:.2f}")
            print(f"Category: {product['category']}")
            print(f"Subcategory: {product['subcategory']}")
            print(f"QBO Category:Subcategory: {product['qbo_category_subcategory']}")
            print(f"QuickBooks ID: {product['quickbooks_id']}")
            print(f"Added At: {product['added_at']}")
            print()
    
    # Display QBO items
    if notifier.qbo_new_items:
        print("🆕 NEW ITEMS ADDED TO QUICKBOOKS:")
        print("-" * 40)
        for item in notifier.qbo_new_items:
            print(f"Name: {item['name']}")
            print(f"Item Type: {item['item_type']}")
            print(f"SKU: {item['sku']}")
            print(f"Category: {item['category']}")
            print(f"Price: ${item['price']:.2f}")
            print(f"Added At: {item['added_at']}")
            print()
    
    # Display errors
    if notifier.sync_errors:
        print("❌ SYNC ERRORS:")
        print("-" * 40)
        for error in notifier.sync_errors:
            print(f"System: {error['system']}")
            print(f"Error: {error['error']}")
            print(f"Time: {error['timestamp']}")
            print()
    
    # Show email configuration
    print("📧 EMAIL CONFIGURATION:")
    print("-" * 40)
    print(f"Gmail User: {os.getenv('GMAIL_USER', 'Not configured')}")
    print(f"Notification Emails: {os.getenv('NOTIFICATION_EMAILS', 'Not configured')}")
    print(f"Slack Webhook: {'Configured' if os.getenv('SLACK_WEBHOOK_URL') else 'Not configured'}")

if __name__ == "__main__":
    show_email_text()
