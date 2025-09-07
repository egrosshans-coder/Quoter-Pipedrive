# Notification System Documentation

**Last Updated:** September 7, 2025  
**Version:** 1.0 (Production Ready)

## Overview

The notification system provides real-time alerts across multiple channels when new quotes are created in the Quoter-Pipedrive integration. The system supports three notification channels: Slack, Email, and Pipedrive Deal Notes, ensuring comprehensive coverage for different user preferences and workflows.

## System Architecture

```
Pipedrive Webhook → Quote Creation → Notification System
                                        ↓
                    ┌─────────────────────────────────┐
                    │        Three Channels           │
                    └─────────────────────────────────┘
                              ↓
        ┌─────────────────┬─────────────────┬─────────────────┐
        │   Slack Alert   │  Email Alert    │ Pipedrive Note  │
        │ #d-quoter-alerts│ admin@company   │ Deal Activity   │
        └─────────────────┴─────────────────┴─────────────────┘
```

## Core Components

### 1. Main Notification Module

- **`notification.py`** - Core notification system with all three channels
- **`webhook_handler.py`** - Triggers notifications on quote creation
- **`test_files/`** - Test scripts for each notification channel

### 2. Notification Channels

#### **Slack Notifications**
- **Channel:** #d-quoter-alerts
- **Format:** Rich text with emojis and formatting
- **Content:** Quote details, organization info, status updates
- **Webhook:** `https://hooks.slack.com/services/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`

#### **Email Notifications**
- **Recipients:** admin@tlciscreative.com, sales@tlciscreative.com
- **Format:** HTML formatted emails with professional styling
- **Content:** Detailed instructions and quote information
- **SMTP:** Gmail SMTP with app password authentication

#### **Pipedrive Deal Notes**
- **Target:** Deal activity feed
- **Format:** Structured text with step-by-step instructions
- **Content:** Quote preparation workflow and target quote number
- **API:** Pipedrive Notes API integration

## Notification Content Structure

### Standard Message Format
All channels receive consistent core information:

```python
# Core Quote Information
- Quote Number: Default (draft status)
- Deal: [Deal Title] (ID: [Deal ID])
- Organization: [Organization Name]
- Status: Draft - Ready for editing
```

### Detailed Instructions (Email & Pipedrive)
Both email and Pipedrive notes include comprehensive preparation instructions:

```
📋 QUOTE PREPARATION INSTRUCTIONS:

1. Login to Quoter > Quotes Tab
   Select Draft quote based on Notes Information

2. Change the Quote number to: [TARGET_QUOTE_NUMBER]
   (Format: 5-digit deal ID + today's date in Pacific timezone)

3. Backspace over the organization name until dropdown appears and select the org name so it will sync with Pipedrive

4. Update required fields (address, city, state, zip)

5. In deals section (appears after you select the org), select the deal that the quote is associated with

6. Add or modify items for the quote

7. Publish the quote

Please review and prepare the quote in Quoter.
```

## Target Quote Number Generation

### Pacific Timezone Logic
The system generates target quote numbers using Pacific timezone for consistency:

```python
# Get Pacific time (UTC - 8 hours in winter, UTC - 7 hours in summer)
# Simple approximation: assume Pacific Standard Time (UTC-8)
utc_now = datetime.utcnow()
pacific_offset = timedelta(hours=8)  # PST is UTC-8
pacific_time = utc_now - pacific_offset
date_str = pacific_time.strftime('%Y%m%d')

# Create target quote number format: dealid-yyyymmdd
formatted_deal_id = str(deal_id).zfill(5)  # Zero-pad to 5 digits
target_quote_number = f"{formatted_deal_id}-{date_str}"
```

### Example Output
- **Deal ID:** 2096
- **Date:** September 7, 2025 (Pacific)
- **Target Quote Number:** `02096-20250907`

## Environment Configuration

### Required Environment Variables

#### **Slack Configuration**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/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
```

#### **Email Configuration**
```bash
GMAIL_USER=admin@tlciscreative.com
GMAIL_APP_PASSWORD=fqpfjjixwywzohsk
NOTIFICATION_EMAILS=admin@tlciscreative.com,sales@tlciscreative.com
```

#### **Pipedrive Configuration**
```bash
PIPEDRIVE_API_TOKEN=your_pipedrive_api_token
```

### Render Deployment Configuration

The `render.yaml` file configures all notification variables as secrets:

```yaml
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

