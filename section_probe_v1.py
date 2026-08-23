#!/usr/bin/env python3
"""
section_probe_v1.py — can the API create sections on a quote?

THE QUESTION
------------
Chapter 3 section 8's whole design assumes Render can create sections on a
quote it just made. That has never been tested. Every section we have read
was one that already existed. GET /quotes/{id}/sections returns 403
(POST-only), so the ONLY evidence POST works is the documentation -- and the
docs have been wrong or empty three times in this workstream already.

If sections cannot be created via API, the composition design does not work
as described and needs rethinking before anything is built.

WHAT IT DOES
------------
  Phase 1 (default)  READ ONLY. Reads an existing quote to learn the shape
                     of a section object, so we know what to send.
  Phase 2 (--write)  Creates ONE draft quote, then attempts to create TWO
                     sections on it, then posts a line item into the first.
                     Reads everything back and reports.

Two sections rather than one, deliberately: the design needs several per
quote (one per Item Group), so ordering and multiplicity matter, not just
whether a single POST returns 201.

Phase 2 creates one draft quote tagged zz-SECTION-PROBE-<timestamp> against
the existing zz-test contact. It creates nothing else.

Payload shapes are probed rather than assumed. Each attempt is reported with
its status and the exact validation error, in the same way the line-item
schema was derived (Chapter 3 section 7.10).

Usage:
    export SCALEPAD_API_KEY='...'
    python3 section_probe_v1.py
    python3 section_probe_v1.py --write
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

TEST_QUOTE = "quot_3I9UCyBcqZJ39soTFYS5SodFzlW"   # existing, has a section
TEST_EMAIL = "zz-test-chapter3@tlciscreative.com"
TEST_CLIENT = "zz-Chapter3-CustomNumber-Test"
DEFAULT_TEMPLATE = "tmpl_30O6JTDIbApan1B5gh9hF2w1tfL"   # "Basic"

API_KEY = os.environ.get("SCALEPAD_API_KEY", "").strip()
if not API_KEY:
    sys.exit("ERROR: set SCALEPAD_API_KEY first.")
if API_KEY.startswith("cid_"):
    sys.exit("ERROR: that is a legacy Quoter client_id, not a ScalePad key.")


def req(method, path, body=None, timeout=30):
    """Lowercase x-api-key is mandatory -- Chapter 3 section 2.1.1.
    http.client is used because urllib capitalises header names."""
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


def err_of(body):
    if isinstance(body, dict) and body.get("errors"):
        e = body["errors"][0]
        return f"{e.get('code') or e.get('key')}: {str(e.get('detail'))[:70]}"
    return str(body)[:90]


def sections_of(quote_id):
    s, b = req("GET", f"/quotes/{quote_id}")
    if s != 200 or not isinstance(b, dict):
        return None
    d = b.get("data", b)
    return d.get("sections") or []


def phase1():
    print("=" * 72)
    print("PHASE 1 — READ ONLY: what does an existing section look like?")
    print("=" * 72)
    secs = sections_of(TEST_QUOTE)
    if secs is None:
        print("  could not read the test quote")
        return
    print(f"\n  {len(secs)} section(s) on {TEST_QUOTE}")
    for sec in secs:
        if not isinstance(sec, dict):
            continue
        keys = sorted(sec.keys())
        print(f"\n  section keys: {keys}")
        skinny = {k: v for k, v in sec.items() if k != "line_items"}
        print(f"  values (line_items omitted):")
        print("   " + json.dumps(skinny, indent=2)[:900].replace("\n", "\n   "))
    print("\n  Phase 1 done. Nothing written.")


def phase2():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    print()
    print("=" * 72)
    print("PHASE 2 — create a draft, then try to create sections on it")
    print("=" * 72)

    # --- create a throwaway draft -----------------------------------------
    payload = {
        "template_id": DEFAULT_TEMPLATE,
        "contact": {"email": TEST_EMAIL, "client_name": TEST_CLIENT},
        "custom_number": f"zz-SECTION-PROBE-{stamp}",
    }
    s, b = req("POST", "/quotes", body=payload)
    if s not in (200, 201):
        print(f"  quote create failed ({s}): {err_of(b)}")
        return
    qid = (b.get("data", b) if isinstance(b, dict) else {}).get("id")
    print(f"\n  created draft {qid}  (tag zz-SECTION-PROBE-{stamp})")
    print(f"  sections at creation: {json.dumps((b.get('data', b) or {}).get('sections'))}")

    if not qid:
        print("  no quote id returned; cannot continue")
        return

    # --- find a payload shape the sections endpoint accepts ---------------
    print("\n" + "-" * 72)
    print("Finding an accepted payload shape for POST /quotes/{id}/sections")
    print("-" * 72)

    # Line items turned out to be a BARE ARRAY (section 7.10). Sections may
    # follow the same convention, so array forms are tried first.
    candidates = [
        ("bare array, name",      [{"name": "Balloons"}]),
        ("bare array, name+pos",  [{"name": "Balloons", "position": 1}]),
        ("flat object, name",     {"name": "Balloons"}),
        ("sections[] wrapper",    {"sections": [{"name": "Balloons"}]}),
        ("bare array, empty",     [{}]),
    ]

    good = None
    for label, p in candidates:
        s, b = req("POST", f"/quotes/{qid}/sections", body=p)
        print(f"  {label:24} -> {s}   {err_of(b) if s not in (200,201) else 'OK'}")
        if s in (200, 201):
            good = (label, p, b)
            break
        time.sleep(0.3)

    if not good:
        print("\n" + "=" * 72)
        print("RESULT: no payload shape accepted.")
        print("Either sections cannot be created via API, or the schema is")
        print("something not tried above. Read the error codes: a 422 naming a")
        print("field means the shape is right and a field is missing (keep")
        print("going). A 403 or a uniform 400 means the endpoint is not")
        print("usable this way -- and the section 8 design needs rethinking.")
        print("=" * 72)
        print(f"\nCleanup: draft {qid} tagged zz-SECTION-PROBE-{stamp}")
        return

    label, shape, resp = good
    print(f"\n  accepted shape: {label}")
    print(f"  response: {json.dumps(resp)[:400]}")

    # --- can we create a SECOND one? ordering matters for the design ------
    print("\n" + "-" * 72)
    print("Creating a second section (the design needs several per quote)")
    print("-" * 72)
    second = json.loads(json.dumps(shape))

    def rename(o, newname):
        if isinstance(o, dict):
            return {k: (newname if k == "name" else rename(v, newname))
                    for k, v in o.items()}
        if isinstance(o, list):
            return [rename(x, newname) for x in o]
        return o

    s2, b2 = req("POST", f"/quotes/{qid}/sections",
                 body=rename(second, "Travel & Expenses"))
    print(f"  second section -> {s2}   {err_of(b2) if s2 not in (200,201) else 'OK'}")

    # --- read back --------------------------------------------------------
    time.sleep(1.5)
    secs = sections_of(qid) or []
    print(f"\n  read-back: {len(secs)} section(s) on the quote")
    first_sid = None
    for i, sec in enumerate(secs):
        if not isinstance(sec, dict):
            continue
        if first_sid is None:
            first_sid = sec.get("id")
        print(f"    [{i}] id={sec.get('id')}  name={sec.get('name')!r}  "
              f"line_items={len(sec.get('line_items') or [])}")

    # --- put a line item in, using the confirmed schema -------------------
    if first_sid:
        print("\n" + "-" * 72)
        print("Posting a line item into the new section (schema per 7.10)")
        print("-" * 72)
        # T&E-Parking, resolved live so the category id is real
        s3, b3 = req("GET", "/items?filter[code]=eq:T%26E-PRK-001")
        cat_id, nm, price = None, "Probe line", "0.00"
        if s3 == 200 and isinstance(b3, dict) and b3.get("data"):
            it = b3["data"][0]
            cat_id, nm = it.get("category_id"), it.get("name")
            price = it.get("price_decimal") or "0.00"
        if not cat_id:
            # fall back to a category id from the existing test quote
            old = sections_of(TEST_QUOTE) or []
            for sec in old:
                for li in (sec.get("line_items") or []):
                    c = li.get("category")
                    if isinstance(c, dict) and c.get("id"):
                        cat_id = c["id"]
                        break
                if cat_id:
                    break
        if cat_id:
            li_payload = [{"name": nm, "quantity_decimal": "1",
                           "unit_price_decimal": str(price),
                           "category": {"id": cat_id}}]
            s4, b4 = req("POST", f"/quotes/{qid}/sections/{first_sid}/line-items",
                         body=li_payload)
            print(f"  POST line-item -> {s4}   "
                  f"{err_of(b4) if s4 not in (200,201) else 'OK'}")
            time.sleep(1.0)
            secs = sections_of(qid) or []
            for sec in secs:
                if sec.get("id") == first_sid:
                    print(f"  section now holds "
                          f"{len(sec.get('line_items') or [])} line item(s)")
        else:
            print("  could not resolve a category id; skipped")

    # --- verdict ----------------------------------------------------------
    print("\n" + "=" * 72)
    if len(secs) >= 2:
        print(f"RESULT: SECTIONS ARE CREATABLE — {len(secs)} on one quote.")
        print("Chapter 3 section 8's composition design is viable. Render can")
        print("build a quote from one default template plus N Item Groups,")
        print("one section per group.")
    elif len(secs) == 1:
        print("RESULT: one section created, second failed. Usable but")
        print("constrained — check the second-section error above. A one-")
        print("section-per-quote limit would force all groups into a single")
        print("section and lose the layout benefit.")
    else:
        print("RESULT: nothing read back. Inspect the responses above.")
    print("=" * 72)
    print(f"\nCleanup: draft {qid}, tag zz-SECTION-PROBE-{stamp}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="create one draft quote and attempt section creation")
    a = ap.parse_args()
    phase1()
    if a.write:
        phase2()
    else:
        print("\n" + "=" * 72)
        print("Phase 2 not run — it creates one draft quote.")
        print("Rerun with --write once the section shape above looks right.")
        print("=" * 72)


if __name__ == "__main__":
    main()
