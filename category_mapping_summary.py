#!/usr/bin/env python3
"""
Category Mapping Summary - Quick overview of Quoter to Pipedrive category mappings
"""

import json
import os

def load_mapping_report():
    """Load the existing mapping report."""
    try:
        with open('category_mapping_report.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No mapping report found. Run enhanced_category_mapper.py first.")
        return None

def display_summary():
    """Display a summary of the current mapping status."""
    report = load_mapping_report()
    if not report:
        return
    
    print("🚀 QUOTER TO PIPEDRIVE CATEGORY MAPPING SUMMARY")
    print("=" * 70)
    
    # Overall statistics
    summary = report['summary']
    print(f"📊 MAPPING COVERAGE: {summary['mapping_coverage']}")
    print(f"📁 Total Quoter Categories: {summary['total_quoter_categories']}")
    print(f"✅ Mapped Categories: {summary['mapped_categories']}")
    print(f"❌ Unmapped Categories: {summary['total_quoter_categories'] - summary['mapped_categories']}")
    
    # Current mappings
    print(f"\n🔗 CURRENT MAPPINGS ({len(report['pipedrive_mappings']['mapped_categories'])}):")
    print("-" * 50)
    
    for category in report['pipedrive_mappings']['mapped_categories']:
        print(f"   ✅ {category}")
    
    # Priority unmapped categories (main categories first)
    unmapped_main = report['unmapped_categories']['unmapped_main']
    print(f"\n📁 PRIORITY UNMAPPED MAIN CATEGORIES ({len(unmapped_main)}):")
    print("-" * 50)
    
    # Sort by importance (put high-volume categories first)
    priority_order = [
        'Product', 'Laser', 'LED Tubes/Floor/Panels', 'Drones', 'Robotics',
        'Projection', 'Spheres', 'Wristbands/Lanyards/Orbs', 'Pyro', 'Fog',
        'Confetti/Streamers', 'CO2', 'Water', 'Apparel', 'AI', 'Snow'
    ]
    
    for priority_cat in priority_order:
        for cat in unmapped_main:
            if cat['name'] == priority_cat:
                print(f"   🔴 {cat['name']} (ID: {cat['id']})")
                break
    
    # Show remaining unmapped main categories
    remaining_main = [cat for cat in unmapped_main if cat['name'] not in priority_order]
    if remaining_main:
        print(f"\n📁 OTHER UNMAPPED MAIN CATEGORIES ({len(remaining_main)}):")
        print("-" * 50)
        for cat in remaining_main:
            print(f"   ⚪ {cat['name']} (ID: {cat['id']})")
    
    # Subcategory mapping status
    unmapped_sub = report['unmapped_categories']['unmapped_sub']
    print(f"\n🔗 UNMAPPED SUBCATEGORIES ({len(unmapped_sub)}):")
    print("-" * 50)
    print(f"   💡 Focus on mapping main categories first, then key subcategories")
    print(f"   💡 High-priority subcategories to consider:")
    
    # Suggest some key subcategories
    key_subcategories = [
        'Sphere', 'Panel', 'Floor', 'Tubes', 'Graphics', 'Mapping',
        'Video', 'Cannons', 'Fire', 'Confetti', 'Streamers'
    ]
    
    for key_sub in key_subcategories:
        for cat in unmapped_sub:
            if cat['name'] == key_sub:
                parent = cat.get('parent_category', 'Unknown')
                print(f"      🔴 {cat['name']} (Parent: {parent})")
                break
    
    # Action items
    print(f"\n📋 ACTION ITEMS:")
    print("-" * 50)
    print(f"   1. 🔴 Map high-priority main categories first")
    print(f"   2. 🔴 Map key subcategories for mapped main categories")
    print(f"   3. 📝 Update dynamic_category_manager.py with new mappings")
    print(f"   4. 🧪 Test mappings with sample products")
    print(f"   5. 📊 Monitor mapping coverage improvement")
    
    # Current mapping efficiency
    coverage_percent = float(summary['mapping_coverage'].rstrip('%'))
    if coverage_percent < 20:
        status = "🔴 CRITICAL - Need immediate attention"
    elif coverage_percent < 40:
        status = "🟡 LOW - Significant work needed"
    elif coverage_percent < 60:
        status = "🟠 MEDIUM - Good progress, more work needed"
    elif coverage_percent < 80:
        status = "🟢 GOOD - Well mapped, minor gaps"
    else:
        status = "🟢 EXCELLENT - Well mapped"
    
    print(f"\n📈 CURRENT STATUS: {status}")
    print(f"   Target: 80%+ coverage for production use")

def main():
    """Main function."""
    display_summary()

if __name__ == "__main__":
    main()
