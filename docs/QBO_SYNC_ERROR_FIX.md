# QBO Sync Error Fix - "Property Name:failed to parse json object"

## 🔍 **Problem Analysis**

The error `"Property Name:failed to parse json object; a property specified is unsupported or invalid"` occurs when SyncQ tries to sync Pipedrive products to QuickBooks Online (QBO). This is a **QBO API rejection** due to invalid/unsupported properties in the JSON payload.

## 🎯 **Root Cause**

The issue was in the `pipedrive.py` file where products were being created with fields that are incompatible with QBO:

### **Problematic Fields:**
1. **`unit: "piece"`** - QBO doesn't recognize this unit type
2. **`tax: 0`** - QBO expects different tax format
3. **`visible_to: 3`** - Pipedrive-specific field that shouldn't go to QBO
4. **Invalid price/cost formats** - QBO expects specific number formats

## ✅ **Solutions Implemented**

### **1. Cleaned Up Product Fields**
- Changed `unit` from `"piece"` to `"each"` (QBO standard)
- Removed `tax` and `visible_to` fields (Pipedrive-specific)
- Improved price/cost handling with proper validation

### **2. Added QBO Compatibility Validator**
Created `validate_product_for_qbo_compatibility()` function that:
- Validates and cleans all product data
- Limits field lengths to QBO requirements
- Converts prices to proper format (cents)
- Removes invalid/empty values
- Ensures positive values only

### **3. Enhanced Error Handling**
- Added detailed error logging
- Logs product data that causes errors
- Better exception handling for debugging

## 🚀 **How to Test the Fix**

### **Step 1: Run the Updated Sync**
```bash
python sync_with_date_filter.py
```

### **Step 2: Monitor SyncQ Status**
1. Check Pipedrive products for the "SyncQ" status field
2. Look for successful syncs instead of JSON parsing errors
3. Verify products appear in QuickBooks Online

### **Step 3: Check Logs**
Look for these success messages:
```
✅ QBO-compatible product data: {...}
✅ Successfully created/updated product in Pipedrive
```

## 🔧 **Additional Recommendations**

### **1. SyncQ Configuration**
- Ensure SyncQ is configured to map the correct Pipedrive fields to QBO
- Verify the field mappings in SyncQ dashboard
- Check if custom fields need special handling

### **2. QBO Field Mapping**
Common QBO item fields that SyncQ should map:
- `Name` ← Pipedrive `name`
- `SKU` ← Pipedrive `code`
- `Description` ← Pipedrive `description`
- `Unit Price` ← Pipedrive `price`
- `Purchase Cost` ← Pipedrive `cost`
- `Type` ← Set to "Inventory" or "Service"

### **3. Monitor for Future Issues**
- Watch for new products that fail to sync
- Check SyncQ logs for any remaining errors
- Validate new product data before creating in Pipedrive

## 📋 **Troubleshooting**

### **If Errors Persist:**

1. **Check SyncQ Field Mapping:**
   - Log into SyncQ dashboard
   - Verify Pipedrive → QBO field mappings
   - Ensure no invalid field mappings exist

2. **Validate Product Data:**
   - Check for special characters in product names
   - Ensure prices are valid numbers
   - Verify category mappings are correct

3. **Test with Single Product:**
   - Create one test product in Pipedrive
   - Monitor SyncQ status field
   - Check if it syncs successfully to QBO

### **Common QBO API Issues:**
- **Field length limits:** Names max 100 chars, descriptions max 500 chars
- **Invalid characters:** Special characters in names/descriptions
- **Negative values:** Prices and costs must be positive
- **Invalid units:** Use standard QBO units like "each", "hour", "day"

## 🎉 **Expected Results**

After implementing these fixes:
- ✅ Products sync successfully from Pipedrive to QBO
- ✅ No more "failed to parse json object" errors
- ✅ SyncQ status field shows "Success" instead of errors
- ✅ Products appear correctly in QuickBooks Online

## 📞 **Next Steps**

1. **Deploy the updated code**
2. **Test with a few products first**
3. **Monitor SyncQ status fields**
4. **Verify products appear in QBO**
5. **Run full sync once confirmed working**

If issues persist, the problem may be in SyncQ configuration rather than the product data format.
