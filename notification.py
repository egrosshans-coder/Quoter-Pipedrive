#!/usr/bin/env python3
"""
Notification Module - Handles notifications for quote automation
"""

import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.logger import logger
from pipedrive import API_TOKEN, BASE_URL

def send_slack_notification(message, channel="#d-quoter-alerts"):
    """
    Send notification to Slack channel.
    
    Args:
        message (str): Message to send
        channel (str): Slack channel (default: #d-quoter-alerts)
    
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    if not webhook_url:
        logger.warning("⚠️ SLACK_WEBHOOK_URL not configured - skipping Slack notification")
        return False
    
    try:
        # Format message for Slack
        slack_message = {
            "text": message,
            "channel": channel,
            "username": "Quoter Bot",
            "icon_emoji": ":robot_face:"
        }
        
        # Send to Slack webhook
        response = requests.post(
            webhook_url,
            json=slack_message,
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"📢 Slack notification sent successfully to {channel}")
            return True
        else:
            logger.error(f"❌ Slack notification failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Slack notification error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error sending Slack notification: {str(e)}")
        return False

def send_email_notification(subject, message, recipients=None):
    """
    Send email notification via Gmail SMTP.
    
    Args:
        subject (str): Email subject
        message (str): Email message
        recipients (list): List of email addresses
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Get Gmail configuration from environment
    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not gmail_user or not gmail_app_password:
        logger.warning("⚠️ Gmail credentials not configured - skipping email notification")
        return False
    
    if not recipients:
        logger.warning("⚠️ No email recipients specified - skipping email notification")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = gmail_user
        msg['To'] = ', '.join(recipients) if isinstance(recipients, list) else recipients
        msg['Subject'] = subject
        
        # Create HTML version of the message
        html_message = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #2c3e50; margin-bottom: 20px;">{subject}</h2>
                    <div style="background-color: white; padding: 20px; border-radius: 5px; border-left: 4px solid #3498db;">
                        {message.replace(chr(10), '<br>')}
                    </div>
                    <div style="margin-top: 20px; font-size: 12px; color: #7f8c8d;">
                        <p>This is an automated notification from the Quoter system.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_message, 'html'))
        
        # Connect to Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_app_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        
        logger.info(f"📧 Email notification sent successfully to {recipients}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Gmail authentication failed - check your app password")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"❌ Gmail SMTP error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error sending email: {str(e)}")
        return False

def send_pipedrive_note_notification(deal_id, message):
    """
    Send notification as a note in Pipedrive deal.
    
    Args:
        deal_id (str): Pipedrive deal ID
        message (str): Note content to add to deal
    
    Returns:
        bool: True if note created successfully, False otherwise
    """
    if not API_TOKEN:
        logger.warning("⚠️ PIPEDRIVE_API_TOKEN not configured - skipping Pipedrive note")
        return False
    
    if not deal_id:
        logger.warning("⚠️ No deal ID provided - skipping Pipedrive note")
        return False
    
    try:
        headers = {"Content-Type": "application/json"}
        params = {"api_token": API_TOKEN}
        
        # Create note data
        note_data = {
            "content": message,
            "deal_id": int(deal_id)
        }
        
        # Send note to Pipedrive
        response = requests.post(
            f"{BASE_URL}/notes",
            headers=headers,
            params=params,
            json=note_data,
            timeout=10
        )
        
        if response.status_code == 201:
            logger.info(f"📝 Pipedrive note created successfully for deal {deal_id}")
            return True
        else:
            logger.error(f"❌ Pipedrive note creation failed: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Pipedrive note error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error creating Pipedrive note: {str(e)}")
        return False

