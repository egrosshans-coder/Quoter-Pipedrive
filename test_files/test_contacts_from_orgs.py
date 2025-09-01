#!/usr/bin/env python3
"""
Test script to verify contact reading from Pipedrive
based on sub-organizations ready for quote creation
"""

from pipedrive import get_sub_organizations_ready_for_quotes, get_deal_by_id
from utils.logger import logger
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_contacts_for_organization(org_id, deal_id):
    """
    Get contacts associated with a specific organization and deal.
    
    Args:
        org_id (int): Organization ID
        deal_id (int): Deal ID
        
    Returns:
        list: List of contacts associated with the organization/deal
    """
    API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
    BASE_URL = "https://api.pipedrive.com/v1"
    
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found")
        return []
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        # First, get the deal to see what contacts are associated
        deal_response = requests.get(
            f"{BASE_URL}/deals/{deal_id}",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if deal_response.status_code != 200:
            logger.error(f"Failed to get deal {deal_id}: {deal_response.status_code}")
            return []
        
        deal_data = deal_response.json().get("data", {})
        person_data = deal_data.get("person_id", {})
        
        if not person_data:
            logger.warning(f"No person data found in deal {deal_id}")
            return []
        
        # person_id can be either a direct object or a list of objects
        if isinstance(person_data, list):
            persons = person_data
        else:
            persons = [person_data]
        
        contacts = []
        for person in persons:
            if person and isinstance(person, dict):
                # The person data is already in the deal response
                contacts.append(person)
                logger.info(f"Found contact: {person.get('name', 'Unknown')} (ID: {person.get('value', 'Unknown')})")
            elif person:
                # Fallback: try to get person by ID if it's just a number
                try:
                    person_id = int(person)
                    person_response = requests.get(
                        f"{BASE_URL}/persons/{person_id}",
                        headers=headers,
                        params=params,
                        timeout=10
                    )
                    
                    if person_response.status_code == 200:
                        person_data = person_response.json().get("data", {})
                        contacts.append(person_data)
                        logger.info(f"Found contact: {person_data.get('name', 'Unknown')} (ID: {person_id})")
                    else:
                        logger.warning(f"Failed to get person {person_id}: {person_response.status_code}")
                except (ValueError, TypeError):
                    logger.warning(f"Invalid person data format: {person}")
                
                if person_response.status_code == 200:
                    person_data = person_response.json().get("data", {})
                    contacts.append(person_data)
                    logger.info(f"Found contact: {person_data.get('name', 'Unknown')} (ID: {person_id})")
                else:
                    logger.warning(f"Failed to get person {person_id}: {person_response.status_code}")
        
        return contacts
        
    except Exception as e:
        logger.error(f"Error getting contacts for organization {org_id}: {e}")
        return []

def get_organization_contacts(org_id):
    """
    Get all contacts associated with a specific organization.
    
    Args:
        org_id (int): Organization ID
        
    Returns:
        list: List of contacts associated with the organization
    """
    API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
    BASE_URL = "https://api.pipedrive.com/v1"
    
    if not API_TOKEN:
        logger.error("PIPEDRIVE_API_TOKEN not found")
        return []
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        # Get organization details to see associated persons
        org_response = requests.get(
            f"{BASE_URL}/organizations/{org_id}",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if org_response.status_code != 200:
            logger.error(f"Failed to get organization {org_id}: {org_response.status_code}")
            return []
        
        org_data = org_response.json().get("data", {})
        
        # Get persons associated with this organization
        persons_response = requests.get(
            f"{BASE_URL}/organizations/{org_id}/persons",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if persons_response.status_code == 200:
            persons_data = persons_response.json().get("data", [])
            if persons_data:
                logger.info(f"Found {len(persons_data)} contacts associated with organization {org_id}")
                return persons_data
            else:
                logger.info(f"No contacts found for organization {org_id}")
                return []
        else:
            logger.warning(f"Failed to get persons for organization {org_id}: {persons_response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting organization contacts for {org_id}: {e}")
        return []

def test_contact_reading():
    """
    Test reading contacts from organizations ready for quotes.
    """
    print("🧪 Testing Contact Reading from Pipedrive Organizations")
    print("=" * 60)
    
    # Get organizations ready for quotes
    ready_orgs = get_sub_organizations_ready_for_quotes()
    
    if not ready_orgs:
        print("❌ No organizations ready for quotes found")
        return
    
    print(f"✅ Found {len(ready_orgs)} organizations ready for quotes")
    print()
    
    for i, org in enumerate(ready_orgs[:3], 1):  # Test first 3 organizations
        org_id = org.get("id")
        org_name = org.get("name")
        deal_id = org.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")  # Deal_ID field
        
        print(f"🔍 Testing Organization {i}: {org_name} (ID: {org_id})")
        print(f"   Deal ID: {deal_id}")
        print("-" * 40)
        
        if deal_id:
            # Test getting contacts from the deal
            print("📋 Testing contacts from deal...")
            deal_contacts = get_contacts_for_organization(org_id, deal_id)
            
            if deal_contacts:
                print(f"   ✅ Found {len(deal_contacts)} contacts in deal:")
                for contact in deal_contacts:
                    print(f"      • {contact.get('name', 'Unknown')} (ID: {contact.get('id')})")
                    print(f"        Email: {contact.get('email', 'N/A')}")
                    print(f"        Phone: {contact.get('phone', 'N/A')}")
            else:
                print("   ❌ No contacts found in deal")
        
        # Test getting contacts from the organization
        print("📋 Testing contacts from organization...")
        org_contacts = get_organization_contacts(org_id)
        
        if org_contacts:
            print(f"   ✅ Found {len(org_contacts)} contacts in organization:")
            for contact in org_contacts:
                print(f"      • {contact.get('name', 'Unknown')} (ID: {contact.get('id')})")
                print(f"        Email: {contact.get('email', 'N/A')}")
                print(f"        Phone: {contact.get('phone', 'N/A')}")
        else:
            print("   ❌ No contacts found in organization")
        
        print()
    
    print("=" * 60)
    print("🎯 Contact Reading Test Complete!")

def main():
    """
    Main function to run the contact reading test.
    """
    try:
        test_contact_reading()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
