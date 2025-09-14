# Template Line Items Solution

**Last Updated:** September 13, 2025  
**Version:** 2.0 (Production Ready - 11 Templates)

## Overview

This document describes the complete solution for the Quoter API limitation where templates accept a `template_id` but ignore template line items during quote creation. The solution implements a template mapping system that automatically retrieves and adds template-specific line items to draft quotes.

## The Problem

### Quoter API Limitation

When creating quotes via the Quoter API, we discovered a critical limitation:

1. **Templates accept `template_id`** but **ignore template line items** during quote creation
2. **Template line items are NOT automatically populated** when creating quotes from templates
3. **Quoter API doesn't expose template line items** for direct retrieval
4. **Manual line item addition is required** after quote creation

### Impact on Quote Creation

Without this solution:
- ✅ Quotes are created with correct template styling/layout
- ❌ Template-specific line items are missing
- ❌ Quotes lack the intended content and pricing
- ❌ Manual intervention required for each quote

## The Solution: Template Mapping System

### Core Architecture

```
Pipedrive Webhook → Webhook Handler → Quote Creation → Template Mapping → Line Item Addition
       ↓                    ↓              ↓                ↓                    ↓
   Deal Data         Template Selection  Quote Created   Template Lookup    Items Added
```

### System Components

#### 1. Template Mapping System (`template_mapping.py`)

**Purpose:** Defines which line items should be added to quotes based on the selected template.

**Key Features:**
- Template-specific line item definitions using Quoter item IDs
- Cover letter and appended content support
- Bundle concept for related items
- Fallback to default instructional items

**Example Template Bundle:**
```python
"Floating Video": {
    "parent_category": "Hologram",
    "child_categories": ["FV", "FV-Graphics"],
    "cover_letter": "Thank you for your interest in our floating video holographic package...",
    "appended_content": "This package includes holographic fans in various sizes...",
    "line_items": [
        {
            "item_id": "item_30LOcZVgitq6sXrFcy0HxeAY1xO",
            "name": "FV-Standard Graphics Pkg",
            "category": "FV",
            "quantity": 1
        }
    ]
}
```

#### 2. Enhanced Quote Creation (`quoter.py`)

**Purpose:** Integrates template mapping with the quote creation process.

**Key Functions:**
- `get_template_name_from_id()` - Resolves template ID to template name
- `add_default_instructional_item()` - Fallback for unmapped templates
- `create_comprehensive_quote_from_pipedrive()` - Main quote creation with line items

**Integration Flow:**
```python
# Step 1: Create quote with template
quote_data = {
    "contact_id": contact_id,
    "template_id": template_id,
    "currency_abbr": "USD",
    "name": f"Quote for {org_name}"
}

# Step 2: Add template-specific line items
template_name = get_template_name_from_id(template_id, access_token)
success = add_template_line_items_to_quote(quote_id, template_name, access_token)
```

#### 3. Webhook Handler Integration (`webhook_handler.py`)

**Purpose:** Automatically triggers template line item addition during quote creation.

**Integration Points:**
- Uses `create_comprehensive_quote_from_pipedrive()` function
- Automatically adds template line items after quote creation
- Provides fallback to default instructional items

## Implementation Details

### 1. Template Name Resolution

**Function:** `get_template_name_from_id(template_id, access_token)`

**Process:**
1. Fetch all available templates from Quoter API
2. Match template ID to template name
3. Return template name for mapping lookup

**Code:**
```python
def get_template_name_from_id(template_id, access_token):
    response = requests.get(
        "https://api.quoter.com/v1/quote_templates",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    templates = response.json().get("data", [])
    for template in templates:
        if template.get("id") == template_id:
            return template.get("name") or template.get("title")
    return None
```

### 2. Template Line Item Addition

**Function:** `add_template_line_items_to_quote(quote_id, template_name, access_token)`

