#!/usr/bin/env python3
"""Probe for a Clients endpoint that returns client.id (UUID). Run from quoter_sync."""
import json
from scalepad_v2 import ScalePadV2Client
c = ScalePadV2Client()

# Try likely client/customer endpoints and filters
paths = [
    "/quoter/v1/clients?page_size=50",
    "/quoter/v1/clients?filter[name]=cont:zz50",
    "/quoter/v1/customers?page_size=50",
    "/quoter/v1/organizations?page_size=50",
]
for p in paths:
    print("="*70); print("GET", p); print("="*70)
    try:
        r = c.get(p)
    except Exception as e:
        print("  ✗", str(e)[:200]); continue
    rows = r.get("data", []) if isinstance(r, dict) else []
    print(f"  total_count={r.get('total_count')}  rows={len(rows)}")
    if rows:
        print("  keys:", list(rows[0].keys()))
        for x in rows[:5]:
            print("   ", json.dumps(x)[:300])
    print()
