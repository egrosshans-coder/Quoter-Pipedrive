# Daily Product / Item Report System Documentation

**Last Updated:** September 7, 2025  
**Version:** 1.0 (Production Ready)

## Overview

The Daily Product / Item Report system provides comprehensive daily reports on product and item changes across three integrated systems: Quoter, Pipedrive, and QuickBooks Online. The system uses Quoter as the source of truth and tracks corresponding changes in Pipedrive and QBO using intelligent mapping logic.

## System Architecture

```
Quoter (Source of Truth) → Daily Report Generation
         ↓
    Smart Filtering Logic
         ↓
┌─────────────────────────────────────────────────┐
│           Cross-System Mapping                  │
└─────────────────────────────────────────────────┘
         ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   Quoter Items  │ Pipedrive Prods │   QBO Items     │
│   (by date)     │ (by supplier_sku)│  (by name)      │
└─────────────────┴─────────────────┴─────────────────┘
         ↓
┌─────────────────────────────────────────────────┐
│         Email Report Generation                 │
│     (Only if Quoter items > 0)                 │
└─────────────────────────────────────────────────┘
```

## Core Components

### 1. Main Report Module

- **`detailed_sync_notification.py`** - Core report generation system
- **`quoter.py`** - Quoter API integration for item fetching
- **`pipedrive.py`** - Pipedrive API integration for product data
- **`quoter_to_qbo_sync.py`** - QuickBooks Online API integration

### 2. Smart Filtering Logic

#### **Quoter Items (Source of Truth)**
- **Created Today**: Items with `created_at` = today's date
- **Modified Today**: Items with `modified_at` = today's date
- **Smart Logic**: If `modified_count == created_count`, all modified items are new
- **Additional Updates**: If `modified_count > created_count`, find additional updated items

#### **Pipedrive Products (Mapped by supplier_sku)**
- **Mapping Field**: Quoter `sku` field contains Pipedrive product ID
- **Logic**: Find Pipedrive products where `id` matches Quoter `supplier_sku`
- **Type Inheritance**: Inherits "new" or "updated" status from Quoter item

#### **QBO Items (Mapped by Name)**
- **Mapping Field**: Quoter `name` field matches QBO `Name` field
- **Logic**: Find QBO items where `Name` matches Quoter item name
- **Type Inheritance**: Inherits "new" or "updated" status from Quoter item

## Report Content Structure

### Email Report Format

#### **Header Section**
```
📊 Daily Product / Item Report - 2025-09-07 15:06:48
```

#### **Summary Section**
```
📊 Summary
• New Quoter Items: 9
• New Pipedrive Products: 9
• New QuickBooks Items: 9
• Errors: 0
```

#### **Quoter Items Table**
| Product Name | Code | Price | Category/Subcategory | Supplier SKU | Type | Added At |
|--------------|------|-------|---------------------|--------------|------|----------|
| zz-test item3 | TEST3 | $4.50 | Balloons:Latex | 1190 | 🆕 New | 2025-09-07 00:24:43 |

#### **Pipedrive Products Table**
| Product ID | Name | Code | Price | Category | Subcategory | QBO Category:Subcategory | QuickBooks ID | Type | Added At |
|------------|------|------|-------|----------|-------------|-------------------------|---------------|------|----------|
| 1190 | zz-test item3 | TEST3 | $4.50 | Service | None | Service | Pending | 🆕 New | 2025-09-07 00:24:43 |

#### **QBO Items Table**
| Name | Item Type | SKU | Category | Price | Sync Type | Added At |
|------|-----------|-----|----------|-------|-----------|----------|
| zz-test item3 | Service | TEST3 | Service | $4.50 | 🆕 New | 2025-09-07 00:24:43 |

## Data Field Mappings

### Quoter Item Fields
```python
{
    "name": "Product Name",
    "code": "Product Code", 
    "price_decimal": "Price (as string)",
    "category_id": "Category ID for hierarchy lookup",
    "sku": "Supplier SKU (Pipedrive Product ID)",
    "created_at": "Creation timestamp (ISO format)",
    "modified_at": "Last modification timestamp (ISO format)"
}
```

