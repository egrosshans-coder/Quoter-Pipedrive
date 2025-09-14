# Template Line Items Solution Flow

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TEMPLATE LINE ITEMS SOLUTION                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Pipedrive     │    │   Webhook        │    │   Quoter API    │    │   Template      │
│   Deal Created  │───▶│   Handler        │───▶│   Quote         │───▶│   Mapping       │
│   (HID-QBO-     │    │   Activated      │    │   Creation      │    │   System        │
│   Status =      │    │                  │    │                 │    │                 │
│   QBO-SubCust)  │    │                  │    │                 │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │                        │
                                ▼                        ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                       │   Extract Deal  │    │   Create Quote  │    │   Resolve       │
                       │   & Org Data    │    │   with Template │    │   Template      │
                       │                 │    │   ID            │    │   Name          │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │                        │
                                ▼                        ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                       │   Create        │    │   Get Quote ID  │    │   Get Template  │
                       │   Contact in    │    │   from Creation │    │   Bundle        │
                       │   Quoter        │    │   Response      │    │   (Line Items)  │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │                        │
                                ▼                        ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                       │   Contact ID    │    │   Quote ID      │    │   Template      │
                       │   Ready         │    │   Ready         │    │   Line Items    │
                       │                 │    │                 │    │   Ready         │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │                        │
                                ▼                        ▼                        ▼
                       ┌─────────────────────────────────────────────────────────────────┐
                       │                    LINE ITEM ADDITION                           │
                       │                                                                 │
                       │  For each line_item in template_bundle:                        │
                       │   1. Get item details from Quoter API                          │
                       │   2. Create line item data with quote_id                       │
                       │   3. POST to /v1/line_items                                    │
                       │   4. Verify success and log results                            │
                       │                                                                 │
                       │  If template mapping fails:                                    │
                       │   → Add default instructional item                             │
                       └─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Quote Ready   │
                       │   with Template │
                       │   Line Items    │
                       │                 │
                       │   ✅ Styling    │
                       │   ✅ Content    │
                       │   ✅ Pricing    │
                       └─────────────────┘
```

## Key Components

### 1. Template Mapping System (`template_mapping.py`)
```
TEMPLATE_BUNDLES = {
    "Floating Video": {
        "line_items": [
            {
                "item_id": "item_30LOcZVgitq6sXrFcy0HxeAY1xO",
                "name": "FV-Standard Graphics Pkg",
                "category": "FV",
                "quantity": 1
            }
        ]
    }
}
```

### 2. Enhanced Quote Creation (`quoter.py`)
```
def create_comprehensive_quote_from_pipedrive():
    # Step 1: Create quote with template_id
    quote_data = {
        "contact_id": contact_id,
        "template_id": template_id,
        "currency_abbr": "USD"
    }
    
    # Step 2: Add template line items
    template_name = get_template_name_from_id(template_id, access_token)
    add_template_line_items_to_quote(quote_id, template_name, access_token)
```

### 3. Webhook Integration (`webhook_handler.py`)
```
# Automatically triggers template line item addition
quote_data = create_comprehensive_quote_from_pipedrive(organization_data, deal_data)
```

## API Endpoints Used

### Quote Creation
```
POST https://api.quoter.com/v1/quotes
{
    "contact_id": "cont_xxx",
    "template_id": "tmpl_xxx",
    "currency_abbr": "USD",
    "name": "Quote for Organization"
}
```

### Line Item Addition
```
POST https://api.quoter.com/v1/line_items
{
    "quote_id": "quot_xxx",
    "item_id": "item_xxx",
    "quantity": 1
}
```

### Template Information
```
GET https://api.quoter.com/v1/quote_templates
GET https://api.quoter.com/v1/items/{item_id}
```

## Error Handling & Fallbacks

### Template Mapping Failure
```
Template Not Found → Default Instructional Item
API Error → Continue with Other Items
Network Timeout → Retry with Backoff
```

### Line Item Addition Failure
```
Item Not Found → Skip Item, Log Warning
API Error → Continue with Other Items
Validation Error → Log Error, Continue
```

## Benefits

### ✅ Solves API Limitation
- Templates accept `template_id` but ignore line items
- Manual line item addition required
- Template mapping system provides automation

### ✅ Maintains Template Styling
- Quote uses correct template for layout
- Template-specific line items added automatically
- Cover letters and appended content included

### ✅ Reliable and Accurate
- Uses Quoter item IDs for precise pricing
- Handles API failures gracefully
- Provides fallback for unmapped templates

### ✅ Production Ready
- Integrated with webhook handler
- Comprehensive error handling
- Detailed logging and monitoring
- Tested and validated

## Testing

### Test Script
```bash
python test_template_line_items.py
```

### Test Coverage
- ✅ Template name resolution
- ✅ Template mapping lookup
- ✅ Quote creation with line items
- ✅ Fallback system verification
- ✅ Integration testing

## Current Status

### ✅ Completed
- Template mapping system implementation
- Integration with webhook handler
- Error handling and fallbacks
- Testing and validation
- Documentation

### 🔄 Available Templates
- **Floating Video:** 4 line items with cover letter and appended content
- **Default Fallback:** Instructional item for unmapped templates

### 📋 Ready for Production
- System is fully integrated and tested
- Automatic template line item addition works
- Fallback system provides default items
- Comprehensive error handling in place
