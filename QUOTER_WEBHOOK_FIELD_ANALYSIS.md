# Quoter Webhook Field Analysis

This document analyzes the fields captured by Quoter's webhook when quotes are published. This analysis is crucial for understanding what data is available for Stage 3 implementation (quote number formatting and Pipedrive updates).

## **📋 Webhook Data Structure**

### **Quote Information**
| Field | Value | Type | Description |
|-------|--------|------|-------------|
| `Data ID` | `7228156` | String | Quote ID in Quoter |
| `Data Number` | `7` | Integer | Quote number (not our xxxxx-nn format) |
| `Data Name` | `Quote for Blue Owl Capital-2096` | String | Quote name with organization and deal ID |
| `Data Status` | `pending` | String | Quote status (pending/published) |
| `Data UUID` | `2778-ec1b0c16-4cf0-4e45-8daf-f4848450521d` | String | Unique identifier |
| `Data Expiry Date` | `2025-09-14 07:00:00` | String | Quote expiration date |
| `Data Parent Quote ID` | `null` | String | Parent quote ID for revisions |
| `Data Revision` | `null` | String | Revision number |

### **Person/Contact Information**
| Field | Value | Type | Description |
|-------|--------|------|-------------|
| `Data Person ID` | `1725219` | String | Contact ID in Quoter |
| `Data Person Public ID` | `cont_31IMDsmHdlYFe4Y1mK6oninSGge` | String | Public contact identifier |
| `Data Person First Name` | `Robert` | String | Contact first name |
| `Data Person Last Name` | `Lee` | String | Contact last name |
| `Data Person Organization` | `Blue Owl Capital-2096` | String | Organization name with deal ID suffix |
| `Data Person Title` | `` | String | Job title (empty in this case) |
| `Data Person Email` | `robert.lee@blueowl.com` | String | Contact email address |
| `Data Person Work Phone` | `212-970-6981` | String | Work phone number |
| `Data Person Mobile Phone` | `212-970-6981` | String | Mobile phone number |

### **Address Information**
| Field | Value | Type | Description |
|-------|--------|------|-------------|
| `Data Person Billing Address Line1` | `464 W 39th St` | String | Street address |
| `Data Person Billing Address City` | `Los Angeles` | String | City |
| `Data Person Billing Address State Code` | `CA` | String | State abbreviation |
| `Data Person Billing Address State Name` | `California` | String | Full state name |
| `Data Person Billing Address Country Code` | `US` | String | Country abbreviation |
| `Data Person Billing Address Postal Code` | `90731` | String | ZIP code |

### **Financial Information**
| Field | Value | Type | Description |
|-------|--------|------|-------------|
| `Data Total Upfront` | `2,575.00` | String | Total upfront cost |
| `Data Total Recurring` | `null` | String | Recurring cost (none in this case) |
| `Data Total Margin Dollars` | `1,545.00` | String | Total margin in dollars |
| `Data Total Margin Percent` | `60.00` | String | Total margin percentage |
| `Data Shipping` | `0.00` | String | Shipping cost |
| `Data Currency Code` | `USD` | String | Currency abbreviation |

### **Quote Owner Information**
| Field | Value | Type | Description |
|-------|--------|------|-------------|
| `Data Quote Owner ID` | `136185` | String | Quote owner ID |
| `Data Quote Owner Name` | `Eric Grosshans` | String | Quote owner full name |
| `Data Quote Owner Email` | `eric@tlciscreative.com` | String | Quote owner email |

### **Form Information**
| Field | Value | Type | Description |
|-------|--------|------|-------------|
| `Data Form ID` | `50826` | String | Form template ID |
| `Data Form Slug` | `test` | String | Form template slug |
| `Data Form Title` | `test` | String | Form template title |

## **🎯 Key Insights for Implementation**

### **Phase 1: Data Extraction** ✅
- **Contact Information**: Complete name, email, phone, address data available
- **Organization Data**: Organization name with deal ID suffix (e.g., "Blue Owl Capital-2096")
- **Financial Data**: Total amounts, margins, shipping costs available
- **Quote Metadata**: Status, expiration, revision information available

