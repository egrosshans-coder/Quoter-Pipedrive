#!/usr/bin/env python3
"""
Webhook Handler - Receives events from Pipedrive automation
Triggers quote creation when sub-organization is ready.
"""

import json
import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from quoter import create_draft_quote, create_comprehensive_quote_from_pipedrive
from pipedrive import get_deal_by_id, get_organization_by_id, update_deal_with_quote_info
from notification import send_quote_created_notification
from utils.logger import logger

load_dotenv()

app = Flask(__name__)

def update_quote_with_sequential_number(quote_id, deal_id):
    """
    Update a published quote with sequential numbering in xxxxx-yy format.
    
    Args:
        quote_id (str): The quote ID from Quoter
        deal_id (str): The deal ID from Pipedrive
        
    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        # Generate sequential quote number
        from quoter import generate_sequential_quote_number
        quote_number = generate_sequential_quote_number(deal_id)
        logger.info(f"🎯 Updating quote {quote_id} with custom_number: {quote_number}")
        
        # Get access token
        from quoter import get_access_token
        access_token = get_access_token()
        if not access_token:
            logger.error("❌ Failed to get OAuth token for quote update")
            return False
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Update the quote with our sequential numbering
        update_data = {
            "custom_number": quote_number
        }
        
        response = requests.put(
            f"https://api.quoter.com/v1/quotes/{quote_id}",
            json=update_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Successfully updated quote {quote_id} with custom_number: {quote_number}")
            return True
        else:
            logger.error(f"❌ Failed to update quote {quote_id}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating quote {quote_id} with custom_number: {e}")
        return False

@app.route('/webhook/pipedrive/organization', methods=['POST'])
@app.route('/webhook/pipedrive/organization/', methods=['POST'])
def handle_organization_webhook():
    """
    Handle webhook events from Pipedrive when organizations are updated.
    Specifically triggers when HID-QBO-Status changes to 'QBO-SubCust'.
    """
    try:
        # Verify webhook authenticity (optional but recommended)
        # TODO: Add webhook signature verification
        
        # Handle both JSON and form data formats
        if request.content_type == 'application/json':
            data = request.get_json()
            logger.info(f"Received JSON webhook: {json.dumps(data, indent=2)}")
            # Check if data is nested under 'data' key or direct
            organization_data = data.get('data', data) if 'data' in data else data
        else:
            # Handle form data (key-value pairs from Pipedrive automation)
            form_data = request.form.to_dict()
            logger.info(f"Received form webhook: {json.dumps(form_data, indent=2)}")
            organization_data = form_data
        
        # Handle empty data from Pipedrive retries/timeouts
        if not organization_data:
            logger.info("Received empty webhook data (likely from Pipedrive retry/timeout)")
            return jsonify({"status": "ignored", "reason": "empty_data"}), 200
        
        # Handle Pipedrive automation format where organization ID might be in {{organization.name}} key
        logger.info(f"DEBUG: Looking for organization ID in data: {organization_data}")
        organization_id = organization_data.get('id')
        logger.info(f"DEBUG: organization_id from 'id': {organization_id}")
        if not organization_id:
            # Try the Pipedrive automation format
            organization_id = organization_data.get('{{organization.name}}')
            logger.info(f"DEBUG: organization_id from '{{organization.name}}': {organization_id}")
        
        if not organization_id:
            logger.error(f"DEBUG: No organization ID found. Available keys: {list(organization_data.keys())}")
            return jsonify({"error": "No organization ID"}), 400
        
        # Check if this is a sub-organization ready for quotes
        # Look for HID-QBO-Status = 289 (QBO-SubCust)
        hid_status = organization_data.get('454a3767bce03a880b31d78a38c480d6870e0f1b')
        if not hid_status:
            # Try the Pipedrive automation format
            hid_status = organization_data.get('{{organization.454a3767bce03a880b31d78a38c480d6870e0f1b}}')
        
        # Check if status is ready for quotes (289 or "QBO-SubCust")
        if hid_status not in [289, "289", "QBO-SubCust"]:
            logger.info(f"Organization {organization_id} not ready for quotes (status: {hid_status})")
            return jsonify({"status": "ignored", "reason": "not_ready_for_quotes"}), 200
        
        # Process organizations from all owners (no owner restriction)
        owner_id = organization_data.get('owner_id', {}).get('value')
        owner_name = organization_data.get('owner_id', {}).get('name', 'Unknown')
        logger.info(f"Processing organization {organization_id} owned by {owner_name} (ID: {owner_id})")
        
        # Get organization name and extract deal ID from the end of the name
        organization_name = organization_data.get('name', 'Unknown Organization')
        
        # Extract deal ID from organization name (e.g., "Blue Owl Capital-2096" -> "2096")
        deal_id = None
        if organization_name and '-' in organization_name:
            deal_id = organization_name.split('-')[-1]
            logger.info(f"Extracted deal ID: {deal_id} from organization: {organization_name}")
        else:
            logger.error(f"Organization {organization_id} name '{organization_name}' does not contain deal ID (expected format: 'Name-DealID')")
            return jsonify({"error": "No deal ID in organization name"}), 400
        
        logger.info(f"Processing organization {organization_id} ({organization_name}) for deal {deal_id}")
        
        # Get deal information
        deal_data = get_deal_by_id(deal_id)
        if not deal_data:
            logger.error(f"Could not find deal {deal_id} for organization {organization_id}")
            return jsonify({"error": "Deal not found"}), 404
        
        deal_title = deal_data.get("title", f"Deal {deal_id}")
        
        # Create comprehensive draft quote using our enhanced function with template selection
        # Pass deal data to enable template selection from Pipedrive dropdown
        quote_data = create_comprehensive_quote_from_pipedrive(organization_data, deal_data)
        
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
        
        # Handle different content types from Quoter
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            # Quoter sends URL-encoded form data with JSON in the 'data' field
            try:
                raw_data = request.get_data(as_text=True)
                logger.info(f"Raw webhook data received: '{raw_data}' (length: {len(raw_data) if raw_data else 0})")
                
                if not raw_data or raw_data.strip() == '':
                    logger.warning("Received empty request body from Quoter")
                    data = {}
                else:
                    # Parse URL-encoded form data
                    from urllib.parse import parse_qs, unquote
                    form_data = parse_qs(raw_data)
                    
                    # Extract the 'data' field which contains URL-encoded JSON
                    if 'data' in form_data and form_data['data']:
                        encoded_json = form_data['data'][0]
                        decoded_json = unquote(encoded_json)
                        data = json.loads(decoded_json)
                        logger.info(f"Successfully parsed URL-encoded JSON: {json.dumps(data, indent=2)}")
                    else:
                        logger.warning("No 'data' field found in form data")
                        data = {}
                        
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse webhook data: '{raw_data}' - Error: {e}")
                return jsonify({"error": "Invalid webhook data format"}), 400
        
        logger.info(f"Received Quoter quote published webhook: {json.dumps(data, indent=2)}")
        
        # Extract quote data (Quoter sends it directly at root level)
        quote_data = data  # The entire data IS the quote data
        quote_id = quote_data.get('id')
        quote_status = quote_data.get('status')
        
        if not quote_id:
            logger.warning(f"Received webhook with no quote data: {json.dumps(data, indent=2)}")
            return jsonify({"status": "ignored", "reason": "no_quote_data"}), 200
        
        # Check if this is a revision or original quote
        is_revision = quote_data.get('parent_quote_id') is not None
        parent_quote_id = quote_data.get('parent_quote_id')
        revision_number = quote_data.get('revision')
        
        if is_revision:
            logger.info(f"Processing revision {revision_number} of quote {parent_quote_id}")
        else:
            logger.info(f"Processing original quote {quote_id}")
        
        # Process quotes that are ready for Pipedrive updates (pending or published)
        if quote_status not in ['pending', 'published']:
            logger.info(f"Quote {quote_id} not ready for Pipedrive update (status: {quote_status})")
            return jsonify({"status": "ignored", "reason": "not_ready_for_update"}), 200
        
        # Check if we've already processed this specific quote/revision
        processed_quotes_file = "processed_quotes.txt"
        quote_key = f"{quote_id}:{revision_number or 'original'}"
        
        try:
            with open(processed_quotes_file, 'r') as f:
                processed_quotes = f.read().splitlines()
        except FileNotFoundError:
            processed_quotes = []
        
        if quote_key in processed_quotes:
            logger.info(f"Quote {quote_id} (revision {revision_number or 'original'}) already processed, skipping")
            return jsonify({"status": "ignored", "reason": "already_processed"}), 200
        
        logger.info(f"Processing {'revision' if is_revision else 'original'} quote: {quote_id}")
        
        # Extract quote details
        quote_name = quote_data.get('name', 'Unknown Quote')
        quote_number = quote_data.get('number', 'No Number')
        quote_total = quote_data.get('total', {})
        contact_data = quote_data.get('person', {})
        contact_id = contact_data.get('public_id')
        
        # Debug logging for contact_data
        logger.info(f"🔍 DEBUG: Raw person data from quote: {quote_data.get('person', {})}")
        logger.info(f"🔍 DEBUG: Constructed contact_data: {contact_data}")
        logger.info(f"🔍 DEBUG: contact_data type: {type(contact_data)}")
        logger.info(f"🔍 DEBUG: contact_data keys: {list(contact_data.keys()) if isinstance(contact_data, dict) else 'Not a dict'}")
        
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
            logger.info(f"   Type: {'Revision' if is_revision else 'Original'}")
            if is_revision:
                logger.info(f"   Parent Quote: {parent_quote_id}")
                logger.info(f"   Revision: {revision_number}")
            logger.info(f"   Contact: {contact_id}")
            logger.info(f"   Deal ID: {deal_id}")
            logger.info(f"   Amount: ${total_amount}")
            logger.info(f"   Status: {quote_status}")
            logger.info(f"🔍 DEBUG: About to call update_deal_with_quote_info with contact_data: {contact_data}")
            
            # Update Pipedrive with quote information
            try:
                # Extract deal ID from organization name (e.g., "Blue Owl Capital-2096" -> "2096")
                org_name = contact_data.get('organization', '')
                if '-' in org_name:
                    deal_id = org_name.split('-')[-1]
                    logger.info(f"Extracted deal ID: {deal_id} from organization: {org_name}")
                else:
                    logger.error(f"Could not extract deal ID from organization name: {org_name}")
                    return jsonify({"error": "Invalid organization name format"}), 400
                
                # Update the deal with quote information
                from pipedrive import update_deal_with_quote_info
                success = update_deal_with_quote_info(
                    deal_id=deal_id,
                    quote_id=quote_id,
                    quote_number=quote_number,
                    quote_amount=total_amount,
                    quote_status=quote_status,
                    contact_data=contact_data
                )
                
                if success:
                    logger.info(f"✅ Successfully updated Pipedrive deal {deal_id} with quote {quote_id}")
                    
                    # Update the organization address fields instead of contact address
                    try:
                        # Extract organization ID from the contact data or get it from Pipedrive
                        # We'll need to get the organization ID from Pipedrive using the org name
                        from pipedrive import get_organization_by_name, update_organization_address
                        
                        org_name_clean = org_name.split('-')[0] if '-' in org_name else org_name  # Remove deal ID suffix
                        org_data = get_organization_by_name(org_name_clean)
                        
                        if org_data and org_data.get('id'):
                            org_id = org_data['id']
                            logger.info(f"🔄 Updating organization {org_id} address fields with quote data")
                            
                            success = update_organization_address(org_id, contact_data)
                            if success:
                                logger.info(f"✅ Successfully updated organization {org_id} address information")
                            else:
                                logger.warning(f"⚠️ Failed to update organization {org_id} address information")
                        else:
                            logger.warning(f"⚠️ Could not find organization '{org_name_clean}' in Pipedrive")
                            
                    except Exception as e:
                        logger.error(f"❌ Error updating organization address: {e}")
                    
                    # Update the quote with sequential numbering ONLY if it's a new quote (not a revision)
                    if not is_revision:
                        try:
                            logger.info(f"🎯 Updating NEW quote {quote_id} with sequential numbering...")
                            # TODO: Uncomment when custom_number field becomes updatable
                            # numbering_update_result = update_quote_with_sequential_number(quote_id, deal_id)
                            
                            # if numbering_update_result:
                            #     logger.info(f"✅ Successfully updated NEW quote {quote_id} with sequential numbering")
                            # else:
                            #     logger.warning(f"⚠️ Failed to update quote {quote_id} with sequential numbering")
                            
                            # For now, just log the custom number that would be assigned
                            from quoter import generate_sequential_quote_number
                            custom_number = generate_sequential_quote_number(deal_id)
                            logger.info(f"📝 Would assign custom_number '{custom_number}' to quote {quote_id} (currently disabled)")
                            
                        except Exception as e:
                            logger.warning(f"⚠️ Error generating sequential numbering: {e}")
                    else:
                        logger.info(f"📝 Skipping sequential numbering for REVISION {quote_id} (revision {revision_number})")
                        logger.info(f"   Revisions keep the same quote number as the parent quote")
                    
                    # Mark this quote/revision as processed
                    try:
                        with open(processed_quotes_file, 'a') as f:
                            f.write(f"{quote_key}\n")
                        logger.info(f"✅ Marked quote {quote_id} (revision {revision_number or 'original'}) as processed")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to mark quote as processed: {e}")
                    
                    # Send notification
                    # TODO: Implement send_quote_published_notification function
                    logger.info(f"Quote {quote_id} - notification pending")
                    
                    return jsonify({
                        "status": "success",
                        "quote_id": quote_id,
                        "deal_id": deal_id,
                        "type": "revision" if is_revision else "original",
                        "amount": total_amount,
                        "message": f"{'Revision' if is_revision else 'Original'} quote ready for Pipedrive update to deal {deal_id}"
                    }), 200
                
            except Exception as e:
                logger.error(f"❌ Error updating Pipedrive: {e}")
                return jsonify({"error": f"Failed to update Pipedrive: {str(e)}"}), 500
        else:
            logger.error(f"Quote {quote_id} missing required data: contact_id={contact_id}, deal_id={deal_id}")
            return jsonify({"error": "Missing contact_id or deal_id"}), 400
                
    except Exception as e:
        logger.error(f"❌ Error processing Quoter webhook: {e}")
        return jsonify({"error": str(e)}), 500

def cleanup_old_processed_quotes():
    """Clean up old processed quotes to prevent file from growing indefinitely."""
    processed_quotes_file = "processed_quotes.txt"
    try:
        with open(processed_quotes_file, 'r') as f:
            processed_quotes = f.read().splitlines()
        
        # Keep only the last 1000 processed quotes
        if len(processed_quotes) > 1000:
            processed_quotes = processed_quotes[-1000:]
            with open(processed_quotes_file, 'w') as f:
                f.write('\n'.join(processed_quotes) + '\n')
            logger.info(f"🧹 Cleaned up processed quotes file, kept last 1000 entries")
            
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"⚠️ Failed to cleanup processed quotes: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    # Clean up old processed quotes on health check
    cleanup_old_processed_quotes()
    
    return jsonify({
        "service": "quote-automation-webhook",
        "status": "healthy",
        "endpoints": {
            "health": "/health",
            "env": "/env",
            "qbo": "/qbo",
            "pipedrive_webhook": "/webhook/pipedrive/organization",
            "quoter_webhook": "/webhook/quoter/quote-published"
        }
    })

@app.route('/env', methods=['GET'])
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

@app.route('/qbo', methods=['GET'])
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

@app.route('/', methods=['GET'])
def root():
    """Root endpoint providing information about the webhook server."""
    return jsonify({
        "service": "Quote Automation Webhook Server",
        "description": "Handles webhooks from Pipedrive and Quoter for automated quote creation and updates",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "env": "/env (GET) - Check environment variables",
            "qbo": "/qbo (GET) - Test QBO connection",
            "pipedrive_webhook": "/webhook/pipedrive/organization (POST)",
            "quoter_webhook": "/webhook/quoter/quote-published (POST)"
        },
        "usage": {
            "pipedrive": "Send organization updates to trigger quote creation",
            "quoter": "Send quote published events to update Pipedrive deals",
            "testing": "Use /env and /qbo to verify QBO integration setup"
        }
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting Quote Automation Webhook Server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

# Ensure the app runs on Render
port = int(os.environ.get("PORT", 8000))
logger.info(f"🚀 Starting Quote Automation Webhook Server on port {port}")
app.run(host="0.0.0.0", port=port, debug=False)
