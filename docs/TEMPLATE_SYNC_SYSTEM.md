# Template Sync System Documentation

**Last Updated:** September 7, 2025  
**Version:** 1.0 (Production Ready)

## Overview

The Template Sync System automatically synchronizes Quoter quote templates with Pipedrive custom enum fields, enabling dynamic template selection during quote creation. The system ensures that new templates created in Quoter are automatically available in Pipedrive deal custom fields, and provides intelligent template selection logic for the webhook handler.

## System Architecture

```
Quoter Templates → Template Sync System → Pipedrive Enum Field
       ↓                    ↓                    ↓
   API Fetch          Smart Detection      Custom Field Update
       ↓                    ↓                    ↓
┌─────────────────────────────────────────────────────────────┐
│                GitHub Actions Automation                   │
│              (Twice Daily + Manual Trigger)                │
└─────────────────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────────────────┐
│              Webhook Handler Integration                   │
│            (Dynamic Template Selection)                    │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Template Synchronization Scripts

#### **`sync_templates_to_pipedrive.py`** - Main Sync Script
- **Purpose**: Primary script for syncing Quoter templates to Pipedrive
- **Functionality**: 
  - Fetches all templates from Quoter API
  - Compares with existing Pipedrive enum options
  - Adds new templates to Pipedrive enum field
  - Handles duplicate detection and case changes
- **Usage**: `python sync_templates_to_pipedrive.py`

#### **`auto_sync_templates.py`** - Automated Sync Utility
- **Purpose**: Enhanced sync utility with error handling and logging
- **Functionality**:
  - Class-based approach for better organization
  - Comprehensive error handling and retry logic
  - Detailed logging and status reporting
  - Token management and API validation
- **Usage**: `python auto_sync_templates.py`

### 2. Template Selection Logic

#### **`debug_files/template_selection_logic.py`** - Dynamic Selection
- **Purpose**: Provides template selection logic for webhook handler
- **Key Functions**:
  - `get_template_id_by_name()` - Lookup template ID by name
  - `get_template_selection_from_deal()` - Extract from Pipedrive deal
  - `select_template_for_quote()` - Main selection logic with fallbacks

### 3. GitHub Actions Automation

#### **`.github/workflows/smart-template-sync.yml`** - Automated Sync
- **Schedule**: Twice daily (2 AM PT and 2 PM PT)
- **Manual Trigger**: Available via GitHub Actions interface
- **Features**:
  - Automatic template detection and sync
  - Change detection and logging
  - Error handling and notifications
  - Full history comparison for accuracy

## Template Selection Process

### 1. Dynamic Template Selection Flow

```python
def select_template_for_quote(deal_id, access_token):
    """
    Select template for quote creation based on deal custom field
    """
    # Step 1: Get template selection from Pipedrive deal
    template_selection = get_template_selection_from_deal(deal_id)
    
    if template_selection:
        # Step 2: Lookup template ID by name
        template_id = get_template_id_by_name(template_selection, access_token)
        
        if template_id:
            return template_id
    
    # Step 3: Fallback to default template
    return get_default_template_id(access_token)
```

### 2. Pipedrive Custom Field Integration

#### **Enum Field Configuration**
- **Field ID**: `90` (Quote Template)
- **Field Type**: Custom enum field
- **Options**: Dynamically populated from Quoter templates
- **Format**: Template names as display values

#### **Deal Custom Field Mapping**
```python
def get_template_selection_from_deal(deal_id):
    """Extract template selection from Pipedrive deal custom field"""
    deal_data = get_deal_by_id(deal_id)
    custom_fields = deal_data.get("custom_fields", {})
    
    # Look for template selection in custom fields
    for field_key, field_value in custom_fields.items():
        if field_value and isinstance(field_value, str):
            # Check if this looks like a template name
            if is_valid_template_name(field_value):
                return field_value
    
    return None
