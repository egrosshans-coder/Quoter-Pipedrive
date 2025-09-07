#!/usr/bin/env python3
"""
Show real output from the detailed sync notification system
"""

import os
from dotenv import load_dotenv
from detailed_sync_notification import DetailedSyncNotifier, gather_sync_data

load_dotenv()

def show_real_output():
    """Show real output from the notification system"""
    print("🔍 Running detailed sync notification with real data...")
    print("=" * 60)
    
    # Create notifier
    notifier = DetailedSyncNotifier()
    
    # Gather real data from all systems
    gather_sync_data()
    
    # Display summary
    print(f"\n📊 SUMMARY:")
    print(f"   New Quoter Items: {len(notifier.quoter_new_items)}")
    print(f"   New Pipedrive Products: {len(notifier.pipedrive_new_products)}")
    print(f"   New QuickBooks Items: {len(notifier.qbo_new_items)}")
    print(f"   Errors: {len(notifier.sync_errors)}")
    
    # Display Quoter items
    if notifier.quoter_new_items:
        print(f"\n🆕 NEW ITEMS ADDED TO QUOTER ({len(notifier.quoter_new_items)}):")
        print("-" * 50)
        for i, item in enumerate(notifier.quoter_new_items[:5], 1):  # Show first 5
            print(f"{i}. {item['name']}")
            print(f"   Code: {item['code']}")
            print(f"   Price: ${item['price']:.2f}" if item['price'] else "   Price: N/A")
            print(f"   Category: {item['category']}")
            print(f"   Subcategory: {item['subcategory']}")
            print(f"   Supplier SKU: {item['supplier_sku']}")
            print(f"   Added At: {item['added_at']}")
            print()
        
        if len(notifier.quoter_new_items) > 5:
            print(f"   ... and {len(notifier.quoter_new_items) - 5} more items")
    
    # Display Pipedrive products
    if notifier.pipedrive_new_products:
        print(f"\n🆕 NEW PRODUCTS ADDED TO PIPEDRIVE ({len(notifier.pipedrive_new_products)}):")
        print("-" * 50)
        for i, product in enumerate(notifier.pipedrive_new_products[:5], 1):  # Show first 5
            print(f"{i}. {product['name']} (ID: {product['id']})")
            print(f"   Code: {product['code']}")
            print(f"   Price: ${product['price']:.2f}" if product['price'] else "   Price: N/A")
            print(f"   Category: {product['category']}")
            print(f"   Subcategory: {product['subcategory']}")
            print(f"   QBO Category:Subcategory: {product['qbo_category_subcategory']}")
            print(f"   QuickBooks ID: {product['quickbooks_id']}")
            print(f"   Added At: {product['added_at']}")
            print()
        
        if len(notifier.pipedrive_new_products) > 5:
            print(f"   ... and {len(notifier.pipedrive_new_products) - 5} more products")
    
    # Display QBO items
    if notifier.qbo_new_items:
        print(f"\n🆕 NEW ITEMS ADDED TO QUICKBOOKS ({len(notifier.qbo_new_items)}):")
        print("-" * 50)
        for i, item in enumerate(notifier.qbo_new_items[:5], 1):  # Show first 5
            print(f"{i}. {item['name']}")
            print(f"   Item Type: {item['item_type']}")
            print(f"   SKU: {item['sku']}")
            print(f"   Category: {item['category']}")
            print(f"   Price: ${item['price']:.2f}" if item['price'] else "   Price: N/A")
            print(f"   Added At: {item['added_at']}")
            print()
        
        if len(notifier.qbo_new_items) > 5:
            print(f"   ... and {len(notifier.qbo_new_items) - 5} more items")
    
    # Display errors
    if notifier.sync_errors:
        print(f"\n❌ SYNC ERRORS ({len(notifier.sync_errors)}):")
        print("-" * 50)
        for i, error in enumerate(notifier.sync_errors, 1):
            print(f"{i}. {error['system']}: {error['error']}")
            print(f"   Time: {error['timestamp']}")
            print()
    
    print("=" * 60)
    print("✅ Real data output completed!")

if __name__ == "__main__":
    show_real_output()
