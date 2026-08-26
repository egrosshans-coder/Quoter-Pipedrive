"""
quote_composer.py — build a draft quote on ScalePad v2 from Pipedrive deal data.

The v2 replacement for quoter.create_comprehensive_quote_from_pipedrive().

SERVICE LAYER. Business logic lives here; transport and resource wrappers live
in scalepad_v2.py / scalepad_quotes.py / scalepad_items.py, per DECISIONS
D-003/D-004. Nothing here is imported by the legacy path, so it cannot affect
production until webhook_handler is pointed at it.

WHAT CHANGES FROM THE LEGACY PATH
---------------------------------
    legacy                                  v2
    ------                                  --
    enum_mapping dict, 11 hard-coded ids  → option_map() read at runtime
    TEMPLATE_BUNDLES dict of line items   → Item Groups read from Quoter
    prices baked into the Python dict     → $0.00, salesperson prices it
    POST /v1/contacts, then use its id    → contact resolved inside createQuote
    flat line items, no sections          → one section per Item Group
    api.quoter.com (legacy OAuth)         → api.scalepad.com (x-api-key)

The point of the exercise: a quote's contents come from Quoter at run time.
Change the catalog and the next quote is already correct, with no deploy.

TWO PIPEDRIVE FIELDS
--------------------
     90  Quote Template  enum  presentation: layout, cover page, branding
    102  Quote Effects   set   content: which Item Groups compose the quote

Both are read by option id -> label at run time. No id table in code.

Usage (also runnable standalone for testing):
    from quote_composer import create_quote_v2
    result = create_quote_v2(organization_data, deal_data)
"""

import os

from utils.logger import logger

# Pipedrive custom field keys. The numeric ids (90, 102) address the field
# definition; these hashes are how the values arrive in a deal payload.
FIELD_QUOTE_TEMPLATE = 90
FIELD_QUOTE_EFFECTS = 102
KEY_QUOTE_TEMPLATE = "42ab0c919271cb24f3587f0b01ea2af166019c8d"
KEY_QUOTE_EFFECTS = "118a5ce132f73d7fec1822e2a0431b51ac2a2994"

# Deal_ID custom field on the organisation, carried over from the legacy path.
KEY_DEAL_ID = "15034cf07d05ceb15f0a89dcbdcc4f5963485 84e".replace(" ", "")

DEFAULT_TEMPLATE_ID = os.getenv("QUOTER_DEFAULT_TEMPLATE_ID",
                                "tmpl_3ITGNwiAtd8fvLEpiiaBK79Z1YP")  # "Standard"


# ----------------------------------------------------------------- helpers ---

def _deal_field(deal_data, key):
    """Read a custom field from a deal payload, tolerating shapes.

    Pipedrive returns custom fields keyed by hash, but a webhook may deliver
    them flattened, nested under custom_fields, or as {"value": ...}.
    """
    if not deal_data:
        return None
    val = deal_data.get(key)
    if val is None:
        val = (deal_data.get("custom_fields") or {}).get(key)
    if isinstance(val, dict):
        val = val.get("value") or val.get("id")
    return val


def _resolve_labels(pd_fields, field_id, raw):
    """Turn stored option id(s) into label(s) using a RUNTIME lookup.

    This is what replaces the hard-coded enum_mapping in
    template_selection_logic.py. A deal stores the option's numeric id, never
    its label, so something has to map 451 -> 'Balloons'. Reading it from
    Pipedrive means adding an Item Group needs no code change.

    A `set` field arrives as a comma-separated string of ids; an `enum` as one.
    """
    if raw in (None, ""):
        return []
    option_map = pd_fields.option_map(field_id)
    ids = [str(v).strip() for v in str(raw).split(",") if str(v).strip()]
    labels, unknown = [], []
    for oid in ids:
        label = option_map.get(oid)
        if label:
            labels.append(label)
        else:
            unknown.append(oid)
    if unknown:
        logger.warning(f"⚠️ field {field_id}: option id(s) {unknown} not found. "
                       f"The dropdown may be out of step with Quoter — the "
                       f"sync workflow reconciles it daily.")
    return labels


