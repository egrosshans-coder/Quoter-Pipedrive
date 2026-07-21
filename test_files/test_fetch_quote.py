#!/usr/bin/env python3
"""Fetch an existing quote by id and inspect its line items.
Tests whether a template-created quote has line items via the v2 API
(sidesteps the client_id blocker — we're reading, not creating)."""
import json
from scalepad_v2 import ScalePadV2Client
c = ScalePadV2Client()

quote_id = "quot_3AHHyZ6H4PMgJJ6Ogjh3EiOg30m"  # the zz34 draft from the screenshot
path = f"/quoter/v1/quotes/{quote_id}"
print("GET", path); print("="*70)
try:
    q = c.get(path)
except Exception as e:
    print("✗", str(e)[:300]); raise SystemExit

print("name        :", q.get("name"))
print("draft       :", q.get("draft"))
print("number      :", q.get("number"), " custom_number:", q.get("custom_number"))
print("template_id :", q.get("template_id"))
print("client      :", q.get("client"))
print("contacts    :", q.get("contacts"))

sections = q.get("sections") or []
print("\nsections    :", len(sections))
total_items = 0
for s in sections:
    lis = s.get("line_items") or []
    total_items += len(lis)
    print(f"  section '{s.get('name')}' — {len(lis)} line item(s)")
    for li in lis:
        print(f"    name={li.get('name')!r} code={li.get('code')!r} "
              f"sku={li.get('sku')!r} qty={li.get('quantity_decimal')} "
              f"unit_price={li.get('unit_price_decimal')}")

print("\n" + "="*70)
if total_items > 0:
    print(f"✅ {total_items} line items present via API on a TEMPLATE-CREATED quote.")
    print("   => Strong evidence templates SEED line items. Item Group mirror likely UNNEEDED.")
else:
    print("❌ No line items via API — even though the UI showed them. Investigate.")

print("\n--- raw (first 3000 chars) ---")
print(json.dumps(q, indent=2)[:3000])
