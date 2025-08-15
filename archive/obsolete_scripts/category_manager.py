#!/usr/bin/env python3
"""
Category Mapping Manager
Manages category and subcategory mappings between Quoter and Pipedrive
"""

import requests
import os
from dotenv import load_dotenv
from utils.logger import logger
from quoter import get_quoter_products

load_dotenv()
API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

def get_pipedrive_categories():
    """Get all existing categories from Pipedrive."""
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        url = f"{BASE_URL}/products"
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            products = data.get('data', [])
            
            # Extract unique categories from existing products
            categories = set()
            for product in products:
                if product.get('category'):
                    categories.add(product['category'])
            
            logger.info(f"Found {len(categories)} existing categories in Pipedrive")
            return list(categories)
        else:
            logger.error(f"Failed to fetch Pipedrive categories: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching Pipedrive categories: {e}")
        return []

def analyze_missing_categories():
    """Analyze which categories are missing from Pipedrive."""
    logger.info("=== Analyzing Missing Categories ===")
    
    # Get all Quoter products
    quoter_products = get_quoter_products()
    
    if not quoter_products:
        logger.error("No Quoter products found")
        return
    
    # Extract all categories from Quoter
    quoter_categories = set()
    quoter_subcategories = set()
    
    for product in quoter_products:
        category_id = product.get('category_id')
        if category_id and ' / ' in category_id:
            parts = category_id.split(' / ', 1)
            quoter_categories.add(parts[0])
            quoter_subcategories.add(parts[1])
        elif category_id:
            quoter_categories.add(category_id)
    
    # Get existing Pipedrive categories
    pipedrive_categories = get_pipedrive_categories()
    
    # Find missing categories
    missing_categories = quoter_categories - set(pipedrive_categories)
    
    logger.info(f"📊 Analysis Results:")
    logger.info(f"  📦 Quoter categories: {len(quoter_categories)}")
    logger.info(f"  📁 Pipedrive categories: {len(pipedrive_categories)}")
    logger.info(f"  ❌ Missing categories: {len(missing_categories)}")
    
    if missing_categories:
        logger.info(f"\n=== Missing Categories ===")
        for category in sorted(missing_categories):
            logger.info(f"  • {category}")
    
    return missing_categories, quoter_subcategories

def create_category_mapping_script():
    """Create a script to add missing categories to Pipedrive."""
    logger.info("=== Creating Category Mapping Script ===")
    
    missing_categories, subcategories = analyze_missing_categories()
    
    if not missing_categories:
        logger.info("✅ All categories are already mapped!")
        return
    
    # Create the mapping script
    script_content = """#!/usr/bin/env python3
\"\"\"
Category Mapping Script - Add missing categories to Pipedrive
Run this script to add the missing categories found in the analysis.
\"\"\"

import requests
import os
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()
API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

def add_category_to_pipedrive(category_name):
    \"\"\"Add a category to Pipedrive (manual process).\"\"\"
    logger.info(f"📝 To add category '{category_name}' to Pipedrive:")
    logger.info(f"  1. Go to Pipedrive → Settings → Product Fields")
    logger.info(f"  2. Add new category: {category_name}")
    logger.info(f"  3. Note the category ID")
    logger.info(f"  4. Update the mapping in dynamic_category_manager.py")

def main():
    \"\"\"Main function to guide category addition.\"\"\"
    logger.info("=== Category Addition Guide ===")
    
    missing_categories = [
"""
    
    for category in sorted(missing_categories):
        script_content += f'        "{category}",\n'
    
    script_content += """    ]
    
    logger.info(f"Found {len(missing_categories)} missing categories")
    
    for category in missing_categories:
        add_category_to_pipedrive(category)
        logger.info("")  # Empty line for readability
    
    logger.info("=== Next Steps ===")
    logger.info("1. Add the categories to Pipedrive manually")
    logger.info("2. Update the mappings in dynamic_category_manager.py")
    logger.info("3. Run the sync again")

if __name__ == "__main__":
    main()
"""
    
    # Write the script to a file
    with open("add_missing_categories.py", "w") as f:
        f.write(script_content)
    
    logger.info("✅ Created add_missing_categories.py")
    logger.info("📝 Run this script to add missing categories")

def update_dynamic_category_manager():
    """Update the dynamic category manager with new mappings."""
    logger.info("=== Updating Dynamic Category Manager ===")
    
    missing_categories, subcategories = analyze_missing_categories()
    
    if not missing_categories:
        logger.info("✅ No missing categories to add")
        return
    
    # Generate updated mappings
    logger.info(f"\n=== Suggested Category Mappings ===")
    logger.info("Add these to dynamic_category_manager.py:")
    logger.info("")
    logger.info("manual_mappings = {")
    
    # Start with existing mappings
    existing_mappings = {
        "Tanks": 30,
        "Balloons": 31,
        "Hologram": 28,
        "Service": 29,
    }
    
    for name, id_val in existing_mappings.items():
        logger.info(f'    "{name}": {id_val},')
    
    # Add new mappings (you'll need to get the actual IDs from Pipedrive)
    for i, category in enumerate(sorted(missing_categories)):
        logger.info(f'    "{category}": NEXT_AVAILABLE_ID,  # TODO: Get ID from Pipedrive')
    
    logger.info("}")
    
    logger.info(f"\n=== Suggested Subcategory Mappings ===")
    logger.info("Add these to dynamic_category_manager.py:")
    logger.info("")
    logger.info("manual_subcategory_mappings = {")
    
    existing_subcategories = {
        "1-to-3 Splitter": 40,
        "Drop": 41,
        "FV": 42,
    }
    
    for name, id_val in existing_subcategories.items():
        logger.info(f'    "{name}": {id_val},')
    
    # Add new subcategory mappings
    for subcategory in sorted(subcategories):
        if subcategory not in existing_subcategories:
            logger.info(f'    "{subcategory}": NEXT_AVAILABLE_ID,  # TODO: Get ID from Pipedrive')
    
    logger.info("}")

def main():
    """Main function to manage categories."""
    logger.info("=== Category Mapping Manager ===")
    
    # Analyze missing categories
    missing_categories, subcategories = analyze_missing_categories()
    
    if missing_categories:
        # Create mapping script
        create_category_mapping_script()
        
        # Update dynamic category manager
        update_dynamic_category_manager()
        
        logger.info(f"\n=== Summary ===")
        logger.info(f"📊 Missing categories: {len(missing_categories)}")
        logger.info(f"📊 Missing subcategories: {len(subcategories)}")
        logger.info(f"📝 Run add_missing_categories.py to add them")
    else:
        logger.info("✅ All categories are properly mapped!")

if __name__ == "__main__":
    main() 