# Quoter-Pipedrive-QBO Sync System Documentation

**Last Updated:** September 7, 2025  
**Version:** 2.0 (Robust A/B/C Logic Implementation)

## Overview

This documentation covers the complete bidirectional sync system between Quoter, Pipedrive, and QuickBooks Online (QBO). The system handles product synchronization with intelligent matching logic, timestamp management, and robust error handling.

## System Architecture

```
Quoter (Source) ←→ Pipedrive (Hub) ←→ QuickBooks Online (Destination)
     ↓                ↓                    ↓
  Items API      Products API         Items API
  Categories     Custom Fields        SyncQ Integration
  OAuth          Search API           OAuth
```

## Core Components

### 1. Main Sync Scripts

- **`sync_with_date_filter.py`** - Entry point for Quoter → Pipedrive sync
- **`quoter_to_qbo_sync.py`** - Quoter → QBO sync
- **`pipedrive.py`** - Core Pipedrive integration logic
- **`quoter.py`** - Quoter API integration
- **`category_manager.py`** - Category mapping utilities

### 2. GitHub Actions Workflows

- **`.github/workflows/complete-sync.yml`** - Automated daily sync (2 PM UTC)
- **`.github/workflows/qbo-sync.yml`** - QBO-specific sync workflow

## Timestamp Management

### UTC Consistency
All timestamps are handled in UTC to prevent timezone-related sync issues:

```python
# sync_with_date_filter.py
def save_sync_date():
    current_datetime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def get_last_sync_date():
    default_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00.000Z")
```

### Date Filtering Logic
- **Last Sync File:** `last_sync_date.txt` stores UTC timestamp
- **Default Range:** 7 days ago if no previous sync date
- **Format:** ISO 8601 with microseconds (`2025-09-07T08:47:53.667Z`)

## Sequencing and Execution Order

### Automated Daily Sequence (GitHub Actions)
```yaml
# .github/workflows/complete-sync.yml
- name: Quoter to Pipedrive Sync
  run: python sync_with_date_filter.py

- name: Quoter to QBO Sync  
  run: python quoter_to_qbo_sync.py
```

### Manual Testing Sequences
1. **Order 1:** Quoter → Pipedrive → QBO
2. **Order 2:** Quoter → QBO → Pipedrive
3. **Order 3:** Complete cycle validation

## A/B/C Logic Implementation

The core product matching logic handles three scenarios:

### Scenario A: Has supplier_sku (Quoter)
```python
if sku:
    # A. Has supplier_sku → Update existing Pipedrive product
    existing_product = find_product_by_id(sku, headers, params)
    if existing_product:
        product_id = existing_product["id"]
        # Update existing product + set 4 fields
        # NO supplier_sku update (already has it)
```

### Scenario B: No supplier_sku + Pipedrive has QBO ID
```python
else:
    existing_product = find_product_by_name(product_name, headers, params)
    if existing_product:
        qb_id = existing_product.get("1213a9ae4c45178ff7c81bde38c3cdfbdc71bbd4")
        if qb_id:
            # B. No supplier_sku BUT Pipedrive has QuickBooks ID → Update existing (from QBO/SyncQ)
            product_id = existing_product["id"]
            # Update existing product + set 4 fields + update Quoter supplier_sku
```

### Scenario C: No supplier_sku + No QBO ID
```python
        else:
            # C. No supplier_sku AND no QuickBooks ID → Create new product
            # Create new product with all 4 fields + update Quoter supplier_sku
```

## Product Lookup Strategy: Name → ID

### Two-Step Lookup Process
Due to Pipedrive API limitations, custom fields are not returned by the search API:

```python
def find_product_by_name(product_name, headers, params):
    # Step 1: Search by name using search API
    response = requests.get(f"{BASE_URL}/products/search", ...)
    
    # Step 2: Get full product data with custom fields
    for result in search_results:
        if product.get("name") == product_name:
            product_id = product.get("id")
            # Get full product data with all custom fields
            full_product = find_product_by_id(product_id, headers, params)
            return full_product
```

### Why This Approach?
- **Search API:** Fast name matching but limited field data
- **Get by ID API:** Complete product data including custom fields
- **QBO ID Field:** `1213a9ae4c45178ff7c81bde38c3cdfbdc71bbd4` (QuickBooks Id : SyncQ)

## Four-Field Update System

### Required Pipedrive Fields
```python
# Field Keys
CATSUB_FIELD_KEY = "9c636133839b978b686bbc952fbd5dc41d5cd087"
QBO_ITEMTYPE_FIELD_KEY = "b65439db55a0f1d772dc1570c8818f3b8a188b25"
PRODUCT_SERVICE_FIELD_KEY = "b82ad04a30171b69c4649e6f66f956ade0a51886"
SYNC_FIELD_KEY = "98ec4970ff4f9f9cc17926d27675eee823a4eb86"

# Option IDs
QBO_SERVICE_ID = 74
QBO_NONINVENTORY_ID = 71
PS_SERVICE_ID = 248
PS_NONINVENTORY_ID = 435
SYNC_YES_ID = 83
```

### Field Population Logic
1. **CatSub:** `"Category:Subcategory"` format (e.g., "Balloons:Latex")
2. **QBO Item Type:** Service (74) or NonInventory (71) based on product code
3. **Product/Service:** Service (248) or NonInventory (435) based on product code  
4. **Sync to QuickBooks:** Always "Yes" (83)

