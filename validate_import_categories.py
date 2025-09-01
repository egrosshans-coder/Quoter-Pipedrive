#!/usr/bin/env python3
"""
Category Validation Script
Checks categories in an import file against existing Pipedrive categories
to identify new categories that need to be added to Pipedrive.
"""

import os
import sys
import json
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Pipedrive configuration
PIPEDRIVE_API_TOKEN = os.getenv('PIPEDRIVE_API_TOKEN')

def get_pipedrive_categories():
    """
    Fetch all existing categories from Pipedrive.
    Returns a dictionary of category names and their IDs.
    """
    print("🔍 Fetching existing Pipedrive categories...")
    
    headers = {
        "Authorization": f"Bearer {PIPEDRIVE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get product fields to find category field
        response = requests.get(f"{BASE_URL}/productFields", headers=headers, timeout=10)
        response.raise_for_status()
        
        fields_data = response.json()
        category_field = None
        
        # Find the category field
        for field in fields_data.get('data', []):
            if field.get('name') == 'Category':
                category_field = field
                break
        
        if not category_field:
            print("❌ Could not find Category field in Pipedrive")
            return {}
        
        # Get category options
        category_options = category_field.get('options', [])
        categories = {}
        
        for option in category_options:
            category_id = option.get('id')
            category_name = option.get('label')
            if category_id and category_name:
                categories[category_name] = category_id
        
        print(f"✅ Found {len(categories)} existing Pipedrive categories")
        return categories
        
    except Exception as e:
        print(f"❌ Error fetching Pipedrive categories: {e}")
        return {}

def analyze_import_file(file_path):
    """
    Analyze the import file to extract all unique categories.
    Supports CSV and JSON formats.
    """
    print(f"📁 Analyzing import file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return set()
    
    categories = set()
    file_extension = file_path.lower().split('.')[-1]
    
    try:
        if file_extension == 'csv':
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Look for category-related fields
                    for field_name, value in row.items():
                        if 'category' in field_name.lower() and value:
                            categories.add(value.strip())
                            
        elif file_extension == 'json':
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # Handle different JSON structures
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            for field_name, value in item.items():
                                if 'category' in field_name.lower() and value:
                                    categories.add(str(value).strip())
                elif isinstance(data, dict):
                    # Handle nested structures
                    def extract_categories(obj, path=""):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                current_path = f"{path}.{key}" if path else key
                                if 'category' in key.lower() and value:
                                    categories.add(str(value).strip())
                                elif isinstance(value, (dict, list)):
                                    extract_categories(value, current_path)
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                current_path = f"{path}[{i}]"
                                extract_categories(item, current_path)
                    
                    extract_categories(data)
        else:
            print(f"❌ Unsupported file format: {file_extension}")
            print("Supported formats: CSV, JSON")
            return set()
            
        print(f"✅ Found {len(categories)} unique categories in import file")
        return categories
        
    except Exception as e:
        print(f"❌ Error analyzing import file: {e}")
        return set()

def validate_categories(import_categories, pipedrive_categories):
    """
    Compare import categories with existing Pipedrive categories.
    Returns categories that exist and categories that need to be added.
    """
    print("\n🔍 Validating categories...")
    
    existing_categories = {}
    new_categories = {}
    
    for category_name in import_categories:
        if category_name in pipedrive_categories:
            existing_categories[category_name] = pipedrive_categories[category_name]
        else:
            new_categories[category_name] = None
    
    return existing_categories, new_categories

def generate_report(existing_categories, new_categories, pipedrive_categories):
    """
    Generate a comprehensive report of the category validation.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print("\n" + "="*80)
    print(f"📊 CATEGORY VALIDATION REPORT")
    print(f"📅 Generated: {timestamp}")
    print("="*80)
    
    # Summary
    total_import = len(existing_categories) + len(new_categories)
    total_existing = len(existing_categories)
    total_new = len(new_categories)
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total categories in import file: {total_import}")
    print(f"   Categories already in Pipedrive: {total_existing}")
    print(f"   New categories to add: {total_new}")
    print(f"   Coverage: {(total_existing/total_import)*100:.1f}%")
    
    # Existing categories
    if existing_categories:
        print(f"\n✅ EXISTING CATEGORIES ({len(existing_categories)}):")
        print("-" * 60)
        for name, category_id in existing_categories.items():
            print(f"   {name:<30} → Pipedrive ID: {category_id}")
    
    # New categories
    if new_categories:
        print(f"\n❌ NEW CATEGORIES TO ADD ({len(new_categories)}):")
        print("-" * 60)
        for name in new_categories.keys():
            print(f"   {name}")
    
    # All Pipedrive categories for reference
    print(f"\n📋 ALL PIPEDRIVE CATEGORIES ({len(pipedrive_categories)}):")
    print("-" * 60)
    for name, category_id in sorted(pipedrive_categories.items()):
        print(f"   {name:<30} → ID: {category_id}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if total_new == 0:
        print("   🎉 All categories are already in Pipedrive! You're ready to import.")
    else:
        print(f"   ⚠️  Add {total_new} new categories to Pipedrive before importing.")
        print("   📝 Consider if any categories can be consolidated or renamed.")
        print("   🔄 Run this validation again after adding new categories.")
    
    print("\n" + "="*80)
    
    # Save report to file
    report_filename = f"category_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(f"CATEGORY VALIDATION REPORT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write(f"{'='*80}\n\n")
        
        f.write(f"SUMMARY:\n")
        f.write(f"Total categories in import file: {total_import}\n")
        f.write(f"Categories already in Pipedrive: {total_existing}\n")
        f.write(f"New categories to add: {total_new}\n")
        f.write(f"Coverage: {(total_existing/total_import)*100:.1f}%\n\n")
        
        if existing_categories:
            f.write(f"EXISTING CATEGORIES:\n")
            for name, category_id in existing_categories.items():
                f.write(f"{name} → Pipedrive ID: {category_id}\n")
            f.write("\n")
        
        if new_categories:
            f.write(f"NEW CATEGORIES TO ADD:\n")
            for name in new_categories.keys():
                f.write(f"{name}")
            f.write("\n")
        
        f.write(f"ALL PIPEDRIVE CATEGORIES:\n")
        for name, category_id in sorted(pipedrive_categories.items()):
            f.write(f"{name} → ID: {category_id}\n")
    
    print(f"📄 Report saved to: {report_filename}")

def main():
    """
    Main function to run the category validation.
    """
    print("🚀 CATEGORY VALIDATION TOOL")
    print("=" * 50)
    
    # Check environment variables
        print("❌ Missing required environment variables:")
        print("   - PIPEDRIVE_API_TOKEN")
        print("\nPlease check your .env file.")
        return
    
    # Get file path from command line or prompt
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("📁 Enter the path to your import file: ").strip()
    
    if not file_path:
        print("❌ No file path provided.")
        return
    
    # Step 1: Get existing Pipedrive categories
    pipedrive_categories = get_pipedrive_categories()
    if not pipedrive_categories:
        print("❌ Could not fetch Pipedrive categories. Exiting.")
        return
    
    # Step 2: Analyze import file
    import_categories = analyze_import_file(file_path)
    if not import_categories:
        print("❌ No categories found in import file. Exiting.")
        return
    
    # Step 3: Validate categories
    existing_categories, new_categories = validate_categories(import_categories, pipedrive_categories)
    
    # Step 4: Generate report
    generate_report(existing_categories, new_categories, pipedrive_categories)
    
    print("\n✅ Category validation complete!")

if __name__ == "__main__":
    main()
