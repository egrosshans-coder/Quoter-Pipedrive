# 📁 QUOTER_SYNC FOLDER CLEANUP & ARCHIVE PLAN

## 🎯 **GOAL**: Clean up quoter_sync folder by moving unnecessary files to archive

---

## 📋 **CURRENT FILE ANALYSIS**

### **🏗️ CORE PRODUCTION FILES (KEEP)**
- `quoter.py` - Main Quoter integration functions
- `pipedrive.py` - Pipedrive API functions  
- `webhook_handler.py` - Webhook handling
- `session_manager.py` - Session management
- `requirements.txt` - Dependencies
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules

### **🧪 ACTIVE TEST FILES (KEEP)**
- `test_comprehensive_quote.py` - Main comprehensive quote test
- `test_two_step_quote_creation.py` - Two-step process test
- `verify_two_step_process.py` - Verification script (new)
- `test_contacts_from_orgs.py` - Contact testing

### **📚 DOCUMENTATION (KEEP)**
- `COMPREHENSIVE_PIPEDRIVE_MAPPING.md` - Data mapping guide
- `Quoter_API_Draft_Quote_Fields.md` - API field documentation
- `QUOTER_PIPEDRIVE_INTEGRATION_RESEARCH.md` - Integration research
- `WEBHOOK_DEPLOYMENT.md` - Webhook deployment guide

---

## 🗂️ **FILES TO ARCHIVE**

### **📝 CHAT SESSIONS & EXPORTS (ARCHIVE)**
- `20250814_laptop_export_chat.md` (545KB) - Old chat export
- `cursor_desktop_chat_session_0814_1842.md` (181KB) - Old chat session
- `Chat-cursor_08132025.md` (411KB) - Old chat session
- `20250811-cursor_quoter.md` (307KB) - Old chat session
- `cursor_importing_files_from_desktop.md` (96KB) - Old import notes

### **📊 SESSION SUMMARIES (ARCHIVE OLD ONES)**
- `SESSION_SUMMARY_20250813_0813.md` - Old session summary
- `SESSION_SUMMARY_20250813_0902.md` - Old session summary  
- `SESSION_SUMMARY_20250813_0904.md` - Old session summary
- `SESSION_SUMMARY_20250813.md` - Old session summary
- `SESSION_SUMMARY_20250814_0903.md` - Old session summary
- `SESSION_SUMMARY_20250814_0911.md` - Old session summary
- `SESSION_SUMMARY_20250814_1052.md` - Old session summary
- `SESSION_SUMMARY_20250814_1844.md` - Old session summary

**KEEP ONLY**: `SESSION_SUMMARY_20250814_1846.md` (most recent)

### **🧪 OBSOLETE TEST FILES (ARCHIVE)**
- `test_template_selection.py` - Obsolete template test
- `test_single_org.py` - Obsolete single org test
- `test_single_quote_fixed.py` - Obsolete quote test
- `test_webhook.py` - Obsolete webhook test
- `verify_quote_3465.py` - Obsolete verification
- `test_quote_requirements.py` - Obsolete requirements test
- `test_quote_status.py` - Obsolete status test
- `test_simple_contact_search.py` - Obsolete contact test
- `test_org_3465.py` - Obsolete org test
- `test_pagination.py` - Obsolete pagination test
- `test_quote_automation.py` - Obsolete automation test
- `test_quote_creation_3465.py` - Obsolete creation test
- `test_quote_creation_fixed.py` - Obsolete fixed test
- `test_quote_numbering.py` - Obsolete numbering test
- `test_custom_numbering.py` - Obsolete custom test
- `test_enhanced_quote_creation.py` - Obsolete enhanced test
- `test_get_quotes.py` - Obsolete get quotes test
- `test_improved_contact_search.py` - Obsolete improved test
- `test_minimal_quote.py` - Obsolete minimal test
- `test_contacts_search.py` - Obsolete contacts search
- `test_create_single_quote.py` - Obsolete single quote test

### **🔧 OBSOLETE DEVELOPMENT FILES (ARCHIVE)**
- `backup_desktop_work_quoter.py` - Backup file
- `backup_desktop_work_pipedrive.py` - Backup file
- `add_instructional_line_item.py` - Obsolete line item script
- `research_pipedrive_integration.py` - Research script
- `simplified_approach.md` - Obsolete approach
- `simplified_quote_creator.py` - Obsolete creator
- `native_pipedrive_quotes.py` - Obsolete native quotes
- `explore_pipedrive_data.py` - Exploration script
- `debug_organizations.py` - Debug script
- `deep_dive_pipedrive.py` - Deep dive script
- `custom_webhook.py` - Obsolete webhook
- `cross_system_sync.py` - Sync script
- `chat_auto_save.py` - Auto-save script
- `cleanup_dev_files.py` - Cleanup script
- `dashboard.py` - Dashboard script
- `category_manager.py` - Category management
- `csv_reader.py` - CSV reader
- `dynamic_category_manager.py` - Dynamic category management
- `category_mapper.py` - Category mapping
- `main.py` - Main script
- `scheduler.py` - Scheduler script
- `sync_with_date_filter.py` - Date filter sync
- `duplicate_prevention.md` - Duplicate prevention
- `quote_automation_requirements.md` - Requirements
- `quote_monitor.py` - Quote monitoring
- `quote_numbering_research.md` - Numbering research
- `notification.py` - Notification system
- `dashboard_data.json` - Dashboard data

### **📁 DIRECTORIES TO EVALUATE**
- `chat_backups/` - Check if needed
- `test_files/` - Check if needed  
- `utils/` - Check if needed
- `.github/` - Keep (GitHub Actions)
- `venv/` - Keep (virtual environment)

---

## 🚀 **ARCHIVE ACTION PLAN**

### **Phase 1: Create Archive Structure**
```
quoter_sync/
├── archive/
│   ├── chat_sessions/
│   ├── old_tests/
│   ├── obsolete_scripts/
│   └── old_documentation/
```

### **Phase 2: Move Files**
1. **Move chat sessions** to `archive/chat_sessions/`
2. **Move old tests** to `archive/old_tests/`
3. **Move obsolete scripts** to `archive/obsolete_scripts/`
4. **Move old documentation** to `archive/old_documentation/`

### **Phase 3: Clean Up**
1. **Remove archived files** from main directory
2. **Update .gitignore** to exclude archive folder
3. **Verify core functionality** still works

---

## 💾 **ESTIMATED SPACE SAVINGS**

- **Current total**: ~2.5MB+ of files
- **Files to archive**: ~1.8MB+ 
- **Space saved**: ~70% reduction
- **Remaining core files**: ~700KB

---

## ⚠️ **BEFORE ARCHIVING**

1. **Verify all core functions work** after cleanup
2. **Test main automation** still functions
3. **Ensure no broken imports** exist
4. **Backup entire folder** before starting

---

## 🎯 **FINAL GOAL**

Clean, focused quoter_sync folder with only:
- Core production code
- Active test files  
- Current documentation
- Essential utilities
