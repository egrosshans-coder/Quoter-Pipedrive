#!/usr/bin/env python3
"""
Test script for detailed sync notification system
"""

import os
from dotenv import load_dotenv
from detailed_sync_notification import DetailedSyncNotifier

load_dotenv()

def test_notification():
    """Test the detailed notification system with sample data"""
    print("🧪 Testing detailed sync notification system...")
    
    # Show current last sync date
    try:
        with open("last_sync_date.txt", "r") as f:
            last_sync = f.read().strip()
            print(f"📅 Current last sync date: {last_sync}")
    except:
        print("⚠️ Could not read last_sync_date.txt")
    
    notifier = DetailedSyncNotifier()
    
    # Add some sample Quoter items
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
    
    # Add some sample Pipedrive products
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
    
    # Add some sample QBO items
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
    
    # Add a sample error
    notifier.add_error("Failed to sync product LED-ARCH-001 to QBO", "QBO Sync")
    
    # Generate and display the email content (without sending)
    print("\n📧 Generated Email Content:")
    print("=" * 50)
    email_content = notifier.generate_email_content()
    print(email_content)
    
    print("\n✅ Test completed! Check the email content above.")
    print("💡 To actually send notifications, run: python detailed_sync_notification.py")

if __name__ == "__main__":
    test_notification()