### Pipedrive Product Fields
```python
{
    "id": "Product ID",
    "name": "Product Name",
    "code": "Product Code",
    "prices": [{"price": 4.50}],  # Price array
    "category": "Category ID",
    "ae55145d60840de457ff9e785eba68f0b39ab777": "Subcategory",
    "9c636133839b978b686bbc952fbd5dc41d5cd087": "QBO Category:Subcategory",
    "1213a9ae4c45178ff7c81bde38c3cdfbdc71bbd4": "QuickBooks ID",
    "add_time": "Creation time (YYYY-MM-DD HH:MM:SS)"
}
```

### QBO Item Fields
```python
{
    "Name": "Item Name",
    "Type": "Item Type (Service/Product)",
    "Sku": "SKU (if available)",
    "IncomeAccountRef": {"name": "Category Name"},
    "UnitPrice": "Price",
    "MetaData": {
        "CreateTime": "Creation timestamp (ISO format)",
        "LastUpdatedTime": "Last update timestamp (ISO format)"
    }
}
```

## Smart Filtering Algorithm

### Quoter Item Processing
```python
def get_new_quoter_items_since(last_sync_date):
    # First pass: Get all items created today
    created_today = []
    for product in all_products:
        if product_created_date == last_sync_date:
            product["item_type"] = "new"
            created_today.append(product)
    
    # Second pass: Get all items modified today
    modified_today = []
    for product in all_products:
        if product_modified_date == last_sync_date:
            modified_today.append(product)
    
    # Smart filtering: Compare counts
    if modified_count == created_count:
        # All modified items are just the new ones
        return created_today
    else:
        # Find additional items that were modified but not created today
        additional_updates = []
        for item in modified_today:
            if item["id"] not in created_ids:
                item["item_type"] = "updated"
                additional_updates.append(item)
        
        return created_today + additional_updates
```

### Cross-System Mapping
```python
def get_pipedrive_products_by_quoter_items(quoter_items):
    # Get all Pipedrive products
    all_products = fetch_all_pipedrive_products()
    
    # Find matches by supplier_sku
    matching_products = []
    quoter_supplier_skus = {item.get("supplier_sku") for item in quoter_items}
    
    for product in all_products:
        if str(product.get("id")) in quoter_supplier_skus:
            # Inherit type from Quoter item
            for quoter_item in quoter_items:
                if str(quoter_item.get("supplier_sku")) == str(product.get("id")):
                    product["item_type"] = quoter_item.get("item_type", "new")
                    break
            matching_products.append(product)
    
    return matching_products
```

## Date Filtering Logic

### Date-Only Comparison
All date comparisons use date-only logic (ignoring time):

```python
# Convert timestamps to date-only for comparison
product_date = product_created.replace(hour=0, minute=0, second=0, microsecond=0)
if product_date == last_sync_date:
    # Include in report
```

### Timezone Handling
- **Quoter**: ISO format with timezone (`2025-09-07T00:24:43Z`)
- **Pipedrive**: Local format without timezone (`2025-09-07 00:24:43`)
- **QBO**: ISO format with timezone (`2025-09-07T00:24:43-07:00`)

All timestamps are normalized to UTC for consistent comparison.

## Report Generation Logic

### Conditional Report Sending
```python
def send_notifications(self):
    # Don't send report if no Quoter items were added
    if len(self.quoter_new_items) == 0:
        print("📊 No Quoter items added today - skipping report")
        return True
    
    # Send detailed report
    return self.send_email()
```

### Email Content Generation
```python
def generate_email_content(self):
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; }}
            .section {{ margin: 20px 0; }}
            .section h2 {{ color: #333; border-bottom: 2px solid #007cba; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Daily Product / Item Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</h1>
        </div>
        <!-- Report content -->
    </body>
    </html>
    """
    return html_content
```

## Environment Configuration

### Required Environment Variables

#### **Quoter API Configuration**
```bash
QUOTER_CLIENT_ID=your_quoter_client_id
QUOTER_CLIENT_SECRET=your_quoter_client_secret
QUOTER_REDIRECT_URI=your_quoter_redirect_uri
```

#### **Pipedrive API Configuration**
```bash
PIPEDRIVE_API_TOKEN=your_pipedrive_api_token
```

