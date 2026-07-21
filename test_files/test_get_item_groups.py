import os
import json
import requests
from dotenv import load_dotenv

# ==========================================================
# Load Environment
# ==========================================================

load_dotenv()

API_KEY = os.getenv("SCALEPAD_API_KEY")

if not API_KEY:
    raise ValueError("Missing SCALEPAD_API_KEY in .env")

# ==========================================================
# Get Item Groups
# ==========================================================

url = "https://api.scalepad.com/quoter/v1/item-groups"

headers = {
    "x-api-key": API_KEY,
    "accept": "application/json",
}

response = requests.get(
    url,
    headers=headers,
    timeout=30,
)

# ==========================================================
# Display Results
# ==========================================================

print(f"Status: {response.status_code}")

try:
    data = response.json()

    print(f"\nTotal Groups: {data.get('total_count', 0)}")
    print("-" * 60)

    for group in data.get("data", []):
        print(f"Name    : {group['name']}")
        print(f"ID      : {group['id']}")
        print(f"Created : {group.get('record_created_at')}")
        print(f"Updated : {group.get('record_updated_at')}")
        print("-" * 60)

except ValueError:
    print(response.text)
