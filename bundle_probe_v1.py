#!/usr/bin/env python3
"""
bundle_probe_v1.py — does a Quoter Bundle behave like an item to the API?

THE QUESTION
------------
A Bundle is built on the Item model (the add form posts data[Item][title]).
If a Bundle surfaces in GET /items with its own item_id, then:

  * it can be assigned to an Item Group, and
  * Render could post ONE id and have the API expand it into members.

That would let each Item Group hold "6 feature items + 1 XTE bundle ref"
instead of 14 flat items, so shared blocks are maintained in one place.

If instead the Bundle is absent from /items, or posts as a single opaque
line, then bundles are a UI convenience only and Item Groups must carry
every item flat. Both are workable; this decides which.

PHASES
------
  Phase 1 (default)  READ ONLY. Looks for the bundle in GET /items and
                     reports its shape.
  Phase 2 (--write)  Posts the bundle's item_id as ONE line item to a
                     section on the zz test quote, then reads the quote
                     back and counts what actually landed.

Phase 2 writes only to quote quot_3I9UCyBcqZJ39soTFYS5SodFzlW, which is
already tagged test data and slated for deletion.

Usage:
    export SCALEPAD_API_KEY='...'
    python3 bundle_probe_v1.py
    python3 bundle_probe_v1.py --write
"""

import argparse
import http.client
import json
import os
import ssl
import sys
import time
import urllib.parse

BASE = "https://api.scalepad.com/quoter/v1"
HOST = "api.scalepad.com"
BUNDLE_NAME = "zz-TEST-Bundle-TE"
TEST_QUOTE = "quot_3I9UCyBcqZJ39soTFYS5SodFzlW"

API_KEY = os.environ.get("SCALEPAD_API_KEY", "").strip()
if not API_KEY:
    sys.exit("ERROR: set SCALEPAD_API_KEY first.")
if API_KEY.startswith("cid_"):
    sys.exit("ERROR: that is a legacy Quoter client_id, not a ScalePad key.")