#### **QuickBooks Online Configuration**
```bash
QBO_CLIENT_ID=your_qbo_client_id
QBO_CLIENT_SECRET=your_qbo_client_secret
QBO_REDIRECT_URI=your_qbo_redirect_uri
QBO_REALM_ID=your_qbo_realm_id
```

#### **Email Configuration**
```bash
GMAIL_USER=admin@tlciscreative.com
GMAIL_APP_PASSWORD=your_gmail_app_password
NOTIFICATION_EMAILS=admin@tlciscreative.com,sales@tlciscreative.com
```

### Render Deployment Configuration

The `render.yaml` file configures all required variables as secrets:

```yaml
envVarsFrom:
  - key: QUOTER_CLIENT_ID
    fromSecret: true
  - key: QUOTER_CLIENT_SECRET
    fromSecret: true
  - key: QUOTER_REDIRECT_URI
    fromSecret: true
  - key: PIPEDRIVE_API_TOKEN
    fromSecret: true
  - key: QBO_CLIENT_ID
    fromSecret: true
  - key: QBO_CLIENT_SECRET
    fromSecret: true
  - key: QBO_REDIRECT_URI
    fromSecret: true
  - key: QBO_REALM_ID
    fromSecret: true
  - key: GMAIL_USER
    fromSecret: true
  - key: GMAIL_APP_PASSWORD
    fromSecret: true
  - key: NOTIFICATION_EMAILS
    fromSecret: true
```

## API Integration Details

### Quoter API Integration
```python
def get_quoter_products():
    """Fetch all products from Quoter API with pagination"""
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    all_products = []
    page = 1
    while True:
        url = f"https://api.quoter.com/v1/items?page={page}&per_page=100"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            break
            
        data = response.json()
        products = data.get("data", [])
        if not products:
            break
            
        all_products.extend(products)
        page += 1
    
    return all_products
```

### Pipedrive API Integration
```python
def get_pipedrive_products_by_quoter_items(quoter_items):
    """Get Pipedrive products matching Quoter items by supplier_sku"""
    pipedrive_token = os.getenv("PIPEDRIVE_API_TOKEN")
    url = "https://api.pipedrive.com/v1/products"
    params = {"api_token": pipedrive_token, "limit": 100}
    
    all_products = []
    while True:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code != 200:
            break
            
        data = response.json()
        products = data.get("data", [])
        if not products:
            break
            
        all_products.extend(products)
        
        # Check pagination
        pagination = data.get("additional_data", {}).get("pagination", {})
        if not pagination.get("more_items_in_collection", False):
            break
        params["start"] = pagination.get("next_start", params["start"] + 100)
    
    # Find matches by supplier_sku
    matching_products = []
    quoter_supplier_skus = {item.get("supplier_sku") for item in quoter_items}
    
    for product in all_products:
        if str(product.get("id")) in quoter_supplier_skus:
            matching_products.append(product)
    
    return matching_products
```

### QuickBooks Online API Integration
```python
def get_qbo_items_by_quoter_items(quoter_items):
    """Get QBO items matching Quoter items by name"""
    qbo_client = QBOClient()
    all_items = qbo_client.get_existing_items()
    
    if not all_items:
        return []
    
    # Find matches by name
    matching_items = []
    quoter_names = {item.get("name") for item in quoter_items}
    
    for item in all_items:
        if item.get("Name") in quoter_names:
            matching_items.append(item)
    
    return matching_items
```

## Category Management Integration

### Quoter Category Hierarchy
```python
def get_category_path_from_item(item_data):
    """Get complete category path from Quoter Categories API"""
    category_id = item_data.get('category_id')
    if not category_id:
        return None
    
    # Query Categories API for full hierarchy
    url = f"https://api.quoter.com/v1/categories/{category_id}"
    response = requests.get(url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        category_data = response.json()
        current_category_name = category_data.get('name', 'Unknown')
        parent_category = category_data.get('parent_category')
        
        if parent_category:
            return f"{parent_category} / {current_category_name}"
        else:
            return current_category_name
    
    return None
```