def _contact_from_webhook(organization_data, deal_data):
    """Pull contact and organisation details out of the webhook payload.

    Mirrors the legacy fast path: the webhook carries {{deal.person_name}} and
    {{person.email}} directly, avoiding a Pipedrive API round trip. Falls back
    to a deal-derived dummy address when no email is present, exactly as the
    legacy code does — Quoter requires one to resolve a contact.
    """
    name = (organization_data.get("{{deal.person_name}}")
            or organization_data.get("person_name") or "")
    email = (organization_data.get("{{person.email}}")
             or organization_data.get("person_email") or "")
    org_name = organization_data.get("name", "")
    deal_id = _deal_field(organization_data, KEY_DEAL_ID) or \
        (deal_data or {}).get("id")

    if not email:
        email = f"{deal_id}@gmail.com"
        logger.info(f"📧 No email in webhook; using placeholder {email} "
                    f"(matches legacy behaviour)")

    # Address, from the flat keys webhook_handler sets. billing_address is
    # REQUIRED to create a contact, so a fallback is needed where Pipedrive
    # has none -- otherwise no quote can be created at all.
    return {
        "name": name, "email": email, "org_name": org_name,
        "deal_id": deal_id,
        "address": organization_data.get("address") or "",
        "address2": organization_data.get("address2") or "",
        "city": organization_data.get("city") or "",
        "region_iso": organization_data.get("state") or "",
        "postal_code": organization_data.get("postal_code") or "",
        "country_iso": organization_data.get("country") or "US",
    }


# -------------------------------------------------------------------- main ---

def create_quote_v2(organization_data, deal_data=None, dry_run=False):
    """Create a draft quote on v2, composed from Item Groups.

    Returns a dict shaped like the legacy function's return value so
    webhook_handler can switch between them: {"id": ..., "sections": n, ...}
    or None on failure.
    """
    from pd_fields import PipedriveFields
    from scalepad_quotes import ScalePadQuotes
    from scalepad_items import QuoterItemsV2

    pd_fields = PipedriveFields()
    quotes = ScalePadQuotes()

    contact = _contact_from_webhook(organization_data, deal_data)
    if not contact["deal_id"]:
        logger.error("❌ No deal ID found; cannot compose a quote")
        return None

    logger.info(f"🎯 Composing v2 quote for deal {contact['deal_id']} "
                f"({contact['org_name']})")

    # --- field 90: presentation -------------------------------------------
    template_labels = _resolve_labels(
        pd_fields, FIELD_QUOTE_TEMPLATE,
        _deal_field(deal_data, KEY_QUOTE_TEMPLATE))

    template_id = DEFAULT_TEMPLATE_ID
    if template_labels:
        wanted = template_labels[0]
        for t in (quotes.client.get("/quoter/v1/quote-templates?page_size=200")
                  or {}).get("data", []):
            if (t.get("title") or "").strip() == wanted.strip():
                template_id = t["id"]
                break
        else:
            logger.warning(f"⚠️ Template {wanted!r} selected in Pipedrive but "
                           f"not found in Quoter; using the default")
    logger.info(f"📄 Template: {template_labels or '(default)'} -> {template_id}")

    # --- field 102: content ------------------------------------------------
    group_names = _resolve_labels(
        pd_fields, FIELD_QUOTE_EFFECTS,
        _deal_field(deal_data, KEY_QUOTE_EFFECTS))
    if not group_names:
        logger.error("❌ No Quote Effects selected on the deal. Nothing to "
                     "compose — the field is required from the Send Quote "
                     "stage onward, so this deal was moved without one.")
        return None
    logger.info(f"🎛️  Effects: {', '.join(group_names)}")

    # --- resolve groups to line items --------------------------------------
    # Section names come from item_group_defs.json, not from the group name:
    # Quoter has no setting to hide section headings, so the internal taxonomy
    # (SFX-Balloons) must not reach the customer (Balloon Effects).
    section_names = _load_section_names()
    catalog = {i["id"]: i for i in QuoterItemsV2().iter_all_items()}

    plan, missing = [], []
    for name in group_names:
        group = quotes.find_group(name)
        if not group:
            missing.append(name)
            continue
        items = [catalog[i] for i in quotes.group_item_ids(group["id"])
                 if i in catalog]
        if not items:
            logger.warning(f"⚠️ Item Group {name!r} has no members; skipping")
            continue
        plan.append((name, section_names.get(name, name), items))

    if missing:
        logger.error(f"❌ Item Group(s) not found in Quoter: {missing}. The "
                     f"Pipedrive dropdown is ahead of the catalog.")
        return None
    if not plan:
        logger.error("❌ Nothing to compose after resolving groups")
        return None

    total_items = sum(len(i) for _n, _s, i in plan)
    logger.info(f"📋 Plan: {len(plan)} section(s), {total_items} line item(s)")
    for name, section, items in plan:
        logger.info(f"   {name} -> {section!r}: {len(items)} item(s)")

    if dry_run:
        logger.info("🧪 DRY RUN — nothing written")
        return {"dry_run": True, "sections": len(plan),
                "line_items": total_items,
                "groups": [n for n, _s, _i in plan]}

    # --- create ------------------------------------------------------------
    # --- ensure the contact exists ----------------------------------------
    # createQuote RESOLVES a contact from contact.email; it does not create
    # one. An unknown email returns 422 ERR_CONTACT_NOT_FOUND. The legacy path
    # created the contact first via POST /v1/contacts and passed its id; on v2
    # the email is the handle, but the record still has to exist.
    name_parts = (contact["name"] or "").rsplit(" ", 1)
    first_name = name_parts[0] if name_parts and name_parts[0] else "Unknown"
    last_name = name_parts[1] if len(name_parts) > 1 else "Contact"
    try:
        if not contact["address"]:
            logger.info("📍 No address on the organisation; using a placeholder "
                        "(billing_address is required to create a contact)")
        _rec, created = quotes.ensure_contact(
            contact["email"], first_name, last_name, contact["org_name"],
            address=contact["address"] or None,
            address2=contact["address2"] or None,
            city=contact["city"] or None,
            region_iso=contact["region_iso"] or None,
            postal_code=contact["postal_code"] or None,
            country_iso=contact["country_iso"] or "US")
        logger.info(f"👤 Contact {contact['email']}: "
                    f"{'created' if created else 'already present'}")
    except Exception as e:
        logger.error(f"❌ Could not resolve or create contact "
                     f"{contact['email']}: {str(e)[:300]}")
        logger.error("   The v2 contact schema has not been exercised before; "
                     "read the field names in the 422 above and adjust "
                     "ScalePadQuotes.create_contact.")
        return None

    custom_number = None
    if os.getenv("ENABLE_CUSTOM_NUMBER_PATCH", "false").lower() in (
            "true", "1", "yes"):
        # v2 sets custom_number AT CREATE, which legacy could not do.
        from quoter import generate_sequential_quote_number
        custom_number = generate_sequential_quote_number(contact["deal_id"])

    quote = quotes.create_quote(
        template_id=template_id,
        contact_email=contact["email"],
        client_name=contact["org_name"],
        custom_number=custom_number,
        name=f"Quote for {contact['org_name']}",
    )
    qid = (quote or {}).get("id")
    if not qid:
        logger.error(f"❌ No quote id returned: {quote}")
        return None
    logger.info(f"✅ Created draft {qid}")

    # --- sections and line items -------------------------------------------
    # All sections in ONE call, then fill each with the id re-read immediately
    # beforehand. Section reads are eventually consistent: an id read straight
    # after a write can 404 (Chapter 3 §9). add_line_items_retrying handles it.
    quotes.create_sections(qid, [s for _n, s, _i in plan])

    written = 0
    for idx, (name, section, items) in enumerate(plan):
        payload = [quotes.line_item_from_catalog(it) for it in items]
        try:
            _resp, tries = quotes.add_line_items_retrying(
                qid, idx, payload, expect_name=section)
            written += len(payload)
            note = f" (after {tries} attempts)" if tries > 1 else ""
            logger.info(f"   + {section}: {len(payload)} item(s){note}")
        except Exception as e:
            logger.error(f"   ❌ {section}: {str(e)[:200]}")

    logger.info(f"🎉 Quote {qid}: {len(plan)} section(s), {written} line item(s), "
                f"all at $0.00 for the salesperson to price")

    result = dict(quote)
    result["sections"] = len(plan)
    result["line_items"] = written
    result["groups"] = [n for n, _s, _i in plan]
    return result


