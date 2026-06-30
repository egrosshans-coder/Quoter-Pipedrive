#!/usr/bin/env python3
"""
List ALL field keys returned by Pipedrive for one organization.
Use this to verify the correct merge tags for webhooks: {{organization.<key>}}

Standard (non-custom) address fields in Pipedrive use these API keys:
  - address              (full address string)
  - address_locality      (city)
  - address_admin_area_level_1  (state)
  - address_postal_code   (zip)   <-- NOT "zipcode"
  - address_country      (country)
  - address_subpremise   (line 2 / suite)
  - address_street_number, address_route  (street components)

Run from quoter_sync with .env set:
  python3 debug_files/list_organization_api_keys.py [ORG_ID]
"""

import sys
import os
import requests

BASE_URL = "https://api.pipedrive.com/v1"

# Load API_TOKEN: from env, or from quoter_sync/.env (no dotenv required)
API_TOKEN = os.environ.get("PIPEDRIVE_API_TOKEN")
if not API_TOKEN:
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    if k.strip() == "PIPEDRIVE_API_TOKEN":
                        API_TOKEN = v.strip().strip('"').strip("'")
                        break

# Standard address keys Pipedrive uses (for reference in output)
ADDRESS_KEYS = {
    "address",
    "address_subpremise",
    "address_street_number",
    "address_route",
    "address_locality",
    "address_admin_area_level_1",
    "address_postal_code",
    "address_country",
}


def list_organization_keys(org_id=None):
    if not API_TOKEN:
        print("❌ PIPEDRIVE_API_TOKEN not found in .env")
        return

    if not org_id:
        r = requests.get(
            f"{BASE_URL}/organizations",
            params={"api_token": API_TOKEN, "limit": 1},
            timeout=10,
        )
        if r.status_code != 200:
            print("❌ Failed to fetch organizations:", r.status_code)
            return
        data = r.json().get("data", [])
        if not data:
            print("❌ No organizations found")
            return
        org_id = data[0]["id"]
        print(f"📌 No ORG_ID given – using first organization: {org_id}\n")

    r = requests.get(
        f"{BASE_URL}/organizations/{org_id}",
        params={"api_token": API_TOKEN},
        timeout=10,
    )
    if r.status_code != 200:
        print(f"❌ Failed to get organization {org_id}: {r.status_code}")
        return

    org = r.json().get("data", {})
    if not org:
        print("❌ No organization data in response")
        return

    keys = sorted(org.keys())
    print("=" * 70)
    print(f"Organization ID: {org_id}  |  Name: {org.get('name', 'N/A')}")
    print("=" * 70)
    print("\n✅ Use these EXACT keys in your webhook body as:  {{organization.<key>}}\n")
    print("ALL KEYS RETURNED BY API (key → value):")
    print("-" * 70)

    for k in keys:
        val = org.get(k)
        if val is None or val == "":
            val_str = "(empty)"
        elif isinstance(val, (dict, list)):
            val_str = str(val)[:60] + "..." if len(str(val)) > 60 else str(val)
        else:
            val_str = str(val)[:50] + "..." if len(str(val)) > 50 else str(val)
        is_address = "  [address]" if k in ADDRESS_KEYS else ""
        print(f"  {k}{is_address}")
        print(f"      → value: {val_str}")
        print(f"      → webhook: {{{{organization.{k}}}}}")
        print()

    print("-" * 70)
    print("ADDRESS FIELDS (for street, city, state, zip):")
    print("-" * 70)
    for k in sorted(ADDRESS_KEYS):
        in_response = "✓ in response" if k in org else "✗ not in response"
        print(f"  {k}: {org.get(k, '(missing)')}  {in_response}")
        print(f"      Webhook: {{{{organization.{k}}}}}")
    print()
    print("NOTE: Zip is 'address_postal_code', not 'zipcode'.")
    print("      City is 'address_locality'. State is 'address_admin_area_level_1'.")


if __name__ == "__main__":
    org_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    list_organization_keys(org_id)