### **Phase 2: Quote Number Formatting** ✅
- **Deal ID Extraction**: Available from `person.organization` field (e.g., "Blue Owl Capital-2096" → "2096")
- **Sequential Numbering**: Can be implemented using our `generate_sequential_quote_number()` function
- **Implementation Flow**: 
  1. Quote is published → webhook received
  2. Extract deal ID from organization name
  3. Generate sequential number (e.g., 02096-01, 02096-02)
  4. Update the published quote with our numbering
  5. Update Pipedrive with quote information

### **Phase 3: Pipedrive Integration** ✅
- **Quote Status Updates**: Can update deal status to "presented" when quote is published
- **Contact Address Updates**: Can sync billing address back to Pipedrive person records
- **Deal Value Updates**: Can update deal value with quote total amount
- **Revision Handling**: Can distinguish between original quotes and revisions

## **📊 Data Availability Summary**

### **✅ Available Fields:**
- **Quote ID**: `7228156` ✅
- **Quote Number**: `7` ✅ (Quoter's internal numbering)
- **Contact Name**: `Robert Lee` ✅
- **Organization**: `Blue Owl Capital-2096` ✅
- **Deal ID**: `2096` (extracted from organization name) ✅
- **Address**: Complete billing address ✅
- **Phone**: Work and mobile numbers ✅
- **Email**: `robert.lee@blueowl.com` ✅
- **Total Amount**: `$2,575.00` ✅
- **Status**: `pending` ✅

### **⚠️ Fields to Generate:**
- **Sequential Quote Number**: Need to generate `02096-01` format ✅
- **Deal Status**: Need to update Pipedrive deal status ✅
- **Contact Address**: Need to sync back to Pipedrive ✅

## **🚀 Implementation Status**

### **✅ Completed:**
1. **Webhook Handler**: Receives and processes published quotes
2. **Data Extraction**: Extracts all necessary fields from webhook
3. **Deal ID Parsing**: Successfully extracts deal ID from organization name
4. **Pipedrive Updates**: Updates deals with quote information
5. **Sequential Numbering Function**: Generates xxxxx-yy format numbers
6. **Quote Update Function**: Updates published quotes with our numbering

### **🎯 Current Flow:**
1. **Quote Published** → Quoter webhook sent
2. **Webhook Received** → Data parsed and validated
3. **Deal ID Extracted** → From organization name suffix
4. **Quote Type Determined** → Check `parent_quote_id` field
5. **If NEW Quote** → Generate sequential number (02096-01, 02096-02, etc.)
6. **If REVISION** → Keep existing quote number, skip sequential numbering
7. **Quote Updated** → With appropriate numbering (new quotes only)
8. **Pipedrive Updated** → Deal status, value, and contact information
9. **Processing Tracked** → Prevents duplicate updates

### **🔧 Technical Implementation:**
- **Sequential Numbering**: `generate_sequential_quote_number(deal_id)` function
- **Quote Updates**: `update_quote_with_sequential_number(quote_id, deal_id)` function
- **Webhook Processing**: `handle_quoter_quote_published()` function
- **Pipedrive Integration**: `update_deal_with_quote_info()` function

## **📝 Notes**

- **Quote numbers are NOT set during draft creation** - they're only assigned when quotes are published
- **Sequential numbering happens AFTER publication** via webhook processing
- **Format**: `xxxxx-yy` where `xxxxx` is 5-digit deal ID with leading zeros, `yy` is sequential number
- **Examples**: `02096-01`, `02096-02`, `02217-01`, `00123-01`
- **Revision vs. New Quote Logic**:
  - **Revisions** (`parent_quote_id` present): Keep same quote number, skip sequential numbering
  - **New Quotes** (`parent_quote_id` null): Generate next sequential number for the deal
- **Revision Support**: Handles both original quotes and revisions with duplicate prevention