```

### 3. Template ID Resolution

#### **Quoter API Integration**
```python
def get_template_id_by_name(template_name, access_token):
    """Get template ID by name from Quoter API"""
    url = "https://api.quoter.com/v1/quote_templates"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    templates = response.json().get("data", [])
    
    for template in templates:
        if template.get("name") == template_name:
            return template.get("id")
    
    return None
```

## Synchronization Process

### 1. Template Detection

#### **Quoter Template Fetching**
```python
def get_quoter_templates(access_token):
    """Fetch all templates from Quoter API"""
    url = "https://api.quoter.com/v1/quote_templates"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    return response.json().get("data", [])
```

#### **Pipedrive Enum Field Fetching**
```python
def get_pipedrive_enum_options(field_id, api_token):
    """Get current enum options from Pipedrive"""
    url = f"https://api.pipedrive.com/v1/productFields/{field_id}"
    params = {"api_token": api_token}
    
    response = requests.get(url, params=params)
    field_data = response.json().get("data", {})
    return field_data.get("options", [])
```

### 2. Change Detection

#### **Smart Comparison Logic**
```python
def detect_template_changes(quoter_templates, pipedrive_options):
    """Detect new templates and changes"""
    quoter_names = {template["name"] for template in quoter_templates}
    pipedrive_names = {option["label"] for option in pipedrive_options}
    
    # Find new templates
    new_templates = quoter_names - pipedrive_names
    
    # Find case changes (same name, different case)
    case_changes = []
    for quoter_name in quoter_names:
        for pipedrive_name in pipedrive_names:
            if quoter_name.lower() == pipedrive_name.lower() and quoter_name != pipedrive_name:
                case_changes.append((pipedrive_name, quoter_name))
    
    return new_templates, case_changes
```

### 3. Enum Field Updates

#### **Adding New Templates**
```python
def add_template_to_pipedrive(template_name, field_id, api_token):
    """Add new template to Pipedrive enum field"""
    url = f"https://api.pipedrive.com/v1/productFields/{field_id}/options"
    params = {"api_token": api_token}
    data = {"label": template_name}
    
    response = requests.post(url, params=params, json=data)
    return response.status_code == 201
```

#### **Updating Case Changes**
```python
def update_template_case(old_name, new_name, field_id, api_token):
    """Update template name case in Pipedrive"""
    # Find the option ID for the old name
    option_id = get_option_id_by_name(old_name, field_id, api_token)
    
    if option_id:
        # Update the option with new name
        url = f"https://api.pipedrive.com/v1/productFields/{field_id}/options/{option_id}"
        params = {"api_token": api_token}
        data = {"label": new_name}
        
        response = requests.put(url, params=params, json=data)
        return response.status_code == 200
    
    return False
```

## GitHub Actions Configuration

### 1. Workflow Structure

```yaml
name: Smart Template Sync

on:
  # Manual trigger with options
  workflow_dispatch:
    inputs:
      check_quoter:
        description: 'Check Quoter for new templates'
        required: false
        default: 'true'
        type: boolean
  
  # Twice daily schedule
  schedule:
    - cron: '0 10 * * *'  # 2 AM PT (10 AM UTC)
    - cron: '0 22 * * *'  # 2 PM PT (10 PM UTC)

jobs:
  check-and-sync:
    runs-on: ubuntu-latest
    # ... workflow steps
```

### 2. Environment Variables

```yaml
env:
  QUOTER_CLIENT_ID: ${{ secrets.QUOTER_CLIENT_ID }}
  QUOTER_CLIENT_SECRET: ${{ secrets.QUOTER_CLIENT_SECRET }}
  QUOTER_REDIRECT_URI: ${{ secrets.QUOTER_REDIRECT_URI }}
  PIPEDRIVE_API_TOKEN: ${{ secrets.PIPEDRIVE_API_TOKEN }}
