#!/usr/bin/env python3
"""
zz_artifact_sweep_v1.py — find every zz- tagged test artifact. READ ONLY.

Chapter 3 section 9 lists test artifacts left in the production account. That
list was written by hand across several sessions and may be incomplete. This
sweeps for them so the cleanup list is derived from the account rather than
from memory.

DELETES NOTHING. Issues GET requests only. It prints what it finds and how to
remove each item; removal is a decision for you to make deliberately, in the
UI, where you can see what you are deleting.

Usage:
    export SCALEPAD_API_KEY='...'
    python3 zz_artifact_sweep_v1.py
"""

import http.client
import json
import os
import ssl
import sys
import time
import urllib.parse

BASE = "https://api.scalepad.com/quoter/v1"
HOST = "api.scalepad.com"
MARKERS = ("zz-", "zz_", "ZZ-", "test-chapter3", "TEMPLATE-PROBE")

API_KEY = os.environ.get("SCALEPAD_API_KEY", "").strip()
if not API_KEY:
    sys.exit("ERROR: set SCALEPAD_API_KEY first.")
if API_KEY.startswith("cid_"):
    sys.exit("ERROR: that is a legacy Quoter client_id, not a ScalePad key.")


def get(path, params=None, timeout=30):
    """Lowercase x-api-key is mandatory -- see Chapter 3 addendum 2.1.1."""
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote,
                                            safe="[]:")
    parts = urllib.parse.urlsplit(url)
    target = parts.path + (("?" + parts.query) if parts.query else "")
    conn = None
    try:
        conn = http.client.HTTPSConnection(HOST, timeout=timeout,
                                           context=ssl.create_default_context())
        conn.putrequest("GET", target, skip_accept_encoding=True)
        conn.putheader("x-api-key", API_KEY)
        conn.putheader("Accept", "application/json")
        conn.endheaders()
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
    """Cursor pagination. Size params are ignored by the API (addendum 2.2.2),
    so completeness is checked against total_count rather than assumed."""
    s, b = get(path)
    if s != 200 or not isinstance(b, dict):
        return [], None, s
    rows = list(b.get("data", []))
    total = b.get("total_count")
    cursor = b.get("next_cursor")
    seen = {cursor}
    while cursor:
        s2, b2 = get(path, {"cursor": cursor})
        if s2 != 200 or not isinstance(b2, dict):
            break
        batch = b2.get("data", [])
        if not batch:
            break
        rows.extend(batch)
        cursor = b2.get("next_cursor")
        if cursor in seen:
            break
        seen.add(cursor)
        time.sleep(0.15)
    return rows, total, s


def tagged(*vals):
    for v in vals:
        if v and any(m.lower() in str(v).lower() for m in MARKERS):
            return True
    return False


def main():
    print("=" * 72)
    print("zz- TEST ARTIFACT SWEEP — READ ONLY, deletes nothing")
    print("=" * 72)

    findings = []

    # --- Quotes -----------------------------------------------------------
    rows, total, s = fetch_all("/quotes")
    print(f"\nQUOTES  (fetched {len(rows)}"
          f"{f' of {total}' if total is not None else ''}, status={s})")
    if total is not None and len(rows) != total:
        print("  !! incomplete pull — treat this list as partial")
    hits = [q for q in rows
            if tagged(q.get("custom_number"), q.get("name"),
                      (q.get("client") or {}).get("name")
                      if isinstance(q.get("client"), dict) else None)]
    if not hits:
        print("  none tagged")
    for q in hits:
        cl = q.get("client")
        cl = cl.get("name") if isinstance(cl, dict) else cl
        print(f"  - {q.get('id')}")
        print(f"      custom_number : {q.get('custom_number')}")
        print(f"      client        : {cl}")
        print(f"      draft         : {q.get('draft')}   number: {q.get('number')}")
        print(f"      created       : {q.get('record_created_at')}")
        findings.append(("quote", q.get("id"), q.get("custom_number")))

    # --- Contacts ---------------------------------------------------------
    rows, total, s = fetch_all("/contacts")
    print(f"\nCONTACTS  (fetched {len(rows)}"
          f"{f' of {total}' if total is not None else ''}, status={s})")
    if s != 200:
        print(f"  endpoint returned {s} — check manually in the UI")
    hits = [c for c in rows
            if tagged(c.get("billing_email"), c.get("first_name"),
                      c.get("last_name"), c.get("billing_organization"))]
    if not hits:
        print("  none tagged")
    for c in hits:
        print(f"  - id={c.get('id')}  email={c.get('billing_email')}")
        print(f"      org: {c.get('billing_organization')}")
        findings.append(("contact", c.get("id"), c.get("billing_email")))

    # --- Item groups ------------------------------------------------------
    rows, total, s = fetch_all("/item-groups")
    print(f"\nITEM GROUPS  (fetched {len(rows)}"
          f"{f' of {total}' if total is not None else ''}, status={s})")
    for g in rows:
        gid = g.get("id")
        a, at, _ = fetch_all(
            f"/item-group-item-assignments?filter[item_group_id]=eq:{gid}")
        mark = "  <-- TEST" if tagged(g.get("name")) else ""
        print(f"  - {g.get('name'):28} {gid}  members={len(a)}{mark}")
        if tagged(g.get("name")):
            findings.append(("item_group", gid, g.get("name")))

    # --- Items ------------------------------------------------------------
    rows, total, s = fetch_all("/items")
    print(f"\nCATALOG ITEMS  (fetched {len(rows)}"
          f"{f' of {total}' if total is not None else ''}, status={s})")
    if total is not None and len(rows) != total:
        print("  !! incomplete pull — treat this list as partial")
    hits = [i for i in rows if tagged(i.get("name"), i.get("code"))]
    if not hits:
        print("  none tagged")
    for i in hits:
        print(f"  - {i.get('name')[:50]:52} {i.get('id')}  code={i.get('code')}")
        findings.append(("item", i.get("id"), i.get("name")))

    # Known test-fixture items from Chapter 3 that are NOT zz- prefixed
    fixtures = [i for i in rows
                if i.get("name", "").lower() in
                ("balloon air filler test", "balloon real-price control")]
    if fixtures:
        print("\n  Untagged test fixtures referenced in Chapter 3 section 7:")
        for i in fixtures:
            print(f"  - {i.get('name')[:50]:52} {i.get('id')}")
            print("      (in use on the test quote; check before removing)")

    # --- Summary ----------------------------------------------------------
    print()
    print("=" * 72)
    print(f"SUMMARY — {len(findings)} tagged artifacts")
    print("=" * 72)
    for kind, ident, label in findings:
        print(f"  {kind:12} {ident}  {label}")
    print("""
Deletion is deliberately not automated here. Two reasons:

  1. Quotes carry three different identifiers (Chapter 3 section 7.6). Deleting
     by the wrong one is a real risk, and the failure is not recoverable.
  2. Some fixtures are referenced by the test quote. Removing an item that a
     quote still points at may leave that quote in a broken state.

Delete these in the Quoter UI, where each record is visible before removal.
Alternatively, leave them: they are clearly tagged, which Chapter 3 section 9
already accepts as a valid outcome.""")


if __name__ == "__main__":
    main()