### Pipedrive Category Mapping
```python
def get_pipedrive_categories():
    """Get Pipedrive category ID to name mapping"""
    pipedrive_token = os.getenv("PIPEDRIVE_API_TOKEN")
    url = "https://api.pipedrive.com/v1/productFields"
    params = {"api_token": pipedrive_token}
    
    response = requests.get(url, params=params, timeout=30)
    if response.status_code == 200:
        data = response.json()
        categories = {}
        for field in data.get("data", []):
            if field.get("key") == "category":
                options = field.get("options", [])
                for option in options:
                    categories[option["label"]] = option["id"]
        return categories
    
    return {}
```

## Error Handling and Logging

### Comprehensive Error Handling
```python
try:
    # Report generation logic
    quoter_items = get_new_quoter_items_since(last_sync_date)
    pipedrive_products = get_pipedrive_products_by_quoter_items(quoter_items)
    qbo_items = get_qbo_items_by_quoter_items(quoter_items)
    
    # Generate and send report
    success = notifier.send_notifications()
    
except requests.exceptions.RequestException as e:
    logger.error(f"❌ Network error: {str(e)}")
    notifier.add_error(str(e), "Network")
except Exception as e:
    logger.error(f"❌ Unexpected error: {str(e)}")
    notifier.add_error(str(e), "System")
```

### Graceful Degradation
- **Missing Quoter Items**: Skip report generation
- **API Failures**: Log error but continue with available data
- **Network Issues**: Timeout after 30 seconds, log and continue
- **Invalid Data**: Validate inputs before processing

### Logging Levels
- **INFO**: Successful operations and normal flow
- **WARNING**: Missing configuration or non-critical failures
- **ERROR**: Critical failures requiring attention
- **DEBUG**: Detailed troubleshooting information

## Testing and Validation

### Test Scripts
Located in project root:

#### **Full Report Test**
```bash
python detailed_sync_notification.py
```
- Tests complete report generation
- Validates all API integrations
- Confirms email delivery

#### **Individual Component Tests**
```bash
# Test Quoter filtering
python -c "
from detailed_sync_notification import get_new_quoter_items_since, get_last_sync_date
last_sync = get_last_sync_date()
items = get_new_quoter_items_since(last_sync)
print(f'Found {len(items)} Quoter items')
"

# Test Pipedrive mapping
python -c "
from detailed_sync_notification import get_pipedrive_products_by_quoter_items
# Test with sample Quoter items
"

# Test QBO mapping
python -c "
from detailed_sync_notification import get_qbo_items_by_quoter_items
# Test with sample Quoter items
"
```

### Production Testing
```python
# Test with real data
from detailed_sync_notification import main
main()  # Generates and sends actual report
```

## Deployment and Configuration

### Render Environment Setup
1. **Add Secrets**: Configure all 11 environment variables in Render dashboard
2. **Deploy**: Push code changes trigger automatic deployment
3. **Verify**: Test report generation after deployment

### Local Development Setup
1. **Environment File**: Create `.env` with all required variables
2. **Dependencies**: Install requirements with `pip install -r requirements.txt`
3. **Testing**: Run test scripts to validate configuration

### Scheduled Execution
The report can be scheduled to run daily using:
- **GitHub Actions**: Automated daily execution
- **Cron Jobs**: Local server scheduling
- **Render Cron**: Cloud-based scheduling

## Monitoring and Maintenance

### Log Monitoring
- **Render Logs**: Check for API failures and errors
- **Email Delivery**: Verify Gmail app password doesn't expire
- **API Limits**: Monitor Quoter, Pipedrive, and QBO API usage

### Data Validation
- **Quoter Items**: Verify date filtering accuracy
- **Pipedrive Mapping**: Confirm supplier_sku matching
- **QBO Mapping**: Validate name-based matching
- **Category Resolution**: Check category hierarchy accuracy

## Troubleshooting Guide

### Common Issues

#### **No Quoter Items Found**
- **Symptom**: Report shows 0 Quoter items
- **Cause**: Date filtering too restrictive or no changes today
- **Solution**: 
  1. Check `last_sync_date.txt` content
  2. Verify Quoter API connectivity
  3. Confirm items exist for the target date

#### **Pipedrive Products Not Found**
- **Symptom**: 0 Pipedrive products despite Quoter items
- **Cause**: supplier_sku mapping failure
- **Solution**:
  1. Verify Quoter `sku` field contains Pipedrive product IDs
  2. Check Pipedrive API connectivity
  3. Confirm product IDs exist in Pipedrive

