#!/bin/bash

# Daily Backup Script for Quoter Sync Production Files
# This script backs up all production files from the main directory
# Run this at the beginning of each work day for safety

echo "🔄 Starting Daily Production Files Backup..."
echo "============================================="

# Check if we're in the right directory
if [ ! -f "pipedrive.py" ]; then
    echo "❌ Error: pipedrive.py not found in current directory"
    echo "   Please run this script from the quoter_sync project directory"
    exit 1
fi

# Create backup directory with timestamp
BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="local_backup/backup_${BACKUP_DATE}"

echo "📁 Creating backup directory: ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# Function to backup production files
backup_production_files() {
    echo "📋 Backing up production files..."
    
    # Python production scripts
    cp pipedrive.py "${BACKUP_DIR}/"
    cp quoter.py "${BACKUP_DIR}/"
    cp webhook_handler.py "${BACKUP_DIR}/"
    cp category_manager.py "${BACKUP_DIR}/"
    cp sync_with_date_filter.py "${BACKUP_DIR}/"
    cp session_manager.py "${BACKUP_DIR}/"
    cp notification.py "${BACKUP_DIR}/"
    cp pipedrive_backup.py "${BACKUP_DIR}/"
    cp progress_summary_generator.py "${BACKUP_DIR}/"
    
    # Utility scripts
    cp validate_import_categories.py "${BACKUP_DIR}/"
    cp retrieve_latest.py "${BACKUP_DIR}/"
    cp end_of_day_sync.py "${BACKUP_DIR}/"
    
    # Shell scripts
    cp sync.sh "${BACKUP_DIR}/"
    cp retrieve.sh "${BACKUP_DIR}/"
    
    # Configuration files
    cp .env "${BACKUP_DIR}/"
    cp requirements.txt "${BACKUP_DIR}/"
    cp render.yaml "${BACKUP_DIR}/"
    cp .gitignore "${BACKUP_DIR}/"
    
    # Documentation
    cp README.md "${BACKUP_DIR}/"
    cp README.txt "${BACKUP_DIR}/"
    
    # Utils folder (core utilities)
    cp -r utils "${BACKUP_DIR}/"
    
    echo "✅ Production files backed up successfully"
}

# Function to create backup manifest
create_backup_manifest() {
    echo "📝 Creating backup manifest..."
    
    MANIFEST_FILE="${BACKUP_DIR}/BACKUP_MANIFEST.txt"
    
    cat > "${MANIFEST_FILE}" << EOF
QUOTER SYNC - DAILY BACKUP MANIFEST
====================================
Backup Date: $(date)
Backup Time: $(date +"%H:%M:%S")
Backup Directory: ${BACKUP_DIR}

PRODUCTION FILES BACKED UP:
==========================

PYTHON SCRIPTS:
- pipedrive.py
- quoter.py
- webhook_handler.py
- category_manager.py
- sync_with_date_filter.py
- session_manager.py
- notification.py
- pipedrive_backup.py
- progress_summary_generator.py

UTILITY SCRIPTS:
- validate_import_categories.py
- retrieve_latest.py
- end_of_day_sync.py

SHELL SCRIPTS:
- sync.sh
- retrieve.sh

CONFIGURATION:
- .env
- requirements.txt
- render.yaml
- .gitignore

DOCUMENTATION:
- README.md
- README.txt

UTILITIES:
- utils/ (entire folder)

BACKUP NOTES:
- This backup contains all production files from the main directory
- Subfolders (docs/, work_logs/, chat_backups/, etc.) are NOT included
- Run this script daily before starting work
- Keep backups for at least 7 days for safety

RESTORE INSTRUCTIONS:
- To restore: copy files from ${BACKUP_DIR} back to main directory
- Be careful not to overwrite newer changes
- Always verify file contents before restoring
EOF

    echo "✅ Backup manifest created: ${MANIFEST_FILE}"
}

# Function to cleanup old backups (keep last 7 days)
cleanup_old_backups() {
    echo "🧹 Cleaning up old backups (keeping last 7 days)..."
    
    # Find and remove backups older than 7 days
    find local_backup/ -name "backup_*" -type d -mtime +7 -exec rm -rf {} \;
    
    echo "✅ Old backups cleaned up"
}

# Main backup process
echo "🚀 Starting backup process..."
backup_production_files
create_backup_manifest
cleanup_old_backups

# Final status
echo ""
echo "🎉 DAILY BACKUP COMPLETED SUCCESSFULLY!"
echo "========================================"
echo "📁 Backup location: ${BACKUP_DIR}"
echo "📋 Manifest file: ${BACKUP_DIR}/BACKUP_MANIFEST.txt"
echo "🗓️  Backup date: $(date)"
echo ""
echo "💡 This backup contains all production files for safety"
echo "🔄 Run this script daily before starting work"
echo "🧹 Old backups are automatically cleaned up after 7 days"

# List current backups
echo ""
echo "📚 Current backups in local_backup/:"
ls -la local_backup/ | grep "backup_"
