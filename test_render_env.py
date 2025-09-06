#!/usr/bin/env python3
"""
Test script to verify Render environment variables are set correctly.
This can be run on Render to check if all QBO credentials are available.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_render_environment():
    """Test if all required environment variables are available."""
    print("🔍 Testing Render Environment Variables...")
    print("=" * 50)
    
    # Required QBO environment variables
    required_vars = [
        'QBO_CLIENT_ID',
        'QBO_CLIENT_SECRET', 
        'QBO_COMPANY_ID',
        'QBO_ACCESS_TOKEN',
        'QBO_REFRESH_TOKEN',
        'QBO_SANDBOX'
    ]
    
    missing_vars = []
    present_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'SECRET' in var or 'TOKEN' in var:
                masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
            present_vars.append(var)
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    print("=" * 50)
    
    if missing_vars:
        print(f"❌ Missing {len(missing_vars)} environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False
    else:
        print(f"✅ All {len(required_vars)} environment variables are set!")
        return True

def test_qbo_connection():
    """Test QBO connection using environment variables."""
    print("\n🔗 Testing QBO Connection...")
    print("=" * 50)
    
    try:
        from qbo_oauth import QBOOAuth
        
        # Test OAuth initialization
        oauth = QBOOAuth()
        print("✅ QBO OAuth client initialized successfully")
        
        # Test getting valid access token
        token = oauth.get_valid_access_token()
        if token:
            print(f"✅ Successfully retrieved access token: {token[:20]}...")
            return True
        else:
            print("❌ Failed to get valid access token")
            return False
            
    except Exception as e:
        print(f"❌ QBO connection failed: {e}")
        return False

def main():
    """Run all environment tests."""
    print("🧪 Render Environment Test")
    print("=" * 50)
    
    # Test 1: Environment variables
    env_ok = test_render_environment()
    
    # Test 2: QBO connection (only if env vars are OK)
    qbo_ok = False
    if env_ok:
        qbo_ok = test_qbo_connection()
    
    # Summary
    print("\n📊 Test Summary:")
    print("=" * 50)
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"QBO Connection: {'✅ PASS' if qbo_ok else '❌ FAIL'}")
    
    if env_ok and qbo_ok:
        print("\n🎉 Render is set up correctly! QBO integration is ready.")
        return 0
    else:
        print("\n⚠️  Render setup needs attention. Check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