```

### 3. Workflow Steps

1. **Checkout Code** - Get latest repository
2. **Set up Python** - Configure Python 3.9 environment
3. **Install Dependencies** - Install required packages
4. **Run Template Sync** - Execute synchronization script
5. **Log Results** - Report changes and status

## Webhook Handler Integration

### 1. Template Selection in Quote Creation

#### **Webhook Handler Integration**
```python
# In webhook_handler.py
def create_quote_with_template(deal_id, organization_id):
    """Create quote with dynamic template selection"""
    # Get template selection from deal custom field
    template_id = select_template_for_quote(deal_id, access_token)
    
    if template_id:
        # Create quote with selected template
        quote_data = {
            "organization_id": organization_id,
            "template_id": template_id,
            "status": "draft"
        }
        
        return create_draft_quote(quote_data, access_token)
    
    return None
```

### 2. Fallback Logic

#### **Default Template Selection**
```python
def get_default_template_id(access_token):
    """Get default template ID as fallback"""
    templates = get_quoter_templates(access_token)
    
    # Look for common default templates
    default_names = ["Default", "Standard", "Basic", "Template"]
    
    for template in templates:
        if template.get("name") in default_names:
            return template.get("id")
    
    # Return first available template
    return templates[0].get("id") if templates else None
```

## API Integration Details

### 1. Quoter API Integration

#### **Template Fetching**
```python
def get_quoter_templates(access_token):
    """Fetch all quote templates from Quoter"""
    url = "https://api.quoter.com/v1/quote_templates"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        logger.error(f"❌ Error fetching Quoter templates: {e}")
        return []
```

#### **Template Lookup by Name**
```python
def get_template_id_by_name(template_name, access_token):
    """Get template ID by name from Quoter"""
    templates = get_quoter_templates(access_token)
    
    for template in templates:
        if template.get("name") == template_name:
            return template.get("id")
    
    return None
```

### 2. Pipedrive API Integration

#### **Enum Field Management**
```python
def get_pipedrive_enum_options(field_id, api_token):
    """Get enum field options from Pipedrive"""
    url = f"https://api.pipedrive.com/v1/productFields/{field_id}"
    params = {"api_token": api_token}
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        field_data = data.get("data", {})
        return field_data.get("options", [])
    except Exception as e:
        logger.error(f"❌ Error fetching Pipedrive enum options: {e}")
        return []
```

#### **Adding New Options**
```python
def add_enum_option(field_id, option_name, api_token):
    """Add new option to Pipedrive enum field"""
    url = f"https://api.pipedrive.com/v1/productFields/{field_id}/options"
    params = {"api_token": api_token}
    data = {"label": option_name}
    
    try:
        response = requests.post(url, params=params, json=data, timeout=30)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"❌ Error adding enum option: {e}")
        return False
```

## Error Handling and Logging

### 1. Comprehensive Error Handling

#### **API Error Handling**
```python
def safe_api_call(func, *args, **kwargs):
    """Wrapper for safe API calls with error handling"""
    try:
        return func(*args, **kwargs)
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return None
```

#### **Template Sync Error Handling**
```python
def sync_templates_with_error_handling():
    """Sync templates with comprehensive error handling"""
    try:
        # Initialize tokens
        quoter_token = get_access_token()
        pipedrive_token = os.getenv("PIPEDRIVE_API_TOKEN")
        
        if not quoter_token or not pipedrive_token:
            logger.error("❌ Missing API tokens")
            return False
        
        # Fetch data
        quoter_templates = get_quoter_templates(quoter_token)
        pipedrive_options = get_pipedrive_enum_options("90", pipedrive_token)
        
        # Detect changes
        new_templates, case_changes = detect_template_changes(
            quoter_templates, pipedrive_options
        )
        
        # Apply changes
        success = apply_template_changes(
            new_templates, case_changes, pipedrive_token
        )
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Template sync failed: {e}")
        return False
