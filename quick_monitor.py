#!/usr/bin/env python3
"""
Quick Monitor - Simple monitoring for current deal automation
Run this to track the automation progress in real-time
"""

import time
import requests
from datetime import datetime
from pipedrive import get_deal_by_id, get_organization_by_id

def quick_monitor(deal_id, check_interval=30):
    """Quick monitoring of deal automation progress."""
    print(f"🚀 Quick Monitor for Deal {deal_id}")
    print(f"⏱️ Check interval: {check_interval} seconds")
    print(f"🕐 Started at: {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    
    check_count = 0
    webhook_ready = False
    
    while True:
        check_count += 1
        current_time = datetime.now().strftime('%H:%M:%S')
        
        print(f"\n🔍 CHECK #{check_count} - {current_time}")
        print("-" * 40)
        
        try:
            # Check webhook server
            try:
                response = requests.get("https://quoter-webhook-server.onrender.com/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Webhook server: HEALTHY")
                else:
                    print(f"❌ Webhook server: UNHEALTHY ({response.status_code})")
            except Exception as e:
                print(f"❌ Webhook server: ERROR - {e}")
            
            # Check deal
            deal_data = get_deal_by_id(deal_id)
            if deal_data:
                stage_name = deal_data.get("stage_name", "Unknown")
                title = deal_data.get("title", "Unknown")
                print(f"📋 Deal: {title}")
                print(f"📊 Stage: {stage_name}")
                
                # Check organization
                org_id = deal_data.get("org_id", {}).get("value")
                if org_id:
                    org_data = get_organization_by_id(org_id)
                    if org_data:
                        org_name = org_data.get("name", "Unknown")
                        owner_name = org_data.get("owner_id", {}).get("name", "Unknown")
                        hid_status = org_data.get("454a3767bce03a880b31d78a38c480d6870e0f1b")
                        
                        print(f"🏢 Organization: {org_name}")
                        print(f"👤 Owner: {owner_name}")
                        
                        # Map status
                        status_map = {
                            None: "Not Set",
                            "0": "Not Started", 
                            "1": "QBO-Website-Verified",
                            "2": "QBO-Cust",
                            "289": "QBO-SubCust ⚡"
                        }
                        status_name = status_map.get(str(hid_status), f"Unknown ({hid_status})")
                        print(f"🔄 HID-QBO-Status: {status_name}")
                        
                        if str(hid_status) == "289":
                            if not webhook_ready:
                                print("🎯 WEBHOOK SHOULD TRIGGER NOW!")
                                print("📝 Check Quoter for draft quote")
                                webhook_ready = True
                            else:
                                print("✅ Webhook already triggered")
                        else:
                            print(f"⏳ Waiting for status 289 (current: {hid_status})")
                    else:
                        print("❌ Organization data not found")
                else:
                    print("❌ No organization ID in deal")
            else:
                print(f"❌ Deal {deal_id} not found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
        
        if webhook_ready and check_count >= 3:
            print("✅ Monitoring complete - webhook triggered!")
            break
            
        print(f"⏳ Waiting {check_interval} seconds...")
        time.sleep(check_interval)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python quick_monitor.py <deal_id> [check_interval]")
        print("Example: python quick_monitor.py 2096 30")
        sys.exit(1)
    
    deal_id = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    try:
        quick_monitor(deal_id, check_interval)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
