# Pipedrive to Quoter Sync Guide

## 🎯 **Purpose**

This script syncs changes from Pipedrive back to Quoter, focusing on:
- **Product names** that were updated
- **Categories** that were fixed (Category:Subcategory format)
- **Product codes** that were updated

## 📋 **Prerequisites**

### **Environment Variables Required:**
```bash
PIPEDRIVE_API_TOKEN=your_pipedrive_token
QUOTER_API_TOKEN=your_quoter_token
```

### **API Access:**
- **Pipedrive API** access for reading products
- **Quoter API** access for updating items

## 🚀 **Usage**

### **1. Test the Comparison Logic:**
```bash
python test_sync_comparison.py
```

### **2. Run the Sync (Dry Run First):**
```bash
# Edit sync_config.py and set dry_run = True
python sync_pipedrive_to_quoter.py
```

### **3. Run the Actual Sync:**
```bash
# Edit sync_config.py and set dry_run = False
python sync_pipedrive_to_quoter.py
```

## 🔧 **Configuration**

### **Fields to Sync:**
Edit `sync_config.py` to enable/disable specific fields:

```python
SYNC_FIELDS = {
    "name": {"enabled": True},
    "code": {"enabled": True},
    "category": {"enabled": True},
    "description": {"enabled": False},  # Disabled
    "price": {"enabled": False}         # Disabled
}
```

### **Dry Run Mode:**
Set `dry_run = True` to see what would be updated without making changes.

## 📊 **What the Script Does**

### **1. Data Fetching:**
- Fetches all products from Pipedrive
- Fetches all items from Quoter
- Creates lookup tables for efficient matching

### **2. Matching:**
- Matches items by product code
- Identifies items that exist in both systems

### **3. Comparison:**
- Compares names, codes, and categories
- **Fetches Quoter categories** to build lookup table
- **Maps Pipedrive category names** to Quoter category IDs
- Identifies differences that need syncing

### **4. Updates:**
- Updates Quoter items with changes from Pipedrive
- Logs all changes and results

## 📝 **Output**

The script provides detailed logging:
- **Items fetched** from each system
- **Matches found** between systems
- **Changes detected** for each item
- **Update results** (success/failure)
- **Summary statistics**

## ⚠️ **Important Notes**

### **Income/Expense Accounts:**
- **Not synced** - these are not working between Pipedrive and QBO
- **Will be addressed** when fixing Quoter → QBO sync

### **Pricing:**
- **Not synced** - you mentioned pricing didn't change
- **Can be enabled** in config if needed

### **Categories:**
- **Category:Subcategory format** from Pipedrive (e.g., "Lighting / LED")
- **Maps to category_id** in Quoter using parent/child schema
- **Fetches Quoter categories** to build proper lookup table
- **Handles both parent categories** and parent/child combinations

## 🛠️ **Troubleshooting**

### **Common Issues:**

1. **API Token Issues:**
   - Check environment variables
   - Verify API token permissions

2. **No Matches Found:**
   - Check product codes in both systems
   - Verify code format consistency

3. **Update Failures:**
   - Check Quoter API permissions
   - Verify field mappings

### **Debug Mode:**
Set `log_level = "DEBUG"` in `sync_config.py` for detailed logging.

## 🎉 **Expected Results**

After running the sync:
- **Product names** updated in Quoter
- **Categories** synced with Pipedrive
- **Product codes** updated
- **Detailed log** of all changes made

## 📞 **Next Steps**

Once this sync is working:
1. **Test with a few items** first
2. **Run full sync** when confident
3. **Address Quoter → QBO** income/expense account issues
4. **Set up automated sync** if needed
