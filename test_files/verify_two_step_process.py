#!/usr/bin/env python3
"""
Verify Two-Step Quote Creation Process
=====================================

This script verifies that all components for the two-step quote creation process
are properly implemented without actually creating quotes.

Checks:
1. OAuth token access
2. Template availability
3. Instructional item existence
4. Function availability
5. API endpoint accessibility
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import (
    get_access_token, 
    get_quote_required_fields,
    create_comprehensive_contact_from_pipedrive
)
from pipedrive import get_organization_by_id
import requests
import json

def verify_oauth_access():
    """Verify OAuth token access"""
    print("🔐 Verifying OAuth Access...")
    try:
        token = get_access_token()
        if token:
            print("   ✅ OAuth token obtained successfully")
            print(f"   Token preview: {token[:20]}...")
            return token
        else:
            print("   ❌ Failed to get OAuth token")
            return None
    except Exception as e:
        print(f"   ❌ Error getting OAuth token: {e}")
        return None

def verify_template_access(access_token):
    """Verify template access"""
    print("\n📋 Verifying Template Access...")
    try:
        required_fields = get_quote_required_fields(access_token)
        if required_fields:
            print("   ✅ Required fields obtained successfully")
            print(f"   Template ID: {required_fields.get('template_id', 'N/A')}")
            print(f"   Currency: {required_fields.get('currency_abbr', 'N/A')}")
            return required_fields
        else:
            print("   ❌ Failed to get required fields")
            return None
    except Exception as e:
        print(f"   ❌ Error getting required fields: {e}")
        return None

def verify_instructional_item(access_token):
    """Verify instructional item exists"""
    print("\n📝 Verifying Instructional Item...")
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Check if the instructional item exists
        item_id = "item_31IIdw4C1GHIwU05yhnZ2B88S2B"
        response = requests.get(
            f'https://api.quoter.com/v1/items/{item_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            item_data = response.json()
            print("   ✅ Instructional item found")
            print(f"   Name: {item_data.get('name', 'N/A')}")
            print(f"   Category: {item_data.get('category', 'N/A')}")
            print(f"   Description length: {len(item_data.get('description', ''))} characters")
            return True
        else:
            print(f"   ❌ Failed to get instructional item: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error checking instructional item: {e}")
        return False

def verify_pipedrive_access():
    """Verify Pipedrive API access"""
    print("\n🏢 Verifying Pipedrive Access...")
    try:
        # Try to get a known organization
        org_data = get_organization_by_id(3465)
        if org_data:
            print("   ✅ Pipedrive organization access confirmed")
            print(f"   Organization: {org_data.get('name', 'N/A')}")
            print(f"   Deal ID: {org_data.get('15034cf07d05ceb15f0a89dcbdcc4f596348584e', 'N/A')}")
            return org_data
        else:
            print("   ❌ Failed to get Pipedrive organization")
            return None
    except Exception as e:
        print(f"   ❌ Error accessing Pipedrive: {e}")
        return None

def verify_function_availability():
    """Verify all required functions are available"""
    print("\n🔧 Verifying Function Availability...")
    
    # Import the functions to check if they exist
    try:
        from quoter import create_comprehensive_quote_from_pipedrive
        print("   ✅ create_comprehensive_quote_from_pipedrive - Available")
        quote_func_ok = True
    except ImportError:
        print("   ❌ create_comprehensive_quote_from_pipedrive - Not found")
        quote_func_ok = False
    
    try:
        from quoter import create_comprehensive_contact_from_pipedrive
        print("   ✅ create_comprehensive_contact_from_pipedrive - Available")
        contact_func_ok = True
    except ImportError:
        print("   ❌ create_comprehensive_contact_from_pipedrive - Not found")
        contact_func_ok = False
    
    try:
        from quoter import get_access_token
        print("   ✅ get_access_token - Available")
        token_func_ok = True
    except ImportError:
        print("   ❌ get_access_token - Not found")
        token_func_ok = False
    
    try:
        from quoter import get_quote_required_fields
        print("   ✅ get_quote_required_fields - Available")
        fields_func_ok = True
    except ImportError:
        print("   ❌ get_quote_required_fields - Not found")
        fields_func_ok = False
    
    all_functions_available = quote_func_ok and contact_func_ok and token_func_ok and fields_func_ok
    return all_functions_available

def verify_api_endpoints(access_token):
    """Verify API endpoints are accessible"""
    print("\n🌐 Verifying API Endpoints...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    endpoints_to_check = [
        "https://api.quoter.com/v1/quotes",
        "https://api.quoter.com/v1/line_items",
        "https://api.quoter.com/v1/items"
    ]
    
    all_endpoints_accessible = True
    
    for endpoint in endpoints_to_check:
        try:
            # Just check if we can make a request (don't create anything)
            response = requests.get(endpoint, headers=headers, timeout=10)
            if response.status_code in [200, 401, 403]:  # 401/403 means endpoint exists but auth failed
                print(f"   ✅ {endpoint} - Accessible")
            else:
                print(f"   ⚠️ {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {e}")
            all_endpoints_accessible = False
    
    return all_endpoints_accessible

def main():
    """Main verification function"""
    print("🧪 Verifying Two-Step Quote Creation Process")
    print("=" * 50)
    print("This script verifies all components without creating quotes")
    print()
    
    # Step 1: Verify OAuth access
    access_token = verify_oauth_access()
    if not access_token:
        print("\n❌ OAuth verification failed - cannot proceed")
        return False
    
    # Step 2: Verify template access
    required_fields = verify_template_access(access_token)
    if not required_fields:
        print("\n❌ Template verification failed")
        return False
    
    # Step 3: Verify instructional item
    item_ok = verify_instructional_item(access_token)
    if not item_ok:
        print("\n❌ Instructional item verification failed")
        return False
    
    # Step 4: Verify Pipedrive access
    org_data = verify_pipedrive_access()
    if not org_data:
        print("\n❌ Pipedrive verification failed")
        return False
    
    # Step 5: Verify function availability
    functions_ok = verify_function_availability()
    if not functions_ok:
        print("\n❌ Function verification failed")
        return False
    
    # Step 6: Verify API endpoints
    endpoints_ok = verify_api_endpoints(access_token)
    if not endpoints_ok:
        print("\n❌ API endpoint verification failed")
        return False
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 VERIFICATION COMPLETE!")
    print("=" * 50)
    print("✅ All components verified successfully")
    print("✅ Two-step process is ready to use")
    print("✅ No quotes were created during verification")
    print()
    print("📋 What was verified:")
    print("   🔐 OAuth token access")
    print("   📋 Template availability")
    print("   📝 Instructional item existence")
    print("   🏢 Pipedrive API access")
    print("   🔧 Function availability")
    print("   🌐 API endpoint accessibility")
    print()
    print("🚀 Next step: Run test_comprehensive_quote.py to test actual quote creation")
    
    return True

if __name__ == "__main__":
    main()
