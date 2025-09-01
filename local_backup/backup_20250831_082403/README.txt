QUOTER SYNC PROJECT - FOLDER ORGANIZATION GUIDE
==================================================

This document outlines the organized folder structure created to maintain a clean,
professional production environment while preserving all development and historical files.

PRODUCTION FILES (Main Directory)
=================================
Core application files that are actively used in production:

PYTHON SCRIPTS:
- pipedrive.py              - Main Pipedrive API client with product sync functionality
- quoter.py                  - Quoter API client for authentication and data access
- webhook_handler.py         - Pipedrive webhook processing and automation
- category_manager.py        - Consolidated category mapping system
- sync_with_date_filter.py   - Main Quoter-Pipedrive synchronization script
- session_manager.py         - Session management utilities
- notification.py            - Notification system utilities
- pipedrive_backup.py        - Pipedrive data backup utilities
- progress_summary_generator.py - Auto-generates progress summaries from chat logs

UTILITY SCRIPTS:
- validate_import_categories.py - Validates import categories against Pipedrive
- retrieve_latest.py          - Retrieves latest data from APIs
- end_of_day_sync.py         - End-of-day synchronization processes

SHELL SCRIPTS:
- sync.sh                     - Main synchronization shell script
- retrieve.sh                 - Data retrieval shell script

CONFIGURATION:
- .env                        - Environment variables and API keys
- requirements.txt            - Python dependencies
- render.yaml                 - Render.com deployment configuration
- .gitignore                  - Git ignore patterns

DOCUMENTATION:
- README.md                   - Main project documentation (GitHub standard)

ORGANIZED SUBFOLDERS
====================

1. docs/ (13 files)
   PURPOSE: Traditional project documentation and research
   CONTENTS:
   - Business logic analysis
   - Category mapping solutions
   - Comprehensive Pipedrive mapping guides
   - Quoter API field documentation
   - Webhook integration guides
   - Session management guides
   - Render deployment documentation
   
   USAGE: Reference for developers and project stakeholders

2. work_logs/ (8 files)
   PURPOSE: Daily progress tracking and automated summaries
   CONTENTS:
   - JSON chat session exports (fast processing)
   - Auto-generated progress summaries
   - Work session records
   
   USAGE: 
   - Progress summary generation
   - Work session tracking
   - Fast JSON-based analysis

3. chat_backups/ (21 files)
   PURPOSE: Human-readable chat session archives
   CONTENTS:
   - Markdown chat session exports
   - Historical conversation logs
   - Development session records
   
   USAGE:
   - Manual review and reference
   - Historical context
   - Human-readable format

4. debug_files/ (10 files)
   PURPOSE: Development and debugging utilities
   CONTENTS:
   - Debug scripts for troubleshooting
   - Development testing utilities
   - Data type checking scripts
   - CSV analysis tools
   
   USAGE:
   - Development troubleshooting
   - Testing and validation
   - Debugging specific issues

5. test_files/ (13 files)
   PURPOSE: Testing and validation scripts
   CONTENTS:
   - Unit tests for various functions
   - Integration test scripts
   - Quote creation tests
   - Webhook testing utilities
   
   USAGE:
   - Quality assurance
   - Functionality testing
   - Integration validation

6. utils/ (5 files)
   PURPOSE: Core utilities and development tools
   CONTENTS:
   - logger.py - Logging utility for production scripts
   - ngrok - Local webhook testing tool
   - Development utilities
   
   USAGE:
   - Core logging functionality for production
   - Local development and testing
   - Webhook testing

7. archive/ (1 subfolder)
   PURPOSE: Historical and completed work
   CONTENTS:
   - csv_import/ - Import files and data that are no longer active
   
   USAGE:
   - Reference for completed work
   - Historical data preservation
   - Import file archives

8. csv_files/ (1 file)
   PURPOSE: CSV processing utilities
   CONTENTS:
   - csv_analysis.py - CSV validation and analysis tools
   
   USAGE:
   - Future CSV import validation
   - Data quality checks
   - Import file processing

FOLDER ORGANIZATION PRINCIPLES
==============================

1. PRODUCTION CLEANLINESS:
   - Main directory contains only essential production files
   - All development, testing, and historical files are organized
   - Easy to identify what's actively used vs. archived

2. LOGICAL GROUPING:
   - Files grouped by purpose and function
   - Clear separation between production and development
   - Easy navigation for different types of work

3. PERFORMANCE OPTIMIZATION:
   - JSON files in work_logs for fast script processing
   - Markdown files in chat_backups for human readability
   - Separate locations for different file types

4. MAINTENANCE EASE:
   - Clear folder purposes
   - Easy to find specific types of files
   - Simple cleanup and organization

WORKFLOW INTEGRATION
====================

PROGRESS SUMMARY GENERATION:
1. Run summary.sh script
2. Exports current chat to both formats:
   - Markdown → chat_backups/ (human readable)
   - JSON → work_logs/ (fast processing)
3. Generates progress summary in work_logs/
4. Maintains organized dual-format workflow

SYNCHRONIZATION:
1. Core sync scripts in main directory
2. Category management in main directory
3. Debug and test files organized separately
4. Clean production environment

MAINTENANCE:
1. Regular progress summary generation
2. Organized file management
3. Clear separation of concerns
4. Easy cleanup and organization

This organization ensures a professional, maintainable project structure while
preserving all development work and historical context.
