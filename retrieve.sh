#!/bin/bash

# Retrieve Latest - One-Click GitHub Sync
# Just run: ./retrieve.sh

echo "📥 RETRIEVE LATEST - ONE-CLICK GITHUB SYNC"
echo "=================================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run this from your quoter_sync folder."
    exit 1
fi

# Check current status before pull
echo "📋 Current status before pull..."
git status

# Fetch latest from GitHub
echo ""
echo "🔄 Fetching latest changes from GitHub..."
git fetch origin
if [ $? -ne 0 ]; then
    echo "❌ Failed to fetch from GitHub"
    exit 1
fi
echo "   ✅ Fetching completed"

# Check what's new
echo ""
echo "🔍 Checking what's new..."
COMMITS_BEHIND=$(git rev-list HEAD..origin/main --count)
if [ "$COMMITS_BEHIND" -gt 0 ]; then
    echo "   📥 Found $COMMITS_BEHIND new commits to pull"
    
    # Show what commits are coming
    echo "   📝 New commits:"
    git log HEAD..origin/main --oneline | head -5 | while read line; do
        echo "      $line"
    done
    if [ "$COMMITS_BEHIND" -gt 5 ]; then
        echo "      ... and $((COMMITS_BEHIND - 5)) more"
    fi
else
    echo "   ✅ Already up to date with GitHub"
    exit 0
fi

# Pull latest changes
echo ""
echo "🔄 Pulling latest changes..."
git pull origin main
if [ $? -ne 0 ]; then
    echo "❌ Failed to pull from GitHub"
    exit 1
fi
echo "   ✅ Pulling completed"

# Show what files were updated
echo ""
echo "📁 Checking what files were updated..."
RECENT_COMMITS=$((COMMITS_BEHIND > 3 ? 3 : COMMITS_BEHIND))
git diff --name-only HEAD~$RECENT_COMMITS HEAD | head -10 | while read file; do
    echo "      $file"
done

# Final status check
echo ""
echo "📊 Final Status Check..."
git status

# Show latest commit
echo ""
echo "📝 Latest commit:"
git log --oneline -1

echo ""
echo "=================================================="
echo "🎉 RETRIEVE COMPLETED SUCCESSFULLY!"
echo "=================================================="
echo "✅ Latest changes pulled from GitHub"
echo "✅ Your local files are now up to date"
echo "✅ Ready to work with the latest code!"
echo ""
echo "🚀 You're all caught up!"
