#!/usr/bin/env python3
"""
Webhook Activity Logger - Logs webhook requests for debugging
Add this to your webhook handler to track all incoming requests
"""

import json
import os
from datetime import datetime
from flask import Flask, request, jsonify

# Create a simple webhook logger endpoint
app = Flask(__name__)

def log_webhook_activity(endpoint, data, response_status=200):
    """Log webhook activity to a file."""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "endpoint": endpoint,
        "request_data": data,
        "response_status": response_status
    }
    
    # Create logs directory if it doesn't exist
    os.makedirs("webhook_logs", exist_ok=True)
    
    # Log to daily file
    log_file = f"webhook_logs/webhook_activity_{datetime.now().strftime('%Y%m%d')}.json"
    
    try:
        # Read existing logs
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Add new log entry
        logs.append(log_entry)
        
        # Write back to file
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
        print(f"📝 Webhook activity logged: {endpoint} at {timestamp}")
        
    except Exception as e:
        print(f"❌ Error logging webhook activity: {e}")

@app.route('/webhook/pipedrive/organization', methods=['POST'])
def log_pipedrive_webhook():
    """Log Pipedrive webhook activity."""
    try:
        data = request.get_json()
        log_webhook_activity("/webhook/pipedrive/organization", data)
        
        # Return success response
        return jsonify({
            "status": "logged",
            "timestamp": datetime.now().isoformat(),
            "message": "Webhook activity logged successfully"
        }), 200
        
    except Exception as e:
        log_webhook_activity("/webhook/pipedrive/organization", {"error": str(e)}, 500)
        return jsonify({"error": str(e)}), 500

@app.route('/webhook/quoter/quote-published', methods=['POST'])
def log_quoter_webhook():
    """Log Quoter webhook activity."""
    try:
        data = request.get_json()
        log_webhook_activity("/webhook/quoter/quote-published", data)
        
        # Return success response
        return jsonify({
            "status": "logged",
            "timestamp": datetime.now().isoformat(),
            "message": "Webhook activity logged successfully"
        }), 200
        
    except Exception as e:
        log_webhook_activity("/webhook/quoter/quote-published", {"error": str(e)}, 500)
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "service": "webhook-logger",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    print("🚀 Starting Webhook Activity Logger")
    print("📝 Logs will be saved to webhook_logs/ directory")
    app.run(host="0.0.0.0", port=5001, debug=True)
