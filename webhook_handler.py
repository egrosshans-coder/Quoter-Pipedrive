#!/usr/bin/env python3
"""
Webhook Handler - Receives events from Pipedrive automation
Triggers quote creation when sub-organization is ready.
"""

import json
import os
import requests
import time
import threading
import hmac
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from quoter import create_draft_quote
from pipedrive import get_deal_by_id, get_organization_by_id, update_deal_with_quote_info, BASE_URL, API_TOKEN
from notification import send_quote_created_notification, send_slack_alert
from utils.logger import logger

load_dotenv()

app = Flask(__name__)

# Rate limiting and queue management
class WebhookRateLimiter:
    def __init__(self, max_concurrent=1, delay_seconds=2):
        self.max_concurrent = max_concurrent
        self.delay_seconds = delay_seconds
        self.active_requests = 0
        self.lock = threading.Lock()
        self.queue = []
        self.processing = False
    
    def can_process(self):
        """Check if we can process a new request"""
        with self.lock:
            return self.active_requests < self.max_concurrent
    
    def start_processing(self):
        """Mark that we're starting to process a request"""
        with self.lock:
            self.active_requests += 1
            logger.info(f"🔄 Starting webhook processing. Active requests: {self.active_requests}")
    
    def finish_processing(self):
        """Mark that we've finished processing a request"""
        with self.lock:
            self.active_requests = max(0, self.active_requests - 1)
            logger.info(f"✅ Finished webhook processing. Active requests: {self.active_requests}")
    
    def wait_if_needed(self):
        """Wait if we're at capacity"""
        if not self.can_process():
            logger.info(f"⏳ Rate limit reached. Waiting {self.delay_seconds} seconds...")
            time.sleep(self.delay_seconds)
            return self.wait_if_needed()  # Recursive wait
        return True

# Global rate limiter
rate_limiter = WebhookRateLimiter(max_concurrent=1, delay_seconds=3)

# Shared-secret gate for inbound webhooks and debug endpoints.
#
# Three accepted methods, in order of preference:
#   1. HTTP Basic Auth  - Pipedrive's automated webhooks support username and
#                         password fields on the webhook definition but do NOT
#                         support custom headers. The credential travels in the
#                         Authorization header and never reaches an access log.
#   2. X-Webhook-Token  - legacy header. Retained until step 6 of the migration.
#   3. ?token=          - legacy query param. Puts the secret in EVERY access
#                         log. Retained until step 6, then removed.
#
# WEBHOOK_SECRET_PREV is honoured while it is set, so a rotation has no window
# in which one side holds the new value and the other still holds the old one.
# Unset it once rotation is complete.
#
# Behavior: fail-OPEN when no secret is configured, fail-CLOSED once one is.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_SECRET_PREV = os.getenv("WEBHOOK_SECRET_PREV")

_WEBHOOK_SECRETS = [s for s in (WEBHOOK_SECRET, WEBHOOK_SECRET_PREV) if s]

if not _WEBHOOK_SECRETS:
    logger.warning("⚠️ WEBHOOK_SECRET not set - inbound webhook/debug-endpoint auth is DISABLED (fail-open). Set WEBHOOK_SECRET to enable.")
if WEBHOOK_SECRET_PREV:
    logger.warning("⚠️ WEBHOOK_SECRET_PREV is set - rotation in progress, the previous secret is still accepted. Unset it when rotation is complete.")


def _secret_matches(candidate):
    """Constant-time comparison against every currently-accepted secret."""
    if not candidate:
        return False
    return any(hmac.compare_digest(candidate, s) for s in _WEBHOOK_SECRETS)