#### **QBO Items Not Found**
- **Symptom**: 0 QBO items despite Quoter items
- **Cause**: Name-based mapping failure
- **Solution**:
  1. Verify Quoter item names match QBO item names exactly
  2. Check QBO API connectivity
  3. Confirm items exist in QuickBooks

#### **Email Not Sending**
- **Symptom**: Report generation succeeds but no email received
- **Cause**: Gmail SMTP configuration issue
- **Solution**:
  1. Verify Gmail app password is valid
  2. Check `GMAIL_USER` and `NOTIFICATION_EMAILS` configuration
  3. Test SMTP connectivity

### Debug Commands
```bash
# Test individual components
python -c "
from detailed_sync_notification import get_last_sync_date
print(f'Last sync date: {get_last_sync_date()}')
"

# Test Quoter API
python -c "
from quoter import get_quoter_products
products = get_quoter_products()
print(f'Quoter products: {len(products)}')
"

# Test Pipedrive API
python -c "
from pipedrive import get_pipedrive_products
products = get_pipedrive_products()
print(f'Pipedrive products: {len(products)}')
"

# Test QBO API
python -c "
from quoter_to_qbo_sync import QBOClient
qbo = QBOClient()
items = qbo.get_existing_items()
print(f'QBO items: {len(items)}')
"
```

## Security Considerations

### Credential Management
- **Environment Variables**: All secrets stored as Render environment variables
- **No Hardcoding**: No credentials in source code
- **Secure Transmission**: HTTPS for all API communications
- **Access Control**: Limited to necessary team members

### Data Privacy
- **Minimal Data**: Only necessary product information included
- **No Sensitive Info**: No passwords or internal data in reports
- **Audit Trail**: All report generation logged for compliance

## Performance and Scalability

### Optimization Features
- **Smart Filtering**: Only processes changed items
- **Efficient Mapping**: Uses set operations for fast lookups
- **Pagination**: Handles large datasets efficiently
- **Memory Efficient**: Minimal memory footprint

### Scalability Considerations
- **Rate Limiting**: Respects API rate limits
- **Batch Processing**: Can handle multiple items efficiently
- **Error Recovery**: Failed API calls don't block report generation
- **Monitoring**: Built-in logging for performance tracking

## Future Enhancements

### Planned Improvements
1. **Report Templates**: Customizable email templates
2. **Additional Filters**: Date range filtering options
3. **Rich Formatting**: Enhanced HTML tables and styling
4. **Analytics**: Report generation and delivery metrics
5. **Retry Logic**: Automatic retry for failed API calls

### Advanced Features
- **Conditional Reports**: Rule-based report triggers
- **Multi-language Support**: Localized report content
- **Export Options**: CSV/Excel export functionality
- **Webhook Integration**: Real-time report triggers

## Integration Points

### GitHub Actions Integration
```yaml
# .github/workflows/daily-product-report.yml
name: Daily Product Report
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily
  workflow_dispatch:

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Generate Daily Report
        run: python detailed_sync_notification.py
        env:
          QUOTER_CLIENT_ID: ${{ secrets.QUOTER_CLIENT_ID }}
          # ... other environment variables
```

### Manual Execution
```bash
# Run report manually
python detailed_sync_notification.py

# Test with specific date
python -c "
from detailed_sync_notification import main
main()
"
```

## Maintenance and Updates

### Regular Maintenance
- **Daily**: Monitor report generation and delivery
- **Weekly**: Verify API credentials and connectivity
- **Monthly**: Review report content and formatting
- **Quarterly**: Audit security and access controls

### Update Procedures
- **Code Changes**: Test locally before deploying
- **Configuration Changes**: Update Render environment variables
- **New Fields**: Add to mapping logic and test thoroughly
- **API Changes**: Update integration code and test

---

**Status:** ✅ **PRODUCTION READY**  
**Last Updated:** September 7, 2025  
**Deployment:** Render Cloud Platform  
**Report Type:** Daily Product / Item Report  
**Systems:** Quoter, Pipedrive, QuickBooks Online
