#!/usr/bin/env python3
"""
Detailed Sync Notification System

Tracks and reports:
1. New items added to Quoter
2. New products added to Pipedrive  
3. New items added to QuickBooks
"""

import os
import json
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

class DetailedSyncNotifier:
    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        self.notification_emails = os.getenv("NOTIFICATION_EMAILS", "").split(",")
        
        # Track changes during sync
        self.quoter_new_items = []
        self.pipedrive_new_products = []
        self.qbo_new_items = []
        self.sync_errors = []
        
    def add_quoter_item(self, item_data):
        """Track new item added to Quoter"""
        # Get creation time from the item data
        created_at = item_data.get("created_at", "")
        if created_at:
            try:
                from datetime import datetime
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                added_at = created_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                added_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            added_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get the complete category path using the existing category_manager function
        from category_manager import get_category_path_from_item
        full_category_path = get_category_path_from_item(item_data)
        
        if full_category_path and " / " in full_category_path:
            # Split the path into category and subcategory
            category_parts = full_category_path.split(" / ", 1)
            main_category = category_parts[0]
            subcategory = category_parts[1]
            
            # Clean and format using the same logic as pipedrive.py build_catsub function
            parent = main_category.replace(":", "-").strip() if main_category else "Unknown"
            child = subcategory.replace(":", "-").strip() if subcategory else ""
            
            if child:
                category_display = f"{parent}:{child}"
            else:
                category_display = parent
        elif full_category_path:
            # Single category (no subcategory)
            parent = full_category_path.replace(":", "-").strip() if full_category_path else "Unknown"
            category_display = parent
        else:
            # Fallback to item's category field
            category = item_data.get("category", "Unknown")
            category_display = category.replace(":", "-").strip() if category else "Unknown"
        
        # Get price from price_decimal field (Quoter API schema)
        price = item_data.get("price_decimal", 0)
        if price is not None:
            try:
                price = float(price)
            except (ValueError, TypeError):
                price = 0
        else:
            price = 0
        
        # Get item type (new or updated)
        item_type = item_data.get("item_type", "new")
        
        self.quoter_new_items.append({
            "name": item_data.get("name", "Unknown"),
            "code": item_data.get("code", "N/A"),
            "price": price,
            "category": category_display,
            "subcategory": item_data.get("subcategory", "N/A"),
            "supplier_sku": item_data.get("supplier_sku", "Pending"),
            "added_at": added_at,
            "item_type": item_type
        })
    
    def add_pipedrive_product(self, product_data):
        """Track new product added to Pipedrive"""
        # Get price from prices array (Pipedrive API schema)
        price = 0
        prices = product_data.get("prices", [])
        if prices and len(prices) > 0:
            price = prices[0].get("price", 0)
        
        # Get category name from category ID using category_manager
        category_id = product_data.get("category")
        category_name = "Unknown"
        if category_id:
            from category_manager import get_pipedrive_categories
            categories = get_pipedrive_categories()
            # Find category name by ID
            for name, cat_id in categories.items():
                if str(cat_id) == str(category_id):
                    category_name = name
                    break
        
        # Get subcategory from custom field
        subcategory = product_data.get("ae55145d60840de457ff9e785eba68f0b39ab777", "N/A")
        
        # Get QBO Category:Subcategory from CatSub field
        qbo_category_subcategory = product_data.get("9c636133839b978b686bbc952fbd5dc41d5cd087", "N/A")
        
        # Get QuickBooks ID from custom field
        quickbooks_id = product_data.get("1213a9ae4c45178ff7c81bde38c3cdfbdc71bbd4", "Pending")
        if quickbooks_id is None:
            quickbooks_id = "Pending"
        
        # Get creation time from add_time
        add_time = product_data.get("add_time", "")
        if add_time:
            try:
                from datetime import datetime
                added_dt = datetime.strptime(add_time, '%Y-%m-%d %H:%M:%S')
                added_at = added_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                added_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            added_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get item type (new or updated)
        item_type = product_data.get("item_type", "new")
        
        self.pipedrive_new_products.append({
            "id": product_data.get("id", "N/A"),
            "name": product_data.get("name", "Unknown"),
            "code": product_data.get("code", "N/A"),
            "price": price,
            "category": category_name,
            "subcategory": subcategory,
            "qbo_category_subcategory": qbo_category_subcategory,
            "quickbooks_id": quickbooks_id,
            "added_at": added_at,
            "item_type": item_type
        })
    
    def add_qbo_item(self, item_data):
        """Track new item added to QuickBooks"""
        # Extract data from QBO item format
        name = item_data.get("Name", "Unknown")
        
        # Get item type from Type field
        item_type = item_data.get("Type", "Unknown")
        
        # Get SKU from Sku field
        sku = item_data.get("Sku", "N/A")
        
        # Get category from IncomeAccountRef
        category = "Unknown"
        income_account = item_data.get("IncomeAccountRef", {})
        if income_account:
            category = income_account.get("name", "Unknown")
        
        # Get price from UnitPrice
        price = item_data.get("UnitPrice", 0)
        if price is None:
            price = 0
        
        # Get creation time from MetaData
        created_time = item_data.get("MetaData", {}).get("CreateTime", "")
        if created_time:
            try:
                created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                added_at = created_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                added_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            added_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get sync type (new or updated)
        sync_type = item_data.get("item_type", "new")
        
        self.qbo_new_items.append({
            "name": name,
            "item_type": item_type,
            "sku": sku,
            "category": category,
            "price": price,
            "added_at": added_at,
            "sync_type": sync_type
        })
    
    def add_error(self, error_msg, system):
        """Track sync errors"""
        self.sync_errors.append({
            "error": error_msg,
            "system": system,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    def generate_email_content(self):
        """Generate detailed HTML email content"""
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .section h2 {{ color: #333; border-bottom: 2px solid #007cba; padding-bottom: 5px; }}
                .item {{ background-color: #f9f9f9; margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }}
                .error {{ background-color: #ffe6e6; border-left-color: #ff4444; }}
                .summary {{ background-color: #e6f3ff; padding: 15px; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Daily Product / Item Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</h1>
            </div>
            
            <div class="summary">
                <h2>📊 Summary</h2>
                <p><strong>New Quoter Items:</strong> {len(self.quoter_new_items)}</p>
                <p><strong>New Pipedrive Products:</strong> {len(self.pipedrive_new_products)}</p>
                <p><strong>New QuickBooks Items:</strong> {len(self.qbo_new_items)}</p>
                <p><strong>Errors:</strong> {len(self.sync_errors)}</p>
            </div>
        """
        
        # Quoter new items section
        if self.quoter_new_items:
            html_content += f"""
            <div class="section">
                <h2>🆕 New Items Added to Quoter ({len(self.quoter_new_items)})</h2>
                <table>
                    <tr>
                        <th>Product Name</th>
                        <th>Code</th>
                        <th>Price</th>
                        <th>Category/Subcategory</th>
                        <th>Supplier SKU</th>
                        <th>Type</th>
                        <th>Added At</th>
                    </tr>
            """
            for item in self.quoter_new_items:
                # Color code the type
                type_color = "#28a745" if item.get('item_type') == 'new' else "#ffc107"
                type_text = "🆕 New" if item.get('item_type') == 'new' else "🔄 Updated"
                
                html_content += f"""
                    <tr>
                        <td>{item['name']}</td>
                        <td>{item['code']}</td>
                        <td>${item['price']:.2f}</td>
                        <td>{item['category']}</td>
                        <td>{item['supplier_sku']}</td>
                        <td style="color: {type_color}; font-weight: bold;">{type_text}</td>
                        <td>{item['added_at']}</td>
                    </tr>
                """
            html_content += "</table></div>"
        
        # Pipedrive new products section
        if self.pipedrive_new_products:
            html_content += f"""
            <div class="section">
                <h2>🆕 New Products Added to Pipedrive ({len(self.pipedrive_new_products)})</h2>
                <table>
                    <tr>
                        <th>Product ID</th>
                        <th>Name</th>
                        <th>Code</th>
                        <th>Price</th>
                        <th>Category</th>
                        <th>Subcategory</th>
                        <th>QBO Category:Subcategory</th>
                        <th>QuickBooks ID</th>
                        <th>Type</th>
                        <th>Added At</th>
                    </tr>
            """
            for product in self.pipedrive_new_products:
                # Color code the type
                type_color = "#28a745" if product.get('item_type') == 'new' else "#ffc107"
                type_text = "🆕 New" if product.get('item_type') == 'new' else "🔄 Updated"
                
                html_content += f"""
                    <tr>
                        <td>{product['id']}</td>
                        <td>{product['name']}</td>
                        <td>{product['code']}</td>
                        <td>${product['price']:.2f}</td>
                        <td>{product['category']}</td>
                        <td>{product['subcategory']}</td>
                        <td>{product['qbo_category_subcategory']}</td>
                        <td>{product['quickbooks_id']}</td>
                        <td style="color: {type_color}; font-weight: bold;">{type_text}</td>
                        <td>{product['added_at']}</td>
                    </tr>
                """
            html_content += "</table></div>"
        
        # QuickBooks new items section
        if self.qbo_new_items:
            html_content += f"""
            <div class="section">
                <h2>🆕 New Items Added to QuickBooks ({len(self.qbo_new_items)})</h2>
                <table>
                    <tr>
                        <th>Name</th>
                        <th>Item Type</th>
                        <th>SKU</th>
                        <th>Category</th>
                        <th>Price</th>
                        <th>Sync Type</th>
                        <th>Added At</th>
                    </tr>
            """
            for item in self.qbo_new_items:
                # Color code the sync type
                sync_color = "#28a745" if item.get('sync_type') == 'new' else "#ffc107"
                sync_text = "🆕 New" if item.get('sync_type') == 'new' else "🔄 Updated"
                
                html_content += f"""
                    <tr>
                        <td>{item['name']}</td>
                        <td>{item['item_type']}</td>
                        <td>{item['sku']}</td>
                        <td>{item['category']}</td>
                        <td>${item['price']:.2f}</td>
                        <td style="color: {sync_color}; font-weight: bold;">{sync_text}</td>
                        <td>{item['added_at']}</td>
                    </tr>
                """
            html_content += "</table></div>"
        
        # Errors section
        if self.sync_errors:
            html_content += f"""
            <div class="section">
                <h2>❌ Sync Errors ({len(self.sync_errors)})</h2>
            """
            for error in self.sync_errors:
                html_content += f"""
                <div class="item error">
                    <strong>{error['system']}:</strong> {error['error']}<br>
                    <small>Time: {error['timestamp']}</small>
                </div>
                """
            html_content += "</div>"
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content
    
    def send_email(self):
        """Send detailed email notification"""
        if not self.gmail_user or not self.gmail_password or not self.notification_emails:
            print("❌ Email configuration missing")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Daily Product / Item Report - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.gmail_user
            msg['To'] = ", ".join(self.notification_emails)
            
            html_content = self.generate_email_content()
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.gmail_user, self.gmail_password)
            server.send_message(msg)
            server.quit()
            
            print("✅ Detailed email notification sent")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def send_slack_notification(self):
        """Send Slack notification with summary"""
        if not self.slack_webhook:
            print("❌ Slack webhook not configured")
            return False
        
        try:
            summary = f"""
            📊 *Daily Product / Item Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
            
            📊 *Summary:*
            • New Quoter Items: {len(self.quoter_new_items)}
            • New Pipedrive Products: {len(self.pipedrive_new_products)}
            • New QuickBooks Items: {len(self.qbo_new_items)}
            • Errors: {len(self.sync_errors)}
            
            📧 *Detailed report sent via email*
            """
            
            payload = {"text": summary}
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            
            if response.status_code == 200:
                print("✅ Slack notification sent")
                return True
            else:
                print(f"❌ Slack notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to send Slack notification: {e}")
            return False
    
    def send_notifications(self):
        """Send email notification only if there are Quoter items (no Slack for product sync)"""
        # Don't send report if no Quoter items were added
        if len(self.quoter_new_items) == 0:
            print("📊 No Quoter items added today - skipping report")
            return True
        
        print("📧 Sending detailed sync notification...")
        
        email_sent = self.send_email()
        
        if email_sent:
            print("✅ Email notification sent successfully")
        else:
            print("❌ Failed to send email notification")
        
        return email_sent

# Global notifier instance
notifier = DetailedSyncNotifier()

def get_pipedrive_products_simple():
    """Simple function to get Pipedrive products"""
    try:
        pipedrive_token = os.getenv("PIPEDRIVE_API_TOKEN")
        if not pipedrive_token:
            return []
        
        url = "https://api.pipedrive.com/v1/products"
        params = {"api_token": pipedrive_token, "limit": 100}
        
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"❌ Failed to fetch Pipedrive products: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching Pipedrive products: {e}")
        return []

def get_qbo_items_simple():
    """Get QuickBooks items using the same method as quoter_to_qbo_sync.py"""
    try:
        from quoter_to_qbo_sync import QBOClient
        
        # Initialize QBO client
        qbo_client = QBOClient()
        
        # Get items from QuickBooks
        items = qbo_client.get_existing_items()
        
        if items:
            print(f"📊 Retrieved {len(items)} items from QuickBooks")
            return items
        else:
            print("📊 No items found in QuickBooks")
            return []
            
    except Exception as e:
        print(f"❌ Error fetching QBO items: {e}")
        return []

def get_last_sync_date():
    """Get the last sync date from last_sync_date.txt (date only, no time)"""
    try:
        with open("last_sync_date.txt", "r") as f:
            last_sync_str = f.read().strip()
            # Parse the ISO format timestamp and extract just the date
            from datetime import datetime, timezone
            full_datetime = datetime.fromisoformat(last_sync_str.replace('Z', '+00:00'))
            # Return just the date part (midnight of that day)
            return full_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    except Exception as e:
        print(f"⚠️ Could not read last_sync_date.txt: {e}")
        # Fallback to yesterday
        from datetime import datetime, timedelta, timezone
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

def get_new_quoter_items_since(last_sync_date):
    """Get Quoter items created/updated since last sync with smart filtering"""
    try:
        from quoter import get_quoter_products
        all_products = get_quoter_products()
        
        # First pass: Get all items created today
        created_today = []
        for product in all_products:
            created_at = product.get("created_at")
            if created_at:
                from datetime import datetime
                product_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                product_date = product_created.replace(hour=0, minute=0, second=0, microsecond=0)
                if product_date == last_sync_date:
                    # Add supplier_sku (Pipedrive product ID) to the product data
                    product["supplier_sku"] = product.get("sku", "Pending")
                    product["item_type"] = "new"  # Mark as new item
                    created_today.append(product)
        
        # Second pass: Get all items modified today
        modified_today = []
        for product in all_products:
            modified_at = product.get("modified_at")
            if modified_at:
                from datetime import datetime
                product_modified = datetime.fromisoformat(modified_at.replace('Z', '+00:00'))
                product_date = product_modified.replace(hour=0, minute=0, second=0, microsecond=0)
                if product_date == last_sync_date:
                    # Add supplier_sku (Pipedrive product ID) to the product data
                    product["supplier_sku"] = product.get("sku", "Pending")
                    modified_today.append(product)
        
        # Smart filtering: Compare counts
        created_count = len(created_today)
        modified_count = len(modified_today)
        
        print(f"🔍 Quoter filtering: {created_count} created, {modified_count} modified today")
        
        if modified_count == created_count:
            # All modified items are just the new ones
            print("✅ All modified items are new items - no additional updates")
            return created_today
        else:
            # Find additional items that were modified but not created today
            created_ids = {item["id"] for item in created_today}
            additional_updates = []
            
            for item in modified_today:
                if item["id"] not in created_ids:
                    item["item_type"] = "updated"  # Mark as updated item
                    additional_updates.append(item)
            
            print(f"✅ Found {len(additional_updates)} additional updated items")
            
            # Return both new and updated items
            all_items = created_today + additional_updates
            return all_items
        
    except Exception as e:
        print(f"❌ Error fetching new Quoter items: {e}")
        return []

def get_pipedrive_products_by_quoter_items(quoter_items):
    """Get Pipedrive products that correspond to Quoter items using supplier_sku"""
    try:
        pipedrive_token = os.getenv("PIPEDRIVE_API_TOKEN")
        if not pipedrive_token:
            return []
        
        # Get all Pipedrive products
        url = "https://api.pipedrive.com/v1/products"
        params = {
            "api_token": pipedrive_token, 
            "limit": 100,
            "start": 0
        }
        
        all_products = []
        while True:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                break
                
            data = response.json()
            products = data.get("data", [])
            if not products:
                break
                
            all_products.extend(products)
            
            # Check pagination
            pagination = data.get("additional_data", {}).get("pagination", {})
            if not pagination.get("more_items_in_collection", False):
                break
            params["start"] = pagination.get("next_start", params["start"] + 100)
        
        # Find Pipedrive products that match Quoter items by supplier_sku
        matching_products = []
        quoter_supplier_skus = {item.get("supplier_sku") for item in quoter_items}
        
        for product in all_products:
            product_id = str(product.get("id", ""))
            if product_id in quoter_supplier_skus:
                # Mark the product type based on Quoter item type
                for quoter_item in quoter_items:
                    if str(quoter_item.get("supplier_sku")) == product_id:
                        product["item_type"] = quoter_item.get("item_type", "new")
                        break
                matching_products.append(product)
        
        print(f"🔍 Found {len(matching_products)} Pipedrive products matching Quoter items")
        return matching_products
        
    except Exception as e:
        print(f"❌ Error fetching Pipedrive products by Quoter items: {e}")
        return []

def get_qbo_items_by_quoter_items(quoter_items):
    """Get QBO items that correspond to Quoter items using supplier_sku"""
    try:
        from quoter_to_qbo_sync import QBOClient
        
        # Initialize QBO client
        qbo_client = QBOClient()
        
        # Get all items from QuickBooks
        all_items = qbo_client.get_existing_items()
        
        if not all_items:
            return []
        
        # Find QBO items that match Quoter items by Name field
        matching_items = []
        quoter_names = {item.get("name") for item in quoter_items}
        
        for item in all_items:
            item_name = item.get("Name", "")
            if item_name in quoter_names:
                # Mark the item type based on Quoter item type
                for quoter_item in quoter_items:
                    if quoter_item.get("name") == item_name:
                        item["item_type"] = quoter_item.get("item_type", "new")
                        break
                matching_items.append(item)
        
        print(f"🔍 Found {len(matching_items)} QBO items matching Quoter items")
        return matching_items
        
    except Exception as e:
        print(f"❌ Error fetching QBO items by Quoter items: {e}")
        return []

def gather_sync_data():
    """Gather data from all three systems to generate detailed report"""
    print("🔍 Gathering sync data from all systems...")
    
    try:
        # Get last sync date
        last_sync_date = get_last_sync_date()
        print(f"📅 Last sync date: {last_sync_date}")
        
        # Get Quoter items (source of truth) - both new and updated
        print("📊 Fetching Quoter items (source of truth)...")
        quoter_items = get_new_quoter_items_since(last_sync_date)
        
        # Get corresponding Pipedrive products using supplier_sku
        print("📊 Fetching corresponding Pipedrive products...")
        pipedrive_products = get_pipedrive_products_by_quoter_items(quoter_items)
        
        # Get corresponding QBO items using supplier_sku
        print("📊 Fetching corresponding QBO items...")
        qbo_items = get_qbo_items_by_quoter_items(quoter_items)
        
        # Add items to notification
        for item in quoter_items:
            notifier.add_quoter_item(item)
        
        for product in pipedrive_products:
            notifier.add_pipedrive_product(product)
        
        for item in qbo_items:
            notifier.add_qbo_item(item)
        
        print(f"✅ Found {len(quoter_items)} Quoter items, {len(pipedrive_products)} matching Pipedrive products, {len(qbo_items)} matching QBO items")
        
        # Debug: Show what was actually found
        if pipedrive_products:
            print("🔍 Pipedrive products matching Quoter items:")
            for product in pipedrive_products:
                print(f"  - {product.get('name', 'Unknown')} (ID: {product.get('id')}) - {product.get('item_type', 'unknown')}")
        else:
            print("🔍 No Pipedrive products found matching Quoter items")
        
    except Exception as e:
        print(f"❌ Error gathering sync data: {e}")
        notifier.add_error(str(e), "Data Gathering")

def main():
    """Main function to generate and send detailed sync report"""
    print("🚀 Starting detailed sync notification...")
    
    # Gather data from all systems
    gather_sync_data()
    
    # Send notifications
    success = notifier.send_notifications()
    
    if success:
        print("✅ Detailed sync notification completed successfully")
    else:
        print("❌ Failed to send detailed sync notification")
        exit(1)

if __name__ == "__main__":
    main()