```

### 2. Logging Configuration

#### **Structured Logging**
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('template_sync.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

#### **Log Levels and Messages**
- **INFO**: Successful operations and normal flow
- **WARNING**: Non-critical issues and fallbacks
- **ERROR**: API failures and critical errors
- **DEBUG**: Detailed troubleshooting information

## Testing and Validation

### 1. Test Scripts

#### **Template Selection Tests**
```python
# test_files/test_template_selection.py
def test_template_selection():
    """Test template selection logic"""
    # Test valid template selection
    template_id = get_template_id_by_name("Test Template", access_token)
    assert template_id is not None
    
    # Test invalid template selection
    template_id = get_template_id_by_name("Non-existent Template", access_token)
    assert template_id is None
```

#### **Enum Mapping Tests**
```python
# test_files/test_enum_mapping.py
def test_enum_mapping():
    """Test enum field mapping"""
    # Test adding new template
    success = add_enum_option("90", "New Template", api_token)
    assert success is True
    
    # Test duplicate handling
    success = add_enum_option("90", "New Template", api_token)
    assert success is False  # Should handle duplicates
```

### 2. Validation Procedures

#### **Pre-Sync Validation**
```python
def validate_sync_prerequisites():
    """Validate prerequisites before sync"""
    # Check API tokens
    if not os.getenv("QUOTER_CLIENT_ID"):
        logger.error("❌ Missing QUOTER_CLIENT_ID")
        return False
    
    if not os.getenv("PIPEDRIVE_API_TOKEN"):
        logger.error("❌ Missing PIPEDRIVE_API_TOKEN")
        return False
    
    # Test API connectivity
    if not test_quoter_connection():
        logger.error("❌ Quoter API connection failed")
        return False
    
    if not test_pipedrive_connection():
        logger.error("❌ Pipedrive API connection failed")
        return False
    
    return True
```

#### **Post-Sync Validation**
```python
def validate_sync_results():
    """Validate sync results"""
    # Verify templates were added
    pipedrive_options = get_pipedrive_enum_options("90", api_token)
    quoter_templates = get_quoter_templates(access_token)
    
    quoter_names = {template["name"] for template in quoter_templates}
    pipedrive_names = {option["label"] for option in pipedrive_options}
    
    # Check if all Quoter templates are in Pipedrive
    missing_templates = quoter_names - pipedrive_names
    
    if missing_templates:
        logger.warning(f"⚠️ Missing templates: {missing_templates}")
        return False
    
    logger.info("✅ All templates synchronized successfully")
    return True
```

## Troubleshooting Guide

### 1. Common Issues

#### **Template Not Found Error**
- **Symptom**: `Template not found` error during quote creation
- **Cause**: Template name mismatch between Quoter and Pipedrive
- **Solution**: 
  1. Check template names in both systems
  2. Run template sync to update Pipedrive
  3. Verify template selection logic

#### **API Authentication Errors**
- **Symptom**: `401 Unauthorized` or `403 Forbidden` errors
- **Cause**: Invalid or expired API tokens
- **Solution**:
  1. Verify API tokens in environment variables
  2. Check token expiration dates
  3. Regenerate tokens if necessary

#### **Enum Field Update Failures**
- **Symptom**: Templates not appearing in Pipedrive enum field
- **Cause**: Insufficient permissions or field configuration issues
- **Solution**:
  1. Verify Pipedrive API token permissions
  2. Check field ID is correct
  3. Ensure field is configured as enum type

### 2. Debug Commands

#### **Test Template Selection**
```bash
# Test template selection logic
python debug_files/template_selection_logic.py

# Test with specific deal ID
python -c "
from debug_files.template_selection_logic import select_template_for_quote
template_id = select_template_for_quote('DEAL_ID', access_token)
print(f'Selected template: {template_id}')
"
```

#### **Test Template Sync**
```bash
# Run template sync manually
python sync_templates_to_pipedrive.py

# Run with verbose logging
python auto_sync_templates.py --verbose
```

#### **Check API Connectivity**
```bash
# Test Quoter API
python -c "
from quoter import get_access_token
token = get_access_token()
print(f'Quoter token: {token[:10]}...' if token else 'No token')
"

