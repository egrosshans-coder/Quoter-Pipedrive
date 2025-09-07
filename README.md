# Quoter Sync

A Python project that synchronizes data between Quoter and Pipedrive APIs, including products/items, quotes, and organizational data with automated progress tracking.

## Project Structure

### Core Integration Files
- `pipedrive.py` - Main Pipedrive API client with product sync functionality
  - **Recent updates:** Fixed price structure to use `prices` array format
  - **Recent updates:** Added decimal value handling for prices and costs
  - **Recent updates:** Enhanced price comparison logic for updates
- `quoter.py` - Quoter API client for authentication and data access
  - **Recent updates:** Refactored to use both `created_at[gt]` and `modified_at[gt]` filters
  - **Recent updates:** Added helper functions for date filtering and deduplication
- `webhook_handler.py` - Pipedrive webhook processing and automation
- `sync_with_date_filter.py` - Main Quoter-Pipedrive synchronization script
- `pd_catsub_backfill.py` - CatSub field backfill script for Pipedrive products
  - **Purpose:** Populates Category:Subcategory fields for QBO integration
  - **Usage:** `python3 pd_catsub_backfill.py --domain your-domain --api-token your-token`
- `last_sync_date.txt` - Tracks last successful sync date for performance
- `notification.py` - Multi-channel notification system (Slack, Email, Pipedrive)
- `session_manager.py` - CLI session management and command grouping

### Monitoring & Troubleshooting
- `automation_monitor.py` - Comprehensive monitoring of Pipedrive automation workflow
- `quick_monitor.py` - Real-time monitoring of specific deals and webhook status
- `webhook_logger.py` - Webhook activity logging and debugging

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
- `sync.sh` - Main synchronization shell script with GitHub Actions workflow validation
- `retrieve.sh` - Data retrieval shell script
- `pipedrive_backup.py` - Pipedrive data backup utilities

### Configuration
- `.env` - Environment variables and API keys
- `requirements.txt` - Python dependencies
- `render.yaml` - Render.com deployment configuration
- `.github/workflows/` - GitHub Actions workflow files
  - `sync.yml` - Regular product sync workflow (every 30 minutes)
  - `catsub-backfill.yml` - CatSub field backfill workflow (daily at 2 AM UTC)
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

## Recent Major Updates (September 2025)

### September 6, 2025: Critical Sync System Overhaul

#### **A, B, C Product Matching Logic Rewrite (`pipedrive.py`)**
**Problem:** Duplicate products being created in Pipedrive due to flawed if-then-else logic that could trigger multiple scenarios.

**Root Cause:** Nested if statements allowed both Scenario B and C to execute, creating duplicate products with identical Pipedrive IDs.

**Solution Applied:**
```python
# OLD (nested if statements - flawed):
if sku:
    # Scenario A logic
else:
    if name_match:
        if qb_id:
            # Scenario B logic
        else:
            # Scenario C logic
    else:
        # Scenario C logic

# NEW (clean if-elif-elif structure):
if sku:
    # A. Has supplier_sku → Update existing Pipedrive product
elif name_match and qb_id:
    # B. No supplier_sku BUT has QuickBooks ID → Update existing (from QBO/SyncQ)
else:
    # C. No supplier_sku AND no QuickBooks ID → Create new product
```

**Result:** Eliminated duplicate product creation. Each item now follows exactly one scenario.

#### **Timezone Consistency Fix (`sync_with_date_filter.py`)**
**Problem:** Date filtering was processing too many items due to timezone mismatch between `last_sync_date.txt` (Pacific time) and Quoter/Pipedrive APIs (UTC).

**Root Cause:** `datetime.now()` saves local time but APIs expect UTC timestamps.

**Solution Applied:**
```python
# OLD (inconsistent timezone):
datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")

# NEW (consistent UTC):
datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
```

**Result:** Date filtering now works correctly, processing only items modified since last sync.

#### **Pipedrive Search API Enhancement (`pipedrive.py`)**
**Problem:** `find_product_by_name()` using Pipedrive search API returned `None` for custom fields like QuickBooks ID, causing Scenario B logic to fail.

**Root Cause:** Pipedrive search API doesn't reliably return custom field values.

**Solution Applied:**
```python
# After finding product by name via search API:
full_product = find_product_by_id(product_id, headers, params)
return full_product  # Now includes all custom fields
```

**Result:** Scenario B (name match + QBO ID check) now works correctly.