**Process:**
1. Get template bundle from mapping system
2. Retrieve line items for template
3. Add each line item to quote using Quoter API
4. Use item IDs for accurate pricing and details

**Code:**
```python
def add_template_line_items_to_quote(quote_id, template_name, access_token):
    line_items = get_template_line_items(template_name)
    
    for item in line_items:
        if "item_id" in item:
            # Get item details from Quoter API
            item_response = requests.get(
                f"https://api.quoter.com/v1/items/{item['item_id']}",
                headers=headers
            )
            
            # Add line item to quote
            line_item_data = {
                "quote_id": quote_id,
                "item_id": item["item_id"],
                "quantity": item.get("quantity", 1)
            }
            
            response = requests.post(
                "https://api.quoter.com/v1/line_items",
                json=line_item_data,
                headers=headers
            )
```

### 3. Fallback System

**Function:** `add_default_instructional_item(quote_id, access_token)`

**Purpose:** Provides fallback when template mapping is not available.

**Features:**
- Uses existing instructional item from Quoter
- Adds completion instructions to draft quotes
- Ensures all quotes have at least one line item

**Code:**
```python
def add_default_instructional_item(quote_id, access_token):
    existing_item_id = "item_31IIdw4C1GHIwU05yhnZ2B88S2B"
    
    # Get item details and add to quote
    item_response = requests.get(f'https://api.quoter.com/v1/items/{existing_item_id}')
    item_data = item_response.json()
    
    line_item_data = {
        "quote_id": quote_id,
        "item_id": existing_item_id,
        "name": item_data.get('name'),
        "category": item_data.get('category'),
        "quantity": 1,
        "unit_price": 1.00
    }
    
    requests.post('https://api.quoter.com/v1/line_items', json=line_item_data)
```

## API Endpoints Used

### Quote Creation
```
POST https://api.quoter.com/v1/quotes
```

### Line Item Addition
```
POST https://api.quoter.com/v1/line_items
```

### Item Retrieval
```
GET https://api.quoter.com/v1/items/{item_id}
```

### Template Information
```
GET https://api.quoter.com/v1/quote_templates
```

## Integration Workflow

### 1. Webhook Trigger
```
Pipedrive Webhook → webhook_handler.py → create_comprehensive_quote_from_pipedrive()
```

### 2. Quote Creation Process
```
1. Extract deal and organization data
2. Create contact in Quoter
3. Select template based on deal custom field
4. Create quote with template_id
5. Resolve template_id to template_name
6. Add template-specific line items
7. Fallback to default instructional item if needed
```

### 3. Template Mapping Lookup
```
template_id → get_template_name_from_id() → template_name → get_template_bundle() → line_items
```

### 4. Line Item Addition
```
For each line_item in template_bundle:
  1. Get item details from Quoter API
  2. Create line item data
  3. POST to /v1/line_items
  4. Verify success
```

## Current Template Mappings

The system now supports **11 comprehensive templates** with **244 total items**:

### Production Templates:

#### 1. Floating Video Template
- **Template Name:** "Floating Video"
- **Items:** 22 items (13 FV hardware + 9 universal T&E/shipping)
- **Categories:** FV, FV-Graphics, Labor, Shipping, T&E
- **Total Value:** $39,895.00

#### 2. LED Wristbands Template
- **Template Name:** "LED Wristbands"
- **Items:** 27 items (18 template-specific + 9 universal)
- **Categories:** Wristbands, Branding, Control Systems, Labor
- **Total Value:** $8,812.00

#### 3. Balloons Template
- **Template Name:** "Balloons"
- **Items:** 16 items (7 balloon hardware + 9 universal)
- **Categories:** Balloons, Labor, Shipping, T&E
- **Total Value:** $6,320.00

#### 4. CO2/Smoke/Upright Foggers Template
- **Template Name:** "CO2/Smoke/Upright Foggers"
- **Items:** 20 items (11 fogger equipment + 9 universal)
- **Categories:** CO2, Tanks, Additional, Labor
- **Total Value:** $6,845.00

