#!/usr/bin/env python3
"""
Test script to examine organization 3465 and find deal ID information.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipedrive import get_organization_by_id
from utils.logger import logger

def main():
    """Examine organization 3465 to find deal ID information."""
    load_dotenv()
    
    org_id = 3465
    logger.info(f"🔍 Examining organization {org_id}...")
    
    # Get organization data
    org_data = get_organization_by_id(org_id)
    
    if not org_data:
        logger.error(f"❌ Failed to get organization {org_id}")
        return
    
    logger.info(f"✅ Successfully retrieved organization {org_id}")
    
    # Print basic organization info
    logger.info(f"Organization Name: {org_data.get('name')}")
    logger.info(f"Organization ID: {org_data.get('id')}")
    
    # Check for custom fields
    logger.info("\n🔍 Checking custom fields...")
    custom_fields = org_data.get('custom_fields', {})
    
    if custom_fields:
        for field_key, field_value in custom_fields.items():
            logger.info(f"Custom Field {field_key}: {field_value}")
    else:
        logger.info("No custom fields found")
    
    # Check for deals
    logger.info("\n🔍 Checking deals...")
    deals = org_data.get('deals', [])
    
    if deals:
        for deal in deals:
            logger.info(f"Deal ID: {deal.get('id')}")
            logger.info(f"Deal Title: {deal.get('title')}")
            logger.info(f"Deal URL: {deal.get('url')}")
            logger.info(f"Deal Status: {deal.get('status')}")
            logger.info("---")
    else:
        logger.info("No deals found")
    
    # Check for persons
    logger.info("\n🔍 Checking persons...")
    persons = org_data.get('persons', [])
    
    if persons:
        for person in persons:
            logger.info(f"Person ID: {person.get('id')}")
            logger.info(f"Person Name: {person.get('name')}")
            logger.info(f"Person Email: {person.get('email')}")
            logger.info("---")
    else:
        logger.info("No persons found")
    
    # Print the full organization data for inspection
    logger.info("\n🔍 Full organization data structure:")
    import json
    logger.info(json.dumps(org_data, indent=2, default=str))

if __name__ == "__main__":
    main()