#### **4-Field Update Integration (`pipedrive.py`)**
**Problem:** Product creation required separate API calls for 4 custom fields, causing timing issues and potential race conditions.

**Solution Applied:**
- Consolidated all 4 fields (CatSub, QBO Item Type, Product/Service, Sync to QuickBooks) into single product creation API call
- Added proper category mapping using `category_manager.py`
- Fixed CatSub field formatting to show "Category:Subcategory" instead of just "Subcategory"

**Result:** Cleaner, more reliable product creation with all fields set atomically.

#### **Bidirectional Sync Enhancement (`pipedrive.py`)**
**Problem:** Pipedrive product IDs weren't being written back to Quoter `supplier_sku` field for new products.

**Solution Applied:**
- Added `update_quoter_sku()` call for both updated AND new products
- Added condition to only update `supplier_sku` if it's initially empty
- Ensured proper error handling for Quoter API calls

**Result:** Complete bidirectional sync - Quoter items get Pipedrive IDs, Pipedrive products get Quoter data.

#### **Project Cleanup and Organization (September 6, 2025)**
**Problem:** Production directory cluttered with test files, debug scripts, and temporary analysis files.

**Solution Applied:**
- **Moved to `test_files/`:** `test_qbo_integration.py`, `qbo_validation_test.py`, `verify_two_step_process.py`, `comprehensive_qbo_analysis.py`, `deep_quoter_analysis.py`
- **Moved to `chat_backups/`:** `PROGRESS_SUMMARY_20250901_091202.md`
- **Moved to `docs/`:** `QBO_SYNC_ERROR_FIX.md`
- **Deleted redundant files:** `bulk_sync_items.py`, `september_items_analysis.csv`, `qbo_items_analysis.json`, `qbo_raw_items.json`, `retrieve_latest.py`, `pd_catsub_backfill_github.py`
- **Kept essential test files:** `test_email_notification.py`, `test_slack_notification.py`

**Result:** Clean production directory with only essential files, proper organization of test and documentation files.

#### **Comprehensive System Documentation (September 6, 2025)**
**Problem:** Complex sync system lacked comprehensive documentation covering all scenarios, logic flows, and troubleshooting.

**Solution Applied:**
- **Created `docs/SYNC_SYSTEM_DOCUMENTATION.md`** - Complete technical documentation covering:
  - Timestamp management and UTC consistency
  - A, B, C product matching logic with detailed scenarios
  - Get by name vs get by ID API patterns
  - 4-field update process and field mapping
  - Error handling and troubleshooting guides
  - Performance optimization and monitoring
  - Configuration and deployment details

**Result:** Complete reference documentation for developers and future maintenance.

### Pipedrive Price Format Fix (`pipedrive.py`)
**Problem:** Decimal prices were being stored as `$0.00` in Pipedrive due to incorrect API format usage.

**Root Cause:** The code was using direct `price` and `cost` fields instead of Pipedrive's required `prices` array format.

**Solution Applied:**
```python
# OLD (incorrect format):
pipedrive_product["price"] = float(product.get("price_decimal", 0))
pipedrive_product["cost"] = float(product.get("cost_decimal", 0))

# NEW (correct format):
pipedrive_product["prices"] = [
    {
        "price": price_value,
        "cost": cost_value,
        "currency": "USD"
    }
]
```

**Result:** Decimal prices now correctly preserved (e.g., `$2.50` instead of `$0.00`).

### Quoter Date Filtering Enhancement (`quoter.py`)
**Problem:** Incremental sync was missing items that were created but not modified since the last sync date.

**Solution Applied:**
- Added support for both `created_at[gt]` and `modified_at[gt]` filters
- Enhanced date format handling to ensure proper ISO 8601 format with timezone
- Improved deduplication logic for combining created and modified items

**Result:** More comprehensive incremental sync that captures all relevant changes.

### GitHub Actions Schedule Update
**Problem:** Sync was running every 30 minutes, causing unnecessary API calls and potential rate limiting.

**Solution Applied:**
- Changed schedule from `*/30 * * * *` to `0 2 * * *` (daily at 2 AM UTC)
- Reduced API load while maintaining daily synchronization

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

### API Documentation
- **Quoter API:** https://api.quoter.com/docs
- **Pipedrive API:** https://developers.pipedrive.com/docs/api/v1

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
- **Enhanced date filtering** - captures both newly created AND modified items
- Category mapping and management with automatic backfill
- **Proper price structure** - uses Pipedrive's `prices` array format
- **Decimal value handling** - correctly processes decimal prices and costs
- Automatic conflict resolution and deduplication
- CatSub field backfill for existing products
- GitHub Actions automation with workflow validation

