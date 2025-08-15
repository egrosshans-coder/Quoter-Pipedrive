#!/usr/bin/env python3
"""
Test script to examine GET /contacts and test different search strategies
for finding existing contacts to prevent duplication.
"""

import requests
import json
from quoter import get_access_token

def test_contacts_search():
    """Test different ways to search for existing contacts."""
    
    print("🔍 Testing Contacts Search Strategies")
    print("=" * 50)
    print("Goal: Find the best way to search for existing contacts")
    print()
    
    # Get OAuth access token
    access_token = get_access_token()
    if not access_token:
        print("❌ Failed to get OAuth token")
        return
    
    print(f"✅ Got access token: {access_token[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test GET /contacts
        print("📡 Testing GET /contacts...")
        response = requests.get(
            "https://api.quoter.com/v1/contacts",
            headers=headers,
            timeout=10
        )
        
        print(f"📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            contacts = data.get("data", [])
            
            print(f"✅ Found {len(contacts)} contacts")
            print()
            
            # Show first few contacts to understand structure
            print("📋 Sample Contact Structure:")
            for i, contact in enumerate(contacts[:3]):
                print(f"\n--- Contact {i+1} ---")
                print(f"ID: {contact.get('id')}")
                print(f"Name: {contact.get('name')}")
                print(f"First Name: {contact.get('first_name')}")
                print(f"Last Name: {contact.get('last_name')}")
                print(f"Organization: {contact.get('organization')}")
                print(f"Email: {contact.get('email')}")
                print(f"Phone: {contact.get('phone')}")
                print(f"Pipedrive Contact ID: {contact.get('pipedrive_contact_id')}")
            
            # Look for Robert Lee specifically
            print(f"\n🔍 Searching for 'Robert Lee' contacts...")
            robert_lees = []
            for contact in contacts:
                if contact.get('name') and 'robert' in contact.get('name').lower() and 'lee' in contact.get('name').lower():
                    robert_lees.append(contact)
            
            if robert_lees:
                print(f"✅ Found {len(robert_lees)} Robert Lee contacts:")
                for i, contact in enumerate(robert_lees):
                    print(f"  {i+1}. ID: {contact.get('id')}")
                    print(f"     Name: {contact.get('name')}")
                    print(f"     Organization: {contact.get('organization')}")
                    print(f"     Email: {contact.get('email')}")
                    print(f"     Pipedrive ID: {contact.get('pipedrive_contact_id')}")
                    print()
            else:
                print("❌ No Robert Lee contacts found")
            
            # Look for contacts with organization "Blue Owl Capital"
            print(f"\n🔍 Searching for 'Blue Owl Capital' organization...")
            blue_owl_contacts = []
            for contact in contacts:
                org = contact.get('organization')
                if org and 'blue owl' in org.lower():
                    blue_owl_contacts.append(contact)
            
            if blue_owl_contacts:
                print(f"✅ Found {len(blue_owl_contacts)} Blue Owl Capital contacts:")
                for i, contact in enumerate(blue_owl_contacts):
                    print(f"  {i+1}. ID: {contact.get('id')}")
                    print(f"     Name: {contact.get('name')}")
                    print(f"     Organization: {contact.get('organization')}")
                    print(f"     Email: {contact.get('email')}")
                    print()
            else:
                print("❌ No Blue Owl Capital contacts found")
            
            # Test search by email
            test_email = "robert.lee@blueowl.com"
            print(f"\n🔍 Testing search by email: {test_email}")
            email_matches = []
            for contact in contacts:
                emails = contact.get('email', [])
                if isinstance(emails, list):
                    for email_item in emails:
                        if email_item.get('value') == test_email:
                            email_matches.append(contact)
                            break
                elif isinstance(emails, str) and emails == test_email:
                    email_matches.append(contact)
            
            if email_matches:
                print(f"✅ Found {len(email_matches)} contacts with email {test_email}:")
                for contact in email_matches:
                    print(f"  - {contact.get('name')} (ID: {contact.get('id')})")
            else:
                print(f"❌ No contacts found with email {test_email}")
            
            print(f"\n💡 Search Strategy Recommendations:")
            print(f"   1. Search by exact email first (most reliable)")
            print(f"   2. Search by name + organization combination")
            print(f"   3. Search by Pipedrive contact ID if available")
            print(f"   4. Only create new contact if no matches found")
            
        else:
            print(f"❌ Failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_contacts_search()
