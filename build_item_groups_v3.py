#!/usr/bin/env python3
"""
build_item_groups_v3.py — create/update Item Groups from a data-driven definition.

WHAT CHANGED FROM v2
--------------------
v2 carried a hard-coded list of six item NAMES, transcribed from a template
sweep. Three problems with that:

  1. It was a list to maintain, which is the thing this project exists to
     eliminate.
  2. Name matching is fragile; codes are unique across all 301 items and
     resolvable server-side via filter[code].
  3. The template is an incomplete view of the catalog. The Balloons template
     carries 6 balloon items; the catalog holds 8. `Balloon- 12 ft` and
     `Balloon- 8 ft` were never on it, so a template-derived group could not
     offer them.

v3 resolves membership from a JSON definition instead:

  code_prefixes  DERIVABLE baseline. Add a BAL- item to the catalog and it
                 joins XRN-Balloons by construction. Nothing to update.
  include_codes  cross-family items a prefix cannot capture -- an exploding
                 balloon wall needing pyro, a laser show needing a technician.
                 Judgement calls, stated explicitly.
  exclude_codes  prefix matches that do not belong.

Why prefix and not category: the API returns only a category's LEAF name, and
16 leaf names collide across parents (Chapter 3 2.3.2). Category selection is
ambiguous AND sweeps in test data -- `Balloons / Latex` holds 11 zz-test
fixtures, so a category-derived Balloons group would be 20 items, 11 junk.
The ZZZ- prefix drops them for free.

DRY RUN BY DEFAULT.

Usage:
    export SCALEPAD_API_KEY='...'
    python3 build_item_groups_v3.py --group XRN-Balloons
    python3 build_item_groups_v3.py --group XRN-Balloons --write
    python3 build_item_groups_v3.py --all
"""

import argparse
import http.client
import json
import os
import ssl
import sys
import time
import urllib.parse
from pathlib import Path

BASE = "https://api.scalepad.com/quoter/v1"
HOST = "api.scalepad.com"
DEFS = Path(os.path.dirname(os.path.abspath(__file__))) / "item_group_defs.json"

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


def fetch_all(path):
    """Cursor pagination. Unrecognised params are silently ignored by this API,
    so completeness is checked against total_count rather than assumed."""
    sep = "&" if "?" in path else "?"
    s, b = req("GET", f"{path}{sep}page_size=200")
    if s != 200 or not isinstance(b, dict):
        return None, None
    rows, total = list(b.get("data") or []), b.get("total_count")
    cursor, seen = b.get("next_cursor"), set()
    while cursor and cursor not in seen:
        seen.add(cursor)
        s2, b2 = req("GET", f"{path}{sep}page_size=200"
                            f"&cursor={urllib.parse.quote(cursor)}")
        if s2 != 200 or not isinstance(b2, dict):
            break
        batch = b2.get("data") or []
        if not batch:
            break
        rows.extend(batch)
        cursor = b2.get("next_cursor")
        time.sleep(0.15)
    return rows, total


def resolve(spec, items):
    """Apply prefixes, includes and excludes. Returns (selected, problems)."""
    by_code = {}
    for it in items:
        c = (it.get("code") or "").strip()
        if c:
            by_code.setdefault(c, []).append(it)

    prefixes = spec.get("code_prefixes") or []
    includes = spec.get("include_codes") or []
    excludes = {c.strip() for c in (spec.get("exclude_codes") or [])}

    picked, why, problems = {}, {}, []

    for it in items:
        code = (it.get("code") or "").strip()
        if not code or code in excludes:
            continue
        hit = next((p for p in prefixes if code.startswith(p)), None)
        if hit:
            picked[it["id"]] = it
            why[it["id"]] = f"prefix {hit}"

    for code in includes:
        rows = by_code.get(code.strip(), [])
        if not rows:
            problems.append((code, "no catalog item with this code"))
            continue
        if len(rows) > 1:
            problems.append((code, f"{len(rows)} items share this code"))
            continue
        it = rows[0]
        if it["id"] not in picked:
            picked[it["id"]] = it
            why[it["id"]] = "explicit include"

    for code in excludes:
        if code not in by_code:
            problems.append((code, "exclude_codes lists a code not in catalog"))

    return [(picked[i], why[i]) for i in picked], problems


