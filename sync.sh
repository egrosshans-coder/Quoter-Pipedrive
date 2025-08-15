#!/bin/bash

# End of Day Sync - One-Click GitHub Sync
# Just run: ./sync.sh

echo "🚀 END OF DAY SYNC - ONE-CLICK GITHUB UPDATE"
echo "=================================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository. Please run this from your quoter_sync folder."
    exit 1
fi

# Check current status
echo "📋 Checking current status..."
git status

# Check if there are changes
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to commit. Everything is already synced!"
    exit 0
fi

# Get timestamp for commit message
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
COMMIT_MSG="End of day sync: $TIMESTAMP - Automated update"

echo ""
echo "🔄 Starting automated sync..."
echo "   Commit message: $COMMIT_MSG"

# Step 1: Add all changes
echo "🔄 Adding all changes..."
git add .
if [ $? -ne 0 ]; then
    echo "❌ Failed to add changes"
    exit 1
fi
echo "   ✅ Adding all changes completed"

# Step 2: Commit changes
echo "🔄 Committing changes..."
git commit -m "$COMMIT_MSG"
if [ $? -ne 0 ]; then
    echo "❌ Failed to commit changes"
    exit 1
fi
echo "   ✅ Committing changes completed"

# Step 3: Push to GitHub
echo "🔄 Pushing to GitHub..."
git push origin main
if [ $? -ne 0 ]; then
    echo "❌ Failed to push to GitHub"
    exit 1
fi
echo "   ✅ Pushing to GitHub completed"

# Final status check
echo ""
echo "📊 Final Status Check..."
git status

echo ""
echo "=================================================="
echo "🎉 END OF DAY SYNC COMPLETED SUCCESSFULLY!"
echo "=================================================="
echo "✅ All changes committed and pushed to GitHub"
echo "✅ Your other PCs can now pull the latest changes"
echo "✅ No manual commands needed!"
echo ""
echo "🚀 Ready for tomorrow's work!"