def req(method, path, params=None, body=None, timeout=30):
    """Lowercase x-api-key is mandatory -- Chapter 3 addendum 2.1.1."""
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote,
                                            safe="[]:")
    parts = urllib.parse.urlsplit(url)
    target = parts.path + (("?" + parts.query) if parts.query else "")
    payload = json.dumps(body).encode() if body is not None else None
    conn = None
    try:
        conn = http.client.HTTPSConnection(HOST, timeout=timeout,
                                           context=ssl.create_default_context())
        conn.putrequest(method, target, skip_accept_encoding=True)
        conn.putheader("x-api-key", API_KEY)
        conn.putheader("Accept", "application/json")
        if payload:
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", str(len(payload)))
        conn.endheaders()
        if payload:
            conn.send(payload)
        r = conn.getresponse()
        raw = r.read().decode("utf-8", "replace")
        try:
            return r.status, json.loads(raw)
        except json.JSONDecodeError:
            return r.status, raw[:1200]
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def fetch_all(path):
    s, b = req("GET", path)
    if s != 200 or not isinstance(b, dict):
        return [], None
    rows = list(b.get("data", []))
    total = b.get("total_count")
    cur = b.get("next_cursor")
    seen = {cur}
    while cur:
        s2, b2 = req("GET", path, params={"cursor": cur})
        if s2 != 200 or not isinstance(b2, dict):
            break
        batch = b2.get("data", [])
        if not batch:
            break
        rows.extend(batch)
        cur = b2.get("next_cursor")
        if cur in seen:
            break
        seen.add(cur)
        time.sleep(0.15)
    return rows, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    print("=" * 72)
    print(f"BUNDLE PROBE  [{'WRITE' if a.write else 'READ ONLY'}]")
    print("=" * 72)

    items, total = fetch_all("/items")
    print(f"\ncatalog: {len(items)} of {total}")

    hit = next((i for i in items
                if (i.get("name") or "").strip() == BUNDLE_NAME), None)

    if not hit:
        print(f"\nRESULT: {BUNDLE_NAME!r} does NOT appear in GET /items.")
        print("Bundles are not exposed as catalog items, so they cannot be")
        print("assigned to an Item Group. Item Groups must carry every item")
        print("flat; bundles remain a quote-builder convenience only.")
        near = [i.get("name") for i in items
                if "zz-TEST" in (i.get("name") or "")]
        if near:
            print(f"\n(similar names present: {near})")
        # Did the count move? 297 was pre-bundle.
        print(f"\ntotal_count is now {total} (was 297 before the bundle).")
        return

    print(f"\nFOUND in /items: {BUNDLE_NAME}")
    print(f"  item_id  : {hit.get('id')}")
    print(f"  code     : {hit.get('code')}")
    print(f"  category : {hit.get('category')}")
    print(f"  price    : {hit.get('price_decimal')}   cost: {hit.get('cost_decimal')}")
    print(f"  pricing  : {hit.get('pricing_scheme')}")
    print("\n  full record:")
    print("   " + json.dumps(hit, indent=2)[:1500].replace("\n", "\n   "))

    bundle_fields = {k: v for k, v in hit.items() if "bundle" in k.lower()}
    print(f"\n  bundle-related fields: {bundle_fields or '(none)'}")
    print("\n  ^ If no member list appears here, the API exposes the bundle as")
    print("    a single item and does not reveal its contents on read.")

    if not a.write:
        print("\n" + "=" * 72)
        print("READ-ONLY done. Rerun with --write to post this one item_id to a")
        print(f"section on {TEST_QUOTE} and count what lands.")
        print("=" * 72)
        return

    # --- Phase 2: does posting the bundle id expand into members? ----------
    print("\n" + "=" * 72)
    print("PHASE 2 — posting the bundle as ONE line item")
    print("=" * 72)

    s, b = req("GET", f"/quotes/{TEST_QUOTE}")
    if s != 200:
        sys.exit(f"ABORT: cannot read test quote ({s})")
    d = b.get("data", b)
    sections = d.get("sections") or []
    if not sections:
        sys.exit("ABORT: test quote has no sections to post into")
    sid = sections[0].get("id")
    before = len(sections[0].get("line_items") or [])
    print(f"\nsection {sections[0].get('name')!r} ({sid})")
    print(f"  line items before: {before}")

    payload = {"item_id": hit["id"], "quantity_decimal": "1"}
    s2, b2 = req("POST", f"/quotes/{TEST_QUOTE}/sections/{sid}/line-items",
                 body=payload)
    print(f"\nPOST line-items -> {s2}")
    if s2 not in (200, 201):
        print(f"  response: {str(b2)[:400]}")
        print("\nRESULT: the API rejected a bundle as a line-item target.")
        return

    time.sleep(1.5)
    s3, b3 = req("GET", f"/quotes/{TEST_QUOTE}")
    d3 = b3.get("data", b3) if isinstance(b3, dict) else {}
    sec = next((x for x in (d3.get("sections") or []) if x.get("id") == sid), {})
    after_items = sec.get("line_items") or []
    added = len(after_items) - before

    print(f"  line items after : {len(after_items)}  (added {added})")
    for it in after_items[before:]:
        print(f"    - {str(it.get('name'))[:44]:46} "
              f"bundle={it.get('bundle')} "
              f"bundle_line_item_id={it.get('bundle_line_item_id')} "
              f"price={it.get('unit_price_decimal')}")

    print("\n" + "=" * 72)
    if added >= 2:
        print(f"RESULT: THE BUNDLE EXPANDED — {added} line items from one POST.")
        print("Item Groups can hold bundle refs. Shared blocks (XTE/XSH/XSV)")
        print("get maintained in ONE place and every group stays correct.")
    elif added == 1:
        one = after_items[-1]
        if one.get("bundle"):
            print("RESULT: posted as ONE line flagged bundle=True.")
            print("Expansion is likely a display-time behaviour driven by")
            print("Bundle Display ('Show Line Items only'). Check the quote")
            print("in the UI to see whether the client-facing view itemizes.")
        else:
            print("RESULT: posted as ONE ordinary line item, no expansion.")
            print("Bundles are a UI convenience; Item Groups carry items flat.")
    else:
        print("RESULT: nothing landed. Inspect the raw response above.")
    print("=" * 72)
    print(f"\nCleanup: this added line(s) to {TEST_QUOTE}, already test data.")


if __name__ == "__main__":
    main()
