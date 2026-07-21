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
# Create Item Group
# ==========================================================

url = "https://api.scalepad.com/quoter/v1/item-groups"

headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "x-api-key": API_KEY,
}

payload = {
    "name": "TEST-Balloons"
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=30
)

# ==========================================================
# Display Results
# ==========================================================

print(f"Status: {response.status_code}")

try:
    print(json.dumps(response.json(), indent=2))
except ValueError:
    print(response.text)
