# Pipedrive to Quoter Sync Tools

This folder contains tools for synchronizing data between Pipedrive and Quoter systems.

## Main Tools

### `sync_pipedrive_to_quoter.py`
**Main sync script** - Compares Pipedrive and Quoter items and syncs changes from Pipedrive to Quoter.
- Handles product name changes
- Handles product code changes  
- Handles category changes (with Quoter's parent/child schema)
- Supports dry run mode
- OAuth authentication for Quoter API

### `sync_config.py`
**Configuration file** for the sync script.
- API settings
- Field mappings
- Sync settings (batch size, dry run, etc.)

## Diagnostic Tools

### `find_missing_quoter_item.py`
**Find missing items** - Identifies Pipedrive items that don't have matches in Quoter.
- Useful for finding items that need to be created in Quoter
- Shows detailed information about missing items

### `find_orphaned_quoter_items.py`
**Find orphaned items** - Identifies Quoter items that don't have matches in Pipedrive.
- Useful for finding items that may need to be removed from Quoter
- Shows detailed information about orphaned items

## Testing Tools

### `test_sync_comparison.py`
**Test script** - Tests the comparison logic without making API calls.
- Validates name change detection
- Validates code change detection
- Validates category change detection
- Tests error handling

## Documentation

### `PIPEDRIVE_TO_QUOTER_SYNC.md`
**Usage guide** - Complete documentation for using the sync tools.
- Setup instructions
- Configuration guide
- Usage examples
- Troubleshooting

## Usage

### Running the Main Sync
```bash
# Dry run (recommended first)
python utils/pipe2quoter/sync_pipedrive_to_quoter.py

# Live sync (after testing)
# Edit sync_config.py to set "dry_run": False
python utils/pipe2quoter/sync_pipedrive_to_quoter.py
```

### Finding Missing Items
```bash
python utils/pipe2quoter/find_missing_quoter_item.py
```

### Finding Orphaned Items
```bash
python utils/pipe2quoter/find_orphaned_quoter_items.py
```

### Testing Comparison Logic
```bash
python utils/pipe2quoter/test_sync_comparison.py
```

## Requirements

- Python 3.9+
- Required packages: `requests`, `python-dotenv`
- Environment variables: `PIPEDRIVE_API_TOKEN`, `QUOTER_API_KEY`, `QUOTER_CLIENT_SECRET`

## Notes

- All tools use OAuth authentication for Quoter API
- Pipedrive API uses token-based authentication
- The sync script handles Quoter's parent/child category schema
- Dry run mode is recommended for testing before live sync
