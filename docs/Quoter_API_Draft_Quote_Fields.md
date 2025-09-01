# Quoter API - Draft Quote Fields

## 📋 **Overview**

This document outlines the **available fields** for creating draft quotes via the Quoter API, based on official API documentation and our testing experience.

**API Endpoint:** `POST /v1/quotes`  
**Documentation Source:** [Quoter API Reference](https://docs.quoter.com/api)  
**Last Updated:** August 13, 2025

## ✅ **Available Fields for Draft Quote Creation**

### **Required Fields (Must be provided):**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `contact_id` | string | ID of the contact in Quoter | `"cont_2r5WGA5WDExgSYmnZp0TVVQqFLA"` |
| `template_id` | string | ID of the quote template to use | `"tmpl_2r5WHEQLKFsyKdyIj5daPCp7mjF"` |
| `currency_abbr` | string | Currency abbreviation for the quote | `"USD"`, `"CAD"` |

### **Optional Fields (Can be provided):**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `name` | string | Display name for the quote | `"Draft: Blue Owl Capital - Deal 2096"` |
| `appended_content` | string | Additional content appended to quote | `"Draft quote ready for sales review"` |
| `cover_letter` | string | Cover letter content | `"Sales rep must review and publish"` |

## ❌ **Fields NOT Available via API**

### **Fields We Attempted (Not Supported):**

| Field | What We Tried | Why It Failed | Alternative |
|-------|---------------|---------------|-------------|
| `number` | Set quote number during creation | Field doesn't exist in API | Must be set manually in UI or via webhook after publish |
| `pipedrive_deal_id` | Link to Pipedrive deal | Field doesn't exist in API | Must be linked manually via UI or set via webhook after publish |
| `status` | Set draft status | Status is automatically "draft" | Cannot be changed via API during creation |

## 🔍 **API Response**

### **Success Response (200):**
```json
{
  "id": "quot_2r5CZzZNKjHlB7FvizOgceEHUhK",
  "url": "https://development.quoter.com/admin/quotes/draft_by_public_id/quot_2r5CZzZNKjHlB7FvizOgceEHUhK"
}
```

### **Response Fields:**
- **`id`** - Unique quote identifier
- **`url`** - Direct link to the draft quote in Quoter admin

## 🚨 **API Limitations**

### **Current Limitations (as documented):**
1. **All quotes created as Draft** - Cannot create published quotes directly
2. **Template items don't transfer** - Line items from templates won't be created
3. **File attachments not created** - Template attachments won't transfer
4. **Custom fields not created** - Template custom fields won't transfer
5. **Owner restrictions** - Drafts owned by API key creator only
6. **Access restrictions** - Admin links only work for Sales Manager+ users

### **Field Limitations:**
1. **Only 6 fields available** - Very limited field set
2. **No quote numbering** - Cannot set quote numbers via API
3. **No Pipedrive integration** - No built-in fields for deal association
4. **No status control** - Status automatically set to "draft"

## 🎯 **Implications for Our Workflow**

### **What We CAN Do via API:**
- ✅ Create draft quotes with basic information
- ✅ Set contact and template
- ✅ Set currency
- ✅ Add descriptive name
- ✅ Add appended content
- ✅ Add cover letter

### **What We CANNOT Do via API:**
- ❌ Set quote numbers
- ❌ Link to Pipedrive deals
- ❌ Create line items
- ❌ Set custom fields
- ❌ Control quote status

### **What Must Be Done Manually:**
1. **Quote numbering** - Sales rep sets in UI
2. **Deal association** - Sales rep links via Pipedrive integration
3. **Line items** - Sales rep adds manually
4. **Custom fields** - Sales rep populates
5. **Publishing** - Sales rep publishes manually

## 🔄 **Recommended Workflow**

### **Step 1: API Draft Creation (Minimal)**
```python
quote_data = {
    "contact_id": contact_id,           # ✅ Required
    "template_id": template_id,         # ✅ Required  
    "currency_abbr": "USD",             # ✅ Required
    "name": f"Draft: {org_name}",      # ✅ Optional
    "appended_content": "Ready for sales review",  # ✅ Optional
    "cover_letter": "Complete required fields and publish"  # ✅ Optional
}
```

### **Step 2: Sales Rep Completion (Manual)**
1. **Review draft quote**
2. **Set quote number**
3. **Link Pipedrive deal**
4. **Add line items**
5. **Fill required fields**
6. **Publish quote**

### **Step 3: Post-Publish Updates (Webhook)**
1. **Quote is published** (triggers webhook)
2. **Webhook can update** custom fields
3. **Webhook can set** metadata
4. **Webhook can modify** quote content

## 💡 **Key Insights**

### **API Design Philosophy:**
- **Minimal creation** - API creates basic structure only
- **Human completion** - Sales reps fill in business details
- **Post-publish automation** - Webhooks handle technical updates

### **Why This Approach:**
1. **Quality control** - Human oversight ensures accuracy
2. **Business logic** - Sales reps understand requirements
3. **Flexibility** - Can handle complex business rules
4. **Audit trail** - Clear responsibility for each step

## 📚 **References**

- **Official API Docs:** [https://docs.quoter.com/api](https://docs.quoter.com/api)
- **API Endpoint:** `POST /v1/quotes`
- **Authentication:** OAuth 2.0 Client Credentials Flow
- **Base URL:** `https://api.quoter.com/v1`

## 🔧 **Testing Notes**

### **What We've Tested:**
- ✅ **Basic quote creation** - Works with required fields
- ✅ **Contact population** - Contact data appears correctly
- ✅ **Template selection** - Templates apply correctly
- ✅ **Field validation** - API rejects invalid fields

### **What We Need to Test:**
- 🔄 **Template modification** - Add draft line item
- 🔄 **Sales rep workflow** - Manual completion process
- 🔄 **Webhook updates** - Post-publish modifications

---

**Note:** This document reflects the current state of the Quoter API as of August 2025. API capabilities may change over time. Always refer to the official documentation for the most up-to-date information.
