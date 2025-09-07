#!/usr/bin/env python3
"""
Test script for Slack notification functionality
"""

import os
import sys
sys.path.append('.')

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not installed, trying to load .env manually")
    # Fallback: manually load .env file
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ .env file loaded manually")
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")

from notification import send_slack_notification

def test_slack_notification():
    """Test the Slack notification functionality"""
    
    # Test message
    test_message = """
🧪 TEST NOTIFICATION

This is a test of the Slack notification system.
If you see this in Slack, the integration is working!

Timestamp: Test run
"""
    
    print("Testing Slack notification...")
    print(f"Message: {test_message.strip()}")
    
    # Check if webhook URL is configured
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL not configured in .env file")
        print("Please add: SLACK_WEBHOOK_URL=your_webhook_url_here")
        return False
    
    print(f"✅ Webhook URL found: {webhook_url[:30]}...")
    
    # Send test notification
    result = send_slack_notification(test_message.strip())
    
    if result:
        print("✅ Slack notification sent successfully!")
        print("Check your Slack channel for the test message.")
    else:
        print("❌ Slack notification failed!")
    
    return result

if __name__ == "__main__":
    test_slack_notification()
