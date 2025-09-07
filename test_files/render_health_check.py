#!/usr/bin/env python3
"""
Simple health check endpoint for Render deployment.
This can be accessed via URL to verify environment variables are working.
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def health_check():
    """Return health status and environment variable status."""
    
    # Check required QBO environment variables
    required_vars = [
        'QBO_CLIENT_ID',
        'QBO_CLIENT_SECRET', 
        'QBO_COMPANY_ID',
        'QBO_ACCESS_TOKEN',
        'QBO_REFRESH_TOKEN',
        'QBO_SANDBOX'
    ]
    
    env_status = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values for security
            if 'SECRET' in var or 'TOKEN' in var:
                env_status[var] = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                env_status[var] = value
        else:
            env_status[var] = "NOT_SET"
            missing_vars.append(var)
    
    # Overall status
    status = "healthy" if not missing_vars else "unhealthy"
    
    return {
        "status": status,
        "environment_variables": env_status,
        "missing_variables": missing_vars,
        "total_required": len(required_vars),
        "total_present": len(required_vars) - len(missing_vars)
    }

def test_qbo_connection():
    """Test QBO connection and return status."""
    try:
        from qbo_oauth import QBOOAuth
        oauth = QBOOAuth()
        token = oauth.get_valid_access_token()
        
        if token:
            return {
                "status": "success",
                "message": "QBO connection successful",
                "token_preview": f"{token[:20]}..."
            }
        else:
            return {
                "status": "error", 
                "message": "Failed to get QBO access token"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"QBO connection failed: {str(e)}"
        }

if __name__ == "__main__":
    # If run directly, print JSON output
    health = health_check()
    qbo_test = test_qbo_connection()
    
    result = {
        "health_check": health,
        "qbo_connection": qbo_test,
        "timestamp": str(os.popen('date').read().strip())
    }
    
    print("Content-Type: application/json")
    print()
    print(json.dumps(result, indent=2))
