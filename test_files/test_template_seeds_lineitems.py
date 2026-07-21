#!/usr/bin/env python3
"""
TEST: Does createQuote(template_id) on the NEW ScalePad API seed line items?

This is the single empirical test that decides whether the Template-Mirror
architecture is still needed.

WHAT IT DOES
  1. Lists your quote templates (so you can pick a real template_id).
  2. Creates a DRAFT quote from one template.
  3. Fetches that draft back.
  4. Reports whether `sections` / line_items came through populated or empty.

INTERPRETATION
  - Line items PRESENT  -> create-from-template SEEDS items. The mirror problem
                           is (largely) solved: read a template's items by
                           creating a throwaway quote and fetching it.
  - Line items EMPTY    -> template seeds styling only. The mirror architecture
                           (or a scrape / a supported read endpoint) is still
                           needed.

REQUIREMENTS
  - .env with SCALEPAD_API_KEY   (same one scalepad_v2.py already uses)
  - A real template_id           (the script lists them for you; or set TEMPLATE_ID)
  - A real contact: email + ScalePad client_id (UUID)
        set CONTACT_EMAIL and CONTACT_CLIENT_ID below, OR pass on the prompt.

  This CREATES A DRAFT QUOTE in your account (harmless — drafts are unpublished
  and can be deleted). It does NOT publish anything.

RUN
    python test_template_seeds_lineitems.py
"""

import os
import json
import sys

# Reuse your existing client exactly as-is.
from scalepad_v2 import ScalePadV2Client

# ----------------------------------------------------------------------
# OPTIONAL: hard-set these to skip the prompts. Leave as None to be asked.
# ----------------------------------------------------------------------
TEMPLATE_ID       = None   # e.g. "qtpl_2awZ8VqGpFn1sMK6tPXkJbDrYhN"  (NEW-API id)
CONTACT_EMAIL     = None   # e.g. "eric@tlciscreative.com"
CONTACT_CLIENT_ID = None   # ScalePad client UUID e.g. "03840c4b-5999-49ac-80b6-0e6000a758fd"
# ----------------------------------------------------------------------


def ask(prompt, current):
    if current:
        return current
    val = input(prompt).strip()
    return val or None


def main():
    client = ScalePadV2Client()  # uses SCALEPAD_API_KEY from .env

    # --- 1. List templates so we have a real template_id -------------------
    print("=" * 70)
    print("STEP 1  Listing quote templates (new API)")
    print("=" * 70)
    try:
        templates = client.get("/quoter/v1/quote-templates")
    except Exception as e:
        print(f"❌ Could not list templates: {e}")
        sys.exit(1)

    rows = templates.get("data", []) if isinstance(templates, dict) else []
    if not rows:
        print("❌ No templates returned. Check the API key / account.")
        sys.exit(1)

    for t in rows:
        print(f"  title : {t.get('title')}")
        print(f"  id    : {t.get('id')}")
        print(f"  slug  : {t.get('slug')}")
        print("  " + "-" * 60)

    template_id = ask("\nPaste the template_id to test: ", TEMPLATE_ID)
    email       = ask("Contact email: ", CONTACT_EMAIL)
    client_id   = ask("ScalePad client_id (UUID): ", CONTACT_CLIENT_ID)

    if not (template_id and email and client_id):
        print("❌ Need template_id, email, and client_id to proceed.")
        sys.exit(1)

    # --- 2. Create a draft quote FROM the template -------------------------
    print("\n" + "=" * 70)
    print("STEP 2  Creating draft quote from template")
    print("=" * 70)
    body = {
        "contact": {"email": email, "client_id": client_id},
        "template_id": template_id,
        "name": "TEST - does template seed line items (safe to delete)",
    }
    try:
        created = client.post("/quoter/v1/quotes", data=body)
    except Exception as e:
        print(f"❌ createQuote failed: {e}")
        sys.exit(1)

    quote_id = created.get("id")
    print(f"✅ Draft created: {quote_id}")
    print(f"   draft flag : {created.get('draft')}")
    # Look at the create response directly first:
    created_sections = created.get("sections")
    print(f"   sections in CREATE response: "
          f"{'POPULATED' if created_sections else 'null/empty'}")

    # --- 3. Fetch the draft back -------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 3  Fetching the draft back")
    print("=" * 70)
    try:
        fetched = client.get(f"/quoter/v1/quotes/{quote_id}")
    except Exception as e:
        print(f"❌ fetch failed: {e}")
        print("   (Create still succeeded; inspect the quote in the UI.)")
        sys.exit(1)

    sections = fetched.get("sections")

    # --- 4. Verdict --------------------------------------------------------
    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)

    line_item_count = 0
    if sections:
        for s in sections:
            lis = s.get("line_items") or []
            line_item_count += len(lis)

    if line_item_count > 0:
        print(f"✅ TEMPLATE SEEDS LINE ITEMS — found {line_item_count} line item(s) "
              f"across {len(sections)} section(s).")
        print("   => Mirror architecture likely UNNECESSARY: read a template's")
        print("      items by creating a throwaway quote and fetching it.")
        print("\n   First line item (for the doc):")
        first = sections[0]["line_items"][0]
        for k in ("name", "code", "sku", "category",
                  "unit_price_decimal", "quantity_decimal", "description"):
            print(f"     {k:20}: {first.get(k)}")
    else:
        print("❌ NO LINE ITEMS — sections came back empty.")
        print("   => Template seeds styling only. Mirror architecture (or a")
        print("      supported read endpoint / scrape) IS still needed.")

    # Full dump for the record
    print("\n--- Full fetched quote (for the doc / evidence) ---")
    print(json.dumps(fetched, indent=2)[:4000])
    print("\n(NOTE: delete this test draft in Quoter when done.)")


if __name__ == "__main__":
    main()