# Test Pipedrive API
python -c "
import os
token = os.getenv('PIPEDRIVE_API_TOKEN')
print(f'Pipedrive token: {token[:10]}...' if token else 'No token')
"
```

### 3. Monitoring and Alerts

#### **GitHub Actions Monitoring**
- Check workflow runs in GitHub Actions tab
- Review logs for errors and warnings
- Monitor sync frequency and success rates

#### **Log File Monitoring**
```bash
# Check recent sync logs
tail -f template_sync.log

# Search for errors
grep -i "error\|failed" template_sync.log

# Check sync statistics
grep -i "synced\|added" template_sync.log
```

## Performance and Optimization

### 1. Sync Performance

#### **Efficient Change Detection**
- Only sync when changes are detected
- Use set operations for fast comparison
- Cache template data when possible

#### **Batch Operations**
- Group multiple enum field updates
- Use parallel processing for large datasets
- Implement retry logic for failed operations

### 2. API Rate Limiting

#### **Rate Limit Handling**
```python
import time

def rate_limited_api_call(func, *args, **kwargs):
    """API call with rate limiting"""
    try:
        return func(*args, **kwargs)
    except requests.exceptions.TooManyRequests:
        logger.warning("⚠️ Rate limit exceeded, waiting 60 seconds...")
        time.sleep(60)
        return func(*args, **kwargs)
```

#### **Request Throttling**
- Implement delays between API calls
- Use exponential backoff for retries
- Monitor API usage and limits

## Security Considerations

### 1. Credential Management

#### **Environment Variables**
- Store all API tokens as environment variables
- Use GitHub Secrets for CI/CD
- Never commit credentials to repository

#### **Token Rotation**
- Regularly rotate API tokens
- Monitor token expiration dates
- Implement automatic token refresh

### 2. Data Privacy

#### **Template Data Handling**
- Only sync template names (not content)
- Avoid logging sensitive template data
- Implement data retention policies

## Future Enhancements

### 1. Planned Improvements

#### **Advanced Template Management**
- Template categorization and filtering
- Template versioning and history
- Bulk template operations

#### **Enhanced Integration**
- Real-time template sync via webhooks
- Template usage analytics
- Custom template validation rules

### 2. Advanced Features

#### **Template Analytics**
- Track template usage patterns
- Generate template performance reports
- Identify popular and unused templates

#### **Smart Template Suggestions**
- AI-powered template recommendations
- Context-aware template selection
- Template optimization suggestions

## Integration Points

### 1. Webhook Handler Integration

#### **Quote Creation Flow**
1. **Pipedrive Webhook** triggers quote creation
2. **Template Selection** reads deal custom field
3. **Template Lookup** finds template ID in Quoter
4. **Quote Creation** uses selected template
5. **Fallback Logic** uses default template if needed

### 2. GitHub Actions Integration

#### **Automated Sync Flow**
1. **Scheduled Trigger** runs twice daily
2. **Change Detection** compares Quoter vs Pipedrive
3. **Template Sync** updates Pipedrive enum field
4. **Validation** verifies sync results
5. **Logging** records all changes and errors

## Maintenance and Updates

### 1. Regular Maintenance

#### **Daily Tasks**
- Monitor GitHub Actions workflow runs
- Check sync logs for errors
- Verify template synchronization

#### **Weekly Tasks**
- Review template usage patterns
- Update documentation if needed
- Check API token expiration

#### **Monthly Tasks**
- Audit template sync performance
- Review and update error handling
- Plan system improvements

### 2. Update Procedures

#### **Code Changes**
- Test locally before deploying
- Update documentation with changes
- Deploy via GitHub Actions

#### **Configuration Changes**
- Update environment variables
- Test with new configurations
- Monitor for issues

---

**Status:** ✅ **PRODUCTION READY**  
**Last Updated:** September 7, 2025  
**Deployment:** GitHub Actions + Render Webhook Server  
**Integration:** Quoter ↔ Pipedrive Template Synchronization
