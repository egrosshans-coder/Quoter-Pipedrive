#!/usr/bin/env python3
"""
apply_archive_filter.py — add YY- archived-template filtering to
sync_quoter_to_pipedrive.py.

Run from the repo root (where sync_quoter_to_pipedrive.py lives):

    python3 apply_archive_filter.py            # dry run, shows the diff
    python3 apply_archive_filter.py --apply    # write it

WHAT IT DOES
    A Quoter template titled YY-<name> is excluded from the Pipedrive dropdown
    but kept in Quoter. Renaming alone is not enough: build_plan() treats a
    rename as a label change on the same option id, so the option stays
    selectable. The exclusion has to happen at fetch time.

SAFETY
    - Verifies all four anchors BEFORE writing anything. Aborts if any is
      missing or ambiguous, so a changed source file cannot be half-patched.
    - Writes sync_quoter_to_pipedrive.py.bak first.
    - Refuses to run twice (detects ARCHIVE_PREFIX already present).
    - Compiles the result and aborts if it does not parse.

This is a one-off utility. Delete it once applied.
"""

import argparse
import difflib
import py_compile
import shutil
import sys
import tempfile
from pathlib import Path

TARGET = Path("sync_quoter_to_pipedrive.py")

# --------------------------------------------------------------------------
# Each edit: (description, exact anchor text, replacement text)
# Anchors are copied verbatim from the current file. If any has changed, the
# script aborts rather than guessing.
# --------------------------------------------------------------------------

ANCHOR_1 = '''RETIRE_PREFIX = "XX-RET-"


def is_retired(label):
    return (label or "").startswith(RETIRE_PREFIX)
'''

REPLACE_1 = '''RETIRE_PREFIX = "XX-RET-"

# Prefix marking a Quoter record that is KEPT but must not be offered in
# Pipedrive. Distinct from RETIRE_PREFIX, which marks a Pipedrive OPTION whose
# Quoter record is gone. Two systems, two meanings:
#
#   XX-RET-   Pipedrive option label   retired - record gone, id kept so old
#                                      deals still resolve to a readable label
#   YY-       Quoter template title    archived - kept in Quoter, hidden here
#   zz-/ZZZ-  Quoter items and quotes  test artifact, safe to delete
#
# Archived templates stay fully usable for manual quote building in the Quoter
# UI. They are hidden only from the dropdown that drives automated composition.
#
# Why this exists: Quoter has no archive and template deletion is permanent,
# while ScalePad describes several API limitations as ones that "will likely be
# updated at some point". Keeping an archived template costs nothing; deleting
# one costs days of reconstruction if template line items ever become readable.
ARCHIVE_PREFIX = "YY-"

# Set from --include-archived in main(). Diagnostic only.
INCLUDE_ARCHIVED = False


def is_retired(label):
    return (label or "").startswith(RETIRE_PREFIX)


def is_archived(label):
    return (label or "").upper().startswith(ARCHIVE_PREFIX)
'''

ANCHOR_2 = '''            print(f"  excluded {before - len(records)} auto-appended group(s) "
                  f"from the dropdown: {', '.join(sorted(skip))}")
    return records
'''

REPLACE_2 = '''            print(f"  excluded {before - len(records)} auto-appended group(s) "
                  f"from the dropdown: {', '.join(sorted(skip))}")

    # Archived records: kept in Quoter, deliberately not offered in Pipedrive.
    # Their options become orphans on the next run and are retired (id kept),
    # so un-archiving later reuses the same option id via to_unretire.
    # Reversing this is a rename in Quoter -- drop the prefix and the record
    # reappears in the dropdown on the next run.
    if not INCLUDE_ARCHIVED:
        archived = [r for r in records if is_archived(r["label"])]
        if archived:
            records = [r for r in records if not is_archived(r["label"])]
            print(f"  excluded {len(archived)} archived record(s) "
                  f"[{ARCHIVE_PREFIX}]: "
                  f"{', '.join(sorted(r['label'] for r in archived))}")
    return records
'''

ANCHOR_3 = '''    a = ap.parse_args()

    cfg = SOURCES[a.source]'''