#### 5. Confetti/Streamers Template
- **Template Name:** "Confetti/Streamers"
- **Items:** 22 items (13 effects hardware + 9 universal)
- **Categories:** Hardware, Confetti/Streamers, Additional, Labor
- **Total Value:** $6,645.00

#### 6. Fireworks/Pyro/Fire Template
- **Template Name:** "Fireworks/Pyro/Fire"
- **Items:** 25 items (16 pyro equipment + 9 universal)
- **Categories:** Firework/Pyrotechnic, Fire Effects, Labor
- **Total Value:** $11,745.00

#### 7. LED Lanyards Template
- **Template Name:** "LED Lanyards"
- **Items:** 23 items (14 lanyard equipment + 9 universal)
- **Categories:** LED Lanyards, Programming, Branding, Labor
- **Total Value:** $8,695.00

#### 8. Basic Template
- **Template Name:** "Basic"
- **Items:** 10 items (1 instructional + 9 universal)
- **Categories:** Rental Items, Shipping, T&E
- **Total Value:** $2,445.00

#### 9. Low Level Fog Template
- **Template Name:** "Low Level Fog"
- **Items:** 18 items (9 fog equipment + 9 universal)
- **Categories:** Hardware, CO2 tanks, Additional items, Labor
- **Total Value:** $5,870.00

#### 10. Robotics Template
- **Template Name:** "Robotics"
- **Items:** 40 items (31 robotic equipment + 9 universal)
- **Categories:** Robot packages, Robot Dog, Robot (Not Dog), Robot Branding, Additional Options, Services - Labor
- **Total Value:** $33,595.00

#### 11. Tank Delivery Template
- **Template Name:** "Tank Delivery"
- **Items:** 21 items (12 tank services + 9 universal)
- **Categories:** Tanks, Shipping, Additional Items
- **Total Value:** $5,995.00

### Universal Bundle (Included with All Templates)
- **Items:** 9 standard items
- **Categories:** Shipping, T&E (Buyout, Baggage, Flights, Ground, Meals, Parking, Per Diem, Rooms)
- **Total Value:** $2,445.00 per template

## Testing and Validation

### Test Script
**File:** `test_template_line_items.py`

**Purpose:** Comprehensive testing of the template mapping system.

**Test Coverage:**
1. Access token validation
2. Template name resolution
3. Template mapping lookup
4. Quote creation with line items
5. Fallback system verification

**Usage:**
```bash
python test_template_line_items.py
```

### Test Results
- ✅ Template name resolution works correctly
- ✅ Template mapping system retrieves line items
- ✅ Line items are added to quotes successfully
- ✅ Fallback system provides default instructional item
- ✅ Integration with webhook handler is seamless

## Error Handling and Logging

### Comprehensive Error Handling
- API call failures are caught and logged
- Template mapping failures fall back to default items
- Line item addition failures are reported but don't stop quote creation
- All errors include detailed logging for troubleshooting

### Logging Levels
- **INFO:** Successful operations and normal flow
- **WARNING:** Non-critical issues and fallbacks
- **ERROR:** API failures and critical errors
- **DEBUG:** Detailed troubleshooting information

### Error Recovery
- Failed template mapping → Default instructional item
- Failed line item addition → Continue with other items
- Failed quote creation → Return error to webhook handler
- API timeout → Retry with exponential backoff

## Performance Considerations

### API Efficiency
- Template information is cached during quote creation
- Item details are fetched only when needed
- Batch processing for multiple line items
- Minimal API calls per quote creation

### Rate Limiting
- Respects Quoter API rate limits
- Implements delays between API calls
- Uses exponential backoff for retries
- Monitors API usage and limits

## Security Considerations

### Data Privacy
- Only template names and item IDs are stored in mapping
- No sensitive template content is logged
- API tokens are handled securely
- Template data is validated before use

