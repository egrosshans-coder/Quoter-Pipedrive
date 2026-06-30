import os
import requests
from dotenv import load_dotenv

load_dotenv()
# Same as quoter.py: OAuth client_id comes from QUOTER_API_KEY
client_id = (os.getenv("QUOTER_API_KEY") or "").strip()
client_secret = (os.getenv("QUOTER_CLIENT_SECRET") or "").strip()

print("Client ID (QUOTER_API_KEY) len:", len(client_id), "prefix:", client_id[:10] if client_id else "(empty)")
print("Secret len:", len(client_secret), "prefix:", client_secret[:6] if client_secret else "(empty)")

r = requests.post(
    "https://api.quoter.com/v1/auth/oauth/authorize",
    json={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    },
    headers={"Accept": "application/json"},
)

print("AUTH Status:", r.status_code)
print("AUTH Body:", r.text[:500])

if r.status_code != 200:
    print("Auth failed, skipping quote fetch")
else:
    data = r.json()
    access_token = data.get("access_token")
    if not access_token:
        print("No access_token in response")
    else:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        # List quotes – see if token has any quote read permission
        r_list = requests.get(
            "https://api.quoter.com/v1/quotes",
            headers=headers,
            timeout=10,
        )
        print("QUOTES LIST STATUS:", r_list.status_code)
        print("QUOTES LIST BODY:", r_list.text[:500])

        # Single quote – use an ID from the list so we're sure it's in this account
        quote_id = "8100244"
        if r_list.status_code == 200:
            list_data = r_list.json()
            items = list_data.get("data") or []
            if items:
                quote_id = str(items[0].get("id", quote_id))
                print("Using quote ID from list:", quote_id)
            else:
                print("List empty, using hardcoded quote_id:", quote_id)

        r2 = requests.get(
            f"https://api.quoter.com/v1/quotes/{quote_id}",
            headers=headers,
            timeout=10,
        )
        print("QUOTE STATUS:", r2.status_code)
        print("QUOTE BODY:", r2.text[:500])
