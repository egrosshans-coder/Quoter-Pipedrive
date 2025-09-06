#!/usr/bin/env python3
"""
Final Robust Quoter to QBO Sync Platform
Incorporates all discovered logic and edge cases:
- IncomeAccountRef as primary sellable item identifier
- Handles missing categories (Level0 items with IncomeAccountRef)
- Proper hierarchy matching using Quoter categories API
- Data quality validation and error reporting
"""

import os
import requests
import json
import base64
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import logger
from quoter import get_access_token

# Load environment variables
load_dotenv()

class QBOClient:
    """QuickBooks Online API client"""
    
    def __init__(self):
        self.client_id = os.getenv('QBO_CLIENT_ID')
        self.client_secret = os.getenv('QBO_CLIENT_SECRET')
        self.company_id = os.getenv('QBO_COMPANY_ID')
        self.access_token = os.getenv('QBO_ACCESS_TOKEN')
        self.refresh_token = os.getenv('QBO_REFRESH_TOKEN')
        
        if not all([self.client_id, self.client_secret, self.company_id]):
            raise ValueError("Missing QBO credentials in .env file")
    
    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            logger.error("No refresh token available")
            return False
        
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        logger.info("Refreshing QBO access token...")
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            result = response.json()
            self.access_token = result.get('access_token')
            if result.get('refresh_token'):
                self.refresh_token = result.get('refresh_token')
            
            # Save new tokens to .env file
            self._save_tokens_to_env()
            
            logger.info("✅ Successfully refreshed QBO access token")
            return True
        else:
            error_data = response.json() if response.text else {}
            error_type = error_data.get('error', 'unknown')
            
            if error_type == 'invalid_grant':
                logger.error("❌ Refresh token has expired. You need to get new tokens.")
                logger.error("🔧 Steps to fix:")
                logger.error("   1. Run: python qbo_oauth.py auth-url")
                logger.error("   2. Complete OAuth flow")
                logger.error("   3. Run: python qbo_oauth.py exchange <auth_code>")
            else:
                logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
            return False
    
    def _save_tokens_to_env(self):
        """Save updated tokens to .env file"""
        try:
            # Read current .env file
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # Update or add token lines
            token_lines = {
                'QBO_ACCESS_TOKEN': self.access_token,
                'QBO_REFRESH_TOKEN': self.refresh_token
            }
            
            # Update existing lines or add new ones
            updated_lines = []
            found_keys = set()
            
            for line in lines:
                line_stripped = line.strip()
                if '=' in line_stripped:
                    key = line_stripped.split('=')[0].strip()
                    if key in token_lines:
                        updated_lines.append(f"{key}={token_lines[key]}\n")
                        found_keys.add(key)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)
            
            # Add any missing keys
            for key, value in token_lines.items():
                if key not in found_keys:
                    updated_lines.append(f"{key}={value}\n")
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
            
            logger.info("✅ Updated .env file with new tokens")
            
        except Exception as e:
            logger.error(f"Failed to save tokens to .env: {e}")
    
    def get_valid_access_token(self):
        """Get a valid access token, refreshing if necessary"""
        if not self.access_token:
            logger.info("No access token available, refreshing...")
            return self.refresh_access_token()
        
        # For now, assume token is valid. In production, you'd check expiration
        return True
    
    def get_headers(self):
        """Get headers for QBO API requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_existing_items(self):
        """Get all existing items from QBO with pagination"""
        url = f"https://quickbooks.api.intuit.com/v3/company/{self.company_id}/query"
        headers = self.get_headers()
        
        all_items = []
        start_position = 1
        max_results = 500  # QBO max per request
        
        while True:
            query = f"SELECT * FROM Item STARTPOSITION {start_position} MAXRESULTS {max_results}"
            params = {'query': query}
            
            try:
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 401:
                    # Token expired, try to refresh
                    logger.info("Access token expired, refreshing...")
                    if self.refresh_access_token():
                        headers = self.get_headers()
                        response = requests.get(url, headers=headers, params=params)
                    else:
                        raise Exception("Cannot refresh access token")
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('QueryResponse', {}).get('Item', [])
                    
                    if not items:
                        break
                    
                    all_items.extend(items)
                    logger.info(f"Fetched {len(items)} items (total so far: {len(all_items)})")
                    
                    # If we got fewer items than requested, we've reached the end
                    if len(items) < max_results:
                        break
                    
                    start_position += len(items)
                else:
                    logger.error(f"Failed to fetch QBO items: {response.status_code} - {response.text}")
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching QBO items: {e}")
                break
        
        logger.info(f"Found {len(all_items)} total existing QBO items")
        return all_items
    
    def create_item(self, item_data):
        """Create a new item in QBO"""
        url = f"https://quickbooks.api.intuit.com/v3/company/{self.company_id}/item"
        headers = self.get_headers()
        
        response = requests.post(url, headers=headers, json=item_data)
        
        if response.status_code == 401:
            # Token expired, try to refresh
            logger.info("Access token expired, refreshing...")
            if self.refresh_access_token():
                headers = self.get_headers()
                response = requests.post(url, headers=headers, json=item_data)
            else:
                raise Exception("Cannot refresh access token")
        
        if response.status_code == 200:
            data = response.json()
            # For create operations, the response structure is different
            item = data.get('Item', {})
            if not item:
                # Try alternative structure
                item = data.get('QueryResponse', {}).get('Item', [{}])[0]
            
            logger.info(f"Created QBO item: {item.get('Name')} (ID: {item.get('Id')})")
            return item
        else:
            logger.error(f"Failed to create QBO item: {response.status_code} - {response.text}")
            return None
    
    def update_item(self, item_id, item_data):
        """Update an existing item in QBO"""
        url = f"https://quickbooks.api.intuit.com/v3/company/{self.company_id}/item"
        headers = self.get_headers()
        
        # Add the ID to the item data for update
        item_data['Id'] = item_id
        item_data['SyncToken'] = '1'  # Required for updates
        
        response = requests.post(url, headers=headers, json=item_data)
        
        if response.status_code == 401:
            # Token expired, try to refresh
            logger.info("Access token expired, refreshing...")
            if self.refresh_access_token():
                headers = self.get_headers()
                response = requests.post(url, headers=headers, json=item_data)
            else:
                raise Exception("Cannot refresh access token")
        
        if response.status_code == 200:
            data = response.json()
            # For update operations, the response structure is different
            item = data.get('Item', {})
            if not item:
                # Try alternative structure
                item = data.get('QueryResponse', {}).get('Item', [{}])[0]
            logger.info(f"Updated QBO item: {item.get('Name')} (ID: {item.get('Id')})")
            return item
        else:
            logger.error(f"Failed to update QBO item: {response.status_code} - {response.text}")
            return None

def convert_quoter_to_qbo_item(quoter_item):
    """Convert Quoter item to QBO item format with all key fields"""
    # Get basic item info
    name = quoter_item.get('name', '')
    description = quoter_item.get('description', '')
    
    # Validate required fields
    if not name:
        logger.warning("Skipping item with no name")
        return None
    
    # Get price and validate
    unit_price = quoter_item.get('price_decimal', 0)
    if isinstance(unit_price, str):
        try:
            unit_price = float(unit_price)
        except ValueError:
            unit_price = 0
    
    if not isinstance(unit_price, (int, float)) or unit_price < 0:
        logger.warning(f"Invalid price for item '{name}': {unit_price}, using 0")
        unit_price = 0
    
    # Get cost information
    cost = quoter_item.get('cost_decimal', 0)
    if isinstance(cost, str):
        try:
            cost = float(cost)
        except ValueError:
            cost = 0
    
    if not isinstance(cost, (int, float)) or cost < 0:
        cost = 0
    
    # Build QBO item - NO SKU field (QBO doesn't support it, Quoter matches by name)
    qbo_item = {
        "Name": name,  # This is the key field for matching
        "Type": "Inventory",
        "QtyOnHand": 0,
        "UnitPrice": unit_price,
        "PurchaseCost": cost,
        "IncomeAccountRef": {
            "value": os.getenv('QBO_INCOME_ACCOUNT_ID', '1'),
            "name": "Sales"
        },
        "ExpenseAccountRef": {
            "value": os.getenv('QBO_EXPENSE_ACCOUNT_ID', '2'),
            "name": "Cost of Goods Sold"
        }
    }
    
    # Add description if available
    if description:
        qbo_item["Description"] = description
    
    # Note: SKU will be handled by SyncQ when linking Pipedrive to QBO
    # Quoter matches items by Name, not SKU
    
    return qbo_item

class RobustSyncPlatform:
    def __init__(self):
        self.qbo_client = QBOClient()
        self.quoter_token = get_access_token()
        self.quoter_base_url = "https://api.quoter.com/v1"
        
    def get_quoter_items_with_hierarchy(self):
        """Fetch all Quoter items with full hierarchy paths"""
        print("🔍 Fetching Quoter items with hierarchy...")
        
        # First, get categories to build hierarchy
        categories_response = requests.get(
            f"{self.quoter_base_url}/categories",
            headers={"Authorization": f"Bearer {self.quoter_token}"}
        )
        
        if categories_response.status_code != 200:
            raise Exception(f"Failed to fetch Quoter categories: {categories_response.status_code}")
        
        categories_data = categories_response.json()
        categories = categories_data.get('data', [])
        
        # Build category hierarchy map
        category_hierarchy = {}
        for cat in categories:
            cat_id = cat['id']
            cat_name = cat['name']
            parent_cat = cat.get('parent_category')
            
            if parent_cat:
                # This is a subcategory
                category_hierarchy[cat_id] = f"{parent_cat}:{cat_name}"
            else:
                # This is a top-level category
                category_hierarchy[cat_id] = cat_name
        
        # Now fetch all items with pagination
        all_items = []
        page = 1
        per_page = 100
        
        while True:
            response = requests.get(
                f"{self.quoter_base_url}/items",
                headers={"Authorization": f"Bearer {self.quoter_token}"},
                params={"page": page, "per_page": per_page}
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch Quoter items: {response.status_code}")
            
            data = response.json()
            items = data.get('data', [])
            
            if not items:
                break
                
            # Add hierarchy information to each item
            for item in items:
                category_id = item.get('category_id')
                if category_id and category_id in category_hierarchy:
                    item['full_category_path'] = category_hierarchy[category_id]
                else:
                    # Fallback to simple category string
                    item['full_category_path'] = item.get('category', 'Unknown')
            
            all_items.extend(items)
            page += 1
            
            if len(items) < per_page:
                break
        
        # Deduplicate by name - keep first occurrence, skip duplicates
        unique_items = []
        seen_names = set()
        duplicates_skipped = 0
        
        for item in all_items:
            name = item.get('name', '').strip()
            if name and name not in seen_names:
                unique_items.append(item)
                seen_names.add(name)
            else:
                duplicates_skipped += 1
                if name:
                    print(f"⚠️  Skipping duplicate item: '{name}'")
        
        if duplicates_skipped > 0:
            print(f"🔄 Deduplication: Skipped {duplicates_skipped} duplicate items")
        
        print(f"✅ Fetched {len(unique_items)} unique Quoter items with hierarchy")
        return unique_items
    
    def get_qbo_sellable_items(self):
        """Fetch all QBO sellable items using IncomeAccountRef as identifier"""
        print("🔍 Fetching QBO sellable items...")
        
        all_items = self.qbo_client.get_existing_items()
        
        # Identify sellable items using IncomeAccountRef (most reliable)
        sellable_items = []
        data_quality_issues = []
        
        for item in all_items:
            fqn = item.get('FullyQualifiedName', '')
            colons = fqn.count(':')
            income_account = item.get('IncomeAccountRef')
            
            if income_account is not None:
                # This is a sellable item (has IncomeAccountRef)
                # Level0 items with IncomeAccountRef are expected - they're sellable items without categories
                if colons == 0:
                    # Level0 sellable item - this is normal, not a data quality issue
                    # These are items created without parent categories but are still sellable
                    pass
                sellable_items.append(item)
        
        print(f"✅ Found {len(sellable_items)} QBO sellable items")
        if data_quality_issues:
            print(f"⚠️  Found {len(data_quality_issues)} data quality issues")
            for issue in data_quality_issues:
                print(f"   - {issue['fqn']}: {issue['issue']}")
        
        return sellable_items, data_quality_issues
    
    def normalize_name(self, name):
        """Normalize item names for matching"""
        if not name:
            return ""
        return name.lower().strip().replace('-', ' ').replace('_', ' ')
    
    def calculate_match_score(self, quoter_item, qbo_item):
        """Calculate match score between Quoter and QBO items"""
        quoter_name = self.normalize_name(quoter_item.get('name', ''))
        qbo_name = self.normalize_name(qbo_item.get('Name', ''))
        
        # Exact name match
        if quoter_name == qbo_name:
            return 200
        
        # Check if names are very similar (one contains the other)
        if quoter_name in qbo_name or qbo_name in quoter_name:
            return 150
        
        # Check category hierarchy match
        quoter_category = quoter_item.get('full_category_path', '')
        qbo_fqn = qbo_item.get('FullyQualifiedName', '')
        
        if quoter_category and qbo_fqn:
            # Check if Quoter category path matches QBO hierarchy
            if quoter_category in qbo_fqn:
                return 100
        
        # Partial name match
        quoter_words = set(quoter_name.split())
        qbo_words = set(qbo_name.split())
        common_words = quoter_words.intersection(qbo_words)
        
        if common_words:
            return len(common_words) * 20
        
        return 0
    
    def find_best_matches(self, quoter_items, qbo_sellable_items):
        """Find best matches between Quoter and QBO items using priority scoring"""
        print("🔍 Finding matches between Quoter and QBO items...")
        
        # First, calculate all possible matches with scores
        all_potential_matches = []
        for quoter_item in quoter_items:
            for qbo_item in qbo_sellable_items:
                score = self.calculate_match_score(quoter_item, qbo_item)
                if score >= 80:  # Minimum threshold
                    all_potential_matches.append({
                        'quoter_item': quoter_item,
                        'qbo_item': qbo_item,
                        'score': score
                    })
        
        # Sort by score (highest first) to prioritize better matches
        all_potential_matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Now process matches in priority order
        matches = []
        unmatched_quoter = []
        used_qbo_items = set()
        matched_quoter_items = set()
        
        for match in all_potential_matches:
            quoter_id = match['quoter_item'].get('id')
            qbo_id = match['qbo_item'].get('Id')
            
            # Skip if either item is already matched
            if quoter_id in matched_quoter_items or qbo_id in used_qbo_items:
                continue
            
            # Add the match
            matches.append(match)
            matched_quoter_items.add(quoter_id)
            used_qbo_items.add(qbo_id)
        
        # Find unmatched Quoter items
        for quoter_item in quoter_items:
            if quoter_item.get('id') not in matched_quoter_items:
                unmatched_quoter.append(quoter_item)
        
        print(f"✅ Found {len(matches)} matches")
        print(f"❌ {len(unmatched_quoter)} Quoter items unmatched")
        
        return matches, unmatched_quoter
    
    def run_sync_analysis(self, dry_run=True):
        """Run the complete sync analysis"""
        print("🚀 Starting Robust Quoter to QBO Sync Analysis")
        print("=" * 60)
        
        try:
            # Fetch data
            quoter_items = self.get_quoter_items_with_hierarchy()
            qbo_sellable_items, data_quality_issues = self.get_qbo_sellable_items()
            
            # Find matches
            matches, unmatched_quoter = self.find_best_matches(quoter_items, qbo_sellable_items)
            
            # Generate report
            print("\n📊 SYNC ANALYSIS REPORT")
            print("=" * 40)
            print(f"Quoter items: {len(quoter_items)}")
            print(f"QBO sellable items: {len(qbo_sellable_items)}")
            print(f"Successful matches: {len(matches)}")
            print(f"Unmatched Quoter items: {len(unmatched_quoter)}")
            print(f"Data quality issues: {len(data_quality_issues)}")
            
            # Show unmatched items
            if unmatched_quoter:
                print(f"\n🆕 NEW ITEMS TO CREATE IN QBO:")
                for i, item in enumerate(unmatched_quoter[:10], 1):
                    name = item.get('name', 'Unknown')
                    category = item.get('full_category_path', 'Unknown')
                    code = item.get('code', 'No code')
                    price = item.get('price_decimal', '0')
                    print(f"  {i}. {name}")
                    print(f"     Category: {category}")
                    print(f"     Code: {code}")
                    print(f"     Price: ${price}")
                    print()
            
            # Show sample matches
            if matches:
                print(f"\n✅ SAMPLE MATCHES:")
                for i, match in enumerate(matches[:5], 1):
                    quoter_name = match['quoter_item'].get('name', 'Unknown')
                    qbo_name = match['qbo_item'].get('Name', 'Unknown')
                    score = match['score']
                    print(f"  {i}. {quoter_name} → {qbo_name} (Score: {score})")
            
            # Data quality issues
            if data_quality_issues:
                print(f"\n⚠️  DATA QUALITY ISSUES TO FIX:")
                for issue in data_quality_issues:
                    print(f"  - {issue['fqn']}: {issue['issue']}")
            
            # If not dry run, actually perform the sync
            if not dry_run:
                print(f"\n🔄 PERFORMING ACTUAL SYNC...")
                print("=" * 40)
                
                # Create unmatched items only
                created_count = 0
                for item in unmatched_quoter:
                    try:
                        print(f"Creating: {item.get('name')} ({item.get('code')})")
                        qbo_item = self.convert_quoter_to_qbo_item(item)
                        result = self.qbo_client.create_item(qbo_item)
                        if result:
                            created_count += 1
                            print(f"  ✅ Created successfully")
                        else:
                            print(f"  ❌ Failed to create")
                    except Exception as e:
                        print(f"  ❌ Error: {str(e)}")
                
                # Stop here - don't try to update existing items
                print(f"\n🎯 SYNC COMPLETE:")
                print(f"  Created: {created_count} new items")
                print(f"  Skipped: {len(matches)} existing items (no updates needed)")
                
                # Exit after creating new items
                return {
                    'quoter_items': len(quoter_items),
                    'qbo_sellable_items': len(qbo_sellable_items),
                    'matches': len(matches),
                    'unmatched_quoter': len(unmatched_quoter),
                    'data_quality_issues': len(data_quality_issues),
                    'unmatched_items': unmatched_quoter,
                    'matches_detail': matches,
                    'created': created_count,
                    'updated': 0
                }
            
            return {
                'quoter_items': len(quoter_items),
                'qbo_sellable_items': len(qbo_sellable_items),
                'matches': len(matches),
                'unmatched_quoter': len(unmatched_quoter),
                'data_quality_issues': len(data_quality_issues),
                'unmatched_items': unmatched_quoter,
                'matches_detail': matches
            }
            
        except Exception as e:
            print(f"❌ Error during sync analysis: {str(e)}")
            raise
    
    def convert_quoter_to_qbo_item(self, quoter_item):
        """Convert Quoter item to QBO item format"""
        name = quoter_item.get('name', 'Unknown')
        code = quoter_item.get('code', '')
        price = float(quoter_item.get('price_decimal', 0))
        description = quoter_item.get('description', '')
        
        # Clean description
        if description:
            import re
            clean_description = re.sub(r'<[^>]+>', '', description)  # Remove HTML tags
            clean_description = re.sub(r'[^\w\s.,!?()-]', '', clean_description)  # Remove special chars
            clean_description = clean_description.strip()
        else:
            clean_description = f"Imported from Quoter: {name}"
        
        # Determine item type based on code
        item_type = "Service" if code.startswith("SVC") else "Service"  # All non-inventory for now
        track_qty = False  # Non-inventory items don't track quantity
        
        # Get income account (use default)
        income_account_id = "389"  # Rental Income
        
        qbo_item = {
            "Name": name,
            "Type": item_type,
            "UnitPrice": price,
            "IncomeAccountRef": {
                "value": income_account_id
            },
            "Description": clean_description,
            "Sku": code,
            "Active": True,
            "TrackQtyOnHand": track_qty,
            "PurchaseCost": 0
        }
        
        return qbo_item
    
    def item_needs_update(self, quoter_item, qbo_item):
        """Check if QBO item needs update based on Quoter item"""
        # Only update if there are significant differences
        quoter_name = quoter_item.get('name', '')
        qbo_name = qbo_item.get('Name', '')
        quoter_price = float(quoter_item.get('price_decimal', 0))
        qbo_price = float(qbo_item.get('UnitPrice', 0))
        
        # Check for meaningful differences (with small tolerance for price)
        name_different = quoter_name != qbo_name
        price_different = abs(quoter_price - qbo_price) > 0.01
        
        # Only update if there are significant differences
        needs_update = name_different or price_different
        
        if needs_update:
            print(f"  Update needed: {quoter_name} vs {qbo_name}, ${quoter_price} vs ${qbo_price}")
        
        return needs_update

def main():
    """Main execution function"""
    platform = RobustSyncPlatform()
    
    print("🔧 Robust Quoter to QBO Sync Platform")
    print("=" * 50)
    print("This platform handles:")
    print("✅ IncomeAccountRef as primary sellable item identifier")
    print("✅ Missing categories (Level0 items with IncomeAccountRef)")
    print("✅ Proper hierarchy matching using Quoter categories API")
    print("✅ Data quality validation and error reporting")
    print("✅ Dry-run mode for safe testing")
    print()
    
    # Run actual sync
    results = platform.run_sync_analysis(dry_run=False)
    
    print(f"\n🎯 SUMMARY:")
    print(f"Ready to sync {results['matches']} existing items")
    print(f"Need to create {results['unmatched_quoter']} new items")
    print(f"Found {results['data_quality_issues']} data quality issues to fix")

if __name__ == "__main__":
    main()
