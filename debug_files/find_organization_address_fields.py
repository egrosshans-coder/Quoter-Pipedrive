#!/usr/bin/env python3
"""
Find organization address field keys in Pipedrive (street, city, state, zip).
Lists all organization custom fields and highlights address-related ones.
Use the reported keys in webhook body as {{organization.<key>}}.
"""

import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipedrive import API_TOKEN, BASE_URL


# Keywords to match address-related field names/keys
ADDRESS_KEYWORDS = (
    "address", "street", "city", "state", "zip", "postal",
    "locality", "route", "country", "admin_area", "subpremise"
)


def find_organization_address_fields():
    """
    List all organization fields and highlight address-related ones with their keys.
    """
    print("🔍 Fetching organization fields from Pipedrive...")
    print("=" * 70)

    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in .env")
        return None

    try:
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

        address_fields = []
        for field in fields:
            name = (field.get("name") or "").lower()
            key = (field.get("key") or "").lower()
            field_key = field.get("key", "")
            field_name = field.get("name", "")
            field_type = field.get("field_type", "")

            is_address = any(kw in name or kw in key for kw in ADDRESS_KEYWORDS)
            if is_address:
                address_fields.append({
                    "name": field_name,
                    "key": field_key,
                    "type": field_type,
                })

        # Report address-related fields
        print("🎯 ADDRESS-RELATED ORGANIZATION FIELDS (for webhook use {{organization.<key>}}):")
        print("-" * 70)
        if address_fields:
            for f in address_fields:
                print(f"   {f['name']}")
                print(f"      Key:  {f['key']}")
                print(f"      Webhook:  {{{{organization.{f['key']}}}}}")
                print(f"      Type: {f['type']}")
                print()
        else:
            print("   No custom address fields found.")
            print("   Pipedrive may use standard fields: address, address_locality,")
            print("   address_admin_area_level_1, address_postal_code, address_country")
            print("   (Check one organization via API to see actual keys.)")

        # Optional: show all fields so user can spot street/city/state/zip by name
        print()
        print("📋 ALL ORGANIZATION FIELDS (name → key):")
        print("-" * 70)
        for field in fields:
            name = field.get("name", "")
            key = field.get("key", "")
            marker = "  🏠" if any(kw in (name + key).lower() for kw in ADDRESS_KEYWORDS) else "   "
            print(f"{marker} {name}")
            print(f"      key: {key}  →  {{{{organization.{key}}}}}")
            print()

        return address_fields

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def show_org_address_keys_from_sample(org_id=None):
    """
    GET one organization and print all keys that look like address.
    Use this to see actual keys returned by API (standard vs custom).
    """
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found")
        return
    if not org_id:
        # Try to get any org from a recent search
        r = requests.get(
            f"{BASE_URL}/organizations",
            params={"api_token": API_TOKEN, "limit": 1},
            timeout=10,
        )
        if r.status_code != 200:
            print("❌ Could not fetch organizations")
            return
        data = r.json().get("data", [])
        if not data:
            print("❌ No organizations found")
            return
        org_id = data[0]["id"]
        print(f"📌 Using first organization ID: {org_id}\n")

    r = requests.get(
        f"{BASE_URL}/organizations/{org_id}",
        params={"api_token": API_TOKEN},
        timeout=10,
    )
    if r.status_code != 200:
        print(f"❌ Failed to get organization {org_id}: {r.status_code}")
        return
    org = r.json().get("data", {})
    keys = list(org.keys())
    address_like = [k for k in keys if any(w in k.lower() for w in ADDRESS_KEYWORDS)]
    print(f"🔍 Organization {org_id} – address-related keys and values:")
    print("-" * 70)
    for k in sorted(address_like):
        print(f"   {k}: {org.get(k)}")
    if not address_like:
        print("   (No address-like keys in response. Keys present:", keys[:20], "...")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Find Pipedrive organization address field keys")
    ap.add_argument("--sample-org", type=int, default=None, help="Org ID to inspect for actual address keys")
    args = ap.parse_args()

    find_organization_address_fields()

    if args.sample_org is not None or os.getenv("SHOW_SAMPLE_ORG"):
        print()
        show_org_address_keys_from_sample(args.sample_org)
