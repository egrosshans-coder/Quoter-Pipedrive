#!/usr/bin/env python3
"""
build_item_group_v1.py — create an Item Group from swept template line items.

Source of the membership list: the Balloons template, read from
/admin/quotes/create/balloons in an authenticated browser session on
2026-08-20 and transcribed below. This is a one-time, human-supervised
population, not an automated scrape (see Chapter 3 addendum, section 9).

DEFAULT IS DRY RUN. Nothing is written without --write.

Matching: catalog items are resolved by NAME against GET /items. Names in the
template form and names in the catalog come from the same records, so exact
match should hit; anything that does not match exactly is reported and the run
stops rather than guessing.

Usage:
    export SCALEPAD_API_KEY='...'
    python3 build_item_group_v1.py              # dry run: match + plan only
    python3 build_item_group_v1.py --write      # creates group + assignments
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

DEFAULT_GROUP_NAME = "XRN-Balloons"

# Feature items only, swept from /admin/quotes/create/balloons 2026-08-20.
#
# The template carries 14 rows. The other 8 are shared blocks and do NOT
# belong here: Shipping & Handling becomes XSH-, and the seven T&E rows become
# XTE-. Holding them once rather than copying them into every feature group is
# the whole point -- the Aug 20 sweep found the shared blocks already diverged
# across the 11 templates (Balloons is missing T&E-Per Diem; LED Wristbands is
# missing the accommodations Buyout).
#
# Note: this template carries NO labor items, unlike six other templates which
# each include some combination of the three generic Service items. Either
# balloon work needs no setup technician, or the template is missing them --
# the same class of omission as the absent Per Diem. Worth confirming before
# treating this list as complete.
TEMPLATE_ITEMS = [
    "Balloon air filler",
    "Balloon drop net",
    "Balloon Moon LED",
    "Balloons per package",
    "Disappearing Balloon Wall",
    "Flying Balloon Wall",
]

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
    """Cursor pagination; size params are ignored by this API (addendum 2.2.2),
    so completeness is verified against total_count rather than assumed."""
    s, b = req("GET", path)
    if s != 200 or not isinstance(b, dict):
        return None, None
    rows = list(b.get("data", []))
    total = b.get("total_count")
    cursor = b.get("next_cursor")
    seen = {cursor}
    while cursor:
        s2, b2 = req("GET", path, params={"cursor": cursor})
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
    return rows, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="actually create the group and assignments")
    ap.add_argument("--name", default=DEFAULT_GROUP_NAME,
                    help=f"item group name (default {DEFAULT_GROUP_NAME!r}). "
                         "Renaming later is cheap -- the Pipedrive sync keeps "
                         "option ids across a rename -- but the group name is "
                         "what Render resolves against, so settle it early.")
    a = ap.parse_args()
    global GROUP_NAME
    GROUP_NAME = a.name

    print("=" * 72)
    print(f"ITEM GROUP BUILD — {GROUP_NAME}"
          f"   [{'WRITE' if a.write else 'DRY RUN'}]")
    print("=" * 72)

    # --- catalog -----------------------------------------------------------
    items, total = fetch_all("/items")
    if items is None:
        sys.exit("ERROR: could not read /items")
    print(f"\ncatalog: fetched {len(items)} of {total}")
    if total is not None and len(items) != total:
        sys.exit("ABORT: incomplete catalog pull — a missing item would be "
                 "silently dropped from the group.")

    by_name = {}
    for it in items:
        by_name.setdefault((it.get("name") or "").strip(), []).append(it)

    # --- match -------------------------------------------------------------
    print(f"\nmatching {len(TEMPLATE_ITEMS)} template line items by name:\n")
    resolved, problems = [], []
    for name in TEMPLATE_ITEMS:
        hits = by_name.get(name.strip(), [])
        if len(hits) == 1:
            it = hits[0]
            print(f"  OK   {name[:40]:42} {it['id']}  "
                  f"code={it.get('code')}  cat={it.get('category')}")
            resolved.append(it)
        elif not hits:
            print(f"  MISS {name[:40]:42} no catalog item with this name")
            problems.append((name, "not found"))
        else:
            print(f"  DUP  {name[:40]:42} {len(hits)} items share this name")
            for h in hits:
                print(f"         -> {h['id']}  code={h.get('code')}")
            problems.append((name, f"{len(hits)} duplicates"))

    if problems:
        print(f"\n{len(problems)} unresolved:")
        for n, why in problems:
            print(f"  - {n}: {why}")
        sys.exit("\nABORT: not writing a partial or ambiguous group. Resolve "
                 "the above (check for renamed or duplicate catalog items) "
                 "and rerun.")

    print(f"\nall {len(resolved)} resolved cleanly.")

    # --- find or create the group -----------------------------------------
    groups, _ = fetch_all("/item-groups")
    existing = next((g for g in (groups or [])
                     if (g.get("name") or "").strip().lower()
                     == GROUP_NAME.lower()), None)

    if existing:
        gid = existing["id"]
        print(f"\ngroup exists: {GROUP_NAME}  {gid}")
        cur, _ = fetch_all(
            f"/item-group-item-assignments?filter[item_group_id]=eq:{gid}")
        cur_ids = {c.get("item_id") for c in (cur or [])}
        print(f"  current members: {len(cur_ids)}")
    else:
        gid, cur_ids = None, set()
        print(f"\ngroup does not exist; will create: {GROUP_NAME}")

    to_add = [it for it in resolved if it["id"] not in cur_ids]
    already = len(resolved) - len(to_add)
    print(f"\nplan: {len(to_add)} assignments to add"
          f"{f' ({already} already present)' if already else ''}")

    if not a.write:
        print("\n" + "=" * 72)
        print("DRY RUN — nothing written. Rerun with --write to apply:")
        print(f"  1. {'create' if not gid else 'reuse'} item group "
              f"{GROUP_NAME!r}")
        print(f"  2. POST {len(to_add)} item-group-item-assignments")
        print("=" * 72)
        return

    # --- write -------------------------------------------------------------
    if not gid:
        s, b = req("POST", "/item-groups", body={"name": GROUP_NAME})
        if s not in (200, 201):
            sys.exit(f"ABORT: create group failed ({s}): {b}")
        gid = (b.get("data", b) if isinstance(b, dict) else {}).get("id")
        print(f"\ncreated group {GROUP_NAME}  {gid}")
        if not gid:
            sys.exit("ABORT: no group id returned")

    ok, failed = 0, []
    for it in to_add:
        s, b = req("POST", "/item-group-item-assignments",
                   body={"item_group_id": gid, "item_id": it["id"]})
        if s in (200, 201):
            ok += 1
            print(f"  + {it['name'][:44]:46} assigned")
        else:
            failed.append((it["name"], s, b))
            print(f"  ! {it['name'][:44]:46} FAILED ({s})")
        time.sleep(0.15)

    # --- verify ------------------------------------------------------------
    final, _ = fetch_all(
        f"/item-group-item-assignments?filter[item_group_id]=eq:{gid}")
    print("\n" + "=" * 72)
    print(f"RESULT: {ok} assigned, {len(failed)} failed")
    print(f"VERIFIED: group {gid} now has {len(final or [])} members "
          f"(expected {len(resolved)})")
    if failed:
        print("\nfailures:")
        for n, s, b in failed:
            print(f"  - {n}: {s} {str(b)[:200]}")
    print("=" * 72)


if __name__ == "__main__":
    main()
