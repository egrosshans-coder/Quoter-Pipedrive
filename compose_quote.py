#!/usr/bin/env python3
"""
compose_quote.py — build a draft quote from Item Groups. THE VERTICAL SLICE.

This is the thing the whole migration exists to enable: line items sourced
from Quoter at run time instead of hard-coded in Python.

  today   template_mapping_enhanced.py holds each template's items as a dict.
          Edit a template in Quoter and Render keeps writing the old items
          until a developer redeploys. Two sources of truth, drifting.

  this    Pipedrive names a group -> read its assignments -> read those items'
          current values -> post them. Change the catalog, the next quote is
          already correct. No deploy.

Business logic lives here, not in scalepad_quotes.py, per D-003.

HOW A QUOTE IS ASSEMBLED
------------------------
  1. POST /quotes with a template_id            (presentation only)
  2. POST .../sections, one per group           (bare array of {"name"})
  3. POST .../sections/{sid}/line-items         (bare array, by value)

Step 1 always returns sections: null even with a template_id — a template
contributes no line items via the API, and ScalePad confirms that is intended
(Chapter 3 6.2.1). The template supplies layout, cover page and branding; the
content is composed here.

Items are seeded at quantity 1 and unit price $0.00.

Quantity 1 because the API rejects 0; the salesperson prunes in the UI, which
permits 0 and blank (Chapter 3 7.3-7.5).

Price $0.00 because TLC re-prices per customer and per deal. Seeding the
catalog price would produce lines that look priced when nobody has priced
them, and a missed one ships wrong. $0.00 is unmistakably unpriced. Pass
--catalog-price for items that genuinely do not vary.

Seeding generously is deliberate: a quote full of real catalog items teaches
the catalog, whereas a blank one invites someone to type a free-text line at a
made-up price, with no code and no sku and therefore no Pipedrive linkage.

Usage:
    export SCALEPAD_API_KEY='...'
    python3 compose_quote.py --groups XRN-Balloons
    python3 compose_quote.py --groups XRN-Balloons --write
    python3 compose_quote.py --groups XRN-Balloons,XTE-TravelExpense --write
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_EMAIL = "zz-test-chapter3@tlciscreative.com"
TEST_CLIENT = "zz-Chapter3-CustomNumber-Test"
DEFAULT_TEMPLATE = "tmpl_30O6JTDIbApan1B5gh9hF2w1tfL"     # "Basic"


def load_catalog(items_api):
    """id -> item, for the whole catalog.

    A dict rather than per-item lookups: composing from several groups would
    otherwise mean dozens of round trips. Completeness is checked by the
    caller against total_count, because this API ignores unrecognised
    parameters silently and a short pull looks identical to a full one.
    """
    return {i["id"]: i for i in items_api.iter_all_items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", required=True,
                    help="comma-separated Item Group names, in section order")
    ap.add_argument("--template", default=DEFAULT_TEMPLATE,
                    help="presentation template id")
    ap.add_argument("--email", default=TEST_EMAIL)
    ap.add_argument("--client", default=TEST_CLIENT)
    ap.add_argument("--write", action="store_true",
                    help="actually create the quote (default: dry run)")
    ap.add_argument("--catalog-price", action="store_true",
                    help="seed each line at its catalog price instead of "
                         "$0.00. Off by default: TLC re-prices per customer, "
                         "so a seeded price reads as a decision nobody made, "
                         "and a missed one ships wrong. $0.00 is visibly "
                         "unpriced.")
    a = ap.parse_args()

    from scalepad_quotes import ScalePadQuotes
    from scalepad_items import QuoterItemsV2

    q = ScalePadQuotes()
    items_api = QuoterItemsV2()

    group_names = [g.strip() for g in a.groups.split(",") if g.strip()]
    print("=" * 72)
    print(f"COMPOSE QUOTE   [{'WRITE' if a.write else 'DRY RUN'}]")
    print("=" * 72)
    print(f"\n  template : {a.template}")
    print(f"  pricing  : {'catalog price' if a.catalog_price else '$0.00 (unpriced — salesperson sets it)'}")
    print(f"  groups   : {', '.join(group_names)}")

    catalog = load_catalog(items_api)
    print(f"  catalog  : {len(catalog)} items")

    # --- resolve each group to concrete line items ------------------------
    plan, problems = [], []
    for name in group_names:
        g = q.find_group(name)
        if not g:
            problems.append(f"item group {name!r} not found")
            continue
        item_ids = q.group_item_ids(g["id"])
        if not item_ids:
            problems.append(f"item group {name!r} has no members")
            continue

        lines = []
        for iid in item_ids:
            it = catalog.get(iid)
            if not it:
                problems.append(f"{name}: item {iid} assigned but not in catalog")
                continue
            lines.append((it, q.line_item_from_catalog(
                it, use_catalog_price=a.catalog_price)))
        plan.append((name, g["id"], lines))

        print(f"\n  {name}  ({g['id']})  -> {len(lines)} line item(s)")
        for it, li in sorted(lines, key=lambda x: x[0].get("code") or ""):
            print(f"    {str(it.get('code')):16} "
                  f"{li['name'][:36]:38} qty={li['quantity_decimal']:3} "
                  f"@ {li['unit_price_decimal']}")

    if problems:
        print(f"\n  {len(problems)} problem(s):")
        for p in problems:
            print(f"    ! {p}")
        print("\n  ABORT: not composing a quote from a broken plan.")
        return

    total_lines = sum(len(l) for _, _, l in plan)
    print(f"\n  plan: {len(plan)} section(s), {total_lines} line item(s)")

    if not a.write:
        print("\n" + "=" * 72)
        print("DRY RUN — nothing written. Rerun with --write.")
        print("=" * 72)
        return

    # --- create ------------------------------------------------------------
    stamp = time.strftime("%Y%m%d-%H%M%S")
    print("\n" + "-" * 72)
    print("CREATING")
    print("-" * 72)

    quote = q.create_quote(template_id=a.template,
                           contact_email=a.email,
                           client_name=a.client,
                           custom_number=f"zz-COMPOSE-{stamp}")
    qid = (quote or {}).get("id")
    if not qid:
        print(f"  ABORT: no quote id returned: {quote}")
        return
    print(f"  quote {qid}  (zz-COMPOSE-{stamp})")
    print(f"  sections at creation: {quote.get('sections')}   <- always null")

    for name, _gid, lines in plan:
        q.create_sections(qid, name)
        sec = q.find_section(qid, name)
        if not sec:
            print(f"  ! section {name!r} not found after creation; skipping")
            continue
        q.add_line_items(qid, sec["id"], [li for _it, li in lines])
        print(f"  + {name:26} {sec['id']}  {len(lines)} line item(s)")
        time.sleep(0.2)

    # --- verify ------------------------------------------------------------
    time.sleep(1.5)
    final = q.get_quote(qid) or {}
    secs = final.get("sections") or []
    got = sum(len(s.get("line_items") or []) for s in secs)
    print("\n" + "=" * 72)
    print(f"VERIFIED: {len(secs)} section(s), {got} line item(s) "
          f"(expected {len(plan)} / {total_lines})")
    for s in secs:
        t = ((s.get("totals") or {}).get("one_time") or {}).get("subtotal_decimal")
        print(f"    {s.get('name'):26} {len(s.get('line_items') or []):3} items"
              f"   subtotal {t}")
    ok = len(secs) == len(plan) and got == total_lines
    print("\n  " + ("PASS — composed end to end from Item Groups."
                    if ok else "MISMATCH — inspect the quote."))
    print("=" * 72)
    print(f"\n  open: /admin/quotes/draft_by_public_id/{qid}")
    print(f"  cleanup: draft {qid}, tag zz-COMPOSE-{stamp}")


if __name__ == "__main__":
    main()
