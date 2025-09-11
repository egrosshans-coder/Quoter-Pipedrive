# Webhook System Design Guide
## Pipedrive-Quoter Integration Best Practices

> **Purpose**: This document outlines the critical design considerations and implementation steps required for a robust webhook integration between Pipedrive and Quoter, based on lessons learned from extensive debugging sessions.

## 🎯 **System Overview**

The webhook system enables automated draft quote creation in Quoter when Pipedrive deals move to the quote stage. The flow is:
1. **Pipedrive Deal** → moves to quote stage
2. **Pipedrive Automation** → triggers webhook
3. **Webhook Server** → processes organization data
4. **Quoter API** → creates contact and draft quote
5. **Slack** → sends notification

---

## 🏗️ **Critical Design Considerations**

### 1. **Data Type Handling**

#### **Integer vs String Issues**
```python
# ❌ WRONG - Inconsistent data types
organization_id = data.get('organization', {}).get('id')  # Could be int or string
deal_id = data.get('deal_id')  # Could be int or string

# ✅ CORRECT - Normalize to strings
organization_id = str(data.get('organization', {}).get('id', ''))
deal_id = str(data.get('deal_id', ''))
```

#### **Array Handling**
```python
# ❌ WRONG - Assuming single item
contact_email = contacts[0]['email']  # IndexError if empty

# ✅ CORRECT - Safe array access
contact_email = contacts[0]['email'] if contacts else None
```

#### **Nested Object Safety**
```python
# ❌ WRONG - Unsafe nested access
org_name = data['organization']['name']

# ✅ CORRECT - Safe nested access
org_name = data.get('organization', {}).get('name', '')
```

### 2. **Pipedrive Webhook Configuration**

#### **Critical Distinction: Manual vs Automated Webhooks**
- **Manual Webhooks**: External systems → Pipedrive (for receiving data)
- **Automated Webhooks**: Pipedrive → External systems (for sending data)

#### **Required Configuration**
```json
{
  "url": "https://quoter-webhook-server.onrender.com/webhook/pipedrive/organization",
  "event": "Organization updated",
  "filter": {
    "HID-QBO-Status": "289"
  },
  "body": {
    "organization": {
      "id": "{{organization.id}}",
      "name": "{{organization.name}}"
    },
    "deal_id": "{{organization.HID-QBO-Status}}"
  }
}
```

### 3. **Data Validation & Error Handling**

#### **Email Validation**
```python
# ❌ WRONG - No validation
email = contact_data.get('email')

# ✅ CORRECT - Validate email format
email = contact_data.get('email', '').strip()
if not email or '@' not in email:
    logger.error(f"Invalid email format: {email}")
    return None
```

#### **Required Field Validation**
```python
# ✅ CORRECT - Validate all required fields
required_fields = ['organization_id', 'deal_id', 'contact_email']
missing_fields = [field for field in required_fields if not locals().get(field)]
if missing_fields:
    logger.error(f"Missing required fields: {missing_fields}")
    return None
```

### 4. **Template Enum Handling**

#### **Template Selection Logic**
```python
# ❌ WRONG - Direct enum usage
template_id = TemplateEnum.STANDARD

# ✅ CORRECT - Safe enum conversion
try:
    template_id = TemplateEnum(template_name.upper())
except ValueError:
    logger.warning(f"Invalid template: {template_name}, using default")
    template_id = TemplateEnum.STANDARD
```

---

## 🔧 **Implementation Steps**

### Step 1: Webhook Server Setup

#### **Environment Variables**
```bash
# Required environment variables
QUOTER_API_KEY=your_quoter_api_key
SLACK_WEBHOOK_URL=your_slack_webhook_url
PIPEDRIVE_API_TOKEN=your_pipedrive_token
```

#### **Flask App Structure**
```python
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/webhook/pipedrive/organization', methods=['POST'])
def handle_organization_webhook():
    try:
        data = request.get_json()
        logger.info(f"Received webhook: {data}")
        
        # Process webhook data
        result = process_organization_webhook(data)
        
        if result:
            return jsonify({"status": "success", "quote_id": result}), 200
        else:
            return jsonify({"status": "error", "message": "Failed to create quote"}), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
```

### Step 2: Data Processing Pipeline

#### **Organization Data Extraction**
```python
def extract_organization_data(data):
    """Safely extract organization data from webhook payload"""
    try:
        organization = data.get('organization', {})
        
        # Normalize data types
        org_id = str(organization.get('id', ''))
        org_name = organization.get('name', '')
        deal_id = str(data.get('deal_id', ''))
        
        # Validate required fields
        if not all([org_id, org_name, deal_id]):
            raise ValueError("Missing required organization data")
            
        return {
            'organization_id': org_id,
            'organization_name': org_name,
            'deal_id': deal_id
        }
        
    except Exception as e:
        logger.error(f"Failed to extract organization data: {e}")
        return None
```

#### **Contact Data Retrieval**
```python
def get_contact_data(deal_id):
    """Retrieve contact data from Pipedrive deal"""
    try:
        # Get deal from Pipedrive
        deal = pipedrive_client.get_deal(deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
            
        # Get primary contact
        contacts = deal.get('contacts', [])
        if not contacts:
            raise ValueError(f"No contacts found for deal {deal_id}")
            
        contact = contacts[0]
        
        # Validate email
        email = contact.get('email', '').strip()
        if not email or '@' not in email:
            raise ValueError(f"Invalid email format: {email}")
            
        return {
            'name': contact.get('name', ''),
            'email': email,
            'phone': contact.get('phone', '')
        }
        
    except Exception as e:
        logger.error(f"Failed to get contact data: {e}")
        return None
```

