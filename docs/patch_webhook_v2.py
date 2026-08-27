#!/usr/bin/env python3
"""
patch_webhook_v2.py — add the v2 composition branch to webhook_handler.py.

Run once from quoter_sync, then delete.

WHAT IT CHANGES
---------------
One call site, near the end of handle_organization_webhook:

    quote_data = create_comprehensive_quote_from_pipedrive(normalized_org_data, deal_data)

becomes a branch on USE_V2_COMPOSITION. Legacy stays exactly as it was and is
still the default, so nothing changes until the flag is set in Render.

WHY THE V2 BRANCH RE-FETCHES THE DEAL
-------------------------------------
The webhook builds a MOCK deal_data from three fields it happens to carry:

    {'id': ..., 'title': ..., '42ab0c91...': template_enum_str}

Field 102 (Quote Effects) is not among them, so the composer would find no
effects and abort. Rather than widening the Pipedrive webhook template -- which
means editing an automation outside this repo, and which the legacy path would
also have to keep working with -- the v2 branch calls get_deal_by_id() and
works from the real record.

That is Chapter 3 section 13.4 in practice: the webhook answers WHEN, the API
answers WHAT. It costs one extra call per quote, which at TLC's volume is
nothing, and it means the payload can shrink later instead of growing.

REVERTING
---------
Set USE_V2_COMPOSITION=false in Render. No deploy, no rollback.

Usage:
    python3 patch_webhook_v2.py
    python3 patch_webhook_v2.py --apply
"""

import argparse
import shutil
import sys
from pathlib import Path

TARGET = Path("webhook_handler.py")

OLD_CALL = """        # Create comprehensive draft quote using our enhanced function with template selection
        quote_data = create_comprehensive_quote_from_pipedrive(normalized_org_data, deal_data)"""

NEW_CALL = '''        # Create the draft quote.
        #
        # USE_V2_COMPOSITION switches between the legacy path and the v2
        # composition path. Default is FALSE, so this changes nothing until the
        # flag is set in Render -- and reverting is a Render setting rather
        # than a deploy.
        use_v2 = os.getenv("USE_V2_COMPOSITION", "false").lower() in (
            "true", "1", "yes")

        if use_v2:
            logger.info("🆕 USE_V2_COMPOSITION=true — composing via Item Groups")

            # Re-fetch the deal from the API rather than using the mock
            # deal_data built above. That mock carries only id, title and the
            # Quote Template enum; field 102 (Quote Effects) is not in the
            # webhook payload at all, and the composer needs it.
            #
            # The webhook answers WHEN, the API answers WHAT. One extra call
            # per quote, and it means the webhook payload can shrink later
            # rather than having to grow.
            full_deal = get_deal_by_id(deal_id)
            if not full_deal:
                logger.error(f"❌ Could not fetch deal {deal_id} for v2 "
                             f"composition")
                send_slack_alert(
                    f"🚨 v2 composition: deal {deal_id} could not be fetched "
                    f"from Pipedrive. Falling back is NOT automatic — check "
                    f"the deal exists and the API token is valid.")
                return jsonify({"error": "Deal not found for v2"}), 404

            from quote_composer import create_quote_v2
            quote_data = create_quote_v2(normalized_org_data, full_deal)
        else:
            quote_data = create_comprehensive_quote_from_pipedrive(
                normalized_org_data, deal_data)'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    if not TARGET.exists():
        sys.exit(f"ERROR: {TARGET} not found. Run this from quoter_sync.")

    s = TARGET.read_text()

    if "USE_V2_COMPOSITION" in s:
        print("  already patched — nothing to do")
        return
    if OLD_CALL not in s:
        print("  ANCHOR NOT FOUND. The call site has changed; apply by hand.")
        print("  Look for: create_comprehensive_quote_from_pipedrive("
              "normalized_org_data, deal_data)")
        return

    print("  will add the USE_V2_COMPOSITION branch at the quote-creation "
          "call site")
    print("  legacy stays the default; nothing changes until the flag is set")

    if not a.apply:
        print("\n  DRY RUN — rerun with --apply")
        return

    backup = TARGET.with_suffix(".py.bak")
    shutil.copy2(TARGET, backup)
    TARGET.write_text(s.replace(OLD_CALL, NEW_CALL))
    print(f"\n  patched. original saved as {backup.name}")
    print("  verify with:  python3 -m py_compile webhook_handler.py")
    print("\n  Then, in Render:")
    print("    1. add SCALEPAD_API_KEY to render.yaml envVarsFrom")
    print("    2. set USE_V2_COMPOSITION=true when ready to switch")


if __name__ == "__main__":
    main()
