#!/usr/bin/env python3
"""
section_diag_v1.py — what actually happens to section ids across writes?

THE PROBLEM
-----------
Composing a quote with more than one section fails. Section 1 fills fine;
posting line items into section 2 returns 404 ERR_NOT_FOUND on the section id,
even when that id was read back moments earlier.

Two guesses have already been made and BOTH were wrong:
  - "creating a second section invalidates the first" -> no
  - "posting line items regenerates the other sections' ids" -> no, a freshly
    read id still 404s

So stop guessing. This prints the full section list at every step and shows
exactly which id is used where.

Worth being clear that multi-section composition has NEVER worked. Earlier
successful runs used a single group, so a single section. Friday's
section_probe created two sections but only ever posted line items into the
first. This path is untested, not regressed.

Creates ONE draft quote tagged zz-SECDIAG-<timestamp>.

Usage:
    export SCALEPAD_API_KEY='...'
    python3 section_diag_v1.py
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_EMAIL = "zz-test-chapter3@tlciscreative.com"
TEST_CLIENT = "zz-Chapter3-CustomNumber-Test"
TEMPLATE = "tmpl_30O6JTDIbApan1B5gh9hF2w1tfL"


def show(q, qid, label):
    secs = q.sections_of(qid)
    print(f"\n  [{label}] {len(secs)} section(s)")
    for i, s in enumerate(secs):
        print(f"    [{i}] id={s.get('id')}  name={s.get('name')!r}  "
              f"items={len(s.get('line_items') or [])}")
    return secs


def main():
    from scalepad_quotes import ScalePadQuotes
    from scalepad_items import QuoterItemsV2

    q = ScalePadQuotes()
    stamp = time.strftime("%Y%m%d-%H%M%S")

    # a real category id to build valid line items with
    cat = None
    for it in QuoterItemsV2().iter_all_items():
        if (it.get("code") or "").startswith("BAL-"):
            cat = it.get("category_id")
            break
    if not cat:
        sys.exit("could not resolve a category_id")

    print("=" * 72)
    print("SECTION ID DIAGNOSTIC")
    print("=" * 72)

    quote = q.create_quote(template_id=TEMPLATE, contact_email=TEST_EMAIL,
                           client_name=TEST_CLIENT,
                           custom_number=f"zz-SECDIAG-{stamp}")
    qid = quote.get("id")
    print(f"\n  quote {qid}   (zz-SECDIAG-{stamp})")

    # --- step 1: create three sections in ONE call ------------------------
    print("\n" + "-" * 72)
    print("STEP 1 — POST /sections with a bare array of three names")
    print("-" * 72)
    resp = q.create_sections(qid, ["Alpha", "Beta", "Gamma"])
    print(f"  create response returned {len(resp)} section(s):")
    for s in resp:
        print(f"    id={s.get('id')}  name={s.get('name')!r}")

    time.sleep(1.5)
    secs = show(q, qid, "read back after create")

    if len(secs) < 3:
        print("\n  !! fewer than three sections exist. The bare array may not")
        print("     create them all, or may replace rather than append.")
        print("     That alone would explain the 404 -- section 2 never existed.")

    # --- step 2: does the id survive a plain re-read? ---------------------
    print("\n" + "-" * 72)
    print("STEP 2 — read twice with no write between. Do ids change?")
    print("-" * 72)
    a = [s.get("id") for s in q.sections_of(qid)]
    time.sleep(0.5)
    b = [s.get("id") for s in q.sections_of(qid)]
    print(f"  read 1: {a}")
    print(f"  read 2: {b}")
    print(f"  stable: {a == b}")
    if a != b:
        print("  !! ids change on every read. They are not durable handles at")
        print("     all, and nothing can be written by id reliably.")

    # --- step 3: fill section 0, then look at everything -------------------
    print("\n" + "-" * 72)
    print("STEP 3 — post one line item into section [0]")
    print("-" * 72)
    secs = q.sections_of(qid)
    sid0 = secs[0]["id"]
    print(f"  using id={sid0}")
    try:
        q.add_line_items(qid, sid0, [q.line_item("diag-alpha", cat, "0", 1)])
        print("  OK")
    except Exception as e:
        print(f"  FAILED: {str(e)[:200]}")
    time.sleep(1.5)
    secs = show(q, qid, "after filling [0]")

    # --- step 4: fill section 1 with a FRESHLY read id --------------------
    print("\n" + "-" * 72)
    print("STEP 4 — post one line item into section [1], id read just now")
    print("-" * 72)
    if len(secs) < 2:
        print("  only one section exists; nothing to try.")
    else:
        sid1 = secs[1]["id"]
        print(f"  using id={sid1}   name={secs[1].get('name')!r}")
        try:
            q.add_line_items(qid, sid1, [q.line_item("diag-beta", cat, "0", 1)])
            print("  OK  <-- so the earlier failure was a stale id after all")
        except Exception as e:
            print(f"  FAILED: {str(e)[:200]}")
            print("\n  A freshly read id was rejected. So either the id is not")
            print("  what the line-items endpoint expects for this section, or")
            print("  sections beyond the first are not real records.")
        time.sleep(1.5)
        show(q, qid, "after attempting [1]")

    # --- step 5: try creating sections one at a time instead --------------
    print("\n" + "-" * 72)
    print("STEP 5 — separate quote: create ONE section, fill it, then create")
    print("         the next and fill that")
    print("-" * 72)
    q2 = q.create_quote(template_id=TEMPLATE, contact_email=TEST_EMAIL,
                        client_name=TEST_CLIENT,
                        custom_number=f"zz-SECDIAG2-{stamp}")
    qid2 = q2.get("id")
    print(f"  quote {qid2}")
    for nm in ["One", "Two"]:
        q.create_sections(qid2, nm)
        time.sleep(1.0)
        cur = q.sections_of(qid2)
        print(f"\n  after creating {nm!r}: {[(s['id'], s['name']) for s in cur]}")
        target = next((s for s in cur if s.get("name") == nm), None)
        if not target:
            print(f"    !! {nm!r} not present after creation")
            continue
        try:
            q.add_line_items(qid2, target["id"],
                             [q.line_item(f"diag-{nm}", cat, "0", 1)])
            print(f"    filled {nm!r} OK")
        except Exception as e:
            print(f"    filling {nm!r} FAILED: {str(e)[:160]}")
        time.sleep(1.0)
    show(q, qid2, "final state of the one-at-a-time quote")

    print("\n" + "=" * 72)
    print("cleanup: drafts tagged zz-SECDIAG-{0} and zz-SECDIAG2-{0}".format(stamp))
    print("=" * 72)


if __name__ == "__main__":
    main()
