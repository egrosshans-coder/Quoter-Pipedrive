#!/usr/bin/env python3
"""
Retrieve Latest - One-Click GitHub Sync
=======================================

This script automatically:
1. Fetches latest changes from GitHub
2. Pulls them to your local machine
3. Shows what was updated
4. Reports the results

Just run: python3 retrieve_latest.py
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

def main():
    """Main retrieve function"""
    print("📥 RETRIEVE LATEST - ONE-CLICK GITHUB SYNC")
    print("=" * 50)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository. Please run this from your quoter_sync folder.")
        return False
    
    # Check current status before pull
    print("📋 Current status before pull...")
    status_result = subprocess.run("git status", shell=True, capture_output=True, text=True)
    print(status_result.stdout)
    
    # Step 1: Fetch latest from GitHub
    success, output = run_command("git fetch origin", "Fetching latest changes from GitHub")
    if not success:
        return False
    
    # Step 2: Check what's new
    print("\n🔍 Checking what's new...")
    try:
        behind_result = subprocess.run("git rev-list HEAD..origin/main --count", shell=True, capture_output=True, text=True, check=True)
        commits_behind = int(behind_result.stdout.strip())
        
        if commits_behind > 0:
            print(f"   📥 Found {commits_behind} new commits to pull")
            
            # Show what commits are coming
            log_result = subprocess.run("git log HEAD..origin/main --oneline", shell=True, capture_output=True, text=True, check=True)
            if log_result.stdout.strip():
                print("   📝 New commits:")
                for line in log_result.stdout.strip().split('\n')[:5]:  # Show first 5
                    print(f"      {line}")
                if commits_behind > 5:
                    print(f"      ... and {commits_behind - 5} more")
        else:
            print("   ✅ Already up to date with GitHub")
            return True
            
    except Exception as e:
        print(f"   ⚠️ Could not determine commits behind: {e}")
    
    # Step 3: Pull latest changes
    print(f"\n🔄 Pulling latest changes...")
    success, output = run_command("git pull origin main", "Pulling latest changes")
    if not success:
        return False
    
    # Step 4: Show what files were updated
    print("\n📁 Checking what files were updated...")
    try:
        # Get the last commit hash before pull
        old_hash = subprocess.run("git rev-parse HEAD", shell=True, capture_output=True, text=True, check=True).stdout.strip()
        
        # Show files changed in the last few commits
        files_result = subprocess.run(f"git diff --name-only HEAD~{min(3, commits_behind)} HEAD", shell=True, capture_output=True, text=True, check=True)
        if files_result.stdout.strip():
            changed_files = files_result.stdout.strip().split('\n')
            print(f"   📝 Updated files:")
            for file in changed_files[:10]:  # Show first 10
                print(f"      {file}")
            if len(changed_files) > 10:
                print(f"      ... and {len(changed_files) - 10} more")
    except Exception as e:
        print(f"   ⚠️ Could not show file changes: {e}")
    
    # Final status check
    print("\n📊 Final Status Check...")
    final_status = subprocess.run("git status", shell=True, capture_output=True, text=True)
    print(final_status.stdout)
    
    # Show latest commit
    print("\n📝 Latest commit:")
    latest_commit = subprocess.run("git log --oneline -1", shell=True, capture_output=True, text=True)
    print(latest_commit.stdout.strip())
    
    print("\n" + "=" * 50)
    print("🎉 RETRIEVE COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print("✅ Latest changes pulled from GitHub")
    print("✅ Your local files are now up to date")
    print("✅ Ready to work with the latest code!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Retrieve failed. Check the errors above.")
        sys.exit(1)
    else:
        print("\n🚀 You're all caught up!")
