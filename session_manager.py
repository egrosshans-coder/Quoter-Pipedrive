#!/usr/bin/env python3
"""
Session Manager - Automated session management for Quoter-Pipedrive integration project

This script automates:
1. Session summary generation from chat logs
2. GitHub sync and commit
3. Cross-system synchronization

Usage:
    python3 session_manager.py --action [summary|sync|pull|all]
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
import re

class SessionManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.session_date = datetime.now().strftime("%Y%m%d")
        self.session_time = datetime.now().strftime("%H%M")
        
    def generate_session_summary(self):
        """Generate session summary from chat logs and recent changes."""
        print("📝 Generating session summary...")
        
        # Get recent git changes
        recent_changes = self._get_recent_changes()
        
        # Get modified files
        modified_files = self._get_modified_files()
        
        # Get new files
        new_files = self._get_new_files()
        
        # Create session summary
        summary_content = self._create_summary_content(recent_changes, modified_files, new_files)
        
        # Write summary file
        summary_filename = f"SESSION_SUMMARY_{self.session_date}_{self.session_time}.md"
        summary_path = self.project_root / summary_filename
        
        with open(summary_path, 'w') as f:
            f.write(summary_content)
        
        print(f"✅ Session summary created: {summary_filename}")
        return summary_path
    
    def _get_recent_changes(self):
        """Get recent git commit messages and changes."""
        try:
            # Get last 5 commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
            return []
        except Exception as e:
            print(f"⚠️  Warning: Could not get git history: {e}")
            return []
    
    def _get_modified_files(self):
        """Get list of modified files."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                modified = []
                for line in result.stdout.strip().split('\n'):
                    if line and line[0] in ['M', 'A', 'D', 'R']:
                        status = line[:2]
                        filename = line[3:]
                        modified.append(f"{status} {filename}")
                return modified
            return []
        except Exception as e:
            print(f"⚠️  Warning: Could not get git status: {e}")
            return []
    
    def _get_new_files(self):
        """Get list of new untracked files."""
        try:
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip().split('\n') if result.stdout.strip() else []
            return []
        except Exception as e:
            print(f"⚠️  Warning: Could not get untracked files: {e}")
            return []
    
    def _create_summary_content(self, recent_changes, modified_files, new_files):
        """Create the session summary content."""
        content = f"""# Session Summary - {datetime.now().strftime("%B %d, %Y")} {datetime.now().strftime("%I:%M %p")}

## 🎯 **Session Overview:**
**Date:** {datetime.now().strftime("%B %d, %Y")}  
**Time:** {datetime.now().strftime("%I:%M %p")}  
**Session ID:** {self.session_date}_{self.session_time}

## 📊 **Project Status:**
**Repository:** Quoter-Pipedrive Integration  
**Branch:** main  
**Last Commit:** {recent_changes[0] if recent_changes else 'None'}

## 🔄 **Recent Changes:**
"""
        
        if recent_changes:
            content += "### **Git History (Last 5 commits):**\n"
            for change in recent_changes:
                content += f"- {change}\n"
        else:
            content += "### **Git History:** No recent commits found\n"
        
        content += "\n## 📁 **File Changes:**\n"
        
        if modified_files:
            content += "### **Modified Files:**\n"
            for file in modified_files:
                content += f"- {file}\n"
        else:
            content += "### **Modified Files:** No modifications detected\n"
        
        if new_files:
            content += "\n### **New Files:**\n"
            for file in new_files:
                content += f"- {file}\n"
        else:
            content += "\n### **New Files:** No new files detected\n"
        
        content += f"""
## 🎯 **Key Accomplishments:**
*[To be filled in manually based on session work]*

## 🔧 **Technical Updates:**
*[To be filled in manually based on session work]*

## 🚨 **Issues Encountered:**
*[To be filled in manually based on session work]*

## 📋 **Next Steps:**
*[To be filled in manually based on session work]*

## 💡 **Insights & Patterns:**
*[To be filled in manually based on session work]*

## 📚 **Files Created/Modified in This Session:**
*[Auto-populated above]*

---

**Session Date:** {datetime.now().strftime("%B %d, %Y")}  
**Duration:** [To be filled in]  
**Participants:** Eric Grosshans, AI Assistant  
**Next Session:** TBD

---
*This summary was auto-generated by session_manager.py*
"""
        return content
    
    def sync_to_github(self):
        """Sync all changes to GitHub."""
        print("🔄 Syncing to GitHub...")
        
        try:
            # Add all files
            print("  📁 Adding files...")
            result = subprocess.run(
                ["git", "add", "."],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode != 0:
                print(f"❌ Failed to add files: {result.stderr}")
                return False
            
            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            if result.returncode == 0:
                print("✅ No changes to commit")
                return True
            
            # Commit changes
            print("  💾 Committing changes...")
            commit_message = f"Session update {self.session_date}_{self.session_time}: automated sync"
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode != 0:
                print(f"❌ Failed to commit: {result.stderr}")
                return False
            
            # Push to GitHub
            print("  🚀 Pushing to GitHub...")
            result = subprocess.run(
                ["git", "push", "origin", "main"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode != 0:
                print(f"❌ Failed to push: {result.stderr}")
                return False
            
            # Verify the transfer worked
            print("  🔍 Verifying transfer...")
            if not self._verify_github_sync():
                print("⚠️  Warning: Transfer verification failed - files may not have synced properly")
                return False
            
            print("✅ Successfully synced to GitHub!")
            return True
            
        except Exception as e:
            print(f"❌ Error syncing to GitHub: {e}")
            return False
    
    def _verify_github_sync(self):
        """Verify that the GitHub sync actually worked by comparing local and remote."""
        try:
            # Fetch latest remote info
            result = subprocess.run(
                ["git", "fetch", "origin"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode != 0:
                print(f"    ❌ Failed to fetch for verification: {result.stderr}")
                return False
            
            # Get local commit hash
            local_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if local_result.returncode != 0:
                print(f"    ❌ Failed to get local commit: {local_result.stderr}")
                return False
            
            local_commit = local_result.stdout.strip()
            
            # Get remote commit hash
            remote_result = subprocess.run(
                ["git", "rev-parse", "origin/main"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if remote_result.returncode != 0:
                print(f"    ❌ Failed to get remote commit: {remote_result.stderr}")
                return False
            
            remote_commit = remote_result.stdout.strip()
            
            # Compare commits
            if local_commit == remote_commit:
                print(f"    ✅ Transfer verified: Local and remote commits match ({local_commit[:8]})")
                return True
            else:
                print(f"    ❌ Transfer verification failed:")
                print(f"       Local:  {local_commit[:8]}")
                print(f"       Remote: {remote_commit[:8]}")
                return False
                
        except Exception as e:
            print(f"    ❌ Verification error: {e}")
            return False
    
    def pull_from_github(self):
        """Pull latest changes from GitHub."""
        print("📥 Pulling from GitHub...")
        
        try:
            # Fetch latest changes
            print("  📡 Fetching latest changes...")
            result = subprocess.run(
                ["git", "fetch", "origin"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode != 0:
                print(f"❌ Failed to fetch: {result.stderr}")
                return False
            
            # Pull changes
            print("  ⬇️  Pulling changes...")
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode != 0:
                print(f"❌ Failed to pull: {result.stderr}")
                return False
            
            print("✅ Successfully pulled from GitHub!")
            return True
            
        except Exception as e:
            print(f"❌ Error pulling from GitHub: {e}")
            return False
    
    def run_full_session(self):
        """Run the complete session workflow."""
        print("🚀 Running full session workflow...")
        print("=" * 50)
        
        # Generate summary
        summary_path = self.generate_session_summary()
        
        # Sync to GitHub
        if self.sync_to_github():
            print(f"\n📝 Session summary created: {summary_path.name}")
            print("💾 All changes committed and pushed to GitHub")
            print("✅ Session workflow complete!")
        else:
            print("❌ Session workflow failed during GitHub sync")
            return False
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Session Manager for Quoter-Pipedrive project")
    parser.add_argument(
        "--action", 
        choices=["summary", "sync", "pull", "all"],
        default="all",
        help="Action to perform (default: all)"
    )
    
    args = parser.parse_args()
    
    manager = SessionManager()
    
    if args.action == "summary":
        manager.generate_session_summary()
    elif args.action == "sync":
        manager.sync_to_github()
    elif args.action == "pull":
        manager.pull_from_github()
    elif args.action == "all":
        manager.run_full_session()

if __name__ == "__main__":
    main()
