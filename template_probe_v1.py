#!/usr/bin/env python3
"""
template_probe_v1.py — does a template's line items materialize server-side?

THE QUESTION
------------
Chapter 3 section 6.2 confirms POST /quotes with a template_id returns
sections: null. That is a fact about the CREATE RESPONSE. It is not the same
claim as "the quote has no sections" -- an API can create a populated
resource and return a thin representation of it.

Nobody has tested the second claim. If the template's line items DO exist on
the created quote, then GET /quotes/{id}/sections reads them back through
documented endpoints, and the template-read blocker is solved without the
/admin scrape route and without waiting on Jon.

PHASES
------
  Phase 1 (default)  READ ONLY. Reads the known test quote to learn the
                     shapes of the sections and line-items endpoints.
  Phase 2 (--create) Creates ONE draft quote from a template, then reads it
                     back. This is a WRITE. See below.

WHAT PHASE 2 WRITES
-------------------
One draft quote, tagged zz-TEMPLATE-PROBE-<timestamp>, against the existing
zz-test contact from Chapter 3. Drafts are not sent to anyone. Chapter 3
created two of these already today. It creates nothing else -- no contacts,
no items, no item groups, no assignments.

Usage:
    export SCALEPAD_API_KEY='...'
    python3 template_probe_v1.py                    # read-only
    python3 template_probe_v1.py --list-templates   # read-only
    python3 template_probe_v1.py --create           # writes one draft
    python3 template_probe_v1.py --create --template "Balloons"
"""

import argparse
import http.client
import json
import ssl
import sys
import time
import urllib.parse
from pathlib import Path

BASE = "https://api.scalepad.com/quoter/v1"
HOST = "api.scalepad.com"
OUTDIR = Path("./quoter_recon")

import os
API_KEY = os.environ.get("SCALEPAD_API_KEY", "").strip()
if not API_KEY:
    sys.exit("ERROR: set SCALEPAD_API_KEY first.\n"
             "  export SCALEPAD_API_KEY='...'")
if API_KEY.startswith("cid_"):
    sys.exit("ERROR: that is a legacy Quoter client_id, not a ScalePad key.")

# From the kickoff brief
TEST_QUOTE = "quot_3I9UCyBcqZJ39soTFYS5SodFzlW"
TEST_EMAIL = "zz-test-chapter3@tlciscreative.com"
TEST_CLIENT = "zz-Chapter3-CustomNumber-Test"


def req(method, path, params=None, body=None, timeout=30):
    """Lowercase x-api-key is mandatory: ScalePad's gateway matches
    case-sensitively and urllib's X-api-key gets a 401 (confirmed Aug 19)."""
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
            return r.status, raw[:1500]
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def get(path, params=None):
    return req("GET", path, params=params)


def show(label, status, body, limit=1400):
    print(f"\n  {label}")
    print(f"    status: {status}")
    txt = json.dumps(body, indent=2) if isinstance(body, (dict, list)) else str(body)
    for line in txt.splitlines()[:40]:
        print(f"    {line[:150]}")
    if len(txt) > limit:
        print("    ... (truncated; full copy saved to ./quoter_recon/)")


def save(name, obj):
    OUTDIR.mkdir(exist_ok=True)
    (OUTDIR / f"{name}.json").write_text(json.dumps(obj, indent=2))


def list_templates():
    print("=" * 72)
    print("TEMPLATES")
    print("=" * 72)
    s, b = get("/quote-templates")
    if s != 200:
        show("GET /quote-templates", s, b)
        return []
    rows = b.get("data", [])
    for t in rows:
        print(f"  {t.get('title','')[:34]:36} {t.get('id')}  slug={t.get('slug')}")
    save("10_templates", rows)
    return rows


def phase1():
    """READ ONLY. Learn the sections / line-items endpoint shapes."""
    print("=" * 72)
    print("PHASE 1 — READ ONLY: shape of the quote/sections/line-item endpoints")
    print("=" * 72)

    s, b = get(f"/quotes/{TEST_QUOTE}")
    save("11_test_quote", b)
    if isinstance(b, dict):
        d = b.get("data", b)
        keys = sorted(d.keys()) if isinstance(d, dict) else "(not a dict)"
        print(f"\n  GET /quotes/{{id}}  status={s}")
        print(f"    top-level keys: {keys}")
        if isinstance(d, dict):
            print(f"    sections field: {json.dumps(d.get('sections'))[:300]}")
    else:
        show(f"GET /quotes/{TEST_QUOTE}", s, b)

    # Is there a standalone sections endpoint for reading? POST is documented;
    # GET is not, so probe rather than assume.
    s, b = get(f"/quotes/{TEST_QUOTE}/sections")
    show(f"GET /quotes/{{id}}/sections", s, b)
    save("12_test_quote_sections", b)

    section_ids = []
    if s == 200 and isinstance(b, dict):
        for sec in b.get("data", []):
            if isinstance(sec, dict) and sec.get("id"):
                section_ids.append(sec["id"])

    for sid in section_ids[:2]:
        s2, b2 = get(f"/quotes/{TEST_QUOTE}/sections/{sid}/line-items")
        show(f"GET /quotes/{{id}}/sections/{sid[:12]}.../line-items", s2, b2)
        save(f"13_line_items_{sid[:12]}", b2)

    print("\n  Phase 1 done. Nothing was written.")
    return section_ids


