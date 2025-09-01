# Quoter Sync

A Python project that synchronizes data between Quoter and Pipedrive APIs, including products/items, quotes, and organizational data with automated progress tracking.

## Project Structure

### Core Integration Files
- `pipedrive.py` - Main Pipedrive API client with product sync functionality
- `quoter.py` - Quoter API client for authentication and data access
- `webhook_handler.py` - Pipedrive webhook processing and automation
- `sync_with_date_filter.py` - Main Quoter-Pipedrive synchronization script
- `last_sync_date.txt` - Tracks last successful sync date for performance
- `notification.py` - Multi-channel notification system (Slack, Email, Pipedrive)
- `session_manager.py` - CLI session management and command grouping

### Product/Item Management
- `category_manager.py` - Consolidated category mapping system
- `validate_import_categories.py` - Validates import categories against Pipedrive
- `retrieve_latest.py` - Retrieves latest data from APIs
- `end_of_day_sync.py` - End-of-day synchronization processes

### Progress Tracking & Analysis
- `progress_summary_generator.py` - Auto-generates progress summaries from chat logs
- `summary.sh` - Automated progress summary generation script
- `daily_backup.sh` - Daily production files backup script

### Utility Scripts
- `sync.sh` - Main synchronization shell script
- `retrieve.sh` - Data retrieval shell script
- `pipedrive_backup.py` - Pipedrive data backup utilities

### Configuration
- `.env` - Environment variables and API keys
- `requirements.txt` - Python dependencies
- `render.yaml` - Render.com deployment configuration
- `.gitignore` - Git ignore patterns

## Organized Subfolders

### 📁 docs/ - Documentation and Analysis
- **Purpose:** Traditional project documentation and research
- **Contents:** Business logic analysis, category mapping solutions, API documentation
- **Usage:** Reference for developers and project stakeholders

### 📁 work_logs/ - Machine-Readable Chat Data
- **Purpose:** JSON exports of chat sessions for automated analysis
- **Contents:** `chat_YYYYMMDD_HHMMSS.json` files with structured chat data
- **Usage:** Fast parsing and analysis by progress_summary_generator.py

### 📁 chat_backups/ - Human-Readable Chat Archives
- **Purpose:** Manual chat exports and generated progress summaries
- **Contents:** 
  - Manually exported chat files (any filename.md)
  - Generated progress summaries (`progress_summary_YYYYMMDD_HHMMSS.md`)
- **Usage:** Human-readable chat history and progress tracking

### 📁 debug_files/ - Development and Testing
- **Purpose:** Temporary files, test scripts, and debugging tools
- **Contents:** Development scripts, test files, temporary outputs
- **Usage:** Development work, testing, and debugging

### 📁 test_files/ - Test Data and Scripts
- **Purpose:** Test data, sample files, and testing utilities
- **Contents:** Test datasets, sample configurations, test scripts
- **Usage:** Testing and validation of system components

### 📁 utils/ - Utility Scripts and Tools
- **Purpose:** Helper scripts, utilities, and common functions
- **Contents:** Utility scripts, helper functions, common tools
- **Usage:** Supporting scripts and shared functionality

### 📁 archive/ - Historical Files
- **Purpose:** Archived files, old versions, and historical data
- **Contents:** Old scripts, previous versions, archived data
- **Usage:** Historical reference and rollback capability

### 📁 csv_files/ - Data Import/Export
- **Purpose:** CSV data files for import/export operations
- **Contents:** CSV files for data migration and bulk operations
- **Usage:** Data import/export and bulk processing

### 📁 local_backup/ - Daily Backups
- **Purpose:** Daily backups of production files
- **Contents:** Timestamped backups of all production files
- **Usage:** Safety backup and rollback capability

## Progress Summary System

The progress summary system provides automated analysis and summarization of chat sessions:

### Workflow
1. **Manual Export:** Export chat session manually to `chat_backups/` (any filename.md)
2. **Automated Processing:** Run `./summary.sh` to process the latest chat file
3. **JSON Creation:** System creates `chat_YYYYMMDD_HHMMSS.json` in `work_logs/`
4. **Analysis:** System analyzes JSON file for progress, tasks, and insights
5. **Summary Generation:** System creates `progress_summary_YYYYMMDD_HHMMSS.md` in `chat_backups/`

