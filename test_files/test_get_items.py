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
# Get Items
# ==========================================================

url = "https://api.scalepad.com/quoter/v1/items?page_size=200"

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

    print(f"\nTotal Items Returned : {len(data.get('data', []))}")
    print(f"Total Items Available: {data.get('total_count')}")
    print("-" * 100)

    for item in data.get("data", []):
        print(f"Name : {item.get('name')}")
        print(f"ID   : {item.get('id')}")
        print(f"Code : {item.get('code')}")
        print(f"SKU  : {item.get('sku')}")
        print("-" * 100)

    if data.get("next_cursor"):
        print("\nNext Cursor:")
        print(data["next_cursor"])

except ValueError:
    print(response.text)