def phase2(template_title=None):
    """WRITE: create one draft from a template, then read it back."""
    print()
    print("=" * 72)
    print("PHASE 2 — creates ONE draft quote from a template, then reads it back")
    print("=" * 72)

    templates = list_templates()
    if not templates:
        print("  no templates readable; aborting")
        return

    chosen = None
    if template_title:
        for t in templates:
            if t.get("title", "").strip().lower() == template_title.strip().lower():
                chosen = t
                break
        if not chosen:
            print(f"  template {template_title!r} not found. Titles above.")
            return
    else:
        for t in templates:
            if t.get("title", "").strip().lower() == "balloons":
                chosen = t
                break
        chosen = chosen or templates[0]

    stamp = time.strftime("%Y%m%d-%H%M%S")
    payload = {
        "template_id": chosen["id"],
        "contact": {"email": TEST_EMAIL, "client_name": TEST_CLIENT},
        "custom_number": f"zz-TEMPLATE-PROBE-{stamp}",
    }

    print(f"\n  template : {chosen.get('title')}  ({chosen['id']})")
    print(f"  tagged as: {payload['custom_number']}")
    print(f"  payload  : {json.dumps(payload)}")

    s, b = req("POST", "/quotes", body=payload)
    save("20_created_quote", b)
    print(f"\n  POST /quotes -> status={s}")
    if s not in (200, 201):
        show("create failed", s, b)
        return

    d = b.get("data", b) if isinstance(b, dict) else {}
    qid = d.get("id")
    print(f"  created quote id: {qid}")
    print(f"  sections in CREATE RESPONSE: {json.dumps(d.get('sections'))[:200]}")
    print("     ^ Chapter 3 section 6.2 already recorded this as null.")
    print("       The real question is what the next three calls return.")

    if not qid:
        print("  no quote id returned; cannot read back")
        return

    time.sleep(1.5)   # allow any server-side template expansion to settle

    print("\n  --- READ-BACK: does the quote actually hold the template's items? ---")

    s1, b1 = get(f"/quotes/{qid}")
    save("21_readback_quote", b1)
    if isinstance(b1, dict):
        d1 = b1.get("data", b1)
        print(f"\n  GET /quotes/{{id}}  status={s1}")
        print(f"    sections: {json.dumps(d1.get('sections'))[:400]}")

    s2, b2 = get(f"/quotes/{qid}/sections")
    show("GET /quotes/{id}/sections", s2, b2)
    save("22_readback_sections", b2)

    found_items = 0
    if s2 == 200 and isinstance(b2, dict):
        for sec in b2.get("data", []):
            sid = sec.get("id")
            if not sid:
                continue
            s3, b3 = get(f"/quotes/{qid}/sections/{sid}/line-items")
            save(f"23_readback_items_{sid[:12]}", b3)
            rows = b3.get("data", []) if isinstance(b3, dict) else []
            found_items += len(rows)
            print(f"\n    section {sec.get('name','(unnamed)')!r} ({sid})"
                  f" -> {len(rows)} line items")
            for it in rows[:12]:
                print(f"       - {it.get('name','')[:52]:54} "
                      f"qty={it.get('quantity_decimal')} "
                      f"price={it.get('unit_price_decimal')}")

    print()
    print("=" * 72)
    if found_items:
        print(f"RESULT: template line items ARE readable — {found_items} found.")
        print("The blocker is solved through documented endpoints. No scrape")
        print("route needed, no dependency on Jon's reply.")
    else:
        print("RESULT: no line items materialized. The template genuinely does")
        print("not expand server-side, confirming Chapter 3 section 6. The")
        print("sweep then needs either Jon's answer or the /admin route.")
    print("=" * 72)
    print(f"\nCleanup: the draft tagged {payload['custom_number']} is in the")
    print("production account and should be deleted or left clearly tagged.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--create", action="store_true",
                    help="create one draft quote from a template (WRITE)")
    ap.add_argument("--template", default=None,
                    help="template title, e.g. 'Balloons'")
    ap.add_argument("--list-templates", action="store_true")
    a = ap.parse_args()

    if a.list_templates:
        list_templates()
        return

    phase1()

    if a.create:
        phase2(a.template)
    else:
        print("\n" + "=" * 72)
        print("Phase 2 not run. It creates one draft quote — rerun with --create")
        print("once you've read the Phase 1 output above.")
        print("=" * 72)


if __name__ == "__main__":
    main()
