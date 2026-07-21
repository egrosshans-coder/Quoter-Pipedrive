#!/usr/bin/env python3
"""
test_contact_lookup.py
Prove email -> client_id resolution before chaining into quote creation.
Run from quoter_sync (imports scalepad_v2). Needs .env SCALEPAD_API_KEY + a known email.
"""
import json, sys
from scalepad_v2 import ScalePadV2Client

EMAIL = None   # optional: hard-set to skip prompt, e.g. "eric@tlciscreative.com"

def main():
    client = ScalePadV2Client()
    email = EMAIL or input("Email to look up (billing_email): ").strip()
    if not email:
        print("❌ Need an email."); sys.exit(1)

    normalized = email.strip().lower()
    if normalized != email:
        print(f"ℹ️  Normalized '{email}' -> '{normalized}'")
    email = normalized

    path = f"/quoter/v1/contacts?filter[billing_email]=eq:{email}"
    print("="*70); print("GET", path); print("="*70)
    try:
        r = client.get(path)
    except Exception as e:
        print(f"❌ Lookup failed: {e}"); sys.exit(1)

    rows = r.get("data", []) if isinstance(r, dict) else []
    total = r.get("total_count") if isinstance(r, dict) else None
    print(f"total_count: {total}   |   rows returned: {len(rows)}")
    print("-"*70)

    if not rows:
        print("❌ NO CONTACT FOUND — in Render this is the 'create contact' branch.")
        sys.exit(0)

    for i, c in enumerate(rows, 1):
        contact_id = c.get("id")
        client_id = (c.get("client") or {}).get("id")
        print(f"MATCH {i}:")
        print(f"  contact id    : {contact_id}  ({'LINKED' if contact_id else 'UNLINKED (id null)'})")
        print(f"  client.id     : {client_id}   <-- createQuote's client_id")
        print(f"  billing_email : {c.get('billing_email')}")
        print(f"  billing_name  : {c.get('billing_first_name')} {c.get('billing_last_name')}")
        print(f"  billing_org   : {c.get('billing_organization')}")
        print("-"*70)

    print("="*70); print("VERDICT"); print("="*70)
    if len(rows) == 1:
        cid = (rows[0].get("client") or {}).get("id")
        if cid:
            print(f"✅ CLEAN: one contact, client.id present.\n   client_id = {cid}")
        else:
            print("⚠️  One contact but client.id NULL — investigate (unlinked/backfill).")
    else:
        print(f"⚠️  {len(rows)} contacts share this email — ambiguous, ALERT don't guess.")

    print("\n--- Raw first record ---")
    print(json.dumps(rows[0], indent=2)[:2500])

if __name__ == "__main__":
    main()
