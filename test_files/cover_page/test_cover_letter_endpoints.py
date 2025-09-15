#!/usr/bin/env python3
"""
Test different endpoints for cover letter content
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quoter import get_access_token
import requests

def test_cover_letter_endpoints():
    print("🔍 TESTING COVER LETTER ENDPOINTS")
    print("=" * 50)
    
    # Get access token
    access_token = get_access_token()
    if not access_token:
        print("❌ No access token")
        return
    
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    
    # Use one of the quotes we created
    quote_id = "quot_32hcKDfHkPeH82RLFJzvbChTkjQ"
    
    # Test different endpoints that might contain cover letter content
    endpoints_to_test = [
        f"/v1/quotes/{quote_id}/content",
        f"/v1/quotes/{quote_id}/cover_letter",
        f"/v1/quotes/{quote_id}/cover_page",
        f"/v1/quotes/{quote_id}/pages",
        f"/v1/quotes/{quote_id}/sections",
        f"/v1/quotes/{quote_id}/template_content",
        f"/v1/quote_contents/{quote_id}",
        f"/v1/quote_pages/{quote_id}",
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 Testing endpoint: {endpoint}")
        
        try:
            response = requests.get(
                f"https://api.quoter.com{endpoint}",
                headers=headers,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Look for cover letter content
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, str) and ('cover' in key.lower() or 'letter' in key.lower() or 'content' in key.lower()):
                            print(f"      {key}: {value[:100]}...")
                elif isinstance(data, list) and data:
                    print(f"      List with {len(data)} items")
                    if data and isinstance(data[0], dict):
                        print(f"      First item keys: {list(data[0].keys())}")
                        
            elif response.status_code == 404:
                print(f"   ❌ Not found")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    test_cover_letter_endpoints()