### Quote Automation
- Monitors Pipedrive for new sub-organizations
- Automatically creates draft quotes in Quoter
- Links quotes to deals and organizations
- Sends notifications to sales team
- Handles Pipedrive automation integration
- **✅ FULLY OPERATIONAL** - End-to-end automation working (Sept 2025)

### Progress Tracking
- Automated chat session analysis
- Progress summary generation
- Task and file tracking
- Context transfer between sessions
- Daily backup and archival

## GitHub Actions Automation

### Automated Workflows
The project uses GitHub Actions for automated synchronization:

#### **Job 1: Complete Sync Workflow** (`complete-sync.yml`)
- **Schedule:** Daily at 2 PM UTC
- **Scripts:** `sync_with_date_filter.py` → `quoter_to_qbo_sync.py` (sequential)
- **Purpose:** Complete end-to-end sync from Quoter to Pipedrive to QBO
- **Features:** 
  - **Step 1:** Quoter → Pipedrive sync with A, B, C logic
  - **Step 2:** Quoter → QBO sync for new/updated items
  - Bidirectional sync (Pipedrive IDs written back to Quoter)
  - Date-filtered updates for performance
  - Category mapping and 4-field updates

#### **Job 2: QBO Sync Only** (`qbo-sync.yml`)
- **Schedule:** Daily at 2:30 PM UTC (30 minutes after complete sync)
- **Script:** `quoter_to_qbo_sync.py`
- **Purpose:** Additional QBO sync for any items missed in main workflow
- **Features:**
  - Standalone QBO synchronization
  - Handles any timing issues from main workflow
  - Dry-run validation and error handling

### Workflow Validation
- **Pre-commit validation** in `sync.sh` checks workflow syntax
- **Prevents broken workflows** from reaching GitHub
- **Warns about problematic patterns** like complex conditional logic

### Manual Triggers
Both workflows support manual execution via GitHub Actions interface:
- Use "Run workflow" button for testing
- Useful for immediate sync or troubleshooting

## Daily Workflow

### Morning Setup
1. Run `./daily_backup.sh` to backup production files
2. Check `chat_backups/` for previous day's progress summaries
3. Review `work_logs/` for recent JSON exports
4. Check GitHub Actions for overnight workflow runs

### During Work
1. Export chat sessions manually to `chat_backups/` (any filename.md)
2. Run `./summary.sh` to generate progress summaries
3. Use `debug_files/` for development work
4. Store test data in `test_files/`
5. Use `./sync.sh` for git operations (includes workflow validation)

### End of Day
1. Run `./daily_backup.sh` for final backup
2. Review generated summaries in `chat_backups/`
3. Archive completed work to `archive/` if needed
4. Verify GitHub Actions workflows are running successfully

## Workflow Integration

This project supports the complete Pipedrive → Quoter → QBO workflow:

1. **Pipedrive Automation** creates sub-organizations when deals reach "Send Quote/Negotiate" stage
2. **Quote Monitor** detects new sub-organizations and creates draft quotes
3. **Product Sync** keeps products synchronized between systems
4. **Notifications** alert sales team when quotes are ready for editing
5. **Progress Tracking** maintains context and documentation across sessions

## Monitoring & Troubleshooting

### Monitoring Programs

#### **1. automation_monitor.py**
- **Purpose:** Comprehensive monitoring of Pipedrive automation workflow
- **Usage:** `python3 automation_monitor.py`
- **Features:**
  - Webhook server health checks
  - Deal status monitoring
  - Organization details tracking
  - HID-QBO-Status progression alerts
  - Webhook trigger verification
  - Quote creation confirmation

#### **2. quick_monitor.py**
- **Purpose:** Real-time monitoring of specific deals
- **Usage:** `python3 quick_monitor.py [DEAL_ID] [INTERVAL]`
- **Example:** `python3 quick_monitor.py 2499 10` (monitor deal 2499 every 10 seconds)
- **Features:**
  - Real-time status updates
  - Webhook trigger detection
  - Quick troubleshooting for specific deals
  - Owner and organization tracking

#### **3. webhook_logger.py**
- **Purpose:** Log all incoming webhook activity
- **Usage:** `python3 webhook_logger.py`
- **Features:**
  - Webhook payload logging
  - Error tracking
  - Debugging support
  - Activity monitoring