### API Call Strategy
- **New Products:** Single API call with all 4 fields
- **Existing Products:** Two API calls (3 fields, then Sync field)

## Bidirectional Sync Logic

### Quoter → Pipedrive Updates
- **Scenario A:** Update existing (no supplier_sku change)
- **Scenario B:** Update existing + update Quoter supplier_sku
- **Scenario C:** Create new + update Quoter supplier_sku

### supplier_sku Update Conditions
```python
# Only update supplier_sku if initially empty
if not sku:  # Only for scenarios B and C
    update_quoter_sku(product.get("id"), product_id)
```

## Error Handling and Validation

### Duplicate Processing Prevention
```python
processed_items = set()  # Track processed items
if item_id in processed_items:
    logger.error(f"🚨 DUPLICATE PROCESSING DETECTED: {item_name}")
    continue
processed_items.add(item_id)
```

### API Error Handling
- **401 Unauthorized:** Token refresh for QBO
- **404 Not Found:** Graceful handling for missing products
- **Rate Limiting:** Built-in retry logic
- **Network Errors:** Comprehensive exception handling

## Category Management

### Category Mapping System
```python
# category_manager.py
def get_category_mapping(category_name):
    """Map Quoter category names to Pipedrive category IDs"""
    
def get_subcategory_mapping(subcategory_name):
    """Map Quoter subcategories to Pipedrive custom field keys"""
```

### CatSub Field Building
```python
def build_catsub(cat_id, subcategory, cat_map):
    """Build CatSub field value from category and subcategory"""
    if main_category and subcategory:
        catsub = f"{main_category}:{subcategory}"
    elif main_category:
        catsub = main_category
    else:
        catsub = None
```

## Testing and Validation

### Test Scenarios
1. **New Item Creation:** Quoter → Pipedrive → QBO
2. **Existing Item Updates:** All three scenarios (A, B, C)
3. **Bidirectional Sync:** Pipedrive ID back to Quoter
4. **Date Filtering:** Only modified items since last sync
5. **Duplicate Prevention:** Multiple runs without duplication

### Dry Run Mode
```python
# Available in quoter_to_qbo_sync.py
results = platform.run_sync_analysis(dry_run=True)
```

## Configuration and Environment

### Required Environment Variables
```bash
# Pipedrive
PIPEDRIVE_API_TOKEN=your_token_here

# Quoter  
QUOTER_CLIENT_ID=your_client_id
QUOTER_CLIENT_SECRET=your_client_secret

# QuickBooks Online
QBO_CLIENT_ID=your_qbo_client_id
QBO_CLIENT_SECRET=your_qbo_client_secret
QBO_COMPANY_ID=your_company_id
QBO_ACCESS_TOKEN=your_access_token
QBO_REFRESH_TOKEN=your_refresh_token
QBO_INCOME_ACCOUNT_ID=389
QBO_EXPENSE_ACCOUNT_ID=2
```

### File Dependencies
- **`last_sync_date.txt`** - Stores last sync timestamp
- **`.env`** - Environment variables
- **`requirements.txt`** - Python dependencies

## Performance Optimizations

### Pagination Handling
- **Quoter API:** 100 items per page
- **Pipedrive API:** 100 organizations per page
- **QBO API:** 500 items per request

### Memory Management
- **Deduplication:** In-memory duplicate detection
- **Batch Processing:** Efficient API call batching
- **Error Recovery:** Graceful failure handling

## Monitoring and Logging

### Log Levels
- **INFO:** Normal operations and progress
- **WARNING:** Non-critical issues
- **ERROR:** Critical failures requiring attention
- **DEBUG:** Detailed troubleshooting information

### Key Metrics
- Items processed per sync
- Success/failure rates
- Processing time
- Duplicate detection counts

## Troubleshooting Guide

### Common Issues

1. **Duplicate Products in Pipedrive**
   - **Cause:** Incorrect A/B/C logic or timezone issues
   - **Solution:** Verify UTC timestamps and logic flow

2. **Missing Custom Fields**
   - **Cause:** Using search API instead of get by ID
   - **Solution:** Two-step lookup (name → ID → full data)

3. **Timezone Mismatches**
   - **Cause:** Mixing local time and UTC
   - **Solution:** Use `datetime.utcnow()` consistently

4. **QBO ID Not Found**
   - **Cause:** Looking in Quoter instead of Pipedrive
   - **Solution:** Check Pipedrive custom field `1213a9ae4c45178ff7c81bde38c3cdfbdc71bbd4`

### Debug Commands
```bash
# Check last sync date
cat last_sync_date.txt

# Run dry run analysis
python quoter_to_qbo_sync.py

# Test specific date range
python sync_with_date_filter.py 2025-09-01
```

## Future Enhancements

### Planned Improvements
1. **Real-time Webhooks:** Instant sync on data changes
2. **Conflict Resolution:** Advanced merge strategies
3. **Audit Logging:** Complete change tracking
4. **Performance Metrics:** Detailed analytics dashboard
5. **Error Recovery:** Automatic retry mechanisms

### Scalability Considerations
- **API Rate Limits:** Implement exponential backoff
- **Large Datasets:** Streaming processing for big data
- **Multi-tenant:** Support for multiple organizations
- **Cloud Deployment:** Container-based scaling

---

**Note:** This documentation reflects the current implementation as of September 7, 2025. For the most up-to-date information, refer to the source code and recent commit history.
