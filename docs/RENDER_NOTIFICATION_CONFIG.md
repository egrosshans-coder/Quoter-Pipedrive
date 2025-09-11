# Render Notification Configuration

**Last Updated:** September 7, 2025  
**Version:** 1.0

## Overview

This document details the Render environment configuration for the notification system, including all required environment variables and their setup procedures.

## Environment Variables Configuration

### **Updated render.yaml**
The `render.yaml` file has been updated to include all notification-related environment variables as secrets:

```yaml
services:
  - type: web
    name: quoter-webhook-server
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python3 webhook_handler.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.0
      - key: PORT
        value: 10000
    envVarsFrom:
      - key: SLACK_WEBHOOK_URL
        fromSecret: true
      - key: GMAIL_USER
        fromSecret: true
      - key: GMAIL_APP_PASSWORD
        fromSecret: true
      - key: PIPEDRIVE_API_TOKEN
        fromSecret: true
      - key: NOTIFICATION_EMAILS
        fromSecret: true
```

## Required Secrets in Render Dashboard

### **1. SLACK_WEBHOOK_URL**
- **Value:** `https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK/URL`
- **Purpose:** Slack webhook for #d-quoter-alerts channel
- **Status:** ✅ Configured and tested

### **2. GMAIL_USER**
- **Value:** `admin@tlciscreative.com`
- **Purpose:** Gmail account for sending notifications
- **Status:** ✅ Configured and tested

### **3. GMAIL_APP_PASSWORD**
- **Value:** `fqpfjjixwywzohsk`
- **Purpose:** Gmail app-specific password for SMTP authentication
- **Status:** ✅ Configured and tested

### **4. PIPEDRIVE_API_TOKEN**
- **Value:** [Your Pipedrive API token]
- **Purpose:** Pipedrive API access for creating deal notes
- **Status:** ✅ Configured and tested

### **5. NOTIFICATION_EMAILS**
- **Value:** `admin@tlciscreative.com,sales@tlciscreative.com`
- **Purpose:** Comma-separated list of email recipients
- **Status:** ✅ Configured and tested

## Configuration Process

### **Step 1: Update render.yaml**
- All notification variables moved to `envVarsFrom` section
- Configured as secrets for security
- Maintains existing non-sensitive variables in `envVars`

### **Step 2: Add Secrets in Render Dashboard**
1. Go to Render service dashboard
2. Navigate to "Environment" tab
3. Add each secret variable with corresponding value
4. Save configuration

### **Step 3: Deploy Changes**
- Push code changes to GitHub
- Render automatically detects changes
- Deploys with new environment configuration
- Verifies all secrets are loaded

## Security Considerations

### **Secret Management**
- All sensitive credentials stored as Render secrets
- No hardcoded values in source code
- Secure transmission and storage
- Access limited to authorized personnel

### **Credential Types**
- **API Keys:** Pipedrive API token
- **Webhook URLs:** Slack webhook endpoint
- **SMTP Credentials:** Gmail app password
- **Email Lists:** Notification recipients

## Testing Configuration

### **Verification Steps**
1. **Deploy:** Push changes to trigger Render deployment
2. **Test Slack:** Run Slack notification test
3. **Test Email:** Run email notification test
4. **Test Pipedrive:** Run Pipedrive note test
5. **Verify Logs:** Check Render logs for any errors

### **Test Commands**
```bash
# Test all notification channels
python test_files/test_slack_notification.py
python test_files/test_email_notification.py
python -c "from notification import send_pipedrive_note_notification; send_pipedrive_note_notification('2096', 'Test note')"
```

## Troubleshooting

### **Common Issues**

#### **Missing Environment Variables**
- **Symptom:** "Environment variable not configured" warnings
- **Solution:** Verify all secrets are added in Render dashboard
- **Check:** Render logs for missing variable errors

#### **Invalid Credentials**
- **Symptom:** Authentication failures in logs
- **Solution:** Verify credential values are correct
- **Check:** Test individual channels for specific errors

#### **Deployment Failures**
- **Symptom:** Build or deployment errors
- **Solution:** Check render.yaml syntax and variable names
- **Check:** Render build logs for configuration errors

### **Debug Commands**
```bash
# Check environment variables in Render
# (Use Render dashboard or shell access)

# Test individual components
curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' $SLACK_WEBHOOK_URL
```

## Maintenance

### **Regular Updates**
- **Monthly:** Verify all credentials are still valid
- **Quarterly:** Review and rotate sensitive credentials
- **As Needed:** Update email lists or webhook URLs

### **Credential Rotation**
1. Generate new credentials
2. Update Render environment variables
3. Test all notification channels
4. Deploy and verify functionality

## Integration Points

### **Webhook Handler Integration**
The notification system is integrated into `webhook_handler.py`:

```python
# webhook_handler.py
from notification import send_quote_created_notification

# When quote is created
send_quote_created_notification(quote_data, deal_data, organization_data)
```

### **Automatic Triggering**
- **Pipedrive Webhook** → Quote Creation → Notification System
- **All 3 Channels** triggered simultaneously
- **Error Handling** ensures failed channels don't block others

---

**Status:** ✅ **CONFIGURED AND DEPLOYED**  
**Last Updated:** September 7, 2025  
**Deployment:** Render Cloud Platform  
**Channels:** Slack, Email, Pipedrive Notes