def send_quote_created_notification(quote_data, deal_data, organization_data):
    """
    Send notification when a new quote is created.
    
    Args:
        quote_data (dict): Quote data from Quoter
        deal_data (dict): Deal data from Pipedrive
        organization_data (dict): Organization data from Pipedrive
    """
    quote_id = quote_data.get("id", "Unknown")
    deal_id = deal_data.get("id", "Unknown")
    org_name = organization_data.get("name", "Unknown")
    deal_title = deal_data.get("title", "Unknown")
    
    message = f"""
🎯 NEW QUOTE CREATED

Quote ID: {quote_id}
Deal: {deal_title} (ID: {deal_id})
Organization: {org_name}
Status: Draft - Ready for editing

Please review and prepare the quote in Quoter.
"""
    
    # Send to Slack
    send_slack_notification(message.strip())
    
    # Send email (if configured) - use detailed message with instructions
    if os.getenv("NOTIFICATION_EMAILS"):
        recipients = os.getenv("NOTIFICATION_EMAILS").split(",")
        
        # Create detailed email message with instructions
        from datetime import datetime, timedelta
        formatted_deal_id = str(deal_id).zfill(5)
        utc_now = datetime.utcnow()
        pacific_offset = timedelta(hours=8)
        pacific_time = utc_now - pacific_offset
        date_str = pacific_time.strftime('%Y%m%d')
        target_quote_number = f"{formatted_deal_id}-{date_str}"
        
        detailed_email_message = f"""🎯 NEW QUOTE CREATED

Quote Number: Default
Deal: {deal_title} (ID: {deal_id})
Organization: {org_name}
Status: Draft - Ready for editing

📋 QUOTE PREPARATION INSTRUCTIONS:

1. Login to Quoter > Quotes Tab

2. Select Draft quote based on Notes Information

3. Change the Quote number to: {target_quote_number}
   (Format: 5-digit deal ID + today's date in Pacific timezone)

4. Backspace over the organization name until dropdown appears and select the org name so it will sync with Pipedrive

5. Update required fields (address, city, state, zip)

6. In deals section (appears after you select the org), select the deal that the quote is associated with

7. Add or modify items for the quote

8. Publish the quote

Please review and prepare the quote in Quoter."""
        
        send_email_notification(
            subject=f"New Quote Created - {org_name}",
            message=detailed_email_message.strip(),
            recipients=recipients
        )
    
    # Send Pipedrive note (if deal ID available)
    if deal_id and deal_id != "Unknown":
        # Draft quotes don't have a number field - only published quotes do
        # Get the quote ID for reference
        quote_id = quote_data.get("id", "Unknown")
        
        # Calculate the target quote number using deal date logic
        from datetime import datetime, timedelta
        
        # Zero-pad deal ID to 5 digits
        formatted_deal_id = str(deal_id).zfill(5)
        
        # Get Pacific time (UTC - 8 hours)
        utc_now = datetime.utcnow()
        pacific_offset = timedelta(hours=8)  # PST is UTC-8
        pacific_time = utc_now - pacific_offset
        date_str = pacific_time.strftime('%Y%m%d')
        
        # Create target quote number format: dealid-yyyymmdd
        target_quote_number = f"{formatted_deal_id}-{date_str}"
        
        pipedrive_message = f"""🎯 NEW QUOTE CREATED

Quote Number: Default
Deal: {deal_title} (ID: {deal_id})
Organization: {org_name}
Status: Draft - Ready for editing

📋 QUOTE PREPARATION INSTRUCTIONS:

1. Login to Quoter > Quotes Tab

2. Select Draft quote based on Notes Information

3. Change the Quote number to: {target_quote_number}
   (Format: 5-digit deal ID + today's date in Pacific timezone)

4. Backspace over the organization name until dropdown appears and select the org name so it will sync with Pipedrive

5. Update required fields (address, city, state, zip)

6. In deals section (appears after you select the org), select the deal that the quote is associated with

7. Add or modify items for the quote

8. Publish the quote

Please review and prepare the quote in Quoter."""
        
        send_pipedrive_note_notification(deal_id, pipedrive_message.strip())
    
    logger.info(f"📢 Notification sent for quote {quote_id}")
    return True