REPLACE_3 = '''    ap.add_argument("--include-archived", action="store_true",
                    help=f"include records whose name starts with "
                         f"{ARCHIVE_PREFIX!r}. Diagnostic only -- the scheduled "
                         f"run must NOT pass this, or archived templates "
                         f"reappear in the dropdown.")
    a = ap.parse_args()

    global INCLUDE_ARCHIVED
    INCLUDE_ARCHIVED = a.include_archived
    if INCLUDE_ARCHIVED:
        print(f"  !! --include-archived: {ARCHIVE_PREFIX} records WILL be "
              f"offered in Pipedrive")

    cfg = SOURCES[a.source]'''

ANCHOR_4 = '''This mirrors the instinct in the older sync_templates_to_pipedrive.py'''

REPLACE_4 = '''ARCHIVED RECORDS
----------------
A Quoter template titled YY-<name> is excluded from the dropdown but kept in
Quoter. Quoter has no archive and deletion is permanent, while the ScalePad API
may one day expose template line items -- at which point the item-named
templates become useful again.

Renaming alone is not enough: build_plan() treats a rename as a label change on
the same option id, so the option would stay selectable. Deleting the option
alone is not enough either -- an option whose record still exists is re-added on
the next run. The exclusion has to happen at fetch time, which is what
ARCHIVE_PREFIX does.

To un-archive: drop the YY- prefix in Quoter. If the option was retired rather
than deleted, to_unretire reuses the SAME option id and every deal that stored
it resolves again.

This mirrors the instinct in the older sync_templates_to_pipedrive.py'''

EDITS = [
    ("1. ARCHIVE_PREFIX, INCLUDE_ARCHIVED, is_archived()", ANCHOR_1, REPLACE_1),
    ("2. fetch_quoter() exclusion",                        ANCHOR_2, REPLACE_2),
    ("3. --include-archived flag and global",              ANCHOR_3, REPLACE_3),
    ("4. docstring section",                               ANCHOR_4, REPLACE_4),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write the change (default: show the diff only)")
    ap.add_argument("--file", default=str(TARGET),
                    help=f"path to patch (default: {TARGET})")
    a = ap.parse_args()

    path = Path(a.file)
    if not path.exists():
        sys.exit(f"ERROR: {path} not found. Run this from the repo root.")

    original = path.read_text()

    if "ARCHIVE_PREFIX" in original:
        sys.exit("ERROR: ARCHIVE_PREFIX already present -- already patched. "
                 "Nothing to do.")

    # --- verify every anchor BEFORE changing anything ----------------------
    problems = []
    for label, anchor, _ in EDITS:
        n = original.count(anchor)
        if n == 0:
            problems.append(f"  {label}: anchor NOT FOUND")
        elif n > 1:
            problems.append(f"  {label}: anchor found {n} times (ambiguous)")
    if problems:
        print("ABORTED -- the source file does not match what this patch expects:")
        print("\n".join(problems))
        print("\nThe file has changed since the patch was written. Do not force it;")
        print("re-read the source and rebuild the anchors.")
        sys.exit(1)

    patched = original
    for label, anchor, replacement in EDITS:
        patched = patched.replace(anchor, replacement, 1)
        print(f"  ok  {label}")

    # --- make sure the result actually parses ------------------------------
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(patched)
        tmp_path = tmp.name
    try:
        py_compile.compile(tmp_path, doraise=True)
    except py_compile.PyCompileError as e:
        sys.exit(f"ABORTED -- patched file does not compile:\n{e}")
    print("  ok  patched file compiles")

    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        patched.splitlines(keepends=True),
        fromfile=str(path), tofile=str(path) + " (patched)"))

    print("\n" + "=" * 72)
    print("".join(diff))
    print("=" * 72)

    if not a.apply:
        print(f"\nDRY RUN -- {path} not modified. Rerun with --apply to write.")
        return

    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup)
    path.write_text(patched)
    print(f"\nWritten. Backup at {backup}")
    print("\nNext:")
    print("  1. python3 sync_quoter_to_pipedrive.py --source templates --field 90")
    print("     (dry run -- expect 2 live records once the ten are renamed)")
    print("  2. rename the ten in Quoter to YY-<name>")
    print("  3. dry run again -- expect 10 orphans")
    print("  4. add --apply --retire-orphans, then delete the ten options in the UI")


if __name__ == "__main__":
    main()
