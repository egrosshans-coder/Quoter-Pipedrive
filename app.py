#!/usr/bin/env python3
"""
Simple Flask app for testing Render environment variables.
This provides web endpoints to check QBO integration status.
"""

import os
import json
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    """Home page with basic info."""
    return """
    <h1>Quoter Sync Health Check</h1>
    <p>Environment testing endpoints:</p>
    <ul>
        <li><a href="/health">/health</a> - Basic health check</li>
        <li><a href="/env">/env</a> - Environment variables status</li>
        <li><a href="/qbo">/qbo</a> - QBO connection test</li>
    </ul>
    """

@app.route('/health')
def health():
    """Basic health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "Service is running",
        "environment": "production" if os.getenv('QBO_SANDBOX', 'true').lower() == 'false' else "sandbox"
    })

@app.route('/env')
def env_check():
    """Check environment variables status."""
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
            # Mask sensitive values
            if 'SECRET' in var or 'TOKEN' in var:
                env_status[var] = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                env_status[var] = value
        else:
            env_status[var] = "NOT_SET"
            missing_vars.append(var)
    
    return jsonify({
        "status": "healthy" if not missing_vars else "unhealthy",
        "environment_variables": env_status,
        "missing_variables": missing_vars,
        "total_required": len(required_vars),
        "total_present": len(required_vars) - len(missing_vars)
    })

@app.route('/qbo')
def qbo_test():
    """Test QBO connection."""
    try:
        from qbo_oauth import QBOOAuth
        oauth = QBOOAuth()
        token = oauth.get_valid_access_token()
        
        if token:
            return jsonify({
                "status": "success",
                "message": "QBO connection successful",
                "token_preview": f"{token[:20]}...",
                "company_id": os.getenv('QBO_COMPANY_ID'),
                "sandbox_mode": os.getenv('QBO_SANDBOX', 'true').lower() == 'true'
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Failed to get QBO access token"
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"QBO connection failed: {str(e)}"
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
