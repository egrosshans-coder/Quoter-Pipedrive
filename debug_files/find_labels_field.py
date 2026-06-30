#!/usr/bin/env python3
"""
Find the Labels field key for Organizations in Pipedrive.
This helps fix the "NOT FOUND" error in Pipedrive automations.

The Labels field is a default field but may need to be referenced by its API key
rather than its display name in automations.
"""

import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipedrive import API_TOKEN, BASE_URL


def find_labels_field():
    """
    Find the Labels field key for Organizations.
    """
    print("🔍 Finding Labels field for Organizations...")
    print("=" * 70)

    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in .env")
        return None

    try:
        # Get all organization fields
        url = f"{BASE_URL}/organizationFields"
        params = {"api_token": API_TOKEN}
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print(f"❌ API error: {response.status_code}")
            print(response.text[:500])
            return None

        data = response.json()
        fields = data.get("data", [])

        print(f"📋 Total organization fields: {len(fields)}\n")

        # Look for Labels field (case-insensitive)
        labels_fields = []
        for field in fields:
            name = field.get("name", "").lower()
            key = field.get("key", "").lower()
            field_key = field.get("key", "")
            field_name = field.get("name", "")
            field_type = field.get("field_type", "")
            is_default = field.get("add_time", None) is None  # Default fields typically don't have add_time

            # Check if it's a labels field
            if "label" in name or "label" in key:
                labels_fields.append({
                    "name": field_name,
                    "key": field_key,
                    "type": field_type,
                    "is_default": is_default,
                    "field_data": field
                })

        # Report Labels fields
        print("🏷️  LABELS-RELATED FIELDS:")
        print("-" * 70)
        if labels_fields:
            for f in labels_fields:
                default_marker = " (DEFAULT)" if f["is_default"] else " (CUSTOM)"
                print(f"   {f['name']}{default_marker}")
                print(f"      Key:  {f['key']}")
                print(f"      Type: {f['type']}")
                print(f"      Automation reference: Use field key '{f['key']}'")
                print()
        else:
            print("   ❌ No Labels field found!")
            print("   This might be a Pipedrive API issue or the field might be disabled.")

        # Also check a sample organization to see what label fields are actually returned
        print("\n🔍 Checking a sample organization for label fields...")
        print("-" * 70)
        
        # Get a sample organization
        org_response = requests.get(
            f"{BASE_URL}/organizations",
            params={"api_token": API_TOKEN, "limit": 1},
            timeout=10
        )
        
        if org_response.status_code == 200:
            orgs = org_response.json().get("data", [])
            if orgs:
                org_id = orgs[0]["id"]
                org_detail_response = requests.get(
                    f"{BASE_URL}/organizations/{org_id}",
                    params={"api_token": API_TOKEN},
                    timeout=10
                )
                
                if org_detail_response.status_code == 200:
                    org_data = org_detail_response.json().get("data", {})
                    label_keys = [k for k in org_data.keys() if "label" in k.lower()]
                    
                    if label_keys:
                        print(f"   Found label-related keys in organization {org_id}:")
                        for key in label_keys:
                            value = org_data.get(key)
                            print(f"      {key}: {value}")
                    else:
                        print(f"   No label-related keys found in organization {org_id}")
                        print(f"   Available keys (first 20): {list(org_data.keys())[:20]}")
        else:
            print(f"   Could not fetch sample organization: {org_response.status_code}")

        # Based on Pipedrive API docs, Labels field might be referenced as:
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("-" * 70)
        print("1. In Pipedrive automations, try using the field KEY instead of the field NAME")
        print("2. The Labels field might be referenced as 'label_ids' in the API")
        print("3. Check if the field is enabled in Settings > Fields > Organizations")
        print("4. Try removing and re-adding the Labels field in your automation")
        print("5. If using merge tags, try: {{organization.label_ids}} or {{organization.<key>}}")
        print("\n6. Common Labels field keys:")
        print("   - 'label_ids' (new Labels field, multiple options)")
        print("   - 'label' (old single Label field)")
        
        return labels_fields

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    find_labels_field()
