#!/usr/bin/env python3
"""
Test Webhook Handler - For testing webhook logic without making real API calls
This is a safe testing environment that doesn't create real quotes or customers.
"""

import json
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

app = Flask(__name__)

@app.route('/webhook/test', methods=['POST'])
def handle_test_webhook():
    """
    Test webhook handler that simulates the production webhook without making real API calls.
    """
    try:
        logger.info("🧪 TEST WEBHOOK: Starting test webhook processing")
        
        # Handle both JSON and form data formats
        if request.content_type == 'application/json':
            data = request.get_json()
            logger.info(f"🧪 TEST: Received JSON webhook: {json.dumps(data, indent=2)}")
            # Check if data is nested under 'data' key or direct
            organization_data = data.get('data', data) if 'data' in data else data
        else:
            # Handle form data (key-value pairs from Pipedrive automation)
            form_data = request.form.to_dict()
            logger.info(f"🧪 TEST: Received form webhook: {json.dumps(form_data, indent=2)}")
            organization_data = form_data
        
        # Handle empty data from Pipedrive retries/timeouts
        if not organization_data:
            logger.info("🧪 TEST: Received empty webhook data (likely from Pipedrive retry/timeout)")
            return jsonify({"status": "ignored", "reason": "empty_data"}), 200
        
        # Handle Pipedrive automation format where organization ID might be in {{organization.name}} key
        logger.info(f"🧪 TEST: Looking for organization ID in data: {organization_data}")
        organization_id = organization_data.get('id')
        logger.info(f"🧪 TEST: organization_id from 'id': {organization_id}")
        if not organization_id:
            # Try the Pipedrive automation format
            organization_id = organization_data.get('{{organization.name}}')
            logger.info(f"🧪 TEST: organization_id from '{{organization.name}}': {organization_id}")
        
        if not organization_id:
            logger.error(f"🧪 TEST: No organization ID found. Available keys: {list(organization_data.keys())}")
            return jsonify({"error": "No organization ID"}), 400
        
        # Check if this is a sub-organization ready for quotes
        # Look for HID-QBO-Status = 289 (QBO-SubCust)
        hid_status = organization_data.get('454a3767bce03a880b31d78a38c480d6870e0f1b')
        if not hid_status:
            # Try the Pipedrive automation format
            hid_status = organization_data.get('{{organization.454a3767bce03a880b31d78a38c480d6870e0f1b}}')
        
        # Check if status is ready for quotes (289 or "QBO-SubCust")
        if hid_status not in [289, "289", "QBO-SubCust"]:
            logger.info(f"🧪 TEST: Organization {organization_id} not ready for quotes (status: {hid_status})")
            return jsonify({"status": "ignored", "reason": "not_ready_for_quotes"}), 200
        
        # Process organizations from all owners (no owner restriction)
        owner_id = organization_data.get('owner_id', {}).get('value')
        owner_name = organization_data.get('owner_id', {}).get('name', 'Unknown')
        logger.info(f"🧪 TEST: Processing organization {organization_id} owned by {owner_name} (ID: {owner_id})")
        
        # Get organization name and extract deal ID from the end of the name
        organization_name = organization_data.get('name', 'Unknown Organization')
        logger.info(f"🧪 TEST: Organization name: {organization_name}")
        
        # Extract deal ID from organization name (format: "Name-DealID")
        if '-' in organization_name:
            deal_id = organization_name.split('-')[-1]
            logger.info(f"🧪 TEST: Extracted deal ID: {deal_id} from organization: {organization_name}")
        else:
            logger.error(f"🧪 TEST: Organization {organization_id} name '{organization_name}' does not contain deal ID (expected format: 'Name-DealID')")
            return jsonify({"error": "No deal ID in organization name"}), 400
        
        logger.info(f"🧪 TEST: Processing organization {organization_id} ({organization_name}) for deal {deal_id}")
        
        # Simulate getting deal information (no real API call)
        logger.info(f"🧪 TEST: Would fetch deal {deal_id} from Pipedrive")
        deal_data = {"id": deal_id, "title": f"Test Deal {deal_id}"}
        
        deal_title = deal_data.get("title", f"Deal {deal_id}")
        
        # Simulate creating comprehensive draft quote (no real API call)
        logger.info(f"🧪 TEST: Would create quote for organization {organization_id}")
        quote_data = {"id": f"test_quote_{organization_id}", "status": "draft"}
        
        if quote_data:
            # Simulate sending notification (no real notification)
            logger.info(f"🧪 TEST: Would send notification for quote {quote_data['id']}")
            
            logger.info(f"🧪 TEST: ✅ Successfully simulated quote creation for organization {organization_id} (deal {deal_id})")
            return jsonify({
                "status": "success",
                "quote_id": quote_data.get("id"),
                "organization_id": organization_id,
                "deal_id": deal_id,
                "test_mode": True
            }), 200
        else:
            logger.error(f"🧪 TEST: ❌ Failed to simulate quote creation for organization {organization_id}")
            return jsonify({"error": "Quote creation simulation failed"}), 500
            
    except Exception as e:
        logger.error(f"🧪 TEST: ❌ Error in test webhook: {e}")
        return jsonify({"error": "Test webhook failed", "details": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the test webhook server."""
    return jsonify({
        "service": "test-webhook-handler",
        "status": "healthy",
        "endpoints": {
            "test_webhook": "/webhook/test",
            "health": "/health"
        }
    }), 200

if __name__ == '__main__':
    logger.info("🧪 Starting Test Webhook Handler")
    app.run(host='0.0.0.0', port=5003, debug=True)