### Access Control
- Template mapping is read-only
- No modification of Quoter templates
- Safe fallback to default items
- Error boundaries prevent system crashes

## Maintenance and Updates

### Adding New Templates
1. Define template bundle in `template_mapping.py`
2. Include line items with Quoter item IDs
3. Add cover letter and appended content if needed
4. Test with `test_template_line_items.py`
5. Deploy and monitor

### Updating Existing Templates
1. Modify template bundle in `template_mapping.py`
2. Update line items, cover letters, or content
3. Test changes with existing quotes
4. Deploy updates
5. Verify in production

### Monitoring
- Check quote creation logs for template mapping success
- Monitor line item addition success rates
- Track fallback usage patterns
- Review error logs for issues

## Benefits of This Solution

### 1. Solves API Limitation
- ✅ Works around Quoter's template restrictions
- ✅ Provides template line items automatically
- ✅ Maintains template styling and layout

### 2. Flexible and Maintainable
- ✅ Easy to add new templates
- ✅ Clear separation of concerns
- ✅ Comprehensive error handling
- ✅ Detailed logging and monitoring

### 3. Reliable and Accurate
- ✅ Uses Quoter item IDs for precise pricing
- ✅ Handles API failures gracefully
- ✅ Provides fallback for unmapped templates
- ✅ Validates all data before use

### 4. Production Ready
- ✅ Integrated with webhook handler
- ✅ Tested and validated
- ✅ Comprehensive documentation
- ✅ Error recovery and monitoring

## Future Enhancements

### 1. Advanced Template Management
- Template categorization and filtering
- Template versioning and history
- Bulk template operations
- Template usage analytics

### 2. Enhanced Integration
- Real-time template sync via webhooks
- Template validation against Quoter data
- Custom template validation rules
- Template optimization suggestions

### 3. Performance Improvements
- Template data caching
- Parallel line item processing
- Batch API operations
- Optimized API call patterns

## Troubleshooting Guide

### Common Issues

#### Template Not Found
- **Symptom:** Template name resolution fails
- **Cause:** Template ID not found in Quoter API
- **Solution:** Verify template exists and API access is correct

#### Line Items Not Added
- **Symptom:** Quote created but no line items
- **Cause:** Template mapping not found or API failure
- **Solution:** Check template mapping and API connectivity

#### API Authentication Errors
- **Symptom:** 401/403 errors during API calls
- **Cause:** Invalid or expired access token
- **Solution:** Verify API credentials and token refresh

### Debug Commands
```bash
# Test template mapping system
python test_template_line_items.py

# Check available templates
python -c "from template_mapping import get_all_template_names; print(get_all_template_names())"

# Verify API connectivity
python -c "from quoter import get_access_token; print('Token:', get_access_token()[:20] if get_access_token() else 'None')"
```

### Log Analysis
```bash
# Check for template mapping errors
grep -i "template.*mapping" logs/

# Monitor line item addition success
grep -i "line.*item.*added" logs/

# Review fallback usage
grep -i "default.*instructional" logs/
```

## Conclusion

The Template Line Items Solution successfully addresses the Quoter API limitation by implementing a comprehensive template mapping system. The solution:

- ✅ **Automatically adds template-specific line items** to draft quotes
- ✅ **Maintains template styling and layout** from Quoter
- ✅ **Provides reliable fallback** for unmapped templates
- ✅ **Integrates seamlessly** with the webhook handler
- ✅ **Includes comprehensive error handling** and logging
- ✅ **Is production-ready** with testing and validation

The system is now ready to automatically populate draft quotes with the correct template line items, eliminating the need for manual intervention and ensuring consistent quote content across all template types.

---

**Status:** ✅ **PRODUCTION READY**  
**Last Updated:** September 10, 2025  
**Integration:** Quoter ↔ Pipedrive Template Line Items System  
**Testing:** Comprehensive test suite available
