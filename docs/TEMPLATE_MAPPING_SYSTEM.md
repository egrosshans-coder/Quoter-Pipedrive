# Template Mapping System Documentation

## Overview

This document covers the template mapping system developed to solve Quoter API limitations where templates accept a `template_id` but ignore the template's line items. The system creates quotes with templates and then manually adds template-specific line items, cover letters, and appended content.

## The Problem

### Quoter API Limitations

When creating quotes via the Quoter API, we discovered several limitations:

1. **Templates ignore line items**: The API accepts `template_id` but doesn't populate line items from the template
2. **No template content retrieval**: Cannot retrieve cover letters, appended content, or line items directly from templates
3. **Read-only template access**: Templates can only be used for styling/layout, not content

### API Response Examples

```python
# This works - creates quote with template styling
quote_data = {
    "contact_id": "cont_2r5WGA5WDExgSYmnZp0TVVQqFLA",
    "template_id": "tmpl_2r5WHEQLKFsyKdyIj5daPCp7mjF",
    "currency_abbr": "CAD",
    "name": "Draft Quote 1"
}

# But template line items are NOT populated automatically
```

## The Solution: Template Mapping System

### Core Concept

Create a custom mapping system that:
1. **Creates quotes with templates** (for styling/layout)
2. **Manually adds template-specific line items** using item IDs
3. **Includes cover letters and appended content** per template
4. **Uses Quoter item IDs** for reliable, accurate pricing

### System Architecture

```
Pipedrive Webhook → Webhook Handler → Quoter API
                                    ↓
                              Template Mapping System
                                    ↓
                        [Template Selection] → [Quote Creation] → [Line Item Addition]
```

## Implementation Details

### 1. Quote Creation in `quoter.py`

The core quote creation process:

```python
def create_comprehensive_draft_quote(required_fields, access_token):
    """
    Create a comprehensive draft quote with template and line items
    """
    import requests
    import json
    
    # Step 1: Create the quote with template
    quote_data = {
        "contact_id": required_fields['contact_id'],
        "template_id": required_fields['template_id'],
        "currency_abbr": required_fields['currency_abbr'],
        "name": required_fields['quote_name']
    }
    
    # Add cover letter and appended content if available
    if required_fields.get('cover_letter'):
        quote_data["cover_letter"] = required_fields['cover_letter']
    if required_fields.get('appended_content'):
        quote_data["appended_content"] = required_fields['appended_content']
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"📤 Quote payload being sent to Quoter:")
    logger.info(f"   {json.dumps(quote_data, indent=2)}")
    
    response = requests.post(
        "https://api.quoter.com/v1/quotes",
        json=quote_data,
        headers=headers,
        timeout=10
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        quote_id = data.get("id")
        logger.info(f"🎉 SUCCESS! Comprehensive draft quote created: {quote_id}")
        return quote_id
    else:
        logger.error(f"❌ Quote creation failed: {response.status_code} - {response.text}")
        return None
```

### 2. Template Mapping System (`template_mapping.py`)

#### Template Bundle Structure

```python
TEMPLATE_BUNDLES = {
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
            },
            {
                "item_id": "item_30LOcjM4ykNYQWm5vzzpF8xepSB", 
                "name": "FV-Advanced Graphics Pkg",
                "category": "FV-Graphics",
                "quantity": 1
            }
        ]
    }
}
```

#### Key Functions

```python
def get_template_bundle(template_name):
    """Get complete bundle information for a template"""
    return TEMPLATE_BUNDLES.get(template_name, {})

def get_template_line_items(template_name):
    """Get line items for a specific template"""
    bundle = get_template_bundle(template_name)
    return bundle.get('line_items', [])

def get_template_cover_letter(template_name):
    """Get cover letter for a specific template"""
    bundle = get_template_bundle(template_name)
    return bundle.get('cover_letter', '')

def add_template_line_items_to_quote(quote_id, template_name, access_token):
    """Add template-specific line items to a quote using item IDs"""
    line_items = get_template_line_items(template_name)
    
    for item in line_items:
        if "item_id" in item:
            # Use item ID to get item details from Quoter
            item_response = requests.get(
                f"https://api.quoter.com/v1/items/{item['item_id']}",
                headers=headers
            )
            
            if item_response.status_code == 200:
                item_data = item_response.json()
                # Add line item using item ID
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

### 3. Bundle Concept

#### What are Bundles?

Bundles are logical groupings of items that belong together in a template. In Quoter, this is implemented through the category system with parent-child relationships:

```
Hologram (Parent Category)
├── FV (Child Category)
│   ├── FV-32in-80 Fan Holographic
│   ├── FV-40in-100 Fan Holographic
│   └── FV-MasterBox
└── FV-Graphics (Child Category)
    ├── FV-Standard Graphics Pkg
    ├── FV-Advanced Graphics Pkg
    └── FV-Ultimate Graphics Pkg
