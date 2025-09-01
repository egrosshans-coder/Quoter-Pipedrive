# Comprehensive Pipedrive → Quoter Data Mapping Strategy

## 🎯 **Goal: Maximum Data Utilization**

**Primary Objective:** Map ALL possible data from Pipedrive to Quoter, even if fields are currently empty  
**Secondary Objective:** Understand how Quoter updates flow back to Pipedrive  
**Business Value:** Demonstrate the power of populated fields to encourage better Pipedrive usage

## 📊 **Current Data Mapping (What We're Using)**

### **Organization Data (Minimal):**
```python
# Currently extracting:
org_name = organization_data.get("name", "")           # Organization name
org_id = organization_data.get("id")                  # Organization ID
deal_id = organization_data.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")  # Deal_ID custom field
```

### **Deal Data (Minimal):**
```python
# Currently extracting:
deal_title = deal_data.get("title", f"Deal {deal_id}")  # Deal title
person_data = deal_data.get("person_id", {})            # Contact information
```

### **Contact Data (Basic):**
```python
# Currently extracting:
contact_name = primary_contact.get("name", "Unknown Contact")
contact_id = primary_contact.get("value")  # Pipedrive person ID
email = email_item.get("value")           # Contact email
phone = phone_item.get("value")           # Contact phone
```

## 🚀 **Target: Comprehensive Data Mapping**

### **1. Organization Fields to Extract (Pipedrive → Quoter):**

#### **Basic Organization Info:**
- `name` - ✅ **Currently using**
- `address` - ❌ **Not extracting** (billing address)
- `address2` - ❌ **Not extracting** (billing address 2)
- `city` - ❌ **Not extracting** (billing city)
- `state` - ❌ **Not extracting** (billing state)
- `postal_code` - ❌ **Not extracting** (billing zip)
- `country` - ❌ **Not extracting** (billing country)
- `phone` - ❌ **Not extracting** (organization phone)
- `email` - ❌ **Not extracting** (organization email)
- `website` - ❌ **Not extracting** (organization website)

#### **Custom Organization Fields:**
- `Deal_ID` - ✅ **Currently using** (custom field)
- `HID-QBO-Status` - ✅ **Currently using** (custom field)
- `Parent_Org_ID` - ❌ **Not extracting** (parent organization)
- `QuickBooks Id : SyncQ` - ❌ **Not extracting** (QBO reference)
- `Company-Type` - ❌ **Not extracting** (business type)
- `Company Revenue` - ❌ **Not extracting** (business size)
- `Company Employees` - ❌ **Not extracting** (business size)

### **2. Contact Fields to Extract (Pipedrive → Quoter):**

#### **Basic Contact Info:**
- `name` - ✅ **Currently using**
- `email` - ✅ **Currently using**
- `phone` - ✅ **Currently using**
- `title` - ❌ **Not extracting** (Mr., Dr., etc.)

#### **Address Information:**
- `address` - ❌ **Not extracting** (contact address)
- `city` - ❌ **Not extracting** (contact city)
- `state` - ❌ **Not extracting** (contact state)
- `postal_code` - ❌ **Not extracting** (contact zip)
- `country` - ❌ **Not extracting** (contact country)

### **3. Deal Fields to Extract (Pipedrive → Quoter):**

#### **Basic Deal Info:**
- `title` - ✅ **Currently using**
- `value` - ❌ **Not extracting** (deal value)
- `currency` - ❌ **Not extracting** (deal currency)
- `stage_id` - ❌ **Not extracting** (deal stage)
- `owner_id` - ❌ **Not extracting** (deal owner)

## 🔄 **Quoter Contact Fields to Populate (All Available):**

### **Basic Information:**
```python
contact_data = {
    "first_name": first_name,           # ✅ From Pipedrive contact
    "last_name": last_name,            # ✅ From Pipedrive contact
    "title": contact_title,            # ❌ NEW: From Pipedrive contact
    "organization": organization_name,  # ✅ From Pipedrive organization
    "email": contact_email,            # ✅ From Pipedrive contact
    "website": org_website,            # ❌ NEW: From Pipedrive organization
}
```

### **Phone Information:**
```python
contact_data = {
    "work_phone": contact_phone,       # ❌ NEW: From Pipedrive contact
    "mobile_phone": contact_mobile,    # ❌ NEW: From Pipedrive contact (if available)
}
```

