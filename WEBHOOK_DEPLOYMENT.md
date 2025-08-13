# Webhook-Based Quote Automation

## Overview

This implementation uses **webhooks** to trigger quote creation immediately when Pipedrive automation creates a sub-organization ready for quotes. This is **much more efficient** than scheduled polling.

## Architecture

```
Pipedrive Automation → Webhook → Our Server → Quoter API → Quote Created
     (Step 8)           (POST)     (Flask)     (API)      (Real-time)
```

## Deployment Options

### Option 1: Local Server (Development/Testing)
```bash
# Install Flask
pip install flask

# Run webhook server
python webhook_handler.py

# Server runs on http://localhost:5000
# Webhook endpoint: http://localhost:5000/webhook/pipedrive/organization
```

### Option 2: Cloud Deployment (Production)

#### A. Heroku
```bash
# Create Heroku app
heroku create quoter-automation-webhook

# Add environment variables
heroku config:set QUOTER_API_KEY=your_key
heroku config:set QUOTER_CLIENT_SECRET=your_secret
heroku config:set PIPEDRIVE_API_TOKEN=your_token

# Deploy
git push heroku main

# Webhook URL: https://your-app-name.herokuapp.com/webhook/pipedrive/organization
```

#### B. Railway/Render/Vercel
Similar deployment process - deploy the Flask app and get a public URL.

## Pipedrive Webhook Setup

1. **Access Pipedrive Admin** → **Integrations** → **API** → **Webhooks**
2. **Create New Webhook**:
   - **URL**: `https://your-domain.com/webhook/pipedrive/organization`
   - **Event**: `Organization updated`
   - **Filters**: 
     - `Owner ID` = `19103598` (Maurice)
     - `HID-QBO-Status` = `289` (QBO-SubCust)

3. **Test the webhook** by updating an organization's status

## Environment Variables

```bash
# Required
QUOTER_API_KEY=your_quoter_api_key
QUOTER_CLIENT_SECRET=your_quoter_client_secret
PIPEDRIVE_API_TOKEN=your_pipedrive_api_token

# Optional
PORT=5000  # Server port (default: 5000)
NOTIFICATION_EMAILS=email1@example.com,email2@example.com
```

## Testing

### Test Webhook Endpoint
```bash
# Test the webhook locally
curl -X POST http://localhost:5000/webhook/pipedrive/organization \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "id": 3652,
      "name": "Test Organization",
      "owner_id": {"value": 19103598},
      "454a3767bce03a880b31d78a38c480d6870e0f1b": 289,
      "15034cf07d05ceb15f0a89dcbdcc4f596348584e": "2439"
    }
  }'
```

### Health Check
```bash
curl http://localhost:5000/health
```

## Advantages Over Scheduling

1. **Real-time response** - Quotes created immediately when ready
2. **No delays** - Instant notification to sales team
3. **Efficient** - Only runs when needed
4. **Reliable** - No missed events or timing issues
5. **Scalable** - Handles multiple events simultaneously

## Monitoring

- **Logs**: Check application logs for webhook events
- **Health checks**: Monitor `/health` endpoint
- **Error tracking**: Webhook failures are logged with details

## Security

- **Webhook verification**: Add signature verification (TODO)
- **HTTPS**: Always use HTTPS in production
- **Rate limiting**: Consider adding rate limiting for webhook endpoints
- **Authentication**: Add API key authentication if needed
