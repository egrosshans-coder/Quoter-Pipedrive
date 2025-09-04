#!/usr/bin/env python3
"""
New Template Selection Logic
Reads template selection from Pipedrive Deal custom field instead of hard-coding.
"""

import requests
import json
import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quoter import get_access_token
from utils.logger import logger

def get_template_id_by_name(template_name, access_token):
    """
    Get template ID by template name from Quoter API.
    
    Args:
        template_name (str): Name of the template (e.g., "test", "Tank Delivery")
        access_token (str): OAuth access token
        
    Returns:
        str: Template ID or None if not found
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "https://api.quoter.com/v1/quote_templates",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get("data", [])
            
            # Search for exact match first
            for template in templates:
                if template.get("title") == template_name:
                    template_id = template.get("id")
                    logger.info(f"✅ Found template '{template_name}' with ID: {template_id}")
                    return template_id
            
            # If no exact match, try case-insensitive search
            for template in templates:
                if template.get("title", "").lower() == template_name.lower():
                    template_id = template.get("id")
                    logger.info(f"✅ Found template '{template_name}' (case-insensitive) with ID: {template_id}")
                    return template_id
            
            logger.warning(f"⚠️ Template '{template_name}' not found in Quoter")
            return None
            
        else:
            logger.error(f"❌ Failed to fetch templates: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error fetching templates: {e}")
        return None

def get_template_from_pipedrive_field(deal_data, access_token, field_id=None):
    """
    Get template selection from Pipedrive Deal custom field.
    
    Args:
        deal_data (dict): Deal data from Pipedrive
        access_token (str): OAuth access token
        field_id (str): Custom field ID for "Quote Template" field
        
    Returns:
        str: Template ID or None if not found
    """
    if not field_id:
        logger.warning("⚠️ No field_id provided for Quote Template field")
        return None
    
    # Get template name from Pipedrive custom field
    template_name = deal_data.get(field_id)
    
    if not template_name:
        logger.info(f"📋 No template specified in Pipedrive field {field_id}")
        return None
    
    logger.info(f"📋 Template specified in Pipedrive: '{template_name}'")
    
    # Convert template name to template ID
    template_id = get_template_id_by_name(template_name, access_token)
    
    if template_id:
        logger.info(f"✅ Using template: '{template_name}' (ID: {template_id})")
    else:
        logger.error(f"❌ Template '{template_name}' not found in Quoter")
    
    return template_id

def get_default_template_fallback(access_token):
    """
    Fallback to current hard-coded template selection logic.
    This maintains backward compatibility.
    
    Args:
        access_token (str): OAuth access token
        
    Returns:
        str: Template ID
    """
    logger.info("🔄 Using fallback template selection logic...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "https://api.quoter.com/v1/quote_templates",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get("data", [])
            
            if templates:
                # Look for the "test" template first, then "Managed Service Proposal" as fallback
                preferred_template = None
                fallback_template = None
                
                for template in templates:
                    title = template.get("title", "")
                    if title == "test":  # Look for exact "test" template first
                        preferred_template = template
                        break
                    elif "Managed Service Proposal" in title:  # Use as fallback
                        fallback_template = template
                
                # Use preferred template, fallback, or first available
                if preferred_template:
                    template_id = preferred_template.get("id")
                    logger.info(f"✅ Using fallback preferred template: {preferred_template.get('title')} (ID: {template_id})")
                    return template_id
                elif fallback_template:
                    template_id = fallback_template.get("id")
                    logger.info(f"✅ Using fallback template: {fallback_template.get('title')} (ID: {template_id})")
                    return template_id
                else:
                    template_id = templates[0].get("id")
                    logger.info(f"✅ Using fallback first available template: {templates[0].get('title', 'N/A')} (ID: {template_id})")
                    return template_id
            else:
                logger.error("❌ No templates found for fallback")
                return None
        else:
            logger.error(f"❌ Failed to get templates for fallback: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error in fallback template selection: {e}")
        return None

def get_quote_template_id(deal_data, access_token, field_id=None):
    """
    Main function to get template ID with Pipedrive field support and fallback.
    
    Args:
        deal_data (dict): Deal data from Pipedrive
        access_token (str): OAuth access token
        field_id (str): Custom field ID for "Quote Template" field
        
    Returns:
        str: Template ID
    """
    logger.info("🎯 Starting template selection process...")
    
    # Try to get template from Pipedrive field first
    if field_id:
        template_id = get_template_from_pipedrive_field(deal_data, access_token, field_id)
        if template_id:
            return template_id
        else:
            logger.info("🔄 Pipedrive field template not found, trying fallback...")
    
    # Fallback to current hard-coded logic
    return get_default_template_fallback(access_token)

def test_template_selection():
    """
    Test the new template selection logic.
    """
    print("🧪 Testing New Template Selection Logic")
    print("=" * 60)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return False
    
    # Test with different template names
    test_templates = [
        "test",
        "Managed Service Proposal - Example Only", 
        "Tank Delivery",
        "LED Wristbands",
        "Non-existent Template"
    ]
    
    print("📋 Testing template name to ID conversion:")
    print()
    
    for template_name in test_templates:
        print(f"🔍 Testing: '{template_name}'")
        template_id = get_template_id_by_name(template_name, access_token)
        
        if template_id:
            print(f"   ✅ Found ID: {template_id}")
        else:
            print(f"   ❌ Not found")
        print()
    
    # Test fallback logic
    print("🔄 Testing fallback logic:")
    fallback_id = get_default_template_fallback(access_token)
    if fallback_id:
        print(f"   ✅ Fallback template ID: {fallback_id}")
    else:
        print(f"   ❌ Fallback failed")
    
    return True

if __name__ == "__main__":
    test_template_selection()
