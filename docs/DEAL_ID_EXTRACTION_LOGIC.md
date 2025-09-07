# Deal ID Extraction Logic

**Last Updated:** September 7, 2025  
**Version:** 1.0

## Overview

This document explains the business logic for extracting deal IDs from organization names in the Quoter-Pipedrive integration system. This logic is critical for the notification system to properly identify which Pipedrive deal should receive notifications.

## Business Rule

**Sub-organizations in Pipedrive have their deal ID embedded in their name using the format: `[Organization Name]-[Deal ID]`**

### **Examples:**
- `Blue Owl Capital-2096` → Deal ID: `2096`
- `Wedding Planning Services-1234` → Deal ID: `1234`
- `Corporate Event-5678` → Deal ID: `5678`

## Implementation

### **Code Location**
The logic is implemented in `webhook_handler.py`:

```python
# Get organization name and extract deal ID from the end of the name
organization_name = organization_data.get('name', 'Unknown Organization')
deal_id = None
if organization_name and '-' in organization_name:
    deal_id = organization_name.split('-')[-1]
    logger.info(f"Extracted deal ID: {deal_id} from organization: {organization_name}")
else:
    logger.error(f"Organization {organization_id} name '{organization_name}' does not contain deal ID (expected format: 'Name-DealID')")
    return jsonify({"error": "No deal ID in organization name"}), 400
```

### **Logic Flow**
1. **Get Organization Name** from Pipedrive organization data
2. **Check for Hyphen** in the organization name
3. **Split on Hyphen** and take the last part as deal ID
4. **Validate Deal ID** is numeric
5. **Log Results** for debugging and monitoring

## Use Cases

### **Notification System**
- **Pipedrive Deal Notes:** Create notes in the correct deal
- **Quote Preparation:** Include deal-specific instructions
- **Target Quote Number:** Generate deal-specific quote numbers

### **Quote Creation Process**
1. **Pipedrive Webhook** triggers quote creation
2. **Organization Data** retrieved from Pipedrive
3. **Deal ID Extracted** from organization name
4. **Quote Created** in Quoter system
5. **Notifications Sent** to all channels with deal context

## Error Handling

### **Missing Deal ID**
- **Symptom:** Organization name doesn't contain hyphen
- **Error:** "No deal ID in organization name"
- **Action:** Log error and return 400 status
- **Impact:** Quote creation fails, no notifications sent

### **Invalid Deal ID**
- **Symptom:** Deal ID is not numeric
- **Error:** Deal ID validation fails
- **Action:** Log warning but continue processing
- **Impact:** Notifications may fail for Pipedrive channel

### **Empty Organization Name**
- **Symptom:** Organization name is None or empty
- **Error:** "Unknown Organization"
- **Action:** Use default value and log warning
- **Impact:** Limited notification context

## Validation Rules

### **Format Validation**
```python
# Expected format: "Name-DealID"
# Valid examples:
# - "Blue Owl Capital-2096" ✅
# - "Wedding Planning-1234" ✅
# - "Corporate Event-5678" ✅

# Invalid examples:
# - "Blue Owl Capital" ❌ (no hyphen)
# - "Blue Owl Capital-" ❌ (empty deal ID)
# - "Blue Owl Capital-ABC" ❌ (non-numeric deal ID)
```

### **Deal ID Validation**
- Must be numeric (integers only)
- Should be positive integer
- No leading zeros required
- No maximum length limit

## Integration Points

### **Webhook Handler**
```python
# webhook_handler.py
def handle_quoter_webhook():
    # Extract deal ID from organization name
    deal_id = extract_deal_id_from_org_name(organization_data)
    
    # Use deal ID for notifications
    send_quote_created_notification(quote_data, deal_data, organization_data)
```

### **Notification System**
```python
# notification.py
def send_quote_created_notification(quote_data, deal_data, organization_data):
    # Deal ID is already extracted and validated
    deal_id = deal_data.get('id')
    
    # Create Pipedrive note with deal context
    send_pipedrive_note_notification(deal_id, message)
```

## Business Context

### **Why This Pattern?**
- **1:1 Relationship:** Each sub-organization corresponds to exactly one deal
- **Easy Identification:** Deal ID is immediately visible in organization name
- **No Additional Lookups:** Eliminates need for complex relationship mapping
- **Human Readable:** Both name and ID are visible to users

### **Pipedrive Structure**
```
Main Organization: "TLC Is Creative"
├── Sub-Organization: "Blue Owl Capital-2096"
├── Sub-Organization: "Wedding Planning-1234"
└── Sub-Organization: "Corporate Event-5678"
```

## Troubleshooting

### **Common Issues**

#### **Deal ID Not Found**
- **Check:** Organization name format in Pipedrive
- **Verify:** Hyphen exists in organization name
- **Confirm:** Deal ID is at the end of the name

#### **Invalid Deal ID Format**
- **Check:** Deal ID is numeric
- **Verify:** No special characters in deal ID
- **Confirm:** Deal ID is not empty

#### **Organization Name Missing**
- **Check:** Pipedrive organization data
- **Verify:** Organization exists and is accessible
- **Confirm:** API permissions for organization data

### **Debug Commands**
```python
# Check organization data
organization_data = get_organization_by_id(organization_id)
print(f"Organization name: {organization_data.get('name')}")

# Test deal ID extraction
deal_id = organization_name.split('-')[-1] if '-' in organization_name else None
print(f"Extracted deal ID: {deal_id}")
```

## Future Considerations

### **Potential Enhancements**
- **Custom Field Mapping:** Use Pipedrive custom fields instead of name parsing
- **Relationship API:** Use Pipedrive's relationship API for deal-organization mapping
- **Validation Rules:** Add more sophisticated deal ID validation
- **Error Recovery:** Implement fallback mechanisms for missing deal IDs

### **Scalability**
- **Multiple Deals:** Handle organizations with multiple deals
- **Complex Names:** Support more complex organization naming patterns
- **Internationalization:** Handle non-ASCII characters in organization names

---

**Status:** ✅ **IMPLEMENTED AND DOCUMENTED**  
**Last Updated:** September 7, 2025  
**Business Rule:** Sub-organization names contain deal ID in format "Name-DealID"  
**Integration:** Webhook Handler → Notification System
