# Deploy Webhook Server to Render (Free)

## 🚀 Quick Deployment Steps

### 1. Create Render Account
- Go to [render.com](https://render.com)
- Sign up for free account
- Verify your email

### 2. Create New Web Service
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Select the `quoter_sync` repository

### 3. Configure Service
- **Name**: `quoter-webhook-server`
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python3 webhook_handler.py`
- **Plan**: Free

### 4. Add Environment Variables
- `PIPEDRIVE_API_TOKEN` = Your Pipedrive API token
- `QUOTER_API_KEY` = Your Quoter API key
- `QUOTER_CLIENT_SECRET` = Your Quoter client secret

### 5. Deploy
- Click "Create Web Service"
- Wait for build to complete
- Get your public URL (e.g., `https://your-app.onrender.com`)

## 🔗 Update Quoter Webhook
Once deployed, update Quoter to send webhooks to:
```
https://your-app.onrender.com/webhook/quoter/quote-published
```

## ✅ Benefits
- **Free hosting** - No cost
- **Public URL** - Quoter can reach it
- **Auto-deploy** - Updates when you push to GitHub
- **HTTPS** - Secure webhooks

## 🎯 Test the Deployment
After deployment, test with:
```bash
curl https://your-app.onrender.com/health
```
