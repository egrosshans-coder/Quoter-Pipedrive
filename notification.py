#!/usr/bin/env python3
"""
Notification Module - Handles notifications for quote automation
"""

import os
from utils.logger import logger

def send_slack_notification(message, channel="#it-d-projects"):
    """
    Send notification to Slack channel.
    
    Args:
        message (str): Message to send
        channel (str): Slack channel (default: #it-d-projects)
    
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    # TODO: Implement Slack webhook integration
    logger.info(f"📢 Slack notification to {channel}: {message}")
    return True

def send_email_notification(subject, message, recipients=None):
    """
    Send email notification.
    
    Args:
        subject (str): Email subject
        message (str): Email message
        recipients (list): List of email addresses
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # TODO: Implement email sending (SMTP, SendGrid, etc.)
    logger.info(f"📧 Email notification to {recipients}: {subject} - {message}")
    return True

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
    
    # Send email (if configured)
    if os.getenv("NOTIFICATION_EMAILS"):
        recipients = os.getenv("NOTIFICATION_EMAILS").split(",")
        send_email_notification(
            subject=f"New Quote Created - {org_name}",
            message=message.strip(),
            recipients=recipients
        )
    
    logger.info(f"📢 Notification sent for quote {quote_id}")
    return True
