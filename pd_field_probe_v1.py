#!/usr/bin/env python3
"""
pd_field_probe_v1.py — can we manage Pipedrive custom-field options via API?

THE QUESTION
------------
If Item Groups become the unit Pipedrive passes to Render, then creating a
group in Quoter needs to surface as a selectable option in Pipedrive. Two
halves, and only the first is usually discussed:

  1. can we ADD an option programmatically?
  2. can we READ BACK its numeric ID?

(2) is the one that matters. Pipedrive stores the option ID on the deal, not
the label. A webhook carries "90": "247", so Render needs 247 -> "Balloons".
If that map is hardcoded in Python, adding a group still means a code change
and nothing is really automated. If the map can be fetched at runtime, the
loop closes.

`sync_templates_to_pipedrive.py` (Jan 2026) adds labels via v1 but never
captures IDs, which is consistent with the mapping having been built by hand.

This also probes whether API v2 exposes dealFields at all -- `pipedrive_v2.py`
only wraps products, so the v2 surface for fields is unverified here.

  Phase 1 (default)  READ ONLY. Lists dealFields, finds enum/set fields,
                     dumps options with their IDs. Tries v1 and v2.
  Phase 2 (--write)  Adds ONE option labelled zz-TEST-<timestamp> to the
                     field given by --field, then reads it back to see
                     whether the new ID is retrievable.

Adding an option is additive and low-risk, but it IS a schema change on a
production custom field. Nothing is deleted -- removing an option that deals
already reference would orphan their data, so this script never does it.

Usage:
    export PIPEDRIVE_API_TOKEN='...'
    python3 pd_field_probe_v1.py
    python3 pd_field_probe_v1.py --field 90
    python3 pd_field_probe_v1.py --field 90 --write
"""

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("ERROR: pip install requests  (or activate the project venv)")

V1 = "https://api.pipedrive.com/v1"
V2 = "https://api.pipedrive.com/api/v2"

TOKEN = os.environ.get("PIPEDRIVE_API_TOKEN", "").strip()
if not TOKEN:
    sys.exit("ERROR: set PIPEDRIVE_API_TOKEN.\n"
             "  export $(grep -v '^#' .env | grep PIPEDRIVE_API_TOKEN | xargs)")

S = requests.Session()


def call(method, url, params=None, body=None):
    p = dict(params or {})
    p["api_token"] = TOKEN
    try:
        r = S.request(method, url, params=p, json=body, timeout=30)
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, r.text[:500]
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def phase1(field_arg):
    print("=" * 72)
    print("PHASE 1 — READ ONLY: custom fields and their options")
    print("=" * 72)

    # Does v2 expose dealFields? pipedrive_v2.py only covers products.
    s2, _ = call("GET", f"{V2}/dealFields", params={"limit": 1})
    print(f"\n  GET /api/v2/dealFields -> {s2}"
          f"   {'available' if s2 == 200 else 'not available; using v1'}")

    s, b = call("GET", f"{V1}/dealFields")
    if s != 200 or not isinstance(b, dict):
        print(f"  GET /v1/dealFields failed ({s}): {str(b)[:200]}")
        return None
    fields = b.get("data") or []
    print(f"  GET /v1/dealFields -> 200, {len(fields)} fields\n")

    choosers = [f for f in fields if f.get("field_type") in ("enum", "set")]
    print(f"  {len(choosers)} enum/set field(s):\n")
    for f in choosers:
        opts = f.get("options") or []
        mark = "  <-- selected" if str(f.get("id")) == str(field_arg) else ""
        print(f"    id={str(f.get('id')):5} {f.get('field_type'):4} "
              f"{str(f.get('name'))[:34]:36} options={len(opts)}{mark}")
        print(f"          key={f.get('key')}")

    target = next((f for f in fields if str(f.get("id")) == str(field_arg)), None)
    if not target:
        print(f"\n  (no field with id {field_arg}; pass --field <id> to inspect one)")
        return None

    print("\n" + "-" * 72)
    print(f"FIELD {target.get('id')} — {target.get('name')!r}")
    print("-" * 72)
    print(f"  key        : {target.get('key')}")
    print(f"  field_type : {target.get('field_type')}")
    opts = target.get("options") or []
    print(f"  options    : {len(opts)}\n")
    for o in opts:
        print(f"    id={str(o.get('id')):6} label={o.get('label')!r}")

    print("\n  ^ THIS is the map Render needs. A webhook carries the option ID,")
    print("    not the label. If this can be fetched at runtime, the ID->label")
    print("    mapping never needs to live in Python.")
    print("\n  Phase 1 done. Nothing written.")
    return target


def phase2(target):
    if not target:
        print("\nNo field selected; pass --field <id>. Skipping write.")
        return
    fid = target.get("id")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    label = f"zz-TEST-{stamp}"

    print()
    print("=" * 72)
    print(f"PHASE 2 — add ONE option to field {fid} ({target.get('name')!r})")
    print("=" * 72)
    print(f"\n  label: {label}")

    before = {str(o.get("id")) for o in (target.get("options") or [])}

    # The additive endpoint. Deliberately NOT a PUT of the whole options
    # array: existing deals store option IDs, and rewriting the array risks
    # renumbering them.
    s, b = call("POST", f"{V1}/dealFields/{fid}/options", body={"label": label})
    print(f"  POST /v1/dealFields/{fid}/options -> {s}")
    if s not in (200, 201):
        print(f"  response: {json.dumps(b)[:400] if isinstance(b, dict) else str(b)[:400]}")
        print("\n  Additive endpoint rejected. Fallback would be PUT /v1/dealFields/{id}")
        print("  with the FULL options array — riskier, since it can renumber")
        print("  existing option IDs that deals already reference. Not attempted here.")
        return
    print(f"  response: {json.dumps(b)[:300]}")

    # --- the part that actually matters: is the new ID retrievable? -------
    time.sleep(1.0)
    s2, b2 = call("GET", f"{V1}/dealFields/{fid}")
    opts = ((b2 or {}).get("data") or {}).get("options") or []
    new = [o for o in opts if str(o.get("id")) not in before]

    print("\n" + "-" * 72)
    print("READ-BACK")
    print("-" * 72)
    print(f"  options before: {len(before)}   after: {len(opts)}")
    for o in new:
        print(f"  NEW  id={o.get('id')}  label={o.get('label')!r}")

    print("\n" + "=" * 72)
    if new:
        print("RESULT: options are BOTH creatable and readable by ID.")
        print("Render can fetch GET /v1/dealFields/{id} at runtime and build")
        print("the option-ID -> name map itself. Adding an Item Group then")
        print("needs one sync call and NO code change.")
    else:
        print("RESULT: the POST reported success but no new option was read")
        print("back. Inspect the raw responses above before relying on this.")
    print("=" * 72)
    print(f"\nCleanup: option {label!r} remains on field {fid}. Remove it in")
    print("Pipedrive's UI (Settings > Data fields). Do NOT delete options that")
    print("existing deals reference — that orphans their stored value.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--field", default="90",
                    help="dealField numeric id to inspect (default 90)")
    ap.add_argument("--write", action="store_true",
                    help="add one zz-TEST option to that field")
    a = ap.parse_args()
    target = phase1(a.field)
    if a.write:
        phase2(target)
    else:
        print("\n" + "=" * 72)
        print("Phase 2 not run — it adds one option to a production field.")
        print("Rerun with --write once the field above looks right.")
        print("=" * 72)


if __name__ == "__main__":
    main()
