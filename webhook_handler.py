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
from pipedrive import get_deal_by_id, get_organization_by_id, update_deal_with_quote_info
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
        
        # Handle both Content-Type: application/json and raw JSON
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            # Try to parse raw JSON data even without Content-Type header
            try:
                raw_data = request.get_data(as_text=True)
                data = json.loads(raw_data) if raw_data else {}
                logger.info(f"Parsed JSON without Content-Type header: {raw_data}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON data: {e}")
                return jsonify({"error": "Invalid JSON data"}), 400
        
        logger.info(f"Received Quoter quote published webhook: {json.dumps(data, indent=2)}")
        
        # Extract quote data
        quote_data = data.get('data', {})
        quote_id = quote_data.get('id')
        quote_status = quote_data.get('status')
        
        if not quote_id:
            logger.error("No quote ID in webhook data")
            return jsonify({"error": "No quote ID"}), 400
        
        # Process quotes that are ready for Pipedrive updates (pending or published)
        if quote_status not in ['pending', 'published']:
            logger.info(f"Quote {quote_id} not ready for Pipedrive update (status: {quote_status})")
            return jsonify({"status": "ignored", "reason": "not_ready_for_update"}), 200
        
        logger.info(f"Processing published quote: {quote_id}")
        
        # Extract quote details
        quote_name = quote_data.get('name', 'Unknown Quote')
        quote_number = quote_data.get('number', 'No Number')
        quote_total = quote_data.get('total', {})
        contact_data = quote_data.get('person', {})
        contact_id = contact_data.get('public_id')
        
        # Extract deal ID from organization name (e.g., "Blue Owl Capital-2096" -> "2096")
        organization_name = contact_data.get('organization', '')
        deal_id = None
        if organization_name and '-' in organization_name:
            deal_id = organization_name.split('-')[-1]
            logger.info(f"Extracted deal ID: {deal_id} from organization: {organization_name}")
        
        # Extract total amount
        total_amount = quote_total.get('upfront', '0') if isinstance(quote_total, dict) else str(quote_total)
        
        # Get contact information to find Pipedrive organization
        if contact_id and deal_id:
            logger.info(f"Quote {quote_id} ready for Pipedrive update:")
            logger.info(f"   Contact: {contact_id}")
            logger.info(f"   Deal ID: {deal_id}")
            logger.info(f"   Amount: ${total_amount}")
            logger.info(f"   Status: {quote_status}")
            
            # Update Pipedrive deal with quote information
            try:
                # Update Pipedrive deal with quote information
                update_result = update_deal_with_quote_info(
                    deal_id=deal_id,
                    quote_id=quote_id,
                    quote_number=quote_number,
                    quote_amount=total_amount,
                    quote_status=quote_status,
                    contact_data=contact_data
                )
                
                if update_result:
                    logger.info(f"✅ Successfully updated Pipedrive deal {deal_id} with quote {quote_id}")
                else:
                    logger.warning(f"⚠️ Pipedrive update for deal {deal_id} may have failed")
                
                # Send notification
                # TODO: Implement send_quote_published_notification function
                logger.info(f"Quote {quote_id} - notification pending")
                
                return jsonify({
                    "status": "success",
                    "quote_id": quote_id,
                    "deal_id": deal_id,
                    "amount": total_amount,
                    "message": f"Quote ready for Pipedrive update to deal {deal_id}"
                }), 200
                
            except Exception as e:
                logger.error(f"Error updating Pipedrive for quote {quote_id}: {e}")
                return jsonify({"error": f"Pipedrive update failed: {str(e)}"}), 500
        else:
            logger.error(f"Quote {quote_id} missing required data: contact_id={contact_id}, deal_id={deal_id}")
            return jsonify({"error": "Missing contact_id or deal_id"}), 400
                
    except Exception as e:
        logger.error(f"❌ Error processing Quoter webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "quote-automation-webhook"}), 200

if __name__ == '__main__':
    # Run the webhook server
    port = int(os.environ.get('PORT', 8000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    logger.info(f"🚀 Starting webhook server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
