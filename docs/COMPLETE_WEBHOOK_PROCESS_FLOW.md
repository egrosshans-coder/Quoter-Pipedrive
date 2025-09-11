# Complete Webhook Process Flow
## Pipedrive → Quoter → Draft Quote Creation

> **Purpose**: This document outlines the complete step-by-step process from Pipedrive deal stage change to automated draft quote creation in Quoter, based on the working system implementation.

---

## 🎯 **Complete Process Overview**

The webhook system enables **fully automated draft quote creation** when Pipedrive deals move to the quote stage. Here's the complete flow:

```
Pipedrive Deal → Stage Change → Automation → Webhook → Server → Quoter API → Draft Quote Created
```

---

## 📋 **Step-by-Step Process Flow**

### **Step 1: Pipedrive Deal Stage Change**
**Trigger**: Deal moves to "Send Quote/Negotiate" stage
- **User Action**: Sales rep moves deal to quote stage
- **System Response**: Pipedrive automation triggers
- **Timing**: Immediate (real-time)

### **Step 2: Pipedrive Automation Execution**
**Process**: Pipedrive automation runs with 6-minute delays
- **Delay 1**: 6 minutes - Creates parent organization
- **Delay 2**: 6 minutes - Creates sub-organization
- **Status Update**: Sets `HID-QBO-Status` to `289` (QBO-SubCust)
- **Result**: Organization ready for quote creation

### **Step 3: Webhook Configuration Check**
**Critical**: Pipedrive must have **Automated Webhook** configured
- **Webhook Type**: Automated (not Manual)
- **URL**: `https://quoter-webhook-server.onrender.com/webhook/pipedrive/organization`
- **Event**: `Organization updated`
- **Filter**: `HID-QBO-Status` = `289`
- **Body**: JSON payload with organization data

### **Step 4: Webhook Data Payload**
**Pipedrive sends**:
```json
{
  "organization": {
    "id": 3871,
    "name": "ZZ15-Org-2525"
  },
  "deal_id": "2525"
}
```

### **Step 5: Webhook Server Processing**
**Server**: `quoter-webhook-server.onrender.com` receives webhook
- **Endpoint**: `/webhook/pipedrive/organization`
- **Method**: POST
- **Processing**: Flask application processes JSON payload
- **Logging**: Comprehensive logging of all steps

### **Step 6: Data Extraction & Validation**
**Server extracts**:
- **Organization ID**: `3871`
- **Organization Name**: `ZZ15-Org-2525`
- **Deal ID**: `2525` (extracted from organization name)
- **Validation**: Checks for required fields and data integrity

### **Step 7: Pipedrive API Data Retrieval**
**Server calls Pipedrive API**:
- **Deal Data**: Retrieves deal details using deal ID
- **Contact Data**: Gets primary contact information
- **Validation**: Ensures email format is valid (contains `@`)

### **Step 8: Contact Creation in Quoter**
**Server calls Quoter API**:
- **Endpoint**: `/v1/contacts`
- **Payload**: Contact name, email, phone
- **Validation**: Email format validation
- **Result**: Contact created with ID (e.g., `cont_32Wb65VninBWNPaPslkkkVhqnJ2`)

### **Step 9: Draft Quote Creation**
**Server calls Quoter API**:
- **Endpoint**: `/v1/quotes`
- **Payload**: Quote name, contact ID, template, currency
- **Template**: Uses appropriate template based on organization data
- **Result**: Draft quote created with ID (e.g., `quot_32Wb64bfzTJ33EUIUMswT7A8vWW`)

### **Step 10: Success Notification**
**Server sends notification**:
- **Slack**: Success message to `#d-quoter-alerts` channel
- **Content**: Quote ID, organization name, deal ID
- **Status**: Webhook processing complete

---

## 🔧 **Technical Implementation Details**

### **Webhook Server Architecture**
```python
# Flask application structure
@app.route('/webhook/pipedrive/organization', methods=['POST'])
def handle_organization_webhook():
    try:
        # 1. Parse webhook data
        data = request.get_json()
        
        # 2. Extract organization information
        org_data = extract_organization_data(data)
        
        # 3. Get deal and contact data from Pipedrive
        deal_data = get_deal_data(org_data['deal_id'])
        contact_data = get_contact_data(deal_data)
        
        # 4. Create contact in Quoter
        contact_id = create_quoter_contact(contact_data)
        
        # 5. Create draft quote in Quoter
        quote_id = create_draft_quote(org_data, contact_id)
        
        # 6. Send success notification
        send_slack_notification(quote_id, org_data)
        
        return jsonify({"status": "success", "quote_id": quote_id})
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
```

### **Data Flow Validation**
```python
# Critical validation steps
def validate_webhook_data(data):
    # Check required fields
    if not data.get('organization', {}).get('id'):
        raise ValueError("Missing organization ID")
    
    if not data.get('organization', {}).get('name'):
        raise ValueError("Missing organization name")
    
    # Extract deal ID from organization name
    deal_id = extract_deal_id(data['organization']['name'])
    if not deal_id:
        raise ValueError("Cannot extract deal ID from organization name")
    
    return True
```

