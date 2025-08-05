#!/usr/bin/env python3
"""
Cleanup script to remove all development and test files
"""

import os
import glob

def cleanup_dev_files():
    """Remove all development and test files"""
    
    # Files to delete
    files_to_delete = [
        # Test files
        "test_*.py",
        
        # Check files
        "check_*.py",
        
        # Cleanup files (except this one)
        "cleanup_*.py",
        
        # Discovery files
        "discover_*.py",
        
        # Add files
        "add_*.py",
        
        # CSV files (if any)
        "*.csv",
        
        # Temporary files
        "temp_*.py",
        "debug_*.py",
        
        # Sync variations
        "sync_from_*.py",
        
        # Auto files
        "auto_*.py"
    ]
    
    print("🧹 Cleaning up development files...")
    
    total_deleted = 0
    
    for pattern in files_to_delete:
        matching_files = glob.glob(pattern)
        
        for file_path in matching_files:
            # Skip this cleanup script itself
            if file_path == "cleanup_dev_files.py":
                continue
                
            try:
                os.remove(file_path)
                print(f"  ✅ Deleted: {file_path}")
                total_deleted += 1
            except FileNotFoundError:
                print(f"  ⚠️  File not found: {file_path}")
            except Exception as e:
                print(f"  ❌ Error deleting {file_path}: {e}")
    
    print(f"\n🎯 Cleanup complete! Deleted {total_deleted} files.")
    
    # Show remaining files
    print("\n📁 Remaining files:")
    remaining_files = [f for f in os.listdir('.') if f.endswith('.py') and not f.startswith('.')]
    for file in sorted(remaining_files):
        print(f"  📄 {file}")

if __name__ == "__main__":
    cleanup_dev_files() 