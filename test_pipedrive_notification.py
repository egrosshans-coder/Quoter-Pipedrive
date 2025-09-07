#!/usr/bin/env python3
"""
Test script for Pipedrive note notification functionality
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

from notification import send_pipedrive_note_notification

def test_pipedrive_note_notification():
    """Test the Pipedrive note notification functionality"""
    
    # Test message
    test_message = """
🧪 TEST PIPEDRIVE NOTE

This is a test of the Pipedrive note notification system.
If you see this note in the deal, the integration is working!

Features:
• Direct note creation in Pipedrive deals
• Complete audit trail
• Professional formatting
• Error handling

Timestamp: Test run
"""
    
    print("Testing Pipedrive note notification...")
    print(f"Message: {test_message.strip()}")
    
    # Check if Pipedrive API token is configured
    pipedrive_token = os.getenv("PIPEDRIVE_API_TOKEN")
    if not pipedrive_token:
        print("❌ PIPEDRIVE_API_TOKEN not configured in .env file")
        return False
    
    print(f"✅ Pipedrive API token found: {pipedrive_token[:10]}...")
    
    # Get test deal ID from user or use a default
    test_deal_id = input("Enter a Pipedrive deal ID to test with (or press Enter to skip): ").strip()
    
    if not test_deal_id:
        print("⚠️ No deal ID provided - skipping test")
        return False
    
    try:
        test_deal_id = int(test_deal_id)
    except ValueError:
        print("❌ Invalid deal ID - must be a number")
        return False
    
    # Send test note
    result = send_pipedrive_note_notification(test_deal_id, test_message.strip())
    
    if result:
        print("✅ Pipedrive note notification sent successfully!")
        print(f"Check deal {test_deal_id} in Pipedrive for the test note.")
    else:
        print("❌ Pipedrive note notification failed!")
    
    return result

if __name__ == "__main__":
    test_pipedrive_note_notification()
