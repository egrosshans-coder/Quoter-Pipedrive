#!/usr/bin/env python3
"""
Custom Webhook Server for Quoter-Pipedrive Integration

This webhook receives quote creation events from Quoter and handles:
1. Extracting deal ID from organization data
2. Associating the quote with the Pipedrive deal
3. Updating quote fields as needed

Usage:
    python3 custom_webhook.py
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipedrive import get_organization_by_id, get_deal_by_id
from quoter import get_access_token
from utils.logger import logger

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
webhook_logger = logging.getLogger(__name__)

class QuoterWebhookHandler:
    """Handles Quoter webhook events for Pipedrive integration."""
    
    def __init__(self):
        self.quoter_api_key = os.getenv('QUOTER_API_KEY')
        self.pipedrive_api_key = os.getenv('PIPEDRIVE_API_KEY')
        
    def handle_quote_created(self, webhook_data):
        """
        Handle quote creation webhook from Quoter.
        
        Args:
            webhook_data (dict): Webhook payload from Quoter
            
        Returns:
            dict: Response indicating success/failure
        """
        try:
            webhook_logger.info("🔄 Processing quote creation webhook...")
            webhook_logger.info(f"Webhook data: {json.dumps(webhook_data, indent=2)}")
            
            # Extract key information from webhook
            quote_id = webhook_data.get('id')
            quote_number = webhook_data.get('number')
            organization_name = webhook_data.get('organization')
            contact_name = webhook_data.get('person', {}).get('first_name', '') + ' ' + webhook_data.get('person', {}).get('last_name', '')
            
            if not quote_id:
                webhook_logger.error("❌ No quote ID in webhook data")
                return {"success": False, "error": "No quote ID"}
            
            webhook_logger.info(f"📋 Processing Quote:")
            webhook_logger.info(f"   ID: {quote_id}")
            webhook_logger.info(f"   Number: {quote_number}")
            webhook_logger.info(f"   Organization: {organization_name}")
            webhook_logger.info(f"   Contact: {contact_name}")
            
            # Extract deal ID from organization name (format: "CompanyName-1234")
            if not organization_name or "-" not in organization_name:
                webhook_logger.error(f"❌ Invalid organization name format: {organization_name}")
                return {"success": False, "error": "Invalid organization name format"}
            
            deal_id = organization_name.split("-")[-1]
            try:
                # Validate deal ID is numeric
                int(deal_id)
            except ValueError:
                webhook_logger.error(f"❌ Invalid deal ID format: {deal_id}")
                return {"success": False, "error": "Invalid deal ID format"}
            
            webhook_logger.info(f"🔍 Extracted Deal ID: {deal_id}")
            
            # Verify the deal exists in Pipedrive
            deal_data = get_deal_by_id(deal_id)
            if not deal_data:
                webhook_logger.error(f"❌ Deal {deal_id} not found in Pipedrive")
                return {"success": False, "error": f"Deal {deal_id} not found in Pipedrive"}
            
            webhook_logger.info(f"✅ Verified Deal: {deal_data.get('title', f'Deal {deal_id}')}")
            
            # Now we need to update the quote to associate it with the deal
            # Since we can't update via API (403), we'll log what needs to be done manually
            webhook_logger.info(f"🎯 Quote {quote_id} needs manual deal association:")
            webhook_logger.info(f"   1. Open quote in Quoter")
            webhook_logger.info(f"   2. Manually select deal {deal_id} from dropdown")
            webhook_logger.info(f"   3. This will create the Pipedrive association")
            
            # TODO: Implement actual quote update when we have proper permissions
            # For now, we'll just log the information
            
            return {
                "success": True,
                "message": f"Quote {quote_id} processed successfully",
                "deal_id": deal_id,
                "organization": organization_name,
                "manual_steps_required": [
                    "Open quote in Quoter",
                    f"Manually select deal {deal_id} from dropdown",
                    "This will create the Pipedrive association"
                ]
            }
            
        except Exception as e:
            webhook_logger.error(f"❌ Error processing webhook: {e}")
            return {"success": False, "error": str(e)}
    
    def handle_quote_updated(self, webhook_data):
        """Handle quote update webhook from Quoter."""
        webhook_logger.info("🔄 Quote update webhook received (not yet implemented)")
        return {"success": True, "message": "Quote update webhook received"}

# Initialize webhook handler
webhook_handler = QuoterWebhookHandler()

@app.route('/webhook/quoter', methods=['POST'])
def quoter_webhook():
    """Main webhook endpoint for Quoter events."""
    try:
        # Get webhook data
        webhook_data = request.get_json()
        
        if not webhook_data:
            return jsonify({"error": "No webhook data received"}), 400
        
        webhook_logger.info("📥 Webhook received from Quoter")
        webhook_logger.info(f"Event type: {webhook_data.get('event_type', 'unknown')}")
        
        # Handle different event types
        event_type = webhook_data.get('event_type', '')
        
        if event_type == 'quote.created':
            result = webhook_handler.handle_quote_created(webhook_data)
        elif event_type == 'quote.updated':
            result = webhook_handler.handle_quote_updated(webhook_data)
        else:
            webhook_logger.warning(f"⚠️ Unknown event type: {event_type}")
            result = {"success": True, "message": f"Unknown event type: {event_type}"}
        
        return jsonify(result)
        
    except Exception as e:
        webhook_logger.error(f"❌ Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Quoter-Pipedrive Webhook"
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with webhook information."""
    return jsonify({
        "service": "Quoter-Pipedrive Custom Webhook",
        "endpoints": {
            "webhook": "/webhook/quoter",
            "health": "/health"
        },
        "usage": "Configure this URL in Quoter webhook settings",
        "supported_events": ["quote.created", "quote.updated"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('WEBHOOK_PORT', 5000))
    webhook_logger.info(f"🚀 Starting Quoter-Pipedrive Webhook Server on port {port}")
    webhook_logger.info(f"📡 Webhook URL: http://localhost:{port}/webhook/quoter")
    webhook_logger.info(f"🔧 Health Check: http://localhost:{port}/health")
    webhook_logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=True)
