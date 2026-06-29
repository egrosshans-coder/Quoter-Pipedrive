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

# Safety check: virtual environments should never be tracked
echo "🛡️ Checking for tracked virtual environments..."
if git ls-files | grep -Eq '^(venv|\.venv|env|venv_py39_backup)/'; then
    echo ""
    echo "❌ ERROR: A virtual environment is being tracked by Git!"
    echo ""
    git ls-files | grep -E '^(venv|\.venv|env|venv_py39_backup)/'
    echo ""
    echo "Remove it from Git with:"
    echo "    git rm -r --cached <virtual-environment-folder>"
    echo ""
    echo "Sync aborted."
    exit 1
fi
echo "   ✅ No tracked virtual environments found"

# Safety check: real .env files should never be tracked
# Allowed: .env.example, .env.sample, .env.template
echo "🛡️ Checking for tracked .env files..."
tracked_env=""

while IFS= read -r file; do
    case "$file" in
        *.example|*.sample|*.template)
            ;;
        .env|*/.env|*.env.local|*.env.production|*.env.development|*.env.test)
            tracked_env="${tracked_env}${file}\n"
            ;;
    esac
done < <(git ls-files | grep '\.env')

if [ -n "$tracked_env" ]; then
    echo ""
    echo "❌ ERROR: A real .env file is being tracked by Git!"
    printf "%b" "$tracked_env"
    echo ""
    echo "Remove it from Git before syncing:"
    echo "    git rm --cached .env"
    echo ""
    echo "Sync aborted."
    exit 1
fi
echo "   ✅ No tracked real .env files found"

# Validate GitHub Actions workflows before committing
echo "🔍 Validating GitHub Actions workflows..."
if [ -d ".github/workflows" ]; then
    for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
        if [ -f "$workflow" ]; then
            echo "   Checking: $(basename "$workflow")"

            if grep -q "github\.event\.schedule.*==" "$workflow"; then
                echo "   ⚠️  Warning: Found potentially problematic schedule condition in $(basename "$workflow")"
                echo "   💡 Tip: Consider using separate workflow files instead of complex conditionals"
            fi

            if grep -q "if:.*github\.event\.schedule.*!=" "$workflow"; then
                echo "   ⚠️  Warning: Found potentially problematic schedule condition in $(basename "$workflow")"
                echo "   💡 Tip: Consider using separate workflow files instead of complex conditionals"
            fi

            if ! python3 -c "
import sys
try:
    with open('$workflow', 'r') as f:
        content = f.read()
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if '  ' in line and '\t' in line:
            print(f'Mixed indentation on line {i}')
            sys.exit(1)
        if line.count('\"') % 2 != 0:
            print(f'Unclosed quotes on line {i}')
            sys.exit(1)
        if line.count(\"'\") % 2 != 0:
            print(f'Unclosed single quotes on line {i}')
            sys.exit(1)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
" 2>/dev/null; then
                echo "   ❌ YAML syntax error in $(basename "$workflow")"
                echo "   🔧 Please fix YAML syntax before committing"
                exit 1
            fi

            echo "   ✅ $(basename "$workflow") syntax looks good"
        fi
    done
    echo "   ✅ All workflow files validated"
else
    echo "   ℹ️  No .github/workflows directory found"
fi

# Get timestamp for commit message
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
COMMIT_MSG="End of day sync: $TIMESTAMP - Automated update"

echo ""
echo "🔄 Starting automated sync..."
echo "   Commit message: $COMMIT_MSG"

# Step 1: Add all changes
echo "🔄 Adding all changes..."
git add -A
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
