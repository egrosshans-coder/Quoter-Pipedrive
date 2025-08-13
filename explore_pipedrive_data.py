#!/usr/bin/env python3
"""
Explore Pipedrive Data - Comprehensive field discovery script

This script explores ALL available fields in Pipedrive for:
1. Organizations (including custom fields)
2. Deals (including custom fields)  
3. Contacts/Persons (including custom fields)

Goal: Discover what data we can extract for comprehensive Quoter mapping
"""

import os
import json
import requests
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = "https://api.pipedrive.com/v1"

def explore_organization_fields(org_id):
    """Explore all available fields for a specific organization."""
    print(f"🔍 Exploring Organization {org_id} Fields")
    print("=" * 50)
    
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(
            f"{BASE_URL}/organizations/{org_id}",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            org_data = data.get("data")
            
            if org_data:
                print(f"✅ Organization found: {org_data.get('name', 'Unknown')}")
                print()
                
                # Explore all fields
                print("📋 **All Available Fields:**")
                print("-" * 30)
                
                for key, value in org_data.items():
                    if value:  # Only show non-empty fields
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: [EMPTY]")
                
                print()
                
                # Look for address-related fields
                print("🏠 **Address-Related Fields:**")
                print("-" * 30)
                address_fields = ['address', 'address2', 'city', 'state', 'postal_code', 'country', 'zip']
                for field in address_fields:
                    if field in org_data:
                        print(f"  {field}: {org_data[field]}")
                    else:
                        print(f"  {field}: [NOT FOUND]")
                
                print()
                
                # Look for contact-related fields
                print("📞 **Contact-Related Fields:**")
                print("-" * 30)
                contact_fields = ['phone', 'email', 'website']
                for field in contact_fields:
                    if field in org_data:
                        print(f"  {field}: {org_data[field]}")
                    else:
                        print(f"  {field}: [NOT FOUND]")
                
                print()
                
                # Look for custom fields
                print("🔧 **Custom Fields (Long Keys):**")
                print("-" * 30)
                custom_fields = {k: v for k, v in org_data.items() if len(k) > 20}
                if custom_fields:
                    for key, value in custom_fields.items():
                        print(f"  {key}: {value}")
                else:
                    print("  No custom fields found")
                
                return org_data
            else:
                print("❌ No organization data found")
                return None
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def explore_deal_fields(deal_id):
    """Explore all available fields for a specific deal."""
    print(f"🔍 Exploring Deal {deal_id} Fields")
    print("=" * 50)
    
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(
            f"{BASE_URL}/deals/{deal_id}",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            deal_data = data.get("data")
            
            if deal_data:
                print(f"✅ Deal found: {deal_data.get('title', 'Unknown')}")
                print()
                
                # Explore all fields
                print("📋 **All Available Fields:**")
                print("-" * 30)
                
                for key, value in deal_data.items():
                    if value:  # Only show non-empty fields
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: [EMPTY]")
                
                print()
                
                # Look for person/contact data
                print("👤 **Person/Contact Data:**")
                print("-" * 30)
                person_data = deal_data.get("person_id", {})
                if person_data:
                    if isinstance(person_data, list):
                        for i, person in enumerate(person_data):
                            print(f"  Person {i+1}:")
                            for k, v in person.items():
                                print(f"    {k}: {v}")
                    else:
                        for k, v in person_data.items():
                            print(f"    {k}: {v}")
                else:
                    print("  No person data found")
                
                return deal_data
            else:
                print("❌ No deal data found")
                return None
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def explore_person_fields(person_id):
    """Explore all available fields for a specific person."""
    print(f"🔍 Exploring Person {person_id} Fields")
    print("=" * 50)
    
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in environment variables")
        return None
    
    headers = {"Content-Type": "application/json"}
    params = {"api_token": API_TOKEN}
    
    try:
        response = requests.get(
            f"{BASE_URL}/persons/{person_id}",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            person_data = data.get("data")
            
            if person_data:
                print(f"✅ Person found: {person_data.get('name', 'Unknown')}")
                print()
                
                # Explore all fields
                print("📋 **All Available Fields:**")
                print("-" * 30)
                
                for key, value in person_data.items():
                    if value:  # Only show non-empty fields
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: [EMPTY]")
                
                print()
                
                # Look for address-related fields
                print("🏠 **Address-Related Fields:**")
                print("-" * 30)
                address_fields = ['address', 'address2', 'city', 'state', 'postal_code', 'country', 'zip']
                for field in address_fields:
                    if field in person_data:
                        print(f"  {field}: {person_data[field]}")
                    else:
                        print(f"  {field}: [NOT FOUND]")
                
                print()
                
                # Look for contact-related fields
                print("📞 **Contact-Related Fields:**")
                print("-" * 30)
                contact_fields = ['phone', 'email', 'website']
                for field in contact_fields:
                    if field in person_data:
                        print(f"  {field}: {person_data[field]}")
                    else:
                        print(f"  {field}: [NOT FOUND]")
                
                return person_data
            else:
                print("❌ No person data found")
                return None
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main exploration function."""
    print("🚀 Pipedrive Data Field Explorer")
    print("=" * 50)
    print()
    
    # Test with Blue Owl Capital-2096 (organization 3465)
    org_id = 3465
    print(f"🎯 Testing with Organization ID: {org_id}")
    print()
    
    # Explore organization
    org_data = explore_organization_fields(org_id)
    
    if org_data:
        print()
        print("🔍 **Next Steps:**")
        print("1. Check if organization has a deal ID")
        print("2. Explore deal data if available")
        print("3. Explore person/contact data if available")
        print()
        
        # Look for deal ID
        deal_id = org_data.get("15034cf07d05ceb15f0a89dcbdcc4f596348584e")
        if deal_id:
            print(f"📋 Found Deal ID: {deal_id}")
            print("Exploring deal data...")
            print()
            
            deal_data = explore_deal_fields(deal_id)
            
            if deal_data:
                # Look for person data in deal
                person_data = deal_data.get("person_id", {})
                if person_data:
                    if isinstance(person_data, list) and person_data:
                        person_id = person_data[0].get("value")
                    else:
                        person_id = person_data.get("value")
                    
                    if person_id:
                        print(f"👤 Found Person ID: {person_id}")
                        print("Exploring person data...")
                        print()
                        
                        explore_person_fields(person_id)
                    else:
                        print("❌ No person ID found in deal data")
                else:
                    print("❌ No person data found in deal")
            else:
                print("❌ Could not explore deal data")
        else:
            print("❌ No deal ID found in organization")
    else:
        print("❌ Could not explore organization data")
    
    print()
    print("🎯 **Exploration Complete!**")
    print("Check the output above to see what fields are available for mapping.")

if __name__ == "__main__":
    main()