def sync_group(name, spec, items, groups, do_write):
    print("=" * 72)
    print(f"{name}   [{'WRITE' if do_write else 'DRY RUN'}]")
    print("=" * 72)
    if spec.get("description"):
        print(f"  {spec['description']}")
    print(f"  prefixes: {spec.get('code_prefixes') or '(none)'}"
          f"   includes: {spec.get('include_codes') or '(none)'}"
          f"   excludes: {spec.get('exclude_codes') or '(none)'}")

    selected, problems = resolve(spec, items)
    if problems:
        print(f"\n  {len(problems)} definition problem(s):")
        for code, why in problems:
            print(f"    ! {code}: {why}")
        print("\n  ABORT: not writing a group built on a broken definition.")
        return False

    print(f"\n  {len(selected)} item(s):")
    for it, why in sorted(selected, key=lambda x: x[0].get("code") or ""):
        print(f"    {it.get('code'):16} sku={str(it.get('sku')):5} "
              f"{it['name'][:38]:40} [{why}]")

    existing = next((g for g in groups
                     if (g.get("name") or "").strip().lower() == name.lower()),
                    None)
    if existing:
        gid = existing["id"]
        cur, _ = fetch_all(
            f"/item-group-item-assignments?filter[item_group_id]=eq:{gid}")
        cur_ids = {c.get("item_id") for c in (cur or [])}
        print(f"\n  group exists: {gid}   members={len(cur_ids)}")
    else:
        gid, cur_ids = None, set()
        print(f"\n  group does not exist; will create")

    to_add = [it for it, _ in selected if it["id"] not in cur_ids]
    stale = cur_ids - {it["id"] for it, _ in selected}
    print(f"  plan: add {len(to_add)}"
          f"{f', {len(cur_ids) - len(to_add)} already present' if cur_ids else ''}")
    if stale:
        print(f"  NOTE: {len(stale)} assigned item(s) no longer match the")
        print("        definition. Not removed — removal is not implemented,")
        print("        and an assignment is cheap to leave in place. Prune by")
        print("        hand if it matters.")

    if not do_write:
        print()
        return True

    if not gid:
        s, b = req("POST", "/item-groups", body={"name": name})
        if s not in (200, 201):
            print(f"  ABORT: create group failed ({s}): {str(b)[:300]}")
            return False
        gid = (b.get("data", b) if isinstance(b, dict) else {}).get("id")
        print(f"\n  created group {gid}")

    ok, failed = 0, []
    for it in to_add:
        s, b = req("POST", "/item-group-item-assignments",
                   body={"item_group_id": gid, "item_id": it["id"]})
        if s in (200, 201):
            ok += 1
            print(f"    + {it.get('code'):16} {it['name'][:40]}")
        else:
            failed.append((it.get("code"), s, str(b)[:120]))
            print(f"    ! {it.get('code'):16} FAILED ({s})")
        time.sleep(0.15)

    final, _ = fetch_all(
        f"/item-group-item-assignments?filter[item_group_id]=eq:{gid}")
    print(f"\n  RESULT: {ok} added, {len(failed)} failed")
    print(f"  VERIFIED: group now has {len(final or [])} members "
          f"(expected {len(selected)})")
    for c, s, msg in failed:
        print(f"    {c}: {s} {msg}")
    print()
    return not failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", help="group name from item_group_defs.json")
    ap.add_argument("--all", action="store_true", help="every defined group")
    ap.add_argument("--write", action="store_true",
                    help="create groups and assignments (default: dry run)")
    a = ap.parse_args()

    if not DEFS.exists():
        sys.exit(f"ERROR: {DEFS.name} not found next to this script.")
    defs = json.loads(DEFS.read_text()).get("groups") or {}
    if not defs:
        sys.exit("ERROR: no groups defined.")

    if a.all:
        names = list(defs)
    elif a.group:
        if a.group not in defs:
            sys.exit(f"ERROR: {a.group!r} not defined. Available: "
                     f"{', '.join(defs)}")
        names = [a.group]
    else:
        print("Defined groups:")
        for n, spec in defs.items():
            print(f"  {n:24} prefixes={spec.get('code_prefixes')}")
        print("\nPass --group NAME or --all.")
        return

    items, total = fetch_all("/items")
    if items is None:
        sys.exit("ERROR: could not read /items")
    print(f"catalog: fetched {len(items)} of {total}\n")
    if total is not None and len(items) != total:
        sys.exit("ABORT: incomplete catalog pull — a missing item would be "
                 "silently dropped from the group.")

    groups, _ = fetch_all("/item-groups")
    groups = groups or []

    for n in names:
        sync_group(n, defs[n], items, groups, a.write)

    if not a.write:
        print("=" * 72)
        print("DRY RUN — nothing written. Rerun with --write.")
        print("=" * 72)


if __name__ == "__main__":
    main()