### Monitoring Best Practices

#### **When to Use Each Tool:**
- **`quick_monitor.py`** - For immediate troubleshooting of specific deals
- **`automation_monitor.py`** - For comprehensive system health checks
- **`webhook_logger.py`** - For debugging webhook issues

#### **Recommended Monitoring Schedule:**
- **Real-time:** Use `quick_monitor.py` when testing new deals
- **Daily:** Run `automation_monitor.py` for system health checks
- **Debugging:** Use `webhook_logger.py` when investigating webhook issues

### Recent Fixes (September 2025)

#### **✅ Webhook Automation Fully Operational**
- **Issue:** SyncQ "Required parameter Line is missing" error
- **Solution:** Removed optional phone/email mappings from SyncQ
- **Result:** QBO customer creation now works successfully

#### **✅ Contact Creation Fixed**
- **Issue:** Quoter API "last_name is required" error
- **Solution:** Added fallback "Contact" for empty last_name fields
- **Result:** Contact creation now works for all name formats

#### **✅ Owner Restriction Removed**
- **Issue:** Webhook only processed Maurice's organizations
- **Solution:** Removed hardcoded owner restriction
- **Result:** Webhook now processes all owners consistently

#### **✅ Date Filtering Sync Fixed (September 4, 2025)**
- **Issue:** New items created in Quoter not syncing to Pipedrive
- **Root Cause:** Sync script only checked `modified_at[gt]` filter, missing newly created items
- **Solution:** Refactored `quoter.py` to use both `created_at[gt]` and `modified_at[gt]` filters
- **Implementation:** 
  - Added `_fetch_items_with_date_filter()` helper function
  - Added `_combine_and_deduplicate_items()` helper function
  - Made separate API calls for created and modified items
- **Result:** All new items (41 September items) now sync correctly to Pipedrive

#### **✅ Price Data Structure Fixed (September 4, 2025)**
- **Issue:** Price data not appearing in Pipedrive for new items
- **Root Cause:** Pipedrive expects prices in `prices` array format, not direct `price` field
- **Solution:** Updated `pipedrive.py` to use correct Pipedrive price structure:
  ```json
  "prices": [{"price": 75, "cost": 0, "currency": "USD"}]
  ```
- **Result:** All new items now have correct price data in Pipedrive

#### **✅ Decimal Value Handling Fixed (September 4, 2025)**
- **Issue:** `ValueError: invalid literal for int() with base 10: '0.5'` when syncing items with decimal prices
- **Root Cause:** Code tried to convert decimal strings directly to integers
- **Solution:** Added proper decimal string handling in `pipedrive.py`:
  ```python
  if isinstance(price_value, str) and '.' in price_value:
      pipedrive_product["price"] = int(float(price_value))
  else:
      pipedrive_product["price"] = int(price_value)
  ```
- **Result:** Items with decimal prices (e.g., "0.5") now sync without errors

#### **✅ Category Mapping Enhanced (September 4, 2025)**
- **Issue:** New categories "Equipment" and "DMX" had no Pipedrive mappings
- **Solution:** Used `pd_catsub_backfill.py` to populate Category:Subcategory fields
- **Result:** All new items now have proper category mappings:
  - Equipment items → `Equipment:Truss`
  - DMX items → `DMX:Cables`
  - Pyro items → `Pyro:Propane`

#### **✅ GitHub Authentication Fixed (September 4, 2025)**
- **Issue:** `sync.sh` script failing with "Authentication failed" error
- **Root Cause:** GitHub Personal Access Token expired (expired September 7, 2025)
- **Solution:** Generated new token and updated Git remote URL
- **Result:** `sync.sh` script now works correctly again

## Troubleshooting

### GitHub Actions Issues
- **Red failures:** Check workflow syntax and ensure latest code is pushed
- **Workflow validation:** `sync.sh` now validates workflows before committing
- **Schedule issues:** Use separate workflow files instead of complex conditionals
- **Manual testing:** Use "Run workflow" button in GitHub Actions interface

### Common Problems
- **Broken conditional logic:** Avoid complex `if` conditions in workflows
- **Older commit fallback:** Ensure workflow syntax is correct to prevent GitHub Actions from using older code
- **Missing secrets:** Verify all required secrets are configured in GitHub repository settings

