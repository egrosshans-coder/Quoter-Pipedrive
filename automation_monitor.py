#!/usr/bin/env python3
"""
Automation Monitor - Tracks Pipedrive automation progress and webhook activity
Monitors the complete flow from deal stage change to draft quote creation
"""

import time
import json
import requests
from datetime import datetime
from pipedrive import get_deal_by_id, get_organization_by_id
from utils.logger import logger

class AutomationMonitor:
    def __init__(self, deal_id, check_interval=30):
        """
        Initialize the automation monitor for a specific deal.
        
        Args:
            deal_id (str): The deal ID to monitor
            check_interval (int): Seconds between checks (default: 30)
        """
        self.deal_id = deal_id
        self.check_interval = check_interval
        self.start_time = datetime.now()
        self.log_file = f"automation_log_{deal_id}_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        self.log_data = {
            "deal_id": deal_id,
            "start_time": self.start_time.isoformat(),
            "checks": [],
            "status_changes": [],
            "errors": [],
            "webhook_activity": []
        }
        
    def log_status(self, status, details=None):
        """Log a status update with timestamp."""
        timestamp = datetime.now()
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "status": status,
            "details": details or {}
        }
        self.log_data["checks"].append(log_entry)
        
        # Also log to console
        logger.info(f"🔍 [{timestamp.strftime('%H:%M:%S')}] {status}")
        if details:
            for key, value in details.items():
                logger.info(f"   {key}: {value}")
    
    def log_error(self, error_msg, details=None):
        """Log an error with timestamp."""
        timestamp = datetime.now()
        error_entry = {
            "timestamp": timestamp.isoformat(),
            "error": error_msg,
            "details": details or {}
        }
        self.log_data["errors"].append(error_entry)
        logger.error(f"❌ [{timestamp.strftime('%H:%M:%S')}] {error_msg}")
    
    def log_webhook_activity(self, activity_type, details=None):
        """Log webhook activity."""
        timestamp = datetime.now()
        webhook_entry = {
            "timestamp": timestamp.isoformat(),
            "activity_type": activity_type,
            "details": details or {}
        }
        self.log_data["webhook_activity"].append(webhook_entry)
        logger.info(f"⚡ [{timestamp.strftime('%H:%M:%S')}] WEBHOOK: {activity_type}")
    
    def check_deal_status(self):
        """Check the current deal status and stage."""
        try:
            deal_data = get_deal_by_id(self.deal_id)
            if not deal_data:
                self.log_error("Deal not found", {"deal_id": self.deal_id})
                return None
            
            stage_id = deal_data.get("stage_id")
            stage_name = deal_data.get("stage_name", "Unknown")
            title = deal_data.get("title", "Unknown")
            
            self.log_status("Deal Status Check", {
                "deal_id": self.deal_id,
                "title": title,
                "stage_id": stage_id,
                "stage_name": stage_name
            })
            
            return deal_data
            
        except Exception as e:
            self.log_error(f"Error checking deal status: {e}")
            return None
    
    def check_organization_status(self, organization_id):
        """Check the organization's HID-QBO-Status."""
        try:
            org_data = get_organization_by_id(organization_id)
            if not org_data:
                self.log_error("Organization not found", {"org_id": organization_id})
                return None
            
            hid_status = org_data.get("454a3767bce03a880b31d78a38c480d6870e0f1b")
            org_name = org_data.get("name", "Unknown")
            owner_name = org_data.get("owner_id", {}).get("name", "Unknown")
            
            # Map status codes to names
            status_map = {
                None: "Not Set",
                "0": "Not Started",
                "1": "QBO-Website-Verified",
                "2": "QBO-Cust",
                "289": "QBO-SubCust"
            }
            status_name = status_map.get(str(hid_status), f"Unknown ({hid_status})")
            
            self.log_status("Organization Status Check", {
                "org_id": organization_id,
                "org_name": org_name,
                "owner": owner_name,
                "hid_status_code": hid_status,
                "hid_status_name": status_name
            })
            
            return org_data
            
        except Exception as e:
            self.log_error(f"Error checking organization status: {e}")
            return None
    
    def check_webhook_server(self):
        """Check if webhook server is healthy."""
        try:
            response = requests.get("https://quoter-webhook-server.onrender.com/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log_status("Webhook Server Health", {
                    "status": health_data.get("status"),
                    "service": health_data.get("service")
                })
                return True
            else:
                self.log_error(f"Webhook server unhealthy: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"Error checking webhook server: {e}")
            return False
    
    def find_associated_organization(self, deal_data):
        """Find the organization associated with this deal."""
        try:
            # Look for organization in deal data
            org_id = deal_data.get("org_id", {}).get("value")
            if org_id:
                return org_id
            
            # If not found, we might need to search by deal ID in organization names
            # This would require additional API calls
            self.log_status("Organization Search", {
                "message": "No direct org_id found in deal, may need to search by deal ID"
            })
            return None
            
        except Exception as e:
            self.log_error(f"Error finding associated organization: {e}")
            return None
    
    def monitor_automation(self, max_checks=20):
        """
        Monitor the complete automation process.
        
        Args:
            max_checks (int): Maximum number of checks before stopping
        """
        logger.info(f"🚀 Starting automation monitor for deal {self.deal_id}")
        logger.info(f"📝 Log file: {self.log_file}")
        logger.info(f"⏱️ Check interval: {self.check_interval} seconds")
        logger.info(f"🔄 Max checks: {max_checks}")
        
        check_count = 0
        webhook_triggered = False
        
        while check_count < max_checks:
            check_count += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 CHECK #{check_count}/{max_checks} - {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"{'='*60}")
            
            # Check webhook server health
            webhook_healthy = self.check_webhook_server()
            
            # Check deal status
            deal_data = self.check_deal_status()
            if not deal_data:
                logger.error("❌ Cannot continue monitoring - deal not found")
                break
            
            # Find associated organization
            org_id = self.find_associated_organization(deal_data)
            if org_id:
                # Check organization status
                org_data = self.check_organization_status(org_id)
                if org_data:
                    hid_status = org_data.get("454a3767bce03a880b31d78a38c480d6870e0f1b")
                    
                    # Check if webhook should have triggered
                    if str(hid_status) == "289":  # QBO-SubCust
                        if not webhook_triggered:
                            self.log_webhook_activity("STATUS_READY", {
                                "message": "Organization ready for webhook trigger",
                                "org_id": org_id,
                                "status": "QBO-SubCust (289)"
                            })
                            webhook_triggered = True
                            
                            # Check if quote was created in Quoter
                            self.log_status("Checking for Quote Creation", {
                                "message": "Webhook should have triggered - check Quoter for draft quote"
                            })
                        else:
                            self.log_status("Webhook Already Triggered", {
                                "message": "Status is QBO-SubCust, webhook should have fired"
                            })
                    else:
                        self.log_status("Waiting for Automation", {
                            "message": f"Current status: {hid_status}, waiting for 289 (QBO-SubCust)"
                        })
            
            # Save log data
            self.save_log()
            
            # Check if we should continue
            if webhook_triggered and check_count >= 3:  # Give it a few more checks after webhook
                logger.info("✅ Webhook triggered, monitoring complete")
                break
            
            if check_count < max_checks:
                logger.info(f"⏳ Waiting {self.check_interval} seconds for next check...")
                time.sleep(self.check_interval)
        
        # Final summary
        self.generate_summary()
    
    def save_log(self):
        """Save the current log data to file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.log_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving log file: {e}")
    
    def generate_summary(self):
        """Generate a summary of the monitoring session."""
        duration = datetime.now() - self.start_time
        total_checks = len(self.log_data["checks"])
        total_errors = len(self.log_data["errors"])
        webhook_activities = len(self.log_data["webhook_activity"])
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 MONITORING SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Deal ID: {self.deal_id}")
        logger.info(f"Duration: {duration}")
        logger.info(f"Total Checks: {total_checks}")
        logger.info(f"Errors: {total_errors}")
        logger.info(f"Webhook Activities: {webhook_activities}")
        logger.info(f"Log File: {self.log_file}")
        
        if total_errors > 0:
            logger.info(f"\n❌ ERRORS ENCOUNTERED:")
            for error in self.log_data["errors"]:
                logger.info(f"  {error['timestamp']}: {error['error']}")
        
        if webhook_activities > 0:
            logger.info(f"\n⚡ WEBHOOK ACTIVITIES:")
            for activity in self.log_data["webhook_activity"]:
                logger.info(f"  {activity['timestamp']}: {activity['activity_type']}")

def monitor_deal_automation(deal_id, check_interval=30, max_checks=20):
    """
    Convenience function to start monitoring a deal's automation.
    
    Args:
        deal_id (str): The deal ID to monitor
        check_interval (int): Seconds between checks
        max_checks (int): Maximum number of checks
    """
    monitor = AutomationMonitor(deal_id, check_interval)
    monitor.monitor_automation(max_checks)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python automation_monitor.py <deal_id> [check_interval] [max_checks]")
        print("Example: python automation_monitor.py 2096 30 20")
        sys.exit(1)
    
    deal_id = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    max_checks = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    
    monitor_deal_automation(deal_id, check_interval, max_checks)