def _is_authorized(req):
    """True if the request carries an accepted secret, or if none is configured (fail-open).

    Logs which method succeeded, so the legacy paths can be removed on evidence
    rather than on the assumption that nothing uses them.
    """
    if not _WEBHOOK_SECRETS:
        return True

    auth = req.authorization
    if auth and auth.type == "basic":
        if _secret_matches(auth.password):
            logger.info(f"🔑 webhook auth: basic (user={auth.username})")
            return True
        logger.warning(f"🚫 webhook auth: basic rejected (user={auth.username})")
        return False

    if _secret_matches(req.headers.get("X-Webhook-Token")):
        logger.info("🔑 webhook auth: header-token")
        return True

    if _secret_matches(req.args.get("token")):
        logger.info("🔑 webhook auth: query-token")
        return True

    logger.warning("🚫 webhook auth: rejected")
    return False

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
    # Authentication: require shared secret when WEBHOOK_SECRET is configured
    if not _is_authorized(request):
        logger.warning("🚫 Unauthorized Pipedrive webhook request (missing/invalid token)")
        return jsonify({"error": "unauthorized"}), 401

    # Rate limiting: wait if we're at capacity
    if not rate_limiter.wait_if_needed():
        logger.warning("⏳ Rate limit exceeded, rejecting webhook request")
        return jsonify({"status": "rate_limited", "message": "Server busy, please retry"}), 429
    
    # Mark that we're starting to process this request
    rate_limiter.start_processing()
    
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
        
        # Log which address-related keys are present in payload (for debugging)
        address_keys = [k for k in organization_data.keys() if isinstance(k, str) and any(x in k.lower() for x in ('address', 'locality', 'postal', 'route', 'street'))]
        logger.info(f"DEBUG: Address-related keys in payload: {address_keys}")
        # Handle Pipedrive automation format where organization ID is in {{organization.id}} key
        logger.info(f"DEBUG: Looking for organization ID in data: {organization_data}")
        organization_id = organization_data.get('{{organization.id}}')
        logger.info(f"DEBUG: organization_id from '{{organization.id}}': {organization_id}")
        if not organization_id:
            # Fallback to old format
            organization_id = organization_data.get('id')
            logger.info(f"DEBUG: organization_id from 'id': {organization_id}")
            if not organization_id:
                organization_id = organization_data.get('{{organization.name}}')
                logger.info(f"DEBUG: organization_id from '{{organization.name}}': {organization_id}")
        
        if not organization_id:
            logger.error(f"DEBUG: No organization ID found. Available keys: {list(organization_data.keys())}")
            return jsonify({"error": "No organization ID"}), 400
        
        # Copy address from parent org to child org via API (if parent org ID is available)
        # This ensures the child org has address fields populated in Pipedrive
        # Can be disabled via ENABLE_PARENT_ADDRESS_COPY=false to test Pipedrive automation geocoding
        # NOTE: When disabled, we completely bypass address copy - automation will populate address AFTER webhook completes
        enable_address_copy = os.getenv("ENABLE_PARENT_ADDRESS_COPY", "true").lower() in ("true", "1", "yes")
        
        if not enable_address_copy:
            logger.info(f"⏭️  Address copy from parent org is DISABLED (ENABLE_PARENT_ADDRESS_COPY=false)")
            logger.info(f"   Relying on Pipedrive automation geocoding - address will be populated AFTER automation completes")
            logger.info(f"   Skipping all address copy logic")
            parent_org_id = None  # Set to None to skip all address copy code below
        else:
            logger.info(f"✅ Address copy from parent org is ENABLED (backup method)")
            parent_org_id = None
        
        # Method 1: Check for parent org ID in custom field on child org
        # Known Parent_Org_ID field key: 6b4253304d94302a6f387ce6bde138a6dad48026
        parent_org_field_key = os.getenv("PD_CF_PARENT_ORG_ID_KEY", "6b4253304d94302a6f387ce6bde138a6dad48026")
        logger.info(f"🔍 Looking for parent org ID using field key: {parent_org_field_key}")
        if parent_org_field_key:
            field_key_with_prefix = f'{{organization.{parent_org_field_key}}}'
            logger.info(f"🔍 Checking for parent org ID in: '{field_key_with_prefix}' and '{parent_org_field_key}'")
            parent_org_id = (organization_data.get(field_key_with_prefix) or 
                           organization_data.get(parent_org_field_key))
            logger.info(f"🔍 Parent org ID from Method 1: {parent_org_id}")
        
        # Method 2: Check if webhook includes parent org ID directly (common field names)
        if not parent_org_id:
            parent_org_id = (organization_data.get('{{organization.parent_id}}') or 
                           organization_data.get('{{organization.parent_organization_id}}') or
                           organization_data.get('{{organization.Parent_Org_ID}}') or
                           organization_data.get('parent_id') or
                           organization_data.get('parent_organization_id') or
                           organization_data.get('Parent_Org_ID'))
        
        # Method 3: Check if webhook includes parent org ID from deal
        if not parent_org_id:
            parent_org_id = (organization_data.get('{{deal.parent_org_id}}') or
                           organization_data.get('{{deal.parent_organization_id}}') or
                           organization_data.get('parent_org_id'))
        
        # Method 4: Try to get parent org from deal's organization via API (if deal ID is available)
        # Note: This may not work if deal is already linked to child org
        if not parent_org_id:
            deal_id = organization_data.get('{{deal.id}}') or organization_data.get('deal_id')
            if deal_id:
                try:
                    deal_data = get_deal_by_id(deal_id)
                    if deal_data:
                        # Check if deal has a custom field storing parent org ID
                        deal_parent_org_field_key = os.getenv("PD_CF_DEAL_PARENT_ORG_ID_KEY")
                        if deal_parent_org_field_key:
                            parent_org_id = deal_data.get(deal_parent_org_field_key)
                        
                        # Also check deal's org_id - but this might be the child org, so less reliable
                        # Only use if no custom field found
                        if not parent_org_id and deal_data.get('org_id'):
                            deal_org_id = deal_data['org_id'].get('value') if isinstance(deal_data['org_id'], dict) else deal_data['org_id']
                            # If deal org matches child org, skip (deal is already linked to child)
                            if str(deal_org_id) != str(organization_id):
                                # This might be parent org, but not reliable
                                logger.info(f"📍 Found deal org_id {deal_org_id}, but it may not be parent org")
                except Exception as e:
                    logger.debug(f"Could not fetch deal {deal_id} for parent org lookup: {e}")
        
        # Method 5: Fallback - fetch child org from API and check for parent org ID field
        if not parent_org_id:
            try:
                logger.info(f"🔍 Parent org ID not in webhook, fetching child org {organization_id} from API to check for parent org field...")
                child_org_data = get_organization_by_id(organization_id)
                if child_org_data:
                    # Check the custom field directly from API response
                    parent_org_id = child_org_data.get(parent_org_field_key)
                    if parent_org_id:
                        logger.info(f"🔍 Found parent org ID {parent_org_id} from child org API response")
            except Exception as e:
                logger.debug(f"Could not fetch child org {organization_id} for parent org lookup: {e}")
        
        # Only proceed with address copy logic if enabled
        if not enable_address_copy:
            logger.info(f"⏭️  Address copy disabled - skipping all address copy logic")
        else:
            logger.info(f"🔍 Final parent_org_id value: {parent_org_id}")
            if parent_org_id:
                try:
                    # Check if child org already has address fields populated (from geocoding automation)
                    # NOTE: Address may not be populated yet if automation runs AFTER webhook
                    child_has_address = False
                    address_fields_to_check = ["address", "address_locality", "address_street_number", "address_route"]
                    for field in address_fields_to_check:
                        if organization_data.get(f'{{organization.{field}}}') or organization_data.get(field):
                            child_has_address = True
                            break
                    
                    # Also check via API if not in webhook
                    if not child_has_address:
                        try:
                            child_org_check = get_organization_by_id(organization_id)
                            if child_org_check:
                                for field in address_fields_to_check:
                                    if child_org_check.get(field):
                                        child_has_address = True
                                        break
                        except:
                            pass
                    
                    if child_has_address:
                        logger.info(f"📍 Child org {organization_id} already has address fields (geocoding automation worked) - skipping parent copy")
                    else:
                        logger.info(f"📍 Child org {organization_id} missing address - copying from parent org {parent_org_id}...")
                        parent_org = get_organization_by_id(parent_org_id)
                        if parent_org:
                            # Build address payload from parent org
                            address_fields = [
                                "address", "address_street_number", "address_route", "address_subpremise",
                                "address_locality", "address_admin_area_level_1", "address_postal_code", "address_country"
                            ]
                            address_payload = {}
                            for field in address_fields:
                                value = parent_org.get(field)
                                if value not in (None, ""):
                                    address_payload[field] = value
                            
                            if address_payload:
                                # Update child org with parent's address
                                headers = {"Content-Type": "application/json"}
                                params = {"api_token": API_TOKEN}
                                response = requests.put(
                                    f"{BASE_URL}/organizations/{organization_id}",
                                    json=address_payload,
                                    headers=headers,
                                    params=params,
                                    timeout=10
                                )
                                if response.status_code in [200, 201]:
                                    logger.info(f"✅ Successfully copied address from parent org {parent_org_id} to child org {organization_id}")
                                else:
                                    logger.warning(f"⚠️ Failed to copy address: {response.status_code} - {response.text}")
                            else:
                                logger.info(f"📍 Parent org {parent_org_id} has no address fields to copy")
                        else:
                            logger.warning(f"⚠️ Could not fetch parent org {parent_org_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Error copying address from parent org: {e}")
        
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
        organization_name = organization_data.get('{{organization.name}}', 'Unknown Organization')
        
        # If organization name is not provided in webhook data, fetch it from Pipedrive API
        if organization_name == 'Unknown Organization':
            logger.info(f"Organization name not in webhook data, fetching from Pipedrive API for org {organization_id}")
            try:
                org_data = get_organization_by_id(organization_id)
                if org_data and org_data.get('name'):
                    organization_name = org_data['name']
                    logger.info(f"Retrieved organization name from API: {organization_name}")
                else:
                    logger.error(f"Could not retrieve organization name for ID {organization_id}")
                    return jsonify({"error": "Could not retrieve organization name"}), 404
            except Exception as e:
                logger.error(f"Error fetching organization name: {e}")
                return jsonify({"error": "Failed to fetch organization name"}), 500
        
        # Extract deal ID - try direct from webhook first, then fallback to parsing
        deal_id = organization_data.get('{{deal.id}}')
        if deal_id:
            logger.info(f"✅ Using direct deal ID from webhook: {deal_id}")
        else:
            # Fallback: Extract deal ID from organization name (backward compatibility)
            deal_id = organization_data.get('deal_id')
            if deal_id:
                logger.info(f"Using deal ID from webhook data: {deal_id}")
            else:
                # Extract deal ID from organization name (e.g., "Blue Owl Capital-2096" -> "2096")
                if organization_name and '-' in organization_name:
                    deal_id = organization_name.split('-')[-1]
                    logger.info(f"Extracted deal ID: {deal_id} from organization: {organization_name}")
                else:
                    logger.error(f"Organization {organization_id} name '{organization_name}' does not contain deal ID (expected format: 'Name-DealID')")
                    return jsonify({"error": "No deal ID in organization name"}), 400
        
        logger.info(f"Processing organization {organization_id} ({organization_name}) for deal {deal_id}")
        
        # Check if we've already processed this organization recently
        processed_orgs_file = "processed_organizations.txt"
        org_key = f"{organization_id}:{deal_id}"
        
        try:
            with open(processed_orgs_file, 'r') as f:
                processed_orgs = f.read().splitlines()
        except FileNotFoundError:
            processed_orgs = []
        
        if org_key in processed_orgs:
            logger.info(f"Organization {organization_id} (deal {deal_id}) already processed recently, skipping")
            return jsonify({"status": "ignored", "reason": "already_processed"}), 200
        
        # NEW: Try to get all deal data directly from webhook payload (ELIMINATE API CALL)
        deal_title_direct = organization_data.get('{{deal.title}}')
        template_enum_str = organization_data.get('{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}')
        
        # Check if we have all required deal data in webhook
        if deal_title_direct and template_enum_str:
            # We have everything we need - NO API CALL REQUIRED!
            logger.info(f"🚀 ALL deal data available in webhook - eliminating API call!")
            logger.info(f"   Deal ID: {deal_id} (direct)")
            logger.info(f"   Deal Title: {deal_title_direct} (direct)")
            logger.info(f"   Template Enum: {template_enum_str} (direct)")
            
            # Create mock deal_data from webhook
            deal_data = {
                'id': int(deal_id),
                'title': deal_title_direct,
                '42ab0c919271cb24f3587f0b01ea2af166019c8d': template_enum_str
            }
            
            # Add person_id if we have person data from webhook
            # Prioritize {{person.id}} - this is the preferred method for getting labeled phones
            logger.info(f"🔍 Checking for person_id in webhook ({{person.id}} is preferred for labeled phones)...")
            logger.info(f"   {{person.id}}: {organization_data.get('{{person.id}}')}")
            logger.info(f"   {{deal.person_id}}: {organization_data.get('{{deal.person_id}}')}")
            logger.info(f"   person_id: {organization_data.get('person_id')}")
            logger.info(f"   {{deal.person_name}}: {organization_data.get('{{deal.person_name}}')}")
            
            # Prioritize {{person.id}} - most direct way to get person_id for labeled phones
            person_id_from_webhook = (organization_data.get('{{person.id}}') or
                                     organization_data.get('{{deal.person_id}}') or
                                     organization_data.get('person_id') or
                                     organization_data.get('{{deal.person_name}}'))  # Last resort: might be ID
            
            if person_id_from_webhook:
                # Try to parse as integer (person ID)
                try:
                    person_id = int(person_id_from_webhook)
                    deal_data['person_id'] = {'value': person_id}
                    logger.info(f"✅ Added person_id to mock deal_data: {person_id}")
                except (ValueError, TypeError):
                    # If it's actually a name (not numeric), we'll handle it in quoter.py
                    logger.info(f"📋 Person field contains name, not ID: {person_id_from_webhook}")
            else:
                logger.info(f"📋 No person_id in webhook for mock deal_data - will try to fetch from API if needed")
            deal_title = deal_title_direct
            
        else:
            # Fallback: Get deal information via API (backward compatibility)
            logger.info(f"🔄 Missing deal fields in webhook, using API fallback")
            logger.info(f"   Deal title available: {bool(deal_title_direct)}")
            logger.info(f"   Template enum available: {bool(template_enum_str)}")
            
            deal_data = get_deal_by_id(deal_id)
            if not deal_data:
                logger.error(f"Could not find deal {deal_id} for organization {organization_id}")
                return jsonify({"error": "Deal not found"}), 404
                
            deal_title = deal_data.get("title", f"Deal {deal_id}")
            
            # Add template enum to deal_data if we got it directly from webhook
            if template_enum_str:
                deal_data['42ab0c919271cb24f3587f0b01ea2af166019c8d'] = template_enum_str
                logger.info(f"✅ Using direct template from webhook")
        
        def _empty_ok(s):
            """Treat empty, whitespace-only, or colon+quotes as empty."""
            if s is None:
                return ''
            s = str(s).strip().strip('"').strip("'").strip()
            if s in ('', ':', ':"', ':""', '""'):
                return ''
            return s
        
        def _state_to_iso(state_name):
            """Convert full state/province names to ISO codes for Quoter API."""
            if not state_name:
                return ''
            state_name = str(state_name).strip()
            # US States mapping
            us_states = {
                'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR',
                'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE',
                'florida': 'FL', 'georgia': 'GA', 'hawaii': 'HI', 'idaho': 'ID',
                'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS',
                'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
                'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS',
                'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV',
                'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY',
                'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK',
                'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
                'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT',
                'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV',
                'wisconsin': 'WI', 'wyoming': 'WY', 'district of columbia': 'DC'
            }
            # Canadian Provinces mapping
            ca_provinces = {
                'alberta': 'AB', 'british columbia': 'BC', 'manitoba': 'MB', 'new brunswick': 'NB',
                'newfoundland and labrador': 'NL', 'northwest territories': 'NT', 'nova scotia': 'NS',
                'nunavut': 'NU', 'ontario': 'ON', 'prince edward island': 'PE', 'quebec': 'QC',
                'saskatchewan': 'SK', 'yukon': 'YT'
            }
            # Check if already an ISO code (2 uppercase letters)
            if len(state_name) == 2 and state_name.isupper() and state_name.isalpha():
                return state_name
            # Try to match full name (case-insensitive)
            state_lower = state_name.lower()
            if state_lower in us_states:
                return us_states[state_lower]
            if state_lower in ca_provinces:
                return ca_provinces[state_lower]
            # If no match found, return original (API might accept it, or will error and we'll see in logs)
            logger.warning(f"⚠️ Could not convert state '{state_name}' to ISO code, using as-is")
            return state_name

        # Build flat address fields from webhook for quoter (street line 1 from number + route or full)
        addr_street_number_raw = organization_data.get('{{organization.address_street_number}}') or organization_data.get('address_street_number')
        addr_route_raw = organization_data.get('{{organization.address_route}}') or organization_data.get('address_route')
        addr_subpremise_raw = organization_data.get('{{organization.address_subpremise}}') or organization_data.get('address_subpremise')
        addr_locality_raw = organization_data.get('{{organization.address_locality}}') or organization_data.get('address_locality')
        addr_state_raw = organization_data.get('{{organization.address_admin_area_level_1}}') or organization_data.get('address_admin_area_level_1')
        addr_postal_raw = organization_data.get('{{organization.address_postal_code}}') or organization_data.get('address_postal_code')
        addr_country_raw = organization_data.get('{{organization.address_country}}') or organization_data.get('address_country')
        addr_full_raw = organization_data.get('{{organization.address_formatted_address}}') or organization_data.get('{{organization.address}}') or organization_data.get('address')
        logger.info(f"🔍 RAW address from webhook: street_number={addr_street_number_raw!r}, route={addr_route_raw!r}, locality={addr_locality_raw!r}, state={addr_state_raw!r}, postal={addr_postal_raw!r}, country={addr_country_raw!r}, full={addr_full_raw!r}")
        addr_street_number = _empty_ok(addr_street_number_raw)
        addr_route = _empty_ok(addr_route_raw)
        addr_subpremise = _empty_ok(addr_subpremise_raw)
        addr_locality = _empty_ok(addr_locality_raw)
        addr_state_raw_cleaned = _empty_ok(addr_state_raw)
        addr_state = _state_to_iso(addr_state_raw_cleaned)  # Convert to ISO code
        addr_postal = _empty_ok(addr_postal_raw)
        addr_country_raw_cleaned = _empty_ok(addr_country_raw)
        # Convert country to ISO if needed (e.g., "United States" -> "US")
        if addr_country_raw_cleaned:
            country_lower = addr_country_raw_cleaned.lower()
            if country_lower in ('united states', 'usa', 'us'):
                addr_country = 'US'
            elif country_lower in ('canada', 'ca'):
                addr_country = 'CA'
            else:
                # If it's already a 2-letter code, use it; otherwise try to extract or use as-is
                if len(addr_country_raw_cleaned) == 2 and addr_country_raw_cleaned.isupper():
                    addr_country = addr_country_raw_cleaned
                else:
                    addr_country = addr_country_raw_cleaned  # API will validate
        else:
            addr_country = 'US'
        addr_full = _empty_ok(addr_full_raw)
        if not addr_full and (addr_street_number or addr_route):
            addr_full = ' '.join(filter(None, [addr_street_number, addr_route]))
            logger.info(f"🔍 Built addr_full from components: {addr_full!r}")
        # Flat keys quoter expects; only include address2 (subpremise) when non-empty
        flat_address = addr_full or ''
        flat_address2 = addr_subpremise or ''
        flat_city = addr_locality or ''
        flat_state = addr_state or ''
        flat_postal = addr_postal or ''
        flat_country = addr_country or 'US'
        logger.info(f"🔍 State conversion: '{addr_state_raw_cleaned}' -> '{flat_state}'")
        logger.info(f"🔍 Country conversion: '{addr_country_raw_cleaned}' -> '{flat_country}'")

        # If webhook had no address components, try parent org from webhook payload first
        if not flat_address and not flat_city:
            # Check if webhook includes parent org ID
            parent_org_id_webhook = (organization_data.get('{{organization.parent_id}}') or
                                    organization_data.get('{{organization.parent_organization_id}}') or
                                    organization_data.get('parent_id') or
                                    organization_data.get('parent_organization_id'))
            if parent_org_id_webhook:
                try:
                    logger.info(f"📍 Sub-org has no address; fetching parent org {parent_org_id_webhook} from webhook")
                    parent_org = get_organization_by_id(parent_org_id_webhook)
                    if parent_org:
                        parent_address = _empty_ok(parent_org.get('address') or ' '.join(filter(None, [parent_org.get('address_street_number'), parent_org.get('address_route')])))
                        parent_address2 = _empty_ok(parent_org.get('address_subpremise'))
                        parent_city = _empty_ok(parent_org.get('address_locality'))
                        parent_state = _empty_ok(parent_org.get('address_admin_area_level_1'))
                        parent_postal = _empty_ok(parent_org.get('address_postal_code'))
                        parent_country = _empty_ok(parent_org.get('address_country')) or 'US'
                        if parent_address or parent_city:
                            flat_address = parent_address or flat_address
                            flat_address2 = parent_address2 or flat_address2
                            flat_city = parent_city or flat_city
                            flat_state = parent_state or flat_state
                            flat_postal = parent_postal or flat_postal
                            flat_country = parent_country or flat_country
                            logger.info(f"📍 Address filled from parent org {parent_org_id_webhook} (webhook parent fallback)")
                except Exception as e:
                    logger.warning(f"Could not fetch parent org from webhook ID: {e}")
        
        # If still no address (e.g. automation fired before copy-address was saved), fetch sub-org from API
        if not flat_address and not flat_city:
            try:
                # Brief delay so Pipedrive can persist copied address from parent to sub-org
                time.sleep(2)
                org_data = get_organization_by_id(organization_id)
                if org_data:
                    api_address = _empty_ok(org_data.get('address') or ' '.join(filter(None, [org_data.get('address_street_number'), org_data.get('address_route')])))
                    api_address2 = _empty_ok(org_data.get('address_subpremise'))
                    api_city = _empty_ok(org_data.get('address_locality'))
                    api_state = _empty_ok(org_data.get('address_admin_area_level_1'))
                    api_postal = _empty_ok(org_data.get('address_postal_code'))
                    api_country = _empty_ok(org_data.get('address_country')) or 'US'
                    if api_address or api_city:
                        flat_address = api_address or flat_address
                        flat_address2 = api_address2 or flat_address2
                        flat_city = api_city or flat_city
                        flat_state = api_state or flat_state
                        flat_postal = api_postal or flat_postal
                        flat_country = api_country or flat_country
                        logger.info("📍 Address missing in webhook; filled from sub-org API (timing fallback)")
                    else:
                        # Sub-org has no address components - try parent org
                        parent_org_id = None
                        # Check common parent org field names
                        parent_org_id = (org_data.get('parent_id') or 
                                        org_data.get('parent_organization_id') or
                                        (org_data.get('parent_organization', {}) or {}).get('value') if isinstance(org_data.get('parent_organization'), dict) else None)
                        if not parent_org_id and isinstance(org_data.get('parent_organization'), list) and org_data.get('parent_organization'):
                            parent_org_id = org_data['parent_organization'][0].get('value')
                        if parent_org_id:
                            logger.info(f"📍 Sub-org has no address; fetching parent org {parent_org_id} for address")
                            parent_org = get_organization_by_id(parent_org_id)
                            if parent_org:
                                parent_address = _empty_ok(parent_org.get('address') or ' '.join(filter(None, [parent_org.get('address_street_number'), parent_org.get('address_route')])))
                                parent_address2 = _empty_ok(parent_org.get('address_subpremise'))
                                parent_city = _empty_ok(parent_org.get('address_locality'))
                                parent_state = _empty_ok(parent_org.get('address_admin_area_level_1'))
                                parent_postal = _empty_ok(parent_org.get('address_postal_code'))
                                parent_country = _empty_ok(parent_org.get('address_country')) or 'US'
                                if parent_address or parent_city:
                                    flat_address = parent_address or flat_address
                                    flat_address2 = parent_address2 or flat_address2
                                    flat_city = parent_city or flat_city
                                    flat_state = parent_state or flat_state
                                    flat_postal = parent_postal or flat_postal
                                    flat_country = parent_country or flat_country
                                    logger.info(f"📍 Address filled from parent org {parent_org_id} (parent org fallback)")
                                else:
                                    logger.warning(f"Parent org {parent_org_id} also has no address components")
                            else:
                                logger.warning(f"Could not fetch parent org {parent_org_id}")
                        else:
                            logger.info("No parent org ID found in sub-org data")
            except Exception as e:
                logger.warning(f"Could not fetch org address from API: {e}")

        # Create hybrid organization data: simple format + webhook fields + address
        normalized_org_data = {
            # Simple format for quoter.py compatibility
            "id": organization_id,
            "name": organization_name,
            "15034cf07d05ceb15f0a89dcbdcc4f596348584e": deal_id,  # Critical: Deal ID in custom field
            # Keep webhook fields for optimization
            "{{deal.person_name}}": organization_data.get('{{deal.person_name}}'),
            "{{deal.title}}": organization_data.get('{{deal.title}}'),
            "{{deal.id}}": organization_data.get('{{deal.id}}'),
            "{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}": organization_data.get('{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}'),
            "{{person.email}}": organization_data.get('{{person.email}}'),
            # Phone may come as array/object, so we'll extract it in quoter.py
            "{{person.phone}}": organization_data.get('{{person.phone}}') or organization_data.get('{{person.phones}}') or organization_data.get('{{deal.person_phone}}') or organization_data.get('{{organization.phone}}'),
            "{{person.phones}}": organization_data.get('{{person.phones}}'),  # Also store plural version
            "{{deal.person_phone}}": organization_data.get('{{deal.person_phone}}'),
            # Address (flat keys for quoter)
            "address": flat_address,
            "city": flat_city,
            "state": flat_state,
            "postal_code": flat_postal,
            "country": flat_country,
        }
        if flat_address2:
            normalized_org_data["address2"] = flat_address2
        
        logger.info(f"📍 Address from webhook: address={flat_address!r}, city={flat_city!r}, state={flat_state!r}, postal={flat_postal!r}, country={flat_country!r}")
        
        # Compose the quote from Item Groups.
        #
        # This was a branch on USE_V2_COMPOSITION until 2026-08-30. The flag
        # existed so v2 could be deployed without committing to it -- but the
        # rollback it guarded no longer exists (Chapter 3 17.1), and the legacy
        # functions it fell back to have been removed. A flag that cannot be
        # flipped is worse than no flag.
        #
        # The deal is RE-FETCHED rather than read from the webhook payload:
        # that payload carries only id, title and the Quote Template enum,
        # while field 102 (Quote Effects) is not in it at all. The webhook
        # answers WHEN, the API answers WHAT.
        full_deal = get_deal_by_id(deal_id)
        if not full_deal:
            logger.error(f"❌ Could not fetch deal {deal_id} for composition")
            send_slack_alert(
                f"🚨 Quote composition: deal {deal_id} could not be fetched "
                f"from Pipedrive. Check the deal exists and the API token is "
                f"valid.")
            return jsonify({"error": "Deal not found"}), 404

        from quote_composer import create_quote_v2
        quote_data = create_quote_v2(normalized_org_data, full_deal)

        if quote_data:
            # Mark this organization as processed to prevent duplicates
            try:
                with open(processed_orgs_file, 'a') as f:
                    f.write(f"{org_key}\n")
                logger.info(f"✅ Marked organization {organization_id} (deal {deal_id}) as processed")
            except Exception as e:
                logger.warning(f"⚠️ Failed to mark organization as processed: {e}")
            
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
            send_slack_alert(
                f"🚨 STALL Quoter/Render: Deal {deal_id} · Org {organization_name} (#{organization_id})\n"
                f"Draft quote build returned no quote_data — Quoter creation failed. "
                f"Check webhook_handler / Quoter API."
            )
            return jsonify({"error": "Quote creation failed"}), 500
            
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        send_slack_alert(
            f"🚨 STALL Quoter/Render: Deal {locals().get('deal_id', 'unknown')} · "
            f"Org {locals().get('organization_name', 'unknown')} "
            f"(#{locals().get('organization_id', 'unknown')})\n"
            f"Exception while processing webhook: {str(e)[:300]}"
        )
        return jsonify({"error": str(e)}), 500
    finally:
        # Always mark that we've finished processing
        rate_limiter.finish_processing()