### **Billing Address (Complete):**
```python
contact_data = {
    "billing_address": org_address,        # ❌ NEW: From Pipedrive organization
    "billing_address2": org_address2,     # ❌ NEW: From Pipedrive organization
    "billing_city": org_city,             # ❌ NEW: From Pipedrive organization
    "billing_region_iso": org_state,      # ❌ NEW: From Pipedrive organization
    "billing_postal_code": org_zip,       # ❌ NEW: From Pipedrive organization
    "billing_country_iso": org_country,   # ✅ Currently hardcoded to "US"
}
```

### **Shipping Address (Complete):**
```python
contact_data = {
    "shipping_address": org_address,        # ❌ NEW: From Pipedrive organization
    "shipping_address2": org_address2,     # ❌ NEW: From Pipedrive organization
    "shipping_city": org_city,             # ❌ NEW: From Pipedrive organization
    "shipping_region_iso": org_state,      # ❌ NEW: From Pipedrive organization
    "shipping_postal_code": org_zip,       # ❌ NEW: From Pipedrive organization
    "shipping_country_iso": org_country,   # ❌ NEW: From Pipedrive organization
    "shipping_email": contact_email,       # ❌ NEW: From Pipedrive contact
    "shipping_first_name": first_name,     # ❌ NEW: From Pipedrive contact
    "shipping_last_name": last_name,      # ❌ NEW: From Pipedrive contact
    "shipping_organization": organization_name,  # ❌ NEW: From Pipedrive organization
    "shipping_phone": contact_phone,      # ❌ NEW: From Pipedrive contact
    "shipping_label": f"Ship to {first_name} {last_name}",  # ❌ NEW: Generated
}
```

### **Custom Fields:**
```python
contact_data = {
    "pipedrive_contact_id": pipedrive_contact_id,  # ✅ Currently using
    "pipedrive_organization_id": org_id,           # ❌ NEW: From Pipedrive organization
    "pipedrive_deal_id": deal_id,                 # ❌ NEW: From Pipedrive deal
}
```

## 🔄 **Data Flow: Quoter → Pipedrive (Research Needed)**

### **Key Questions:**
1. **Does Quoter automatically sync contact updates back to Pipedrive?**
2. **What triggers the sync?** (Quote creation, contact update, etc.)
3. **Which fields sync back?** (Address, phone, email, etc.)
4. **Is there a webhook or API endpoint for this?**
5. **What's the timing of the sync?**

### **Research Areas:**
1. **Quoter API documentation** - Look for sync endpoints
2. **Pipedrive webhooks** - Check if Quoter sends updates
3. **Quoter UI** - Look for sync settings or indicators
4. **Test scenarios** - Update contact in Quoter, check Pipedrive

## 🛠 **Implementation Plan**

### **Phase 1: Data Extraction Enhancement**
1. **Update Pipedrive API calls** to extract ALL available fields
2. **Add field mapping logic** for address, phone, and custom fields
3. **Handle missing data gracefully** (empty fields don't break the process)

### **Phase 2: Contact Creation Enhancement**
1. **Update contact creation** to use ALL available Quoter fields
2. **Map Pipedrive data** to appropriate Quoter fields
3. **Add validation** for required vs. optional fields

### **Phase 3: Testing & Validation**
1. **Test with various Pipedrive data scenarios** (complete vs. incomplete)
2. **Verify Quoter field population** (check UI for all fields)
3. **Test data flow back to Pipedrive** (if applicable)

### **Phase 4: Documentation & Training**
1. **Document the enhanced data mapping**
2. **Show sales team the benefits** of populated fields
3. **Encourage better Pipedrive usage** for richer data

## 💡 **Expected Benefits**

### **Immediate:**
- **Richer contact information** in Quoter quotes
- **Professional appearance** with complete addresses
- **Better shipping information** for logistics

### **Long-term:**
- **Improved Pipedrive usage** by sales team
- **Better data quality** across both systems
- **Streamlined quote process** with complete information
- **Professional client experience** with detailed quotes

## 🚨 **Implementation Notes**

### **Data Quality:**
- **Handle empty fields gracefully** - Don't break if data is missing
- **Use sensible defaults** - Country, phone types, etc.
- **Log data extraction** - Track what's available vs. what's used

### **Error Handling:**
- **Pipedrive API failures** - Fall back to basic data
- **Quoter field validation** - Handle field-specific errors
- **Missing required fields** - Log warnings, continue with available data

---

**Next Steps:** 
1. **Research Pipedrive field availability** for a sample organization
2. **Update data extraction logic** to capture all fields
3. **Enhance contact creation** to use all available Quoter fields
4. **Test and validate** the enhanced data flow
