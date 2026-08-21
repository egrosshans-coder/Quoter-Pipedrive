#!/usr/bin/env python3
"""
bundle_probe_v2.py — isolate payload schema from bundle behaviour.

WHY v2
------
v1 posted {"item_id": ..., "quantity_decimal": "1"} and got
400 ERR_REQUEST_FORMAT_INVALID, then reported "the API rejected a bundle".
That conclusion was unsound: a format error is about the PAYLOAD SHAPE and
would fail the same way for an ordinary catalog item. No control was run.

v2 fixes that. It finds the correct payload shape using a KNOWN ORDINARY
item first, and only then retries the bundle with that proven shape. That
way a bundle failure means something.

  step 1  find a payload shape the API accepts, using a regular item
  step 2  post the bundle with the same proven shape
  step 3  read back and compare

Writes to quote quot_3I9UCyBcqZJ39soTFYS5SodFzlW only (test data).

Usage:
    export SCALEPAD_API_KEY='...'
    python3 bundle_probe_v2.py            # shows candidate shapes, no writes
    python3 bundle_probe_v2.py --write
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
CONTROL_NAME = "T&E-Parking"        # ordinary item, not in the bundle
TEST_QUOTE = "quot_3I9UCyBcqZJ39soTFYS5SodFzlW"

API_KEY = os.environ.get("SCALEPAD_API_KEY", "").strip()
if not API_KEY:
    sys.exit("ERROR: set SCALEPAD_API_KEY first.")


def req(method, path, params=None, body=None, timeout=30):
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
            return r.status, raw[:800]
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
        return []
    rows = list(b.get("data", []))
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
    return rows


def shapes(item_id, name, category, price):
    """Candidate payloads.

    CONFIRMED Aug 21 2026: the body is a BARE JSON ARRAY of line-item
    objects. Evidence: posting [ {...} ] returned 422 with
    "line_items[0].name is required" -- a VALIDATION error, meaning the
    array parsed and element 0 was inspected. Every wrapped shape
    ({"line_items": [...]}, flat object) returned 400 format-invalid.

    `name` being required confirms line items are created BY VALUE.
    The shapes below test whether item_id is ALSO honoured alongside a
    name -- i.e. whether any reference semantics exist at all.
    """
    by_val = {"name": name, "category": category,
              "quantity": 1, "unit_price": float(price or 0)}
    return [
        ("array by value",        [dict(by_val)]),
        ("array value + item_id", [dict(by_val, item_id=item_id)]),
        ("array value no cat",    [{"name": name, "quantity": 1,
                                    "unit_price": float(price or 0)}]),
    ]


def section_of(quote_id):
    s, b = req("GET", f"/quotes/{quote_id}")
    if s != 200:
        return None, None, 0
    d = b.get("data", b)
    secs = d.get("sections") or []
    if not secs:
        return None, None, 0
    return d, secs[0].get("id"), len(secs[0].get("line_items") or [])


def count_in(quote_id, sid):
    s, b = req("GET", f"/quotes/{quote_id}")
    if s != 200:
        return None, []
    d = b.get("data", b)
    sec = next((x for x in (d.get("sections") or []) if x.get("id") == sid), {})
    li = sec.get("line_items") or []
    return len(li), li


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    items = fetch_all("/items")
    bundle = next((i for i in items
                   if (i.get("name") or "").strip() == BUNDLE_NAME), None)
    control = next((i for i in items
                    if (i.get("name") or "").strip() == CONTROL_NAME), None)

    print("=" * 72)
    print(f"BUNDLE PROBE v2  [{'WRITE' if a.write else 'DRY'}]")
    print("=" * 72)
    print(f"\nbundle  {BUNDLE_NAME:22} -> {bundle and bundle.get('id')}")
    print(f"control {CONTROL_NAME:22} -> {control and control.get('id')}")
    if not bundle or not control:
        sys.exit("ABORT: could not resolve both items")

    _, sid, before = section_of(TEST_QUOTE)
    if not sid:
        sys.exit("ABORT: no section on the test quote")
    print(f"\nsection {sid}   line items now: {before}")

    if not a.write:
        print("\nCandidate payload shapes that would be tried, in order:")
        for label, p in shapes(control["id"], control.get("name"),
                               control.get("category"),
                               control.get("price_decimal")):
            print(f"  {label:22} {json.dumps(p)[:100]}")
        print("\nDRY — rerun with --write.")
        return

    # --- step 1: find an accepted shape using the ORDINARY item -----------
    print("\n" + "-" * 72)
    print("STEP 1 — find a working payload shape with an ORDINARY item")
    print("-" * 72)
    good = None
    for label, payload in shapes(control["id"], control.get("name"),
                                 control.get("category"),
                                 control.get("price_decimal")):
        s, b = req("POST", f"/quotes/{TEST_QUOTE}/sections/{sid}/line-items",
                   body=payload)
        err = ""
        if isinstance(b, dict) and b.get("errors"):
            e = b["errors"][0]
            err = f"  {e.get('code') or e.get('key')}: {str(e.get('detail'))[:60]}"
        print(f"  {label:22} -> {s}{err}")
        if s in (200, 201):
            good = (label, payload)
            break
        time.sleep(0.3)

    if not good:
        print("\nNo payload shape accepted even for an ordinary item.")
        print("So the v1 400 was NOT about bundles at all — the line-item")
        print("POST schema is simply not what we assumed. Nothing is proven")
        print("about bundles either way. Next step: check the ScalePad docs")
        print("page for CreateLineItem (you have it open in a tab) for the")
        print("required body, or Jon.")
        return

    print(f"\n  accepted shape: {good[0]}")
    n1, _ = count_in(TEST_QUOTE, sid)
    print(f"  control item landed — section now has {n1} line items")

    # --- step 2: same shape, but the BUNDLE -------------------------------
    print("\n" + "-" * 72)
    print("STEP 2 — same proven shape, now with the BUNDLE")
    print("-" * 72)
    def swap(o):
        if isinstance(o, dict):
            return {k: (bundle["id"] if k == "item_id"
                        else bundle["name"] if k == "name"
                        else bundle.get("category") if k == "category"
                        else swap(v))
                    for k, v in o.items()}
        if isinstance(o, list):
            return [swap(x) for x in o]
        return o

    payload = swap(good[1])
    print(f"  payload: {json.dumps(payload)[:160]}")

    s, b = req("POST", f"/quotes/{TEST_QUOTE}/sections/{sid}/line-items",
               body=payload)
    print(f"  POST bundle -> {s}")
    if s not in (200, 201):
        print(f"  response: {str(b)[:400]}")
        print("\nRESULT: ordinary item accepted, bundle REJECTED with the same")
        print("shape. Bundles are not valid line-item targets via the API.")
        print("Item Groups must carry every item flat.")
        return

    time.sleep(1.5)
    n2, li = count_in(TEST_QUOTE, sid)
    added = n2 - n1
    print(f"  section now has {n2} line items (bundle added {added})")
    for it in li[n1:]:
        print(f"    - {str(it.get('name'))[:40]:42} "
              f"bundle={it.get('bundle')} "
              f"blid={it.get('bundle_line_item_id')} "
              f"price={it.get('unit_price_decimal')}")

    print("\n" + "=" * 72)
    if added >= 2:
        print(f"RESULT: BUNDLE EXPANDED — {added} lines from one POST.")
        print("Item Groups can hold bundle refs; shared blocks live in ONE place.")
    elif added == 1:
        one = li[-1]
        print("RESULT: bundle posted as ONE line.")
        print(f"  bundle flag={one.get('bundle')}  price={one.get('unit_price_decimal')}")
        if one.get("bundle"):
            print("  Flagged as a bundle — expansion is likely display-time,")
            print("  driven by 'Show Line Items only'. Check the quote in the UI.")
        else:
            print("  Not flagged. Treat bundles as UI-only; groups carry items flat.")
    print("=" * 72)


if __name__ == "__main__":
    main()
