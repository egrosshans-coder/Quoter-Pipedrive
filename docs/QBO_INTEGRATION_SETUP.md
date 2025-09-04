# QuickBooks Online Direct Integration Setup

## Overview
This document explains how to set up direct Quoter → QBO item synchronization, eliminating the need for manual CSV export/import.

## Two Implementation Options

### Option 1: Use Quoter's Native QBO Integration (Recommended)

**Steps:**
1. **Enable in Quoter:**
   - Go to `Settings > Integrations` in Quoter
   - Select QuickBooks under Accounting section
   - Click "Connect to QuickBooks"
   - Sign in to your QBO account
   - Authorize the integration

2. **Configure Field Mappings:**
   - Quoter automatically maps fields to QBO
   - Review mappings in Quoter settings
   - Adjust as needed for your business

3. **Benefits:**
   - ✅ Automatic item sync from Quoter to QBO
   - ✅ No manual CSV export/import needed
   - ✅ Real-time synchronization
   - ✅ Built-in field mapping
   - ✅ Handles quotes → estimates → invoices

### Option 2: Custom API Integration

If you need more control, use the custom `quoter_to_qbo_sync.py` script.

**Prerequisites:**
1. **QBO Developer Account:**
   - Sign up at https://developer.intuit.com/
   - Create a new app
   - Get Client ID and Client Secret

2. **OAuth Setup:**
   - Configure redirect URI
   - Get refresh token for your QBO company
   - Get Company ID from QBO

3. **Environment Variables:**
   ```bash
   # Add to your .env file
   QBO_CLIENT_ID=your_qbo_client_id_here
   QBO_CLIENT_SECRET=your_qbo_client_secret_here
   QBO_REFRESH_TOKEN=your_qbo_refresh_token_here
   QBO_COMPANY_ID=your_qbo_company_id_here  # Can be 9 or 16 digits
   QBO_SANDBOX=true  # Set to false for production
   QBO_INCOME_ACCOUNT_ID=1  # Default income account ID
   QBO_EXPENSE_ACCOUNT_ID=2  # Default expense account ID
   ```

## New Workflow

### Current (Problematic):
```
Quoter → Pipedrive → CSV Export → Manual Import → QBO → SyncQ → Pipedrive
```

### New (Efficient) - Bulk Sync Approach:
```
Quoter → QBO (Bulk Sync) → SyncQ → Pipedrive
```

### How It Works:
1. **Create 30 items in Quoter** → Items live in Quoter only
2. **Run bulk sync script** → All 30 items created in QBO immediately
3. **SyncQ detects QBO items** → Syncs all items to Pipedrive
4. **Items available everywhere** → Ready for quotes, invoicing, etc.

## Benefits

1. **Eliminates Manual Steps:**
   - No more CSV export/import
   - No more data massaging
   - No more manual SyncQ linking

2. **Real-time Sync:**
   - Items appear in QBO immediately
   - SyncQ can detect and sync to Pipedrive
   - Maintains data consistency

3. **Reduced Errors:**
   - No manual data entry
   - No CSV formatting issues
   - No import/export failures

## Testing the Integration

### For Option 1 (Native Integration):
1. Create a test item in Quoter
2. Check if it appears in QBO automatically
3. Verify SyncQ picks it up and syncs to Pipedrive

### For Option 2 (Custom API):
```bash
# Bulk sync ALL items from Quoter to QBO
python bulk_sync_items.py

# Or use the main script with different options
python quoter_to_qbo_sync.py --bulk    # Bulk sync all items
python quoter_to_qbo_sync.py --force   # Force sync (overwrite existing)
python quoter_to_qbo_sync.py 2025-01-01  # Sync items modified since date
```

## Troubleshooting

### Common Issues:
1. **OAuth Token Expired:** Refresh the token in QBO developer console
2. **Company ID Wrong:** Get correct Company ID from QBO
3. **Account IDs Invalid:** Verify income/expense account IDs exist in QBO
4. **Field Mapping Issues:** Check Quoter field mappings for native integration

### Debug Mode:
Enable debug logging in the custom script to see detailed API calls and responses.

## Next Steps

1. **Choose Implementation:** Native integration (easier) or custom API (more control)
2. **Set Up QBO Connection:** Follow the steps above
3. **Test with Sample Items:** Create test items and verify sync
4. **Update Workflow:** Modify your processes to use the new direct sync
5. **Monitor SyncQ:** Ensure SyncQ picks up QBO items and syncs to Pipedrive

## Support Resources

- **Quoter QBO Integration:** https://help.quoter.com/hc/en-us/articles/32086015421851-Integrating-with-QuickBooks-Online
- **QBO API Documentation:** https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/item
- **SyncQ Support:** https://help.syncq.net/pipedrive/
