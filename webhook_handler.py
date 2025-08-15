#!/usr/bin/env python3
"""
Webhook Handler - Receives events from Pipedrive automation
Triggers quote creation when sub-organization is ready.
"""

import json
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from quoter import create_draft_quote, create_comprehensive_quote_from_pipedrive
from pipedrive import get_deal_by_id, get_organization_by_id
from notification import send_quote_created_notification
from utils.logger import logger

load_dotenv()

app = Flask(__name__)

@app.route('/webhook/pipedrive/organization', methods=['POST'])
def handle_organization_webhook():
    """
    Handle webhook events from Pipedrive when organizations are updated.
    Specifically triggers when HID-QBO-Status changes to 'QBO-SubCust'.
    """
    try:
        # Verify webhook authenticity (optional but recommended)
        # TODO: Add webhook signature verification
        
        data = request.get_json()
        logger.info(f"Received webhook: {json.dumps(data, indent=2)}")
        
        # Extract organization data
        organization_data = data.get('data', {})
        organization_id = organization_data.get('id')
        
        if not organization_id:
            logger.error("No organization ID in webhook data")
            return jsonify({"error": "No organization ID"}), 400
        
        # Check if this is a sub-organization ready for quotes
        # Look for HID-QBO-Status = 289 (QBO-SubCust)
        hid_status = organization_data.get('454a3767bce03a880b31d78a38c480d6870e0f1b')
        
        if hid_status != 289:  # Not QBO-SubCust
            logger.info(f"Organization {organization_id} not ready for quotes (status: {hid_status})")
            return jsonify({"status": "ignored", "reason": "not_ready_for_quotes"}), 200
        
        # Check if owned by Maurice (ID: 19103598)
        owner_id = organization_data.get('owner_id', {}).get('value')
        if owner_id != 19103598:
            logger.info(f"Organization {organization_id} not owned by Maurice (owner: {owner_id})")
            return jsonify({"status": "ignored", "reason": "wrong_owner"}), 200
        
        # Get organization name and deal ID
        organization_name = organization_data.get('name', 'Unknown Organization')
        deal_id = organization_data.get('15034cf07d05ceb15f0a89dcbdcc4f596348584e')  # Deal_ID field
        
        if not deal_id:
            logger.error(f"Organization {organization_id} has no associated deal ID")
            return jsonify({"error": "No deal ID associated"}), 400
        
        logger.info(f"Processing organization {organization_id} ({organization_name}) for deal {deal_id}")
        
        # Get deal information
        deal_data = get_deal_by_id(deal_id)
        if not deal_data:
            logger.error(f"Could not find deal {deal_id} for organization {organization_id}")
            return jsonify({"error": "Deal not found"}), 404
        
        deal_title = deal_data.get("title", f"Deal {deal_id}")
        
        # Create comprehensive draft quote using our enhanced function
        quote_data = create_comprehensive_quote_from_pipedrive(organization_data)
        
        if quote_data:
            # Send notification
            send_quote_created_notification(quote_data, deal_data, organization_data)
            
            logger.info(f"✅ Successfully created quote for organization {organization_id} (deal {deal_id})")
            return jsonify({
                "status": "success",
                "quote_id": quote_data.get("id"),
                "organization_id": organization_id,
                "deal_id": deal_id
            }), 200
        else:
            logger.error(f"❌ Failed to create quote for organization {organization_id}")
            return jsonify({"error": "Quote creation failed"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook/quoter/quote-published', methods=['POST'])
def handle_quoter_quote_published():
    """
    Handle webhook events from Quoter when quotes are published.
    Updates Pipedrive with quote information and completes the quote lifecycle.
    """
    try:
        # Verify webhook authenticity (optional but recommended)
        # TODO: Add webhook signature verification
        
        data = request.get_json()
        logger.info(f"Received Quoter quote published webhook: {json.dumps(data, indent=2)}")
        
        # Extract quote data
        quote_data = data.get('data', {})
        quote_id = quote_data.get('id')
        quote_status = quote_data.get('status')
        
        if not quote_id:
            logger.error("No quote ID in webhook data")
            return jsonify({"error": "No quote ID"}), 400
        
        # Only process published quotes
        if quote_status != 'published':
            logger.info(f"Quote {quote_id} not published (status: {quote_status})")
            return jsonify({"status": "ignored", "reason": "not_published"}), 200
        
        logger.info(f"Processing published quote: {quote_id}")
        
        # Extract quote details
        quote_name = quote_data.get('name', 'Unknown Quote')
        quote_number = quote_data.get('number', 'No Number')
        quote_total = quote_data.get('total', 0)
        contact_id = quote_data.get('contact_id')
        
        # Get contact information to find Pipedrive organization
        if contact_id:
            # TODO: Implement contact lookup to get Pipedrive organization ID
            # This will require additional Quoter API calls or storing the mapping
            logger.info(f"Quote {quote_id} published for contact: {contact_id}")
            
            # Update Pipedrive deal with quote information
            # TODO: Implement update_deal_with_quote_info function
            logger.info(f"Quote {quote_id} published successfully - Pipedrive update pending")
            
            # Send notification
            # TODO: Implement send_quote_published_notification function
            logger.info(f"Quote {quote_id} published - notification pending")
            
            return jsonify({
                "status": "success",
                "quote_id": quote_id,
                "message": "Quote published successfully - Pipedrive update pending"
            }), 200
        else:
            logger.error(f"Quote {quote_id} has no contact ID")
            return jsonify({"error": "No contact ID"}), 400
            
    except Exception as e:
        logger.error(f"❌ Error processing Quoter webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "quote-automation-webhook"}), 200

if __name__ == '__main__':
    # Run the webhook server
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting webhook server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
