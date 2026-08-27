#!/usr/bin/env python3
"""
options_probe_v1.py — do Item Options survive an API-created line item?

THE QUESTION
------------
Quoter's Item Options let one catalog item carry a priced choice: FV Graphics
Package with values Standard $500 / Advanced $1500 / Ultimate $3000, marked
REQUIRE SELECTION = Yes, ALLOW MULTIPLE = No.

If that survives an API-created line item, three catalog items collapse into
one line with a tier selector, and the salesperson picks rather than deleting
two seeded lines.

Why it might not. Line items are created BY VALUE (Chapter 3 7.10): name,
quantity_decimal, unit_price_decimal, nested category — and no item_id. The
line may therefore have no link back to the catalog item at all, in which case
there is nothing for Quoter to draw an option selector from. That is exactly
how Bundles behaved: posted by value, they came back as one ordinary line with
bundle=false and no expansion.

REQUIRE SELECTION = Yes makes the answer consequential rather than academic.
If the option does not attach, the posted line is one that CANNOT be completed
— no tier, no way to choose one — which would be worse than seeding the three
separate items and deleting two.

  Phase 1 (default)  READ ONLY.
      a) the item as GET /items returns it in the collection
      b) the same item via GET /items/{id} — single-record endpoints
         sometimes carry nested data the list omits
      c) diff the two, since (b) returning more is the whole hope
  Phase 2 (--write)  Post the item by value into a scratch section on a
      throwaway draft, read the line back, and report every option-shaped
      field on it.

Phase 2 creates one draft quote tagged zz-OPTIONS-PROBE-<timestamp>.

The decisive check is visual and cannot be automated: after Phase 2, open the
created quote in the Quoter editor and look for the tier selector. The API
read tells us whether Quoter recorded a link; only the editor tells us whether
a human can act on it.

Usage:
    export SCALEPAD_API_KEY='...'
    python3 options_probe_v1.py
    python3 options_probe_v1.py --item "FV-Standard Graphics Pkg"
    python3 options_probe_v1.py --write
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

DEFAULT_ITEM = "FV-Standard Graphics Pkg"
TEST_EMAIL = "zz-test-chapter3@tlciscreative.com"
TEST_CLIENT = "zz-Chapter3-CustomNumber-Test"
DEFAULT_TEMPLATE = "tmpl_30O6JTDIbApan1B5gh9hF2w1tfL"     # "Basic"

OPTION_HINTS = ("option", "child", "parent", "variant", "level", "bundle")

API_KEY = os.environ.get("SCALEPAD_API_KEY", "").strip()
if not API_KEY:
    sys.exit("ERROR: set SCALEPAD_API_KEY first.")
if API_KEY.startswith("cid_"):
    sys.exit("ERROR: that is a legacy Quoter client_id, not a ScalePad key.")


def req(method, path, body=None, timeout=30):
    """Lowercase x-api-key is mandatory — Chapter 3 2.1.1."""
    parts = urllib.parse.urlsplit(BASE + path)
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
            return r.status, raw[:900]
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def fetch_items():
    rows, cursor, seen = [], None, set()
    while True:
        p = "/items?page_size=200" + (f"&cursor={urllib.parse.quote(cursor)}"
                                      if cursor else "")
        s, b = req("GET", p)
        if s != 200 or not isinstance(b, dict):
            break
        rows.extend(b.get("data") or [])
        cursor = b.get("next_cursor")
        if not cursor or cursor in seen:
            break
        seen.add(cursor)
    return rows


def option_fields(d):
    return {k: v for k, v in d.items()
            if any(h in k.lower() for h in OPTION_HINTS)}


def phase1(item_name):
    print("=" * 72)
    print("PHASE 1 — READ ONLY: does the API expose Item Options?")
    print("=" * 72)

    items = fetch_items()
    print(f"\n  catalog: {len(items)} items")
    hit = next((i for i in items
                if (i.get("name") or "").strip() == item_name.strip()), None)
    if not hit:
        near = [i["name"] for i in items
                if "graph" in (i.get("name") or "").lower()]
        print(f"  {item_name!r} not found.")
        if near:
            print("  graphics-ish items present:")
            for n in near:
                print(f"    - {n}")
        return None

    print(f"\n  item : {hit.get('name')!r}")
    print(f"  id   : {hit.get('id')}   code={hit.get('code')}  sku={hit.get('sku')}")
    print(f"  price: {hit.get('price_decimal')}")
    print(f"\n  (a) option-shaped fields in the COLLECTION record:")
    print(f"      {json.dumps(option_fields(hit))}")

    s, b = req("GET", f"/items/{hit['id']}")
    print(f"\n  (b) GET /items/{{id}} -> {s}")
    single = None
    if s == 200 and isinstance(b, dict):
        single = b.get("data", b)
        extra = set(single) - set(hit)
        print(f"      keys not present in the collection record: "
              f"{sorted(extra) if extra else 'none'}")
        print(f"      option-shaped fields: {json.dumps(option_fields(single))}")
        if extra:
            print("\n      EXTRA FIELDS:")
            print("       " + json.dumps({k: single[k] for k in extra},
                                          indent=2).replace("\n", "\n       "))
    else:
        print(f"      {str(b)[:300]}")

    src = single or hit
    has = any(("option" in k.lower() and v not in (None, [], {}, False))
              for k, v in src.items())
    print("\n" + "-" * 72)
    if has:
        print("READ RESULT: the API exposes option data on this item.")
        print("Render could at least know a selector exists.")
    else:
        print("READ RESULT: no option data exposed. `show_option_prices` is a")
        print("display flag only; the configured values are not returned.")
        print("So the API cannot see the tiers even though the UI has them.")
    print("-" * 72)
    return hit


def phase2(item):
    if not item:
        print("\nNo item resolved; skipping write.")
        return
    stamp = time.strftime("%Y%m%d-%H%M%S")

    print()
    print("=" * 72)
    print("PHASE 2 — post it by value and see what the line item carries")
    print("=" * 72)

    s, b = req("POST", "/quotes", body={
        "template_id": DEFAULT_TEMPLATE,
        "contact": {"email": TEST_EMAIL, "client_name": TEST_CLIENT},
        "custom_number": f"zz-OPTIONS-PROBE-{stamp}",
    })
    if s not in (200, 201):
        print(f"  quote create failed ({s}): {str(b)[:300]}")
        return
    qid = (b.get("data", b) if isinstance(b, dict) else {}).get("id")
    print(f"\n  draft {qid}  (tag zz-OPTIONS-PROBE-{stamp})")

    s, b = req("POST", f"/quotes/{qid}/sections",
               body=[{"name": "Options Probe"}])
    print(f"  create section -> {s}")
    if s not in (200, 201):
        print(f"  {str(b)[:300]}")
        return

    s, b = req("GET", f"/quotes/{qid}")
    secs = (b.get("data", b) or {}).get("sections") or []
    sid = secs[0].get("id") if secs else None
    if not sid:
        print("  no section id; aborting")
        return

    # Confirmed write schema, Chapter 3 7.10. There is no options field to set.
    payload = [{
        "name": item.get("name"),
        "quantity_decimal": "1",
        "unit_price_decimal": str(item.get("price_decimal") or "0"),
        "category": {"id": item.get("category_id")},
    }]
    s, b = req("POST", f"/quotes/{qid}/sections/{sid}/line-items", body=payload)
    print(f"  post line item -> {s}")
    if s not in (200, 201):
        print(f"  {str(b)[:400]}")
        return

    time.sleep(1.5)
    s, b = req("GET", f"/quotes/{qid}")
    d = b.get("data", b) if isinstance(b, dict) else {}
    li = None
    for sec in (d.get("sections") or []):
        for x in (sec.get("line_items") or []):
            li = x
    if not li:
        print("  no line item read back")
        return

    print(f"\n  line item: {li.get('name')!r}")
    print(f"    unit_price_decimal : {li.get('unit_price_decimal')}")
    print(f"    options            : {json.dumps(li.get('options'))}")
    print(f"    bundle             : {li.get('bundle')}")
    print(f"    optional           : {li.get('optional')}")
    print(f"    optional_group_id  : {li.get('optional_group_id')}")
    print(f"    optional_selected  : {li.get('optional_selected')}")

    opts = li.get("options")
    print("\n" + "=" * 72)
    if opts:
        print("RESULT: the line item CARRIES option data.")
        print("Tiers may be selectable on an API-created line — confirm in the")
        print("editor that the selector actually renders.")
    else:
        print("RESULT: options is null on the created line.")
        print("Consistent with by-value creation having no link back to the")
        print("catalog item — the same reason Bundles did not expand (7.9).")
        print("\nBUT THIS IS NOT YET CONCLUSIVE. The selector could be drawn")
        print("from the item name at render time. Open the quote in the editor")
        print("and look for the Standard/Advanced/Ultimate control. Only that")
        print("settles it, because REQUIRE SELECTION = Yes means a line with")
        print("no selector is a line nobody can complete.")
    print("=" * 72)
    print(f"\n  open: /admin/quotes/draft_by_public_id/{qid}")
    print(f"  cleanup: draft {qid}, tag zz-OPTIONS-PROBE-{stamp}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", default=DEFAULT_ITEM,
                    help="exact catalog item name carrying the options")
    ap.add_argument("--write", action="store_true",
                    help="create one draft quote and post the item into it")
    a = ap.parse_args()
    item = phase1(a.item)
    if a.write:
        phase2(item)
    else:
        print("\n" + "=" * 72)
        print("Phase 2 not run — it creates one draft quote. Rerun with --write.")
        print("=" * 72)


if __name__ == "__main__":
    main()
