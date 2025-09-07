#!/bin/bash
"""
Setup automatic template sync via cron job
This script sets up a cron job to sync Quoter templates to Pipedrive every 30 minutes
"""

# Get the current directory (where the script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/auto_sync_templates.py"

echo "🔄 Setting up automatic template sync..."
echo "📁 Script location: $PYTHON_SCRIPT"

# Check if the Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: $PYTHON_SCRIPT not found"
    exit 1
fi

# Make the Python script executable
chmod +x "$PYTHON_SCRIPT"

# Create a log file path
LOG_FILE="$SCRIPT_DIR/logs/template_sync.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Add cron job (runs every 30 minutes)
CRON_JOB="*/30 * * * * cd $SCRIPT_DIR && python3 $PYTHON_SCRIPT --auto >> $LOG_FILE 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "template_sync"; then
    echo "⚠️  Template sync cron job already exists"
    echo "Current cron jobs:"
    crontab -l | grep template_sync
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Added cron job: Every 30 minutes"
fi

echo ""
echo "📋 Cron job details:"
echo "   • Command: $CRON_JOB"
echo "   • Log file: $LOG_FILE"
echo "   • Frequency: Every 30 minutes"
echo ""
echo "🔧 To manage the cron job:"
echo "   • View: crontab -l"
echo "   • Edit: crontab -e"
echo "   • Remove: crontab -e (delete the line)"
echo ""
echo "📊 To check sync status:"
echo "   • View logs: tail -f $LOG_FILE"
echo "   • Manual sync: python3 $PYTHON_SCRIPT --auto"
