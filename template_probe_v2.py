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

    section_ids = []
    s, b = get(f"/quotes/{TEST_QUOTE}")
    save("11_test_quote", b)
    if s == 200 and isinstance(b, dict):
        d = b.get("data", b)
        print(f"\n  GET /quotes/{{id}}  status={s}")
        print(f"    top-level keys: {sorted(d.keys())}")
        sections = d.get("sections") or []
        print(f"    sections: {len(sections)}")
        for sec in sections:
            if not isinstance(sec, dict):
                continue
            section_ids.append(sec.get("id"))
            items = sec.get("line_items") or []
            print(f"\n    section {sec.get('name') or '(unnamed)'!r} "
                  f"({sec.get('id')}) -> {len(items)} line items")
            if items and isinstance(items[0], dict):
                print(f"      line_item keys: {sorted(items[0].keys())}")
            for it in items[:10]:
                if not isinstance(it, dict):
                    continue
                cat = it.get("category")
                cat_id = cat.get("id") if isinstance(cat, dict) else cat
                print(f"       - {str(it.get('name',''))[:44]:46} "
                      f"qty={it.get('quantity_decimal')} "
                      f"price={it.get('unit_price_decimal')} "
                      f"cat={cat_id}")
    else:
        show(f"GET /quotes/{TEST_QUOTE}", s, b)

    # Confirmed 403 (POST-only). Probed once so the finding stays on record.
    s, b = get(f"/quotes/{TEST_QUOTE}/sections")
    print(f"\n  GET /quotes/{{id}}/sections -> status={s} "
          f"(expected 403; sections come from the quote GET above)")

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

    # Phase 1 confirmed GET /quotes/{id}/sections returns 403 (POST-only), but
    # GET /quotes/{id} embeds sections WITH their line_items nested. So read
    # the whole quote and walk it, rather than enumerating via the 403 path.
    s1, b1 = get(f"/quotes/{qid}")
    save("21_readback_quote", b1)
    print(f"\n  GET /quotes/{{id}}  status={s1}")

    found_items = 0
    if s1 == 200 and isinstance(b1, dict):
        d1 = b1.get("data", b1)
        sections = d1.get("sections")
        if not sections:
            print(f"    sections: {json.dumps(sections)}")
        else:
            print(f"    sections: {len(sections)} found")
            for sec in sections:
                if not isinstance(sec, dict):
                    continue
                items = sec.get("line_items") or []
                found_items += len(items)
                print(f"\n    section {sec.get('name') or '(unnamed)'!r} "
                      f"({sec.get('id')}) -> {len(items)} line items")
                for it in items[:15]:
                    if not isinstance(it, dict):
                        continue
                    cat = it.get("category")
                    cat_id = cat.get("id") if isinstance(cat, dict) else cat
                    print(f"       - {str(it.get('name',''))[:46]:48} "
                          f"qty={it.get('quantity_decimal')} "
                          f"price={it.get('unit_price_decimal')} "
                          f"cat={cat_id}")
                if len(items) > 15:
                    print(f"       ... +{len(items)-15} more")
    else:
        show("read-back failed", s1, b1)

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
