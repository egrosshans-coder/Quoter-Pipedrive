#!/usr/bin/env python3
"""
pd_field_probe_v2.py — can enum options be ADDED without renumbering the
existing ones?

WHY v2
------
v1 of this probe tried POST /v1/dealFields/{id}/options and got:

    404 "Route POST:/v1/dealFields/90/options not found"

That route does not exist. Note the consequence: sync_templates_to_pipedrive.py
(Jan 2026) is built entirely on that endpoint, so it has never worked. The
Quote Template dropdown was populated by hand.

The documented alternative is PUT /v1/dealFields/{id} with the COMPLETE
options array. Existing options must be sent WITH their ids; new ones without.
If ids are omitted, Pipedrive is free to reassign them — and every deal that
already references an option stores its ID, not its label. Renumbering would
silently repoint historical deals at the wrong values.

THE SAFETY PROBLEM
------------------
Field 90 is REQUIRED, IMPORTANT, and carries 11 in-use options. It is the
wrong place to find out whether the theory holds.

So this script tests on a THROWAWAY FIELD it creates itself:

  --create   make a scratch enum field 'zz-PROBE-<ts>' with 2 options
  --test ID  PUT a full array against that field, adding one option, then
             verify every pre-existing option id is unchanged
  --cleanup ID   delete the scratch field

Only once that passes should the same shape be applied to a real field, and
even then with the before-state recorded first.

This script will REFUSE to write to field 90.

Usage:
    export PIPEDRIVE_API_TOKEN='...'
    python3 pd_field_probe_v2.py --create
    python3 pd_field_probe_v2.py --test <new-field-id>
    python3 pd_field_probe_v2.py --cleanup <new-field-id>
"""

import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("ERROR: pip install requests (or activate the project venv)")

V1 = "https://api.pipedrive.com/v1"
PROTECTED = {"90"}          # Quote Template — never write here from this script

TOKEN = os.environ.get("PIPEDRIVE_API_TOKEN", "").strip()
if not TOKEN:
    sys.exit("ERROR: set PIPEDRIVE_API_TOKEN")

S = requests.Session()


def call(method, path, params=None, body=None):
    p = dict(params or {})
    p["api_token"] = TOKEN
    try:
        r = S.request(method, f"{V1}{path}", params=p, json=body, timeout=30)
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, r.text[:400]
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def get_field(fid):
    s, b = call("GET", f"/dealFields/{fid}")
    if s != 200 or not isinstance(b, dict):
        return None
    return b.get("data")


def show_options(opts, label="options"):
    print(f"  {label}: {len(opts)}")
    for o in opts:
        print(f"    id={str(o.get('id')):6} label={o.get('label')!r}")


def do_create():
    stamp = time.strftime("%Y%m%d-%H%M%S")
    name = f"zz-PROBE-{stamp}"
    print("=" * 72)
    print(f"CREATE scratch field {name!r}")
    print("=" * 72)
    body = {
        "name": name,
        "field_type": "enum",
        "options": [{"label": "zz-alpha"}, {"label": "zz-beta"}],
    }
    s, b = call("POST", "/dealFields", body=body)
    print(f"\n  POST /dealFields -> {s}")
    if s not in (200, 201):
        print(f"  {json.dumps(b)[:400]}")
        return
    d = b.get("data") or {}
    print(f"  created field id={d.get('id')}  key={d.get('key')}")
    show_options(d.get("options") or [], "initial options")
    print(f"\n  Next:  python3 pd_field_probe_v2.py --test {d.get('id')}")
    print(f"  Then:  python3 pd_field_probe_v2.py --cleanup {d.get('id')}")
    print("\n  This is an unused scratch field. It appears in Settings > Data")
    print("  fields until deleted, but no deal references it.")


def do_test(fid):
    if str(fid) in PROTECTED:
        sys.exit(f"REFUSING: field {fid} is a protected production field.\n"
                 "Prove the behaviour on a scratch field first (--create).")

    print("=" * 72)
    print(f"TEST — add an option to field {fid} via PUT, preserving ids")
    print("=" * 72)

    before = get_field(fid)
    if not before:
        sys.exit(f"could not read field {fid}")
    print(f"\n  field: {before.get('name')!r}  type={before.get('field_type')}")
    old = before.get("options") or []
    show_options(old, "BEFORE")
    old_ids = {str(o.get("id")): o.get("label") for o in old}

    # Every existing option is resent WITH its id. That is the whole point:
    # omitting ids invites Pipedrive to reassign them.
    stamp = time.strftime("%H%M%S")
    payload_opts = [{"id": o["id"], "label": o["label"]} for o in old]
    payload_opts.append({"label": f"zz-added-{stamp}"})

    print(f"\n  PUT body options: {json.dumps(payload_opts)[:220]}")
    s, b = call("PUT", f"/dealFields/{fid}", body={"options": payload_opts})
    print(f"  PUT /dealFields/{fid} -> {s}")
    if s not in (200, 201):
        print(f"  {json.dumps(b)[:400] if isinstance(b, dict) else str(b)[:400]}")
        print("\n  RESULT: options cannot be added this way either. Dropdown")
        print("  maintenance would then be UI-only, and any new template or")
        print("  Item Group means a manual step in Pipedrive.")
        return

    time.sleep(1.0)
    after = get_field(fid) or {}
    new = after.get("options") or []
    show_options(new, "\n  AFTER")

    # The actual verification: did any pre-existing id move?
    new_ids = {str(o.get("id")): o.get("label") for o in new}
    drifted = [(i, old_ids[i], new_ids.get(i)) for i in old_ids
               if new_ids.get(i) != old_ids[i]]
    added = [i for i in new_ids if i not in old_ids]

    print("\n" + "=" * 72)
    if drifted:
        print("RESULT: DANGEROUS — pre-existing option ids changed meaning:")
        for i, was, now in drifted:
            print(f"    id={i}  was {was!r}  now {now!r}")
        print("Do NOT run this against a field with deals attached.")
    elif added:
        print(f"RESULT: SAFE — option added (new id {added[0]}), and every")
        print("pre-existing id kept its original label. Sending existing")
        print("options with their ids preserves them.")
        print("\nSo a Quoter template or Item Group CAN be pushed to a")
        print("Pipedrive dropdown automatically — via PUT with the full")
        print("array, not the POST .../options route, which does not exist.")
    else:
        print("RESULT: PUT succeeded but no option was added. Inspect above.")
    print("=" * 72)


def do_cleanup(fid):
    if str(fid) in PROTECTED:
        sys.exit(f"REFUSING to delete protected field {fid}.")
    print(f"Deleting scratch field {fid} ...")
    s, b = call("DELETE", f"/dealFields/{fid}")
    print(f"  DELETE /dealFields/{fid} -> {s}")
    print(f"  {json.dumps(b)[:200] if isinstance(b, dict) else str(b)[:200]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--test", metavar="FIELD_ID")
    ap.add_argument("--cleanup", metavar="FIELD_ID")
    a = ap.parse_args()
    if a.create:
        do_create()
    elif a.test:
        do_test(a.test)
    elif a.cleanup:
        do_cleanup(a.cleanup)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