### Sync Issues
- **New items not syncing:** Check if sync script uses both `created_at[gt]` and `modified_at[gt]` filters
- **Price data missing:** Verify Pipedrive uses `prices` array format, not direct `price` field
- **Decimal value errors:** Ensure proper handling of decimal strings (e.g., "0.5" → `int(float("0.5"))`)
- **Category mapping warnings:** Use `pd_catsub_backfill.py` to populate Category:Subcategory fields
- **Authentication failures:** Check GitHub Personal Access Token expiration and update Git remote URL

### Validation Features
- **Pre-commit checks:** `sync.sh` validates YAML syntax and warns about problematic patterns
- **Error prevention:** Stops commits if workflow files have syntax errors
- **Educational warnings:** Shows tips about better workflow patterns

## Major Sync Issues Addressed

### Phase 1: Pipedrive ↔ QBO Sync Issues (via SyncQ)

#### **Problem**: QBO Sync Failures
- **Error**: "Property Name:failed to parse json object; a property specified is unsupported or invalid"
- **Root Cause**: Invalid enum values in Pipedrive "QuickBooks Item Type" custom field
- **Solution**: Updated enum values to match QBO API requirements:
  - ✅ **Valid**: Service, Inventory, NonInventory, Bundle
  - ❌ **Invalid**: Category, Payment, Assembly, etc.

#### **Problem**: Account Reference Issues
- **Error**: "Required parameter ExpenseAccountRef or IncomeAccountRef is missing in the request"
- **Root Cause**: SyncQ couldn't properly map Pipedrive account names to QBO internal IDs
- **Specific Issues**:
  - **Spelling Mismatch**: "Purchase" vs "Purchases" (singular vs plural)
  - **Format Issues**: QBO expects `ReferenceType` objects, not plain strings
  - **Mapping Failures**: "Contracted Labor" failed, "Purchases" worked inconsistently

#### **Resolution**: 
- ✅ **Fixed**: Item names, category formats, purchase flags, missing item types
- ❌ **Unresolved**: Expense/Income account reference mapping (deferred to Quoter-QBO sync)

### Phase 2: Pipedrive → Quoter Sync (New System)

#### **Problem**: Data Discrepancies After QBO Sync
- **Issue**: Modified data in Pipedrive needed to be synced back to Quoter
- **Solution**: Built complete sync system with OAuth authentication
- **Fixed Issues**:
  - ✅ **AI DJ Item**: Code mismatch (`DJ-AI-001` → `AI-DJ-001`)
  - ✅ **Draft Quote Instructions**: Code mismatch (`AI / DJ` → `QTE-DRFT-ITM`)
  - ✅ **Silent Storm T**: Added missing item to Quoter
  - ✅ **Orphaned Items**: Cleaned up 5 duplicate items from Quoter

#### **Final Result**: Perfect sync between Pipedrive and Quoter (244 matches + 1 unique item)

## Lessons Learned & Future Recommendations

### **Source of Truth Strategy**
- **Decision**: **Quoter should be the source of truth** (established weeks ago)
- **Recommended Flow**: 
  1. Create item in Quoter
  2. Push item to QBO
  3. QBO pushes item to Pipedrive
- **Benefits**: Avoids SyncQ mapping issues and maintains data integrity

### **What to Avoid in Future**
1. **Direct Pipedrive → QBO sync** via SyncQ for account references
2. **Enum field mismatches** - always validate against target API requirements
3. **Plain string account references** - use proper `ReferenceType` objects
4. **Inconsistent naming** - maintain strict naming conventions across systems

### **SyncQ Limitations Identified**
- **Account Reference Mapping**: Cannot handle QBO's `ReferenceType` format
- **Real-time Sync Issues**: Batch import works, but real-time sync fails
- **Field Format Conversion**: Sends plain strings instead of required JSON objects

### **Future Implementation Strategy**
- **Quoter → QBO**: Direct API integration with proper `ReferenceType` formatting
- **QBO → Pipedrive**: Use QBO's native Pipedrive integration
- **Avoid SyncQ**: For account reference fields due to format limitations

## Development Guidelines

- **Shared files** (`quoter.py`, `pipedrive.py`, `utils/`) contain common functionality used across multiple features
- **Production files** are focused on core integration and synchronization
- **Utility files** support development, testing, and daily operations
- **Progress tracking** provides automated documentation and context transfer
- **Daily backups** ensure safety and rollback capability
- **Workflow validation** prevents broken GitHub Actions from reaching production

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
   - Generated summaries for context transfer# Updated Sun Sep  7 11:30:46 PDT 2025
