#!/usr/bin/env python3
"""
sync_quoter_to_pipedrive.py — keep a Pipedrive dropdown in step with Quoter.

Handles the three cases: created, renamed, deleted.

WHAT IT SYNCS
-------------
  --source templates    ScalePad GET /quoter/v1/quote-templates   (id, title)
  --source item-groups  ScalePad GET /quoter/v1/item-groups       (id, name)

Both are pushed into a Pipedrive enum/set field's options.

WHY A STATE FILE
----------------
Matching Quoter records to Pipedrive options by LABEL cannot tell a rename
from a delete-plus-create. Rename "Robotics" to "ROB-Robotics" and a
label-matcher adds a new option and orphans the old one — while every deal
still points at the old id.

So this keeps a map of {quoter_id: pipedrive_option_id}. With it, a rename is
a PUT that changes the label and keeps the id, and deals keep resolving. The
map is written next to this script and should be committed.

On first run the map is empty; existing options are adopted by exact
case-insensitive label match, and that pairing is recorded.

DELETION IS DELIBERATELY NOT AUTOMATED
--------------------------------------
Deleting a Quoter template does NOT delete its Pipedrive option. A deal stores
the option id; removing the option orphans that stored value, and the deal's
history silently loses meaning. Orphans are REPORTED for a human to retire in
the UI, after checking nothing references them.

This mirrors the instinct in the older sync_templates_to_pipedrive.py
("These won't be automatically removed for safety") — which was right, even
though that script's endpoint never existed (see pd_fields.py).

Usage:
    export SCALEPAD_API_KEY='...' PIPEDRIVE_API_TOKEN='...'

    python3 sync_quoter_to_pipedrive.py --source templates --field 90
    python3 sync_quoter_to_pipedrive.py --source templates --field 90 --apply
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STATE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Prefix marking an option whose Quoter record is gone. Chosen so retired
# entries sort to the bottom of Pipedrive's A-Z option list and read as
# obviously not-for-selection. The option ID survives, so any deal that
# already stored it still resolves to a meaningful label.
RETIRE_PREFIX = "XX-RET-"


def is_retired(label):
    return (label or "").startswith(RETIRE_PREFIX)


def strip_retired(label):
    return (label or "")[len(RETIRE_PREFIX):] if is_retired(label) else (label or "")

SOURCES = {
    "templates":   {"path": "/quoter/v1/quote-templates", "label_key": "title",
                    "state": "pd_option_map_templates.json"},
    "item-groups": {"path": "/quoter/v1/item-groups",     "label_key": "name",
                    "state": "pd_option_map_item_groups.json"},
}


# ---------------------------------------------------------------- Quoter ----

def fetch_quoter(path, label_key):
    """All records from a ScalePad collection, following cursor pagination.

    Uses ScalePadV2Client (DECISIONS D-002/D-003). Its session sets a literal
    lowercase x-api-key, which the gateway requires — see Chapter 3 2.1.1.
    """
    from scalepad_v2 import ScalePadV2Client
    client = ScalePadV2Client()
    out, cursor, seen = [], None, set()
    while True:
        params = {"page_size": 200}
        if cursor:
            params["cursor"] = cursor
        resp = client.get(path, params=params) or {}
        out.extend(resp.get("data") or [])
        cursor = resp.get("next_cursor")
        if not cursor or cursor in seen:
            break
        seen.add(cursor)
    total = None
    return [{"id": r.get("id"), "label": (r.get(label_key) or "").strip()}
            for r in out if r.get("id")]


# ----------------------------------------------------------------- state ----

def load_state(name):
    p = STATE_DIR / name
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        print(f"  ! {p.name} unreadable; treating as empty")
        return {}


def save_state(name, mapping):
    (STATE_DIR / name).write_text(json.dumps(mapping, indent=2, sort_keys=True))


# ------------------------------------------------------------------ plan ----

def build_plan(records, options, state):
    """Return (to_add, to_rename, orphans, adopted, to_unretire).

    to_add      : records with no option yet
    to_rename   : (option_id, old_label, new_label) — same Quoter id, new label
    orphans     : live options no Quoter record maps to, NOT already retired
    adopted     : first-run pairings matched by label
    to_unretire : (option_id, retired_label, record) — a retired option whose
                  Quoter record came back, so reuse the id rather than making
                  a duplicate

    Options already carrying RETIRE_PREFIX are excluded from `orphans` — they
    have been dealt with, and re-reporting them forever would train people to
    ignore the orphan list.
    """
    by_id = {str(o["id"]): (o.get("label") or "") for o in options}
    by_label = {(o.get("label") or "").strip().lower(): str(o["id"])
                for o in options}
    # retired options, keyed by their ORIGINAL label
    retired_by_label = {strip_retired(lbl).strip().lower(): oid
                        for oid, lbl in by_id.items() if is_retired(lbl)}

    to_add, to_rename, adopted, to_unretire = [], [], [], []
    mapped_option_ids = set()

    for rec in records:
        oid = state.get(rec["id"])

        if oid is None:
            hit = by_label.get(rec["label"].lower())
            if hit:
                adopted.append((rec, hit))
                mapped_option_ids.add(hit)
                continue
            # Was it retired earlier? Reuse the id instead of duplicating.
            back = retired_by_label.get(rec["label"].lower())
            if back:
                to_unretire.append((back, by_id[back], rec))
                mapped_option_ids.add(back)
                continue
            to_add.append(rec)
            continue

        oid = str(oid)
        if oid not in by_id:
            to_add.append(rec)          # mapped option deleted in Pipedrive
            continue

        mapped_option_ids.add(oid)
        current = by_id[oid]
        if is_retired(current):
            to_unretire.append((oid, current, rec))
        elif current.strip() != rec["label"]:
            to_rename.append((oid, current, rec["label"]))

    orphans = [(oid, lbl) for oid, lbl in by_id.items()
               if oid not in mapped_option_ids and not is_retired(lbl)]

    live_ids = {r["id"] for r in records}
    for qid, oid in state.items():
        oid = str(oid)
        if qid not in live_ids and oid in by_id and not is_retired(by_id[oid]):
            orphans.append((oid, by_id[oid]))

    seen, uniq = set(), []
    for o in orphans:
        if o[0] not in seen:
            seen.add(o[0])
            uniq.append(o)
    return to_add, to_rename, uniq, adopted, to_unretire


# ------------------------------------------------------------------ main ----

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=sorted(SOURCES), required=True)
    ap.add_argument("--field", required=True, help="Pipedrive dealField id")
    ap.add_argument("--apply", action="store_true",
                    help="perform the writes (default is a dry run)")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress per-item detail; print a one-line summary. "
                         "Intended for cron, where only changes matter.")
    ap.add_argument("--retire-orphans", action="store_true",
                    help=f"relabel orphaned options with the {RETIRE_PREFIX!r} "
                         "prefix instead of only reporting them. The option id "
                         "is preserved, so deals already storing it still "
                         "resolve. Nothing is ever deleted.")
    a = ap.parse_args()

    cfg = SOURCES[a.source]
    from pd_fields import PipedriveFields, OptionIdDrift
    pd = PipedriveFields()

    print("=" * 72)
    print(f"SYNC {a.source} -> Pipedrive field {a.field}   "
          f"[{'APPLY' if a.apply else 'DRY RUN'}]")
    print("=" * 72)

    field = pd.get_deal_field(a.field)
    if not field:
        sys.exit(f"field {a.field} not found")
    if field.get("field_type") not in ("enum", "set"):
        sys.exit(f"field {a.field} is {field.get('field_type')}, not enum/set")
    print(f"\n  field   : {field.get('name')!r} ({field.get('field_type')})")

    records = fetch_quoter(cfg["path"], cfg["label_key"])
    options = pd.get_options(a.field)
    state = load_state(cfg["state"])
    print(f"  quoter  : {len(records)} record(s)")
    print(f"  pipedrive: {len(options)} option(s)")
    print(f"  state   : {len(state)} known pairing(s)")

    to_add, to_rename, orphans, adopted, to_unretire = build_plan(
        records, options, state)

    if adopted:
        print(f"\n  ADOPT (first-run label match): {len(adopted)}")
        for rec, oid in adopted:
            print(f"    {rec['label']!r}  <->  option {oid}")

    print(f"\n  ADD    : {len(to_add)}")
    for r in to_add:
        print(f"    + {r['label']!r}   ({r['id']})")

    print(f"  RENAME : {len(to_rename)}")
    for oid, old, new in to_rename:
        print(f"    ~ option {oid}: {old!r} -> {new!r}   (id preserved)")

    print(f"  UNRETIRE: {len(to_unretire)}")
    for oid, lbl, rec in to_unretire:
        print(f"    ^ option {oid}: {lbl!r} -> {rec['label']!r}   (id reused)")

    print(f"  ORPHAN : {len(orphans)}")
    for oid, lbl in orphans:
        arrow = f" -> {RETIRE_PREFIX}{lbl!r}" if a.retire_orphans else ""
        print(f"    ? option {oid} {lbl!r} — no live Quoter record{arrow}")
    if orphans and a.retire_orphans:
        print(f"      Will be relabelled with {RETIRE_PREFIX!r}. The id is kept,")
        print("      so deals storing it still resolve to a meaningful label,")
        print("      and the entry sorts to the bottom of the dropdown.")
        print("      Nothing is deleted — removal stays a human decision.")
    elif orphans:
        print("      Reported only. Deals store option ids, so deleting one")
        print("      orphans that deal's stored value. Pass --retire-orphans")
        print("      to relabel them instead, or retire them in the UI.")

    if not a.apply:
        print("\n" + "=" * 72)
        print("DRY RUN — nothing written. Rerun with --apply.")
        print("=" * 72)
        return

    # ---- writes ----------------------------------------------------------
    print("\n" + "-" * 72)
    print("APPLYING")
    print("-" * 72)
    new_state = dict(state)
    for rec, oid in adopted:
        new_state[rec["id"]] = oid

    try:
        for oid, old, new in to_rename:
            pd.rename_option(a.field, oid, new)
            print(f"  renamed option {oid}: {old!r} -> {new!r}")

        for oid, old, rec in to_unretire:
            pd.rename_option(a.field, oid, rec["label"])
            new_state[rec["id"]] = str(oid)
            print(f"  un-retired option {oid}: {old!r} -> {rec['label']!r}")

        for rec in to_add:
            created = pd.add_option(a.field, rec["label"])
            if created:
                new_state[rec["id"]] = str(created["id"])
                print(f"  added {rec['label']!r} -> option {created['id']}")
            else:
                cur = {(o.get('label') or '').strip().lower(): str(o["id"])
                       for o in pd.get_options(a.field)}
                hit = cur.get(rec["label"].lower())
                if hit:
                    new_state[rec["id"]] = hit
                    print(f"  {rec['label']!r} already present -> option {hit}")
        if a.retire_orphans:
            for oid, lbl in orphans:
                pd.rename_option(a.field, oid, f"{RETIRE_PREFIX}{lbl}")
                print(f"  retired option {oid}: {lbl!r} -> "
                      f"{RETIRE_PREFIX}{lbl}")

    except OptionIdDrift as e:
        print(f"\n  ABORTED: {e}")
        print("  Existing option ids changed meaning. Investigate before rerunning.")
        return
    except ValueError as e:
        print(f"\n  ABORTED: {e}")
        return
    finally:
        save_state(cfg["state"], new_state)
        print(f"\n  state written to {cfg['state']} ({len(new_state)} pairings)")

    print(f"\nSUMMARY added={len(to_add)} renamed={len(to_rename)} "
          f"unretired={len(to_unretire)} orphans={len(orphans)}")
    print("\n" + "=" * 72)
    print("DONE. Consumers can resolve option ids at runtime via")
    print(f"  PipedriveFields().option_map({a.field})")
    print("so no id->label mapping needs to live in code.")
    print("=" * 72)


if __name__ == "__main__":
    main()