### Files Created
- `work_logs/chat_YYYYMMDD_HHMMSS.json` - Structured chat data for analysis
- `chat_backups/progress_summary_YYYYMMDD_HHMMSS.md` - Human-readable progress summary

### Analysis Features
- Extracts completed tasks and current files
- Identifies next steps and known issues
- Provides status assessment and key insights
- Tracks session metadata (timestamps, file sizes, session IDs)

### Usage
- Export your chat manually to `chat_backups/` folder
- Run `./summary.sh` to generate analysis and summary
- Review `progress_summary_YYYYMMDD_HHMMSS.md` for insights
- Use summaries to transfer context between chat sessions

## Setup

### Prerequisites
- Python 3.9+
- Virtual environment (venv)
- API access to both Quoter and Pipedrive

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd quoter_sync

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and credentials
```

### Environment Variables
```bash
# Quoter API
QUOTER_CLIENT_ID=your_client_id
QUOTER_CLIENT_SECRET=your_client_secret
QUOTER_REDIRECT_URI=your_redirect_uri

# Pipedrive API
PIPEDRIVE_API_TOKEN=your_api_token

# Notifications
SLACK_WEBHOOK_URL=your_slack_webhook
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
NOTIFICATION_EMAILS=email1@domain.com,email2@domain.com
```

## Features

### Product/Item Sync
- Bidirectional synchronization between Quoter and Pipedrive
- Date-filtered sync for performance optimization
- Category mapping and management
- Price synchronization with proper data type handling
- Automatic conflict resolution

### Quote Automation
- Monitors Pipedrive for new sub-organizations
- Automatically creates draft quotes in Quoter
- Links quotes to deals and organizations
- Sends notifications to sales team
- Handles Pipedrive automation integration

### Progress Tracking
- Automated chat session analysis
- Progress summary generation
- Task and file tracking
- Context transfer between sessions
- Daily backup and archival

## Daily Workflow

### Morning Setup
1. Run `./daily_backup.sh` to backup production files
2. Check `chat_backups/` for previous day's progress summaries
3. Review `work_logs/` for recent JSON exports

### During Work
1. Export chat sessions manually to `chat_backups/` (any filename.md)
2. Run `./summary.sh` to generate progress summaries
3. Use `debug_files/` for development work
4. Store test data in `test_files/`

### End of Day
1. Run `./daily_backup.sh` for final backup
2. Review generated summaries in `chat_backups/`
3. Archive completed work to `archive/` if needed

## Workflow Integration

This project supports the complete Pipedrive → Quoter → QBO workflow:

1. **Pipedrive Automation** creates sub-organizations when deals reach "Send Quote/Negotiate" stage
2. **Quote Monitor** detects new sub-organizations and creates draft quotes
3. **Product Sync** keeps products synchronized between systems
4. **Notifications** alert sales team when quotes are ready for editing
5. **Progress Tracking** maintains context and documentation across sessions

## Development Guidelines

- **Shared files** (`quoter.py`, `pipedrive.py`, `utils/`) contain common functionality used across multiple features
- **Production files** are focused on core integration and synchronization
- **Utility files** support development, testing, and daily operations
- **Progress tracking** provides automated documentation and context transfer
- **Daily backups** ensure safety and rollback capability

## File Organization Principles

1. **Separation of Concerns**
   - Production files in root directory
   - Documentation in `docs/`
   - Development files in `debug_files/`
   - Test files in `test_files/`
   - Utilities in `utils/`
   - Archives in `archive/`

2. **Clear Naming Conventions**
   - Descriptive folder names
   - Consistent file naming
   - Timestamped backups and logs

3. **Safety and Backup**
   - Daily backups in `local_backup/`
   - Multiple backup versions
   - Automatic cleanup of old backups

4. **Progress Tracking**
   - Manual chat exports for human readability
   - Automated JSON processing for machine analysis
   - Generated summaries for context transfer