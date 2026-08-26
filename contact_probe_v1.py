#!/usr/bin/env python3
"""
contact_probe_v1.py — what does POST /quoter/v1/contacts actually want?

Guessing has cost three round trips already:
  {billing_email, first_name, last_name}          -> 422, named three required fields
  + billing_address, billing_country_iso, ...     -> 400 ERR_REQUEST_FORMAT_INVALID

A 400 is about the SHAPE of the body, a 422 about its CONTENTS. So the field
names in the 422 were right and something added afterwards is malformed --
most likely billing_country_iso, which is a guess by analogy with the legacy
v1 contact schema.

The line-item schema was solved the same way: read the field names off a real
record, because on this API the write schema mirrors the read schema.

  Phase 1 (default)  READ ONLY. Dumps a real contact's full field list.
  Phase 2 (--write)  Adds one field at a time, starting from the smallest body
                     the 422 says is acceptable, and reports where it breaks.

Phase 2 creates contacts tagged zz-CONTACTPROBE-<timestamp>@tlciscreative.com.
Note that a standalone contact record keeps id: null permanently (Chapter 3
section 5.1), so these cannot be cleaned up by id -- delete them in the UI by
email.

Usage:
    export SCALEPAD_API_KEY='...'
    python3 contact_probe_v1.py
    python3 contact_probe_v1.py --write
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    from scalepad_v2 import ScalePadV2Client
    c = ScalePadV2Client()

    print("=" * 72)
    print("CONTACT SCHEMA PROBE")
    print("=" * 72)

    # --- phase 1: what does a real contact look like? ---------------------
    r = c.get("/quoter/v1/contacts?page_size=3") or {}
    rows = r.get("data") or []
    print(f"\n  GET /contacts -> {len(rows)} shown of "
          f"{r.get('total_count')} total")
    if not rows:
        print("  no contacts to inspect")
        return

    keys = sorted(rows[0].keys())
    print(f"\n  FIELD NAMES ON A REAL CONTACT ({len(keys)}):")
    for k in keys:
        print(f"    {k}")

    print("\n  billing_* fields specifically:")
    for k in keys:
        if k.startswith("billing"):
            print(f"    {k:34} = {json.dumps(rows[0].get(k))[:60]}")

    print("\n  first record, in full:")
    print("   " + json.dumps(rows[0], indent=2)[:1600].replace("\n", "\n   "))

    if not a.write:
        print("\n" + "=" * 72)
        print("READ ONLY done. The write schema mirrors the read schema on this")
        print("API, so the names above are what POST expects. Rerun with")
        print("--write to confirm by building a body up field by field.")
        print("=" * 72)
        return

    # --- phase 2: build up a body until it breaks -------------------------
    stamp = time.strftime("%Y%m%d-%H%M%S")
    print("\n" + "=" * 72)
    print("PHASE 2 — add one field at a time, find what breaks the shape")
    print("=" * 72)

    base = {
        "billing_email": f"zz-CONTACTPROBE-{stamp}@tlciscreative.com",
        "billing_first_name": "ZZ",
        "billing_last_name": "Probe",
        "billing_address": "1 Test Street",
    }

    # Each step adds one field to the previous body. The first 400 names the
    # culprit, because everything before it was accepted.
    steps = [
        ("minimum (4 required)", {}),
        ("+ billing_country_iso", {"billing_country_iso": "US"}),
        ("+ billing_country", {"billing_country": "US"}),
        ("+ billing_organization", {"billing_organization": "ZZ Probe Org"}),
        ("+ billing_city", {"billing_city": "Los Angeles"}),
        ("+ billing_region_iso", {"billing_region_iso": "CA"}),
        ("+ billing_postal_code", {"billing_postal_code": "90045"}),
    ]

    body = dict(base)
    for label, extra in steps:
        trial = dict(body)
        trial.update(extra)
        trial["billing_email"] = (f"zz-CONTACTPROBE-{stamp}-"
                                  f"{len(trial)}@tlciscreative.com")
        try:
            c.post("/quoter/v1/contacts", data=trial)
            print(f"  {label:26} -> 201  OK")
            body = {k: v for k, v in trial.items()
                    if k != "billing_email"} | {"billing_email": base["billing_email"]}
        except Exception as e:
            msg = str(e)
            short = msg[:150]
            print(f"  {label:26} -> {short}")
            if "ERR_REQUEST_FORMAT_INVALID" in msg:
                print(f"\n  ^^ THIS field breaks the request shape: "
                      f"{list(extra)[0] if extra else '(base)'}")
                print("     Everything before it was accepted, so the working")
                print("     body is the previous step's.")
                break
        time.sleep(0.3)

    print("\n" + "=" * 72)
    print("Working body:")
    print(json.dumps(body, indent=2))
    print("=" * 72)
    print(f"\ncleanup: contacts tagged zz-CONTACTPROBE-{stamp} — delete by")
    print("email in the UI; standalone contact records have no usable id.")


if __name__ == "__main__":
    main()