### Step 3: Quote Creation Process

#### **Contact Creation in Quoter**
```python
def create_quoter_contact(contact_data):
    """Create contact in Quoter"""
    try:
        contact_payload = {
            'name': contact_data['name'],
            'email': contact_data['email'],
            'phone': contact_data.get('phone', '')
        }
        
        response = quoter_client.create_contact(contact_payload)
        if response and response.get('id'):
            logger.info(f"Contact created: {response['id']}")
            return response['id']
        else:
            raise ValueError("Failed to create contact in Quoter")
            
    except Exception as e:
        logger.error(f"Failed to create contact: {e}")
        return None
```

#### **Draft Quote Creation**
```python
def create_draft_quote(organization_data, contact_id):
    """Create draft quote in Quoter"""
    try:
        quote_payload = {
            'name': organization_data['organization_name'],
            'contact_id': contact_id,
            'template_id': get_template_id(organization_data),
            'currency': 'USD'
        }
        
        response = quoter_client.create_quote(quote_payload)
        if response and response.get('id'):
            logger.info(f"Draft quote created: {response['id']}")
            return response['id']
        else:
            raise ValueError("Failed to create draft quote")
            
    except Exception as e:
        logger.error(f"Failed to create draft quote: {e}")
        return None
```

---

## 🚨 **Common Pitfalls & Solutions**

### 1. **Data Type Inconsistencies**
- **Problem**: Pipedrive sends integers, Quoter expects strings
- **Solution**: Always normalize to strings using `str()`

### 2. **Missing Error Handling**
- **Problem**: Webhook fails silently on data issues
- **Solution**: Comprehensive try-catch blocks with detailed logging

### 3. **Invalid Email Data**
- **Problem**: Missing `@` symbol in email addresses
- **Solution**: Validate email format before API calls

### 4. **Template Enum Errors**
- **Problem**: Invalid template names cause crashes
- **Solution**: Safe enum conversion with fallback to default

### 5. **Webhook Configuration Issues**
- **Problem**: Using Manual webhooks instead of Automated webhooks
- **Solution**: Ensure correct webhook type in Pipedrive admin

---

## 🔒 **Security Considerations**

### 1. **Webhook URL Security**
- **Never commit webhook URLs to public repositories**
- **Use environment variables for all sensitive configuration**
- **Regularly rotate webhook URLs**

### 2. **API Key Management**
- **Store API keys in environment variables**
- **Use different keys for development and production**
- **Implement key rotation policies**

### 3. **Input Validation**
- **Validate all incoming webhook data**
- **Sanitize user inputs before API calls**
- **Implement rate limiting**

---

## 📊 **Monitoring & Debugging**

### 1. **Comprehensive Logging**
```python
# Log all critical steps
logger.info(f"Processing webhook for organization: {org_id}")
logger.info(f"Contact created: {contact_id}")
logger.info(f"Draft quote created: {quote_id}")
logger.error(f"Webhook failed: {error_message}")
```

### 2. **Health Checks**
```python
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })
```

### 3. **Error Tracking**
- **Log all errors with context**
- **Send alerts for critical failures**
- **Monitor webhook success rates**

---

## 🚀 **Deployment Checklist**

### Pre-Deployment
- [ ] All environment variables configured
- [ ] Webhook URLs secured and not in public repos
- [ ] Data validation implemented
- [ ] Error handling comprehensive
- [ ] Logging configured
- [ ] Health check endpoint available

### Post-Deployment
- [ ] Test webhook endpoint with sample data
- [ ] Verify Pipedrive webhook configuration
- [ ] Monitor logs for errors
- [ ] Test end-to-end flow
- [ ] Verify Slack notifications

### Ongoing Maintenance
- [ ] Regular log review
- [ ] Monitor webhook success rates
- [ ] Update API keys as needed
- [ ] Review and update error handling
- [ ] Performance monitoring

---

## 📝 **Troubleshooting Guide**

### Common Issues

#### 1. **"Maximum retry limit reached"**
- **Cause**: Pipedrive retrying failed webhooks
- **Solution**: Check webhook server logs for actual errors

#### 2. **"404 - no_service"**
- **Cause**: Invalid or expired webhook URL
- **Solution**: Generate new webhook URL and update configuration

#### 3. **"Invalid email format"**
- **Cause**: Malformed email addresses in Pipedrive
- **Solution**: Fix email data in Pipedrive and re-trigger automation

#### 4. **"Template not found"**
- **Cause**: Invalid template enum value
- **Solution**: Implement safe enum conversion with fallback

---

## 🎯 **Success Metrics**

### Key Performance Indicators
- **Webhook Success Rate**: >95%
- **Quote Creation Success Rate**: >90%
- **Average Processing Time**: <5 seconds
- **Error Resolution Time**: <1 hour

### Monitoring Dashboard
- Real-time webhook status
- Success/failure rates
- Processing times
- Error frequency and types

---

## 📚 **Additional Resources**

- [Pipedrive Webhook Documentation](https://developers.pipedrive.com/docs/api/v1/Webhooks)
- [Quoter API Documentation](https://quoter.com/api/docs)
- [Flask Webhook Best Practices](https://flask.palletsprojects.com/en/2.0.x/patterns/errorpages/)
- [Slack Webhook Security](https://api.slack.com/messaging/webhooks)

---

**Last Updated**: September 10, 2025  
**Version**: 1.0  
**Author**: AI Assistant & Development Team