def _load_section_names():
    """{group_name: client-facing section name} from item_group_defs.json."""
    import json
    from pathlib import Path
    p = Path(os.path.dirname(os.path.abspath(__file__))) / "item_group_defs.json"
    if not p.exists():
        logger.warning("⚠️ item_group_defs.json not found; sections will be "
                       "named after their groups, so the internal prefix will "
                       "appear on the customer's quote")
        return {}
    try:
        return {g: spec["section_name"]
                for g, spec in (json.loads(p.read_text()).get("groups") or {}).items()
                if spec.get("section_name")}
    except Exception as e:
        logger.warning(f"⚠️ could not read item_group_defs.json: {e}")
        return {}


if __name__ == "__main__":
    import argparse
    import json as _json

    ap = argparse.ArgumentParser(
        description="Test v2 composition against a real Pipedrive deal.")
    ap.add_argument("--deal", required=True, help="Pipedrive deal id")
    ap.add_argument("--write", action="store_true",
                    help="actually create the quote (default: dry run)")
    a = ap.parse_args()

    from pipedrive import get_deal_by_id
    deal = get_deal_by_id(a.deal)
    if not deal:
        raise SystemExit(f"deal {a.deal} not found")

    org = deal.get("org_id") or {}
    if isinstance(org, dict):
        org_data = dict(org)
    else:
        org_data = {"name": str(org)}
    org_data[KEY_DEAL_ID] = a.deal

    out = create_quote_v2(org_data, deal, dry_run=not a.write)
    print(_json.dumps(out, indent=2, default=str) if out else "FAILED")
