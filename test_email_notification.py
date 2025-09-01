#!/usr/bin/env python3
"""
Test script for Gmail email notification functionality
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
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ .env file loaded manually")
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")

from notification import send_email_notification

def test_email_notification():
    """Test the Gmail email notification functionality"""
    
    # Test message
    test_subject = "🧪 Test Email - Quoter Notification System"
    test_message = """
🧪 TEST EMAIL NOTIFICATION

This is a test of the Gmail email notification system.
If you receive this email, the integration is working!

Features:
• HTML formatted emails
• Professional styling
• Secure Gmail SMTP
• Business branding

Timestamp: Test run
"""
    
    print("Testing Gmail email notification...")
    print(f"Subject: {test_subject}")
    print(f"Message: {test_message.strip()}")
    
    # Check if Gmail credentials are configured
    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    notification_emails = os.getenv("NOTIFICATION_EMAILS")
    
    if not gmail_user:
        print("❌ GMAIL_USER not configured in .env file")
        return False
    
    if not gmail_app_password:
        print("❌ GMAIL_APP_PASSWORD not configured in .env file")
        return False
    
    if not notification_emails:
        print("❌ NOTIFICATION_EMAILS not configured in .env file")
        return False
    
    print(f"✅ Gmail credentials found: {gmail_user}")
    print(f"✅ App password configured")
    print(f"✅ Notification emails: {notification_emails}")
    
    # Parse email recipients
    recipients = [email.strip() for email in notification_emails.split(',')]
    
    # Send test email
    result = send_email_notification(test_subject, test_message.strip(), recipients)
    
    if result:
        print("✅ Email notification sent successfully!")
        print("Check your email inbox for the test message.")
    else:
        print("❌ Email notification failed!")
    
    return result

if __name__ == "__main__":
    test_email_notification()
