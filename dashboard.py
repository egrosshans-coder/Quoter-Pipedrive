#!/usr/bin/env python3
"""
Monitoring Dashboard for Quoter Sync
Provides real-time insights and sync status monitoring
"""

import os
import json
from datetime import datetime, timedelta
from quoter import get_quoter_products
from pipedrive import find_product_by_id
from utils.logger import logger
import requests
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

class SyncDashboard:
    def __init__(self):
        self.stats = {}
        self.last_sync_time = None
        self.load_sync_log()
    
    def load_sync_log(self):
        """Load sync log to get last sync time."""
        try:
            if os.path.exists("sync_log.txt"):
                with open("sync_log.txt", "r") as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1]
                        if "Sync completed successfully" in last_line:
                            # Extract timestamp from log line
                            timestamp_str = last_line.split(" - ")[0]
                            self.last_sync_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error loading sync log: {e}")
    
    def get_quoter_stats(self):
        """Get statistics from Quoter."""
        logger.info("📊 Getting Quoter statistics...")
        
        try:
            products = get_quoter_products()
            
            if not products:
                return {"error": "No products found"}
            
            # Calculate statistics
            total_products = len(products)
            products_with_sku = len([p for p in products if p.get('sku')])
            products_without_sku = total_products - products_with_sku
            
            # Category breakdown
            categories = {}
            for product in products:
                category = product.get('category', 'Unknown')
                categories[category] = categories.get(category, 0) + 1
            
            # Price statistics
            prices = [float(p.get('price_decimal', 0)) for p in products if p.get('price_decimal')]
            avg_price = sum(prices) / len(prices) if prices else 0
            max_price = max(prices) if prices else 0
            min_price = min(prices) if prices else 0
            
            return {
                "total_products": total_products,
                "products_with_sku": products_with_sku,
                "products_without_sku": products_without_sku,
                "categories": categories,
                "price_stats": {
                    "average": round(avg_price, 2),
                    "maximum": round(max_price, 2),
                    "minimum": round(min_price, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting Quoter stats: {e}")
            return {"error": str(e)}
    
    def get_pipedrive_stats(self):
        """Get statistics from Pipedrive."""
        logger.info("📊 Getting Pipedrive statistics...")
        
        try:
            headers = {"Content-Type": "application/json"}
            params = {"api_token": API_TOKEN}
            
            # Get all products with pagination
            all_products = []
            page = 1
            
            while True:
                response = requests.get(
                    f"{BASE_URL}/products", 
                    headers=headers, 
                    params={**params, "start": (page - 1) * 100, "limit": 100},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    products = data.get('data', [])
                    
                    if not products:
                        break
                        
                    all_products.extend(products)
                    
                    # Check if there are more pages
                    if len(products) < 100:
                        break
                        
                    page += 1
                else:
                    return {"error": f"API error: {response.status_code}"}
            
            total_products = len(all_products)
            
            # Category breakdown
            categories = {}
            for product in all_products:
                category = product.get('category', 'Unknown')
                categories[category] = categories.get(category, 0) + 1
            
            # Price statistics
            prices = [float(p.get('price', 0)) for p in all_products if p.get('price')]
            avg_price = sum(prices) / len(prices) if prices else 0
            max_price = max(prices) if prices else 0
            min_price = min(prices) if prices else 0
            
            return {
                "total_products": total_products,
                "categories": categories,
                "price_stats": {
                    "average": round(avg_price, 2),
                    "maximum": round(max_price, 2),
                    "minimum": round(min_price, 2)
                }
            }
                
        except Exception as e:
            logger.error(f"Error getting Pipedrive stats: {e}")
            return {"error": str(e)}
    
    def get_sync_status(self):
        """Get sync status and health."""
        logger.info("📊 Getting sync status...")
        
        quoter_stats = self.get_quoter_stats()
        pipedrive_stats = self.get_pipedrive_stats()
        
        # Calculate sync health
        sync_health = "🟢 Healthy"
        if "error" in quoter_stats or "error" in pipedrive_stats:
            sync_health = "🔴 Error"
        elif quoter_stats.get("total_products", 0) != pipedrive_stats.get("total_products", 0):
            sync_health = "🟡 Warning"
        
        # Calculate last sync info
        last_sync_info = "Never"
        if self.last_sync_time:
            time_diff = datetime.now() - self.last_sync_time
            if time_diff.days > 0:
                last_sync_info = f"{time_diff.days} days ago"
            elif time_diff.seconds > 3600:
                last_sync_info = f"{time_diff.seconds // 3600} hours ago"
            else:
                last_sync_info = f"{time_diff.seconds // 60} minutes ago"
        
        return {
            "sync_health": sync_health,
            "last_sync": last_sync_info,
            "quoter_stats": quoter_stats,
            "pipedrive_stats": pipedrive_stats
        }
    
    def display_dashboard(self):
        """Display the monitoring dashboard."""
        logger.info("=== Quoter Sync Dashboard ===")
        
        status = self.get_sync_status()
        
        # Display sync status
        logger.info(f"🔄 Sync Status: {status['sync_health']}")
        logger.info(f"🕐 Last Sync: {status['last_sync']}")
        logger.info("")
        
        # Display Quoter stats
        logger.info("📦 Quoter Statistics:")
        quoter_stats = status['quoter_stats']
        if "error" not in quoter_stats:
            logger.info(f"  📊 Total Products: {quoter_stats['total_products']}")
            logger.info(f"  🏷️  With SKU: {quoter_stats['products_with_sku']}")
            logger.info(f"  🆕 Without SKU: {quoter_stats['products_without_sku']}")
            logger.info(f"  💰 Average Price: ${quoter_stats['price_stats']['average']}")
            logger.info(f"  📁 Categories: {len(quoter_stats['categories'])}")
        else:
            logger.error(f"  ❌ Error: {quoter_stats['error']}")
        
        logger.info("")
        
        # Display Pipedrive stats
        logger.info("🔄 Pipedrive Statistics:")
        pipedrive_stats = status['pipedrive_stats']
        if "error" not in pipedrive_stats:
            logger.info(f"  📊 Total Products: {pipedrive_stats['total_products']}")
            logger.info(f"  💰 Average Price: ${pipedrive_stats['price_stats']['average']}")
            logger.info(f"  📁 Categories: {len(pipedrive_stats['categories'])}")
        else:
            logger.error(f"  ❌ Error: {pipedrive_stats['error']}")
        
        logger.info("")
        
        # Display sync comparison
        if "error" not in quoter_stats and "error" not in pipedrive_stats:
            quoter_count = quoter_stats['total_products']
            pipedrive_count = pipedrive_stats['total_products']
            
            logger.info("📊 Sync Comparison:")
            logger.info(f"  📦 Quoter Products: {quoter_count}")
            logger.info(f"  🔄 Pipedrive Products: {pipedrive_count}")
            
            if quoter_count == pipedrive_count:
                logger.info("  ✅ Perfect sync!")
            elif quoter_count > pipedrive_count:
                logger.info(f"  ⚠️  {quoter_count - pipedrive_count} products need syncing")
            else:
                logger.info(f"  ⚠️  {pipedrive_count - quoter_count} extra products in Pipedrive")
        
        logger.info("")
        logger.info("=== Dashboard Complete ===")
    
    def export_dashboard_data(self):
        """Export dashboard data to JSON file."""
        logger.info("📊 Exporting dashboard data...")
        
        status = self.get_sync_status()
        
        # Add timestamp
        status['timestamp'] = datetime.now().isoformat()
        
        # Save to file
        with open("dashboard_data.json", "w") as f:
            json.dump(status, f, indent=2)
        
        logger.info("✅ Dashboard data exported to dashboard_data.json")

def main():
    """Main function to run the dashboard."""
    logger.info("=== Quoter Sync Dashboard ===")
    
    dashboard = SyncDashboard()
    
    # Display the dashboard
    dashboard.display_dashboard()
    
    # Export data
    dashboard.export_dashboard_data()
    
    logger.info("🎯 Dashboard complete!")

if __name__ == "__main__":
    main() 