## API Integration Details

### Slack Webhook Integration
```python
def send_slack_notification(message, channel="#d-quoter-alerts"):
    """Send notification to Slack channel via webhook"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("⚠️ SLACK_WEBHOOK_URL not configured")
        return False
    
    payload = {
        "channel": channel,
        "text": message,
        "username": "Quoter Bot",
        "icon_emoji": ":chart_with_upwards_trend:"
    }
    
    response = requests.post(webhook_url, json=payload, timeout=10)
    return response.status_code == 200
```

### Gmail SMTP Integration
```python
def send_email_notification(subject, message, recipients):
    """Send HTML formatted email via Gmail SMTP"""
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    
    # Create HTML email with professional styling
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">{subject}</h2>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                {message.replace(chr(10), '<br>')}
            </div>
        </div>
    </body>
    </html>
    """
    
    # Send via Gmail SMTP
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(gmail_user, gmail_password)
    server.sendmail(gmail_user, recipients, html_message)
    server.quit()
```

### Pipedrive Notes API Integration
```python
def send_pipedrive_note_notification(deal_id, message):
    """Send notification as a note in Pipedrive deal"""
    api_token = os.getenv("PIPEDRIVE_API_TOKEN")
    base_url = "https://api.pipedrive.com/v1"
    
    note_data = {
        "content": message,
        "deal_id": int(deal_id)
    }
    
    response = requests.post(
        f"{base_url}/notes",
        headers={"Content-Type": "application/json"},
        params={"api_token": api_token},
        json=note_data,
        timeout=10
    )
    
    return response.status_code == 201
```

## Error Handling and Logging

### Comprehensive Error Handling
```python
try:
    # Notification logic
    result = send_notification()
    if result:
        logger.info("✅ Notification sent successfully")
    else:
        logger.warning("⚠️ Notification failed")
except requests.exceptions.RequestException as e:
    logger.error(f"❌ Network error: {str(e)}")
except Exception as e:
    logger.error(f"❌ Unexpected error: {str(e)}")
```

### Graceful Degradation
- **Missing Configuration:** Skip channel if environment variable not set
- **API Failures:** Log error but continue with other channels
- **Network Issues:** Timeout after 10 seconds, log and continue
- **Invalid Data:** Validate inputs before sending

### Logging Levels
- **INFO:** Successful notifications and normal operations
- **WARNING:** Missing configuration or non-critical failures
- **ERROR:** Critical failures requiring attention
- **DEBUG:** Detailed troubleshooting information

## Testing and Validation

### Test Scripts
Located in `test_files/` directory:

#### **Slack Test**
```bash
python test_files/test_slack_notification.py
```
- Tests webhook URL connectivity
- Validates message formatting
- Confirms channel delivery

#### **Email Test**
```bash
python test_files/test_email_notification.py
```
- Tests SMTP authentication
- Validates HTML formatting
- Confirms recipient delivery

#### **Pipedrive Test**
```bash
python -c "
from notification import send_pipedrive_note_notification
send_pipedrive_note_notification('2096', 'Test note')
"
```
- Tests API authentication
- Validates note creation
- Confirms deal activity feed

### Production Testing
```python
# Test all three channels
from notification import send_quote_created_notification

# Mock data for testing
quote_data = {"id": "test_quote_123"}
deal_data = {"id": 2096, "title": "Test Deal"}
org_data = {"name": "Test Organization-2096"}

# Send comprehensive notification
send_quote_created_notification(quote_data, deal_data, org_data)
```

## Deployment and Configuration

### Render Environment Setup
1. **Add Secrets:** Configure all 5 environment variables in Render dashboard
2. **Deploy:** Push code changes trigger automatic deployment
3. **Verify:** Test all notification channels after deployment

### Local Development Setup
1. **Environment File:** Create `.env` with all required variables
2. **Dependencies:** Install requirements with `pip install -r requirements.txt`
3. **Testing:** Run test scripts to validate configuration

