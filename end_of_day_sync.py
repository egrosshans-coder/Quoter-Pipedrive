#!/usr/bin/env python3
"""
End of Day Sync - One-Click GitHub Sync
========================================

This script automatically:
1. Checks for changes
2. Commits them with a timestamp
3. Pushes to GitHub
4. Reports the results

Just run: python3 end_of_day_sync.py
"""

import subprocess
import datetime
import sys
import os

def run_command(command, description):
    """Run a git command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        print(f"   ✅ {description} completed")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"   ❌ {description} failed: {e.stderr}")
        return False, e.stderr

def get_changed_files():
    """Get list of changed files"""
    try:
        result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            return [line for line in result.stdout.strip().split('\n') if line]
        return []
    except:
        return []

def main():
    """Main sync function"""
    print("🚀 END OF DAY SYNC - ONE-CLICK GITHUB UPDATE")
    print("=" * 50)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository. Please run this from your quoter_sync folder.")
        return False
    
    # Check current status
    print("📋 Checking current status...")
    status_result = subprocess.run("git status", shell=True, capture_output=True, text=True)
    print(status_result.stdout)
    
    # Get changed files
    changed_files = get_changed_files()
    
    if not changed_files:
        print("✅ No changes to commit. Everything is already synced!")
        return True
    
    print(f"\n📝 Found {len(changed_files)} changed files:")
    for file in changed_files[:10]:  # Show first 10
        print(f"   {file}")
    if len(changed_files) > 10:
        print(f"   ... and {len(changed_files) - 10} more")
    
    # Generate commit message with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_message = f"End of day sync: {timestamp} - Automated update"
    
    print(f"\n🔄 Starting automated sync...")
    print(f"   Commit message: {commit_message}")
    
    # Step 1: Add all changes
    success, output = run_command("git add .", "Adding all changes")
    if not success:
        return False
    
    # Step 2: Commit changes
    success, output = run_command(f'git commit -m "{commit_message}"', "Committing changes")
    if not success:
        return False
    
    # Step 3: Push to GitHub
    success, output = run_command("git push origin main", "Pushing to GitHub")
    if not success:
        return False
    
    # Final status check
    print("\n📊 Final Status Check...")
    final_status = subprocess.run("git status", shell=True, capture_output=True, text=True)
    print(final_status.stdout)
    
    print("\n" + "=" * 50)
    print("🎉 END OF DAY SYNC COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print("✅ All changes committed and pushed to GitHub")
    print("✅ Your other PCs can now pull the latest changes")
    print("✅ No manual commands needed!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Sync failed. Check the errors above.")
        sys.exit(1)
    else:
        print("\n🚀 Ready for tomorrow's work!")
