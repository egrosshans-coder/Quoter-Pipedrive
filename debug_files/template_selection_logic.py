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
    Handles enum fields that return numeric values.
    
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
    
    # Get template enum value from Pipedrive custom field
    template_enum_value = deal_data.get(field_id)
    
    if not template_enum_value:
        logger.info(f"📋 No template specified in Pipedrive field {field_id}")
        return None
    
    # Map enum values to template names
    enum_mapping = {
        441: 'Basic',
        442: 'Confetti/Streamers',
        443: 'LED Lanyards',
        444: 'LED Wristbands',
        451: 'Balloons',
        452: 'CO2/Smoke/Upright Foggers',
        453: 'Fireworks/pyro/fire',
        454: 'Floating Video',
        455: 'Low level fog',
        456: 'Tank Delivery',
        457: 'Robotics',
    }
    
    # Alternative names for templates that might not match exactly
    alternative_names = {
        'Basic': ['Basic Template', 'Basic Quote', 'Standard', 'Default'],
        'Confetti/Streamers': ['Confetti/streamers', 'Confetti Streamers', 'Streamers'],  # Case sensitivity issue
        'Co2/smoke/upright foggers': ['CO2/smoke/upright foggers', 'Foggers', 'Smoke', 'CO2'],
        'Fireworks/pyro/fire': ['Fireworks', 'Pyro', 'Fire', 'Pyrotechnics'],
        'Floating Video': ['Video', 'Floating', 'Display'],
        'Low level fog': ['Low level', 'Fog', 'Ground fog'],
    }
    
    # Special handling for templates with known mismatches
    # Map Pipedrive names to actual Quoter names to avoid warnings
    template_name_mapping = {
    }
    
    # Convert enum value to template name
    template_name = enum_mapping.get(template_enum_value)
    
    if not template_name:
        logger.error(f"❌ Unknown enum value {template_enum_value} for Quote Template field")
        return None
    
    # Check if we need to map to the actual Quoter template name
    actual_template_name = template_name_mapping.get(template_name, template_name)
    
    logger.info(f"📋 Template specified in Pipedrive: '{template_name}' (enum: {template_enum_value})")
    if actual_template_name != template_name:
        logger.info(f"📋 Mapped to Quoter template name: '{actual_template_name}'")
    
    # Convert template name to template ID
    template_id = get_template_id_by_name(actual_template_name, access_token)
    
    if template_id:
        logger.info(f"✅ Using template: '{template_name}' (ID: {template_id})")
    else:
        # Try alternative names if the primary name is not found
        logger.warning(f"⚠️ Template '{template_name}' not found in Quoter, trying alternatives...")
        
        alternatives = alternative_names.get(template_name, [])
        for alt_name in alternatives:
            logger.info(f"🔍 Trying alternative name: '{alt_name}'")
            template_id = get_template_id_by_name(alt_name, access_token)
            if template_id:
                logger.info(f"✅ Found template with alternative name: '{alt_name}' (ID: {template_id})")
                break
        
        if not template_id:
            logger.warning(f"⚠️ No template found for '{template_name}' or its alternatives, will use fallback")
    
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
                # Look for the "Basic" template first, then "Managed Service Proposal" as fallback
                preferred_template = None
                fallback_template = None
                
                for template in templates:
                    title = template.get("title", "")
                    if title == "Basic":  # Look for exact "Basic" template first
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
