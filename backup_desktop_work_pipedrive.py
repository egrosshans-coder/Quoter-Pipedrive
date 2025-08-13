# BACKUP FILE: Desktop pipedrive.py changes
# Created: 2025-08-12
# Purpose: Backup desktop work for laptop synchronization
# 
# This file contains the changes we made to pipedrive.py on the desktop
# You can compare this with your working laptop version and merge as needed

"""
DESKTOP CHANGES TO pipedrive.py:

1. Added get_organization_by_id() function
2. Added get_deal_by_id() function

These functions were missing and needed for the quote creation system.
"""

# Function 1: get_organization_by_id
def get_organization_by_id(org_id):
    """
    Get organization data from Pipedrive by ID.
    
    Args:
        org_id (int): Organization ID
        
    Returns:
        dict: Organization data if found, None otherwise
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found")
        return None
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(
            f"{BASE_URL}/organizations/{org_id}",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data")
        elif response.status_code == 404:
            logger.warning(f"Organization {org_id} not found")
            return None
        else:
            logger.error(f"Failed to get organization {org_id}: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting organization {org_id}: {e}")
        return None

# Function 2: get_deal_by_id
def get_deal_by_id(deal_id):
    """
    Get deal data from Pipedrive by ID.
    
    Args:
        deal_id (int): Deal ID
        
    Returns:
        dict: Deal data if found, None otherwise
    """
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found")
        return None
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(
            f"{BASE_URL}/deals/{deal_id}",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("data")
        elif response.status_code == 404:
            logger.warning(f"Deal {deal_id} not found")
            return None
        else:
            logger.error(f"Failed to get deal {deal_id}: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting deal {deal_id}: {e}")
        return None

"""
SYNC INSTRUCTIONS:

1. Copy this backup file to your laptop
2. Check if these functions already exist in your laptop pipedrive.py
3. If they don't exist, add them to your laptop version
4. If they do exist, compare implementations and use the better one
5. Update the desktop with your working laptop code

These functions are needed for the quote creation system to work.
"""