@app.route('/webhook/quoter/quote-published', methods=['POST'])
def handle_quoter_quote_published():
    """
    Handle webhook events from Quoter when quotes are published.
    Updates Pipedrive with quote information and completes the quote lifecycle.
    """
    # Authentication: require shared secret when WEBHOOK_SECRET is configured
    if not _is_authorized(request):
        logger.warning("🚫 Unauthorized Quoter webhook request (missing/invalid token)")
        return jsonify({"error": "unauthorized"}), 401

    # Rate limiting: wait if we're at capacity
    if not rate_limiter.wait_if_needed():
        logger.warning("⏳ Rate limit exceeded, rejecting Quoter webhook request")
        return jsonify({"status": "rate_limited", "message": "Server busy, please retry"}), 429
    
    # Mark that we're starting to process this request
    rate_limiter.start_processing()
    
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
        
        # Try to extract deal ID from organization name
        if organization_name and '-' in organization_name:
            # Split by '-' and try to find a numeric deal ID
            parts = organization_name.split('-')
            for part in reversed(parts):  # Check from right to left
                if part.isdigit():
                    deal_id = part
                    logger.info(f"Extracted deal ID: {deal_id} from organization: {organization_name}")
                    break
            
            # If no numeric part found, try the last part anyway
            if not deal_id:
                deal_id = parts[-1]
                logger.info(f"Using last part as deal ID: {deal_id} from organization: {organization_name}")
                
                # Skip if the last part is not numeric (like "Org")
                if not deal_id.isdigit():
                    logger.warning(f"Last part '{deal_id}' is not numeric, skipping quote creation")
                    deal_id = None
        else:
            logger.warning(f"Organization name '{organization_name}' does not contain '-' separator")
        
        # Extract total amount
        total_amount = quote_total.get('upfront', '0') if isinstance(quote_total, dict) else str(quote_total)
        
        # Validate deal ID is numeric
        if deal_id and not deal_id.isdigit():
            logger.error(f"❌ Invalid deal ID format: {deal_id} - must be numeric")
            return jsonify({"error": f"Invalid deal ID format: {deal_id}"}), 400
        
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
                # Use the deal_id we already extracted above
                org_name = contact_data.get('organization', '')
                logger.info(f"Using deal ID: {deal_id} from organization: {org_name}")
                
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
                    
                    # Update the sub-org (deal's organization) address and phone, not the parent org
                    try:
                        from pipedrive import get_deal_by_id, get_organization_by_name, update_organization_address
                        
                        org_id = None
                        deal_data = get_deal_by_id(int(deal_id))
                        if deal_data and deal_data.get('org_id'):
                            org_id = deal_data['org_id'].get('value') if isinstance(deal_data['org_id'], dict) else deal_data['org_id']
                            logger.info(f"🔄 Updating sub-org linked to deal {deal_id}: org_id={org_id}")
                        if not org_id:
                            org_name_clean = org_name.split('-')[0] if '-' in org_name else org_name
                            org_data = get_organization_by_name(org_name_clean)
                            if org_data and org_data.get('id'):
                                org_id = org_data['id']
                                logger.info(f"🔄 Fallback: updating organization by name: {org_name_clean} (id={org_id})")
                        if org_id:
                            success = update_organization_address(org_id, contact_data)
                            if success:
                                logger.info(f"✅ Successfully updated organization {org_id} address and phone")
                            else:
                                logger.warning(f"⚠️ Failed to update organization {org_id} address/phone")
                        else:
                            logger.warning(f"⚠️ Could not resolve organization for deal {deal_id}")
                            
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
    finally:
        # Always mark that we've finished processing
        rate_limiter.finish_processing()

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

def cleanup_old_processed_organizations():
    """Clean up old processed organizations to prevent file from growing indefinitely."""
    processed_orgs_file = "processed_organizations.txt"
    try:
        with open(processed_orgs_file, 'r') as f:
            processed_orgs = f.read().splitlines()
        
        # Keep only the last 500 processed organizations
        if len(processed_orgs) > 500:
            processed_orgs = processed_orgs[-500:]
            with open(processed_orgs_file, 'w') as f:
                f.write('\n'.join(processed_orgs) + '\n')
            logger.info(f"🧹 Cleaned up processed organizations file, kept last 500 entries")
            
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"⚠️ Failed to cleanup processed organizations: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    # Clean up old processed quotes and organizations on health check
    cleanup_old_processed_quotes()
    cleanup_old_processed_organizations()
    
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
    if not _is_authorized(request):
        return jsonify({"error": "unauthorized"}), 401
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
    if not _is_authorized(request):
        return jsonify({"error": "unauthorized"}), 401
    try:
        from qbo_oauth import QBOOAuth
        oauth = QBOOAuth()
        token = oauth.get_valid_access_token()
        
        if token:
            return jsonify({
                "status": "success",
                "message": "QBO connection successful",
                "token_valid": True,
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
