#!/usr/bin/env python3
"""
Cross-System Sync - Simple script to sync between desktop and laptop

This script helps you sync your Quoter-Pipedrive project between different computers
by pulling the latest changes from GitHub.

Usage:
    python3 cross_system_sync.py
"""

import subprocess
import sys
from pathlib import Path

def sync_from_github():
    """Pull latest changes from GitHub to sync with other systems."""
    print("🔄 Cross-System Sync - Pulling from GitHub")
    print("=" * 50)
    
    # Get project root
    project_root = Path(__file__).parent
    
    print(f"📁 Project directory: {project_root}")
    print()
    
    try:
        # Check git status
        print("📊 Checking current git status...")
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=project_root
        )
        
        if result.returncode == 0:
            if result.stdout.strip():
                print("⚠️  You have local changes that might conflict:")
                print(result.stdout.strip())
                print()
                response = input("Do you want to stash these changes before pulling? (y/N): ")
                if response.lower() == 'y':
                    print("📦 Stashing local changes...")
                    subprocess.run(["git", "stash"], cwd=project_root)
                    print("✅ Changes stashed")
                else:
                    print("⚠️  Proceeding without stashing - conflicts may occur")
            else:
                print("✅ Working directory is clean")
        else:
            print("⚠️  Could not check git status")
        
        print()
        
        # Fetch latest changes
        print("📡 Fetching latest changes from GitHub...")
        result = subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True, text=True, cwd=project_root
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to fetch: {result.stderr}")
            return False
        
        print("✅ Fetched latest changes")
        print()
        
        # Show what's new
        print("📋 Recent commits on GitHub:")
        result = subprocess.run(
            ["git", "log", "HEAD..origin/main", "--oneline"],
            capture_output=True, text=True, cwd=project_root
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print(result.stdout.strip())
        else:
            print("No new commits found")
        
        print()
        
        # Pull changes
        print("⬇️  Pulling changes from GitHub...")
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            capture_output=True, text=True, cwd=project_root
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to pull: {result.stderr}")
            return False
        
        # Verify the pull actually worked
        print("🔍 Verifying sync...")
        if not _verify_pull_sync(project_root):
            print("⚠️  Warning: Sync verification failed - files may not have updated properly")
            return False
        
        # Show what files were actually updated
        print("📁 Verifying file changes...")
        _verify_file_changes(project_root)
        
        print("✅ Successfully synced from GitHub!")
        print()
        
        # Show current status
        print("📊 Current project status:")
        result = subprocess.run(
            ["git", "log", "--oneline", "-3"],
            capture_output=True, text=True, cwd=project_root
        )
        
        if result.returncode == 0:
            print("Latest commits:")
            print(result.stdout.strip())
        
        # Restore stashed changes if any
        stash_result = subprocess.run(
            ["git", "stash", "list"],
            capture_output=True, text=True, cwd=project_root
        )
        
        if stash_result.returncode == 0 and stash_result.stdout.strip():
            print()
            response = input("You have stashed changes. Restore them now? (y/N): ")
            if response.lower() == 'y':
                subprocess.run(["git", "stash", "pop"], cwd=project_root)
                print("✅ Stashed changes restored")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        return False

def _verify_file_changes(project_root):
    """Show what files were actually updated during the sync."""
    try:
        # Get the previous commit hash (before pull)
        # We'll use HEAD@{1} to get the previous position
        result = subprocess.run(
            ["git", "rev-parse", "HEAD@{1}"],
            capture_output=True, text=True, cwd=project_root
        )
        
        if result.returncode == 0:
            previous_commit = result.stdout.strip()
            current_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=project_root
            ).stdout.strip()
            
            if previous_commit != current_commit:
                print(f"    📋 Files changed between {previous_commit[:8]} and {current_commit[:8]}:")
                
                # Show what files changed
                diff_result = subprocess.run(
                    ["git", "diff", "--name-status", f"{previous_commit}..{current_commit}"],
                    capture_output=True, text=True, cwd=project_root
                )
                
                if diff_result.returncode == 0 and diff_result.stdout.strip():
                    for line in diff_result.stdout.strip().split('\n'):
                        if line.strip():
                            status, filename = line.split('\t', 1)
                            status_icon = {
                                'A': '🆕',  # Added
                                'M': '✏️',  # Modified
                                'D': '🗑️',  # Deleted
                                'R': '🔄',  # Renamed
                                'C': '📋'   # Copied
                            }.get(status, '❓')
                            print(f"       {status_icon} {filename}")
                else:
                    print("       No files changed")
            else:
                print("    ✅ No commits pulled - already up to date")
        else:
            print("    ℹ️  Could not determine previous commit state")
            
    except Exception as e:
        print(f"    ⚠️  Could not verify file changes: {e}")

def _verify_pull_sync(project_root):
    """Verify that the pull from GitHub actually worked by comparing local and remote."""
    try:
        # Get local commit hash
        local_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=project_root
        )
        if local_result.returncode != 0:
            print(f"    ❌ Failed to get local commit: {local_result.stderr}")
            return False
        
        local_commit = local_result.stdout.strip()
        
        # Get remote commit hash
        remote_result = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            capture_output=True, text=True, cwd=project_root
        )
        if remote_result.returncode != 0:
            print(f"    ❌ Failed to get remote commit: {remote_result.stderr}")
            return False
        
        remote_commit = remote_result.stdout.strip()
        
        # Compare commits
        if local_commit == remote_commit:
            print(f"    ✅ Sync verified: Local and remote commits match ({local_commit[:8]})")
            return True
        else:
            print(f"    ❌ Sync verification failed:")
            print(f"       Local:  {local_commit[:8]}")
            print(f"       Remote: {remote_commit[:8]}")
            return False
            
    except Exception as e:
        print(f"    ❌ Verification error: {e}")
        return False

def main():
    print("🚀 Quoter-Pipedrive Cross-System Sync")
    print("=" * 40)
    print()
    
    success = sync_from_github()
    
    if success:
        print()
        print("🎉 Sync completed successfully!")
        print("Your local system is now up to date with GitHub.")
    else:
        print()
        print("❌ Sync failed. Check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