### **Email Validation**
```python
# Critical email validation
def validate_email(email):
    if not email or '@' not in email:
        raise ValueError(f"Invalid email format: {email}")
    return email.strip()
```

---

## 🚨 **Critical Success Factors**

### **1. Webhook Configuration**
- **Must use Automated Webhook** (not Manual)
- **Correct URL**: `https://quoter-webhook-server.onrender.com/webhook/pipedrive/organization`
- **Proper filters**: `HID-QBO-Status` = `289`
- **Valid JSON payload**: Organization ID, name, deal ID

### **2. Data Integrity**
- **Valid email addresses**: Must contain `@` symbol
- **Complete contact information**: Name, email, phone
- **Proper organization naming**: Must include deal ID for extraction

### **3. Server Health**
- **Render server**: Must be running and accessible
- **Environment variables**: All API keys configured
- **Slack webhook**: Valid and not expired

### **4. API Connectivity**
- **Pipedrive API**: Accessible and authenticated
- **Quoter API**: Accessible and authenticated
- **Network connectivity**: All services can communicate

---

## 📊 **Success Metrics & Monitoring**

### **Key Performance Indicators**
- **Webhook Success Rate**: >95%
- **Quote Creation Success Rate**: >90%
- **Average Processing Time**: <5 seconds
- **Error Resolution Time**: <1 hour

### **Monitoring Endpoints**
- **Health Check**: `https://quoter-webhook-server.onrender.com/health`
- **Webhook Logs**: Render dashboard logs
- **Slack Notifications**: Real-time success/failure alerts

### **Error Tracking**
- **Webhook Failures**: Logged with detailed error messages
- **API Errors**: Pipedrive and Quoter API error tracking
- **Data Validation Errors**: Email format, missing fields
- **Network Issues**: Connectivity and timeout errors

---

## 🔄 **Troubleshooting Common Issues**

### **Issue 1: "Maximum retry limit reached"**
- **Cause**: Pipedrive retrying failed webhooks
- **Solution**: Check webhook server logs for actual errors
- **Prevention**: Ensure all data validation passes

### **Issue 2: "Invalid email format"**
- **Cause**: Missing `@` symbol in email addresses
- **Solution**: Fix email data in Pipedrive
- **Prevention**: Data validation in webhook handler

### **Issue 3: "Webhook not triggered"**
- **Cause**: Incorrect webhook configuration
- **Solution**: Verify Automated Webhook setup in Pipedrive
- **Prevention**: Follow webhook configuration checklist

### **Issue 4: "404 - no_service"**
- **Cause**: Invalid or expired Slack webhook URL
- **Solution**: Generate new webhook URL and update configuration
- **Prevention**: Regular webhook URL rotation

---

## 🎯 **Process Verification Checklist**

### **Pre-Deployment**
- [ ] Pipedrive automation configured
- [ ] Automated webhook configured in Pipedrive
- [ ] Webhook server deployed on Render
- [ ] All environment variables set
- [ ] Slack webhook URL valid

### **Testing**
- [ ] Test webhook endpoint with sample data
- [ ] Verify Pipedrive webhook configuration
- [ ] Test end-to-end flow with test deal
- [ ] Confirm draft quote creation
- [ ] Verify Slack notifications

### **Production**
- [ ] Monitor webhook success rates
- [ ] Check logs for errors
- [ ] Verify quote creation
- [ ] Monitor Slack notifications
- [ ] Regular health checks

---

## 📈 **Process Timeline**

### **Typical Processing Time**
- **Pipedrive Automation**: 12 minutes (2 × 6-minute delays)
- **Webhook Processing**: <5 seconds
- **Total Time**: ~12 minutes from deal stage change to draft quote

### **Real-Time Components**
- **Webhook Trigger**: Immediate
- **Data Processing**: <5 seconds
- **API Calls**: <3 seconds
- **Notifications**: <1 second

---

## 🚀 **System Benefits**

### **Automation Benefits**
- **100% Automated**: No manual intervention required
- **Real-Time**: Immediate quote creation when ready
- **Scalable**: Handles multiple deals simultaneously
- **Reliable**: Robust error handling and logging

### **Business Benefits**
- **Faster Quotes**: 12 minutes vs hours of manual work
- **Consistent Quality**: Standardized quote creation process
- **Error Reduction**: Automated validation prevents mistakes
- **Team Efficiency**: Sales team focuses on selling, not admin

---

## 📝 **Maintenance Requirements**

### **Daily**
- [ ] Check webhook server health
- [ ] Monitor success rates
- [ ] Review error logs

### **Weekly**
- [ ] Verify webhook URLs
- [ ] Check API key expiration
- [ ] Review performance metrics

### **Monthly**
- [ ] Update webhook URLs
- [ ] Review and update documentation
- [ ] Performance optimization

---

**Last Updated**: September 10, 2025  
**Version**: 1.0  
**Status**: ✅ **PRODUCTION READY**
