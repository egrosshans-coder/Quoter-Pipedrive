# Quoter Sync

A Python project that synchronizes data between Quoter and Pipedrive APIs, including products/items, quotes, and organizational data.

## Project Structure

### Core Integration Files (Shared)
- `main.py` - Entry point for product/item sync process
- `quoter.py` - **Shared** Quoter API client (authentication, common functions)
- `pipedrive.py` - **Shared** Pipedrive API client (deals, organizations, common functions)
- `utils/logger.py` - **Shared** Logging configuration
- `.env` - **Shared** Environment variables (API keys, not in git)

### Product/Item Sync (Existing)
- `sync_with_date_filter.py` - Date-filtered product sync
- `scheduler.py` - Automated scheduling for product sync
- `category_manager.py` - Product category management
- `category_mapper.py` - Category mapping between systems
- `dynamic_category_manager.py` - Dynamic category handling
- `csv_reader.py` - CSV import utilities

### Quote Automation (New)
- `quote_monitor.py` - **NEW** Monitor for sub-organizations and create draft quotes
- `quote_creator.py` - **NEW** Quote creation functionality
- `notification.py` - **NEW** Sales team notifications

### Utilities & Testing
- `dashboard.py` - Data visualization dashboard
- `dashboard_data.json` - Dashboard data storage
- `test_files/` - Test files and data
- `cleanup_dev_files.py` - Development cleanup utilities

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```
   Then add your API keys:
   ```
   QUOTER_API_KEY=your_quoter_api_key
   QUOTER_CLIENT_SECRET=your_quoter_client_secret
   PIPEDRIVE_API_TOKEN=your_pipedrive_api_token
   ```

3. **Run the sync:**
   ```bash
   # Product sync
   python main.py
   
   # Quote automation (new)
   python quote_monitor.py
   ```

## Features

### Product/Item Sync
- Syncs products/items from Quoter to Pipedrive
- Handles API authentication and pagination
- Date-filtered sync for efficiency
- Category mapping and management
- Automated scheduling

### Quote Automation (New)
- Monitors for sub-organization creation
- Automatically creates draft quotes in Quoter
- Links quotes to deals and organizations
- Sends notifications to sales team
- Handles Pipedrive automation integration

## Workflow Integration

This project supports the complete Pipedrive → Quoter → QBO workflow:

1. **Pipedrive Automation** creates sub-organizations when deals reach "Send Quote/Negotiate" stage
2. **Quote Monitor** detects new sub-organizations and creates draft quotes
3. **Product Sync** keeps products synchronized between systems
4. **Notifications** alert sales team when quotes are ready for editing

## Development Guidelines

- **Shared files** (`quoter.py`, `pipedrive.py`, `utils/`) contain common functionality used across multiple features
- **Product files** are focused on item/product synchronization
- **Quote files** are focused on quote automation and creation
- **Utility files** support development and testing 