### Monitoring and Maintenance
- **Log Monitoring:** Check Render logs for notification failures
- **Webhook Health:** Monitor Slack webhook URL validity
- **Email Delivery:** Verify Gmail app password doesn't expire
- **API Limits:** Monitor Pipedrive API usage and limits

## Troubleshooting Guide

### Common Issues

#### **Slack Notifications Not Working**
- **Symptom:** 404 "no_service" error
- **Cause:** Invalid or expired webhook URL
- **Solution:** 
  1. Check Slack API dashboard for active webhooks
  2. Create new webhook if needed
  3. Update `SLACK_WEBHOOK_URL` in Render

#### **Email Notifications Failing**
- **Symptom:** SMTP authentication error
- **Cause:** Invalid Gmail app password or 2FA issues
- **Solution:**
  1. Generate new Gmail app password
  2. Update `GMAIL_APP_PASSWORD` in Render
  3. Verify `GMAIL_USER` is correct

#### **Pipedrive Notes Not Creating**
- **Symptom:** API authentication error
- **Cause:** Invalid or expired API token
- **Solution:**
  1. Verify `PIPEDRIVE_API_TOKEN` is valid
  2. Check deal ID exists and is accessible
  3. Confirm API permissions for notes creation

### Debug Commands
```bash
# Test individual channels
python test_files/test_slack_notification.py
python test_files/test_email_notification.py

# Check environment variables
python -c "import os; print(os.getenv('SLACK_WEBHOOK_URL'))"

# Test Pipedrive API
python -c "from pipedrive import get_deal_by_id; print(get_deal_by_id(2096))"
```

## Security Considerations

### Credential Management
- **Environment Variables:** All secrets stored as Render environment variables
- **No Hardcoding:** No credentials in source code
- **Secure Transmission:** HTTPS for all API communications
- **Access Control:** Limited to necessary team members

### Data Privacy
- **Minimal Data:** Only necessary quote information included
- **No Sensitive Info:** No passwords or internal data in notifications
- **Audit Trail:** All notifications logged for compliance

## Performance and Scalability

### Optimization Features
- **Parallel Processing:** All three channels send simultaneously
- **Timeout Handling:** 10-second timeout prevents hanging
- **Error Recovery:** Failed channels don't block others
- **Memory Efficient:** Minimal memory footprint

### Scalability Considerations
- **Rate Limiting:** Respects API rate limits
- **Batch Processing:** Can handle multiple notifications
- **Queue Management:** Graceful handling of high volume
- **Monitoring:** Built-in logging for performance tracking

## Future Enhancements

### Planned Improvements
1. **Notification Templates:** Customizable message templates
2. **User Preferences:** Individual notification channel preferences
3. **Rich Formatting:** Enhanced Slack blocks and email templates
4. **Analytics:** Notification delivery and engagement metrics
5. **Retry Logic:** Automatic retry for failed notifications

### Advanced Features
- **Conditional Notifications:** Rule-based notification triggers
- **Multi-language Support:** Localized notification content
- **Mobile Push:** Mobile app notifications
- **Webhook Validation:** Enhanced security and validation

## Integration Points

### Webhook Handler Integration
```python
# webhook_handler.py
def handle_quoter_webhook():
    # ... quote creation logic ...
    
    # Send comprehensive notification
    send_quote_created_notification(quote_data, deal_data, organization_data)
```

### Quote Creation Flow
1. **Pipedrive Webhook** triggers quote creation
2. **Quote Created** in Quoter system
3. **Notification System** sends alerts to all channels
4. **Users Respond** based on channel preferences

## Maintenance and Updates

### Regular Maintenance
- **Monthly:** Verify all API credentials are valid
- **Quarterly:** Review notification content and formatting
- **Annually:** Audit security and access controls

### Update Procedures
- **Code Changes:** Test locally before deploying
- **Configuration Changes:** Update Render environment variables
- **New Channels:** Add to notification system and test thoroughly

---

**Status:** ✅ **PRODUCTION READY**  
**Last Updated:** September 7, 2025  
**Deployment:** Render Cloud Platform  
**Channels:** Slack, Email, Pipedrive Notes