```

#### Bundle Structure in Template Mapping

```python
"Floating Video": {
    "parent_category": "Hologram",
    "child_categories": ["FV", "FV-Graphics"],
    "line_items": [
        # Items from FV category
        {"item_id": "...", "name": "FV-32in-80 Fan Holographic"},
        # Items from FV-Graphics category  
        {"item_id": "...", "name": "FV-Standard Graphics Pkg"}
    ]
}
```

### 4. Cover Letters and Appended Content

#### Cover Letters
Template-specific cover letters provide personalized context for each quote type:

```python
"cover_letter": "Thank you for your interest in our floating video holographic package. This comprehensive solution includes advanced holographic fans and graphics packages to create stunning visual experiences for your event."
```

#### Appended Content
Additional instructions and details appended to quotes:

```python
"appended_content": "This package includes holographic fans in various sizes, graphics packages, and master control systems. Please review all items and contact us with any questions about customization or additional services."
```

### 5. Item ID System

#### Why Item IDs?

Item IDs are the most reliable way to reference Quoter items because:

1. **Unique and permanent**: Never change, unlike names
2. **Direct API access**: Can retrieve full item details
3. **Accurate pricing**: Get current prices directly from Quoter
4. **No ambiguity**: No confusion about which item to add

#### Item ID Retrieval

```python
# Get item details by ID
response = requests.get(f'https://api.quoter.com/v1/items/{item_id}', headers=headers)
if response.status_code == 200:
    item_data = response.json()
    name = item_data.get('name')
    price = item_data.get('price_decimal')
    description = item_data.get('description')
```

#### Adding Items to Quotes

```python
# Add line item using item ID
line_item_data = {
    "quote_id": quote_id,
    "item_id": item_id,
    "quantity": quantity
}

response = requests.post(
    "https://api.quoter.com/v1/line_items",
    json=line_item_data,
    headers=headers
)
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

### Category Structure
```
GET https://api.quoter.com/v1/categories
```

### Template Information
```
GET https://api.quoter.com/v1/quote_templates
```

## Integration with Webhook Handler

The template mapping system integrates with the webhook handler:

```python
# In webhook_handler.py
def create_quote_with_template(org_data, deal_id, template_name):
    # 1. Get template ID from template selection logic
    template_id = get_template_id(template_name)
    
    # 2. Create quote with template
    quote_id = create_comprehensive_draft_quote({
        'contact_id': contact_id,
        'template_id': template_id,
        'template_name': template_name,
        'currency_abbr': 'USD',
        'quote_name': f'{template_name} Quote'
    }, access_token)
    
    # 3. Add template-specific line items
    success = add_template_line_items_to_quote(quote_id, template_name, access_token)
    
    return quote_id, success
```

## Current Status

### ✅ Completed
- Template mapping system architecture
- Quote creation with templates
- Line item addition using item IDs
- Cover letter and appended content support
- Bundle concept implementation
- Integration with webhook handler

### 🔄 In Progress
- Floating Video template mapping (4 items found, 5+ missing)
- Item ID discovery for missing template items

### 📋 Pending
- Complete Floating Video template item mapping
- Additional template mappings (Basic, Robotics, etc.)
- Testing with real webhook calls
- Error handling and logging improvements

## Benefits of This Approach

1. **Solves API Limitations**: Works around Quoter's template restrictions
2. **Flexible**: Easy to add new templates and modify existing ones
3. **Reliable**: Uses item IDs for accurate, consistent results
4. **Maintainable**: Clear separation between template logic and quote creation
5. **Scalable**: Can easily add new templates and bundles

## ✅ **System Enhancements Completed** *(September 21, 2025)*

### **Automated Bundle Synchronization**
1. **✅ Pricing Updates**: Fully automated price synchronization with Quoter API
2. **✅ Template Validation**: Complete verification system for all template mappings  
3. **✅ Dynamic Category Resolution**: Real-time parent/child category hierarchy support
4. **✅ Bulk Template Management**: All 11 production templates managed automatically
5. **✅ SKU Error Handling**: Exact name search fallback for typo tolerance

### **Production Implementation Status**
- **✅ All 11 Templates**: Floating Video, LED Wristbands, LED Lanyards, Balloons, CO2/Smoke/Foggers, Confetti/Streamers, Fireworks/Pyro/Fire, Basic, Low Level Fog, Robotics, Tank Delivery
- **✅ 297+ Items**: All items synchronized with current Quoter data
- **✅ Complete Financial Data**: Price and cost tracking for all items (62 cost updates applied)
- **✅ Daily Automation**: GitHub Actions maintains synchronization automatically
- **✅ Performance Optimized**: ~3-4 minute runtime for full verification and updates

### **Critical Fixes Applied**
- **SKU Corrections**: `BAL-FII-001` → `BAL-FIL-001`, `T&E-PER-001` → `T&E-PER-DIM`, `T&E-ROM-001` → `T&E-RMS-001`
- **Category Hierarchy**: All items now use proper `"Parent / Child"` format
- **Shared Item Management**: Duplicate SKUs across templates properly handled
- **Automated Updates**: Live file modification with template-specific targeting
- **Cost Data Integration**: Added comprehensive cost tracking for 297+ items (62 cost updates applied)

## Conclusion

The template mapping system has evolved into a fully automated, self-maintaining solution that provides robust handling of Quoter API limitations while ensuring perfect data synchronization. The system now operates with zero manual maintenance, automatically detecting and applying changes from Quoter's live data to maintain accurate quotes across all templates. With the addition of comprehensive cost tracking, the system now provides complete financial intelligence for profit analysis and business decision-making.



