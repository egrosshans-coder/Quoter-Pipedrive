"""
scalepad_quotes.py — Quotes / Sections / Line Items resource wrapper.

ADDITIVE MODULE. Transport and resource wrappers only, no business logic, per
DECISIONS D-003/D-004. Sits over the existing ScalePadV2Client alongside
scalepad_items.py; does not import or modify quoter.py, pipedrive.py or
quoter_to_qbo_sync.py, so it cannot affect the running sync.

D-006 ("investigate and verify endpoints before writing wrapper methods") is
satisfied: every call below was confirmed live 2026-08-21/23 and is recorded in
Chapter 3 sections 7.10 and 7.11.

WHAT THE API ACTUALLY REQUIRES
------------------------------
None of this is guessable from the reference docs — the Create Quote Line Items
page renders its Body Params block empty, so the schema was derived from
successive 422 responses.

  POST /quotes/{id}/sections          body is a BARE ARRAY: [{"name": "..."}]
  POST /quotes/{id}/sections/{sid}/line-items
                                      body is a BARE ARRAY of line items, each:
                                        name                 required
                                        quantity_decimal     required, > 0, string
                                        unit_price_decimal   required, decimal string
                                        category             required, NESTED {"id": ...}

Three traps:
  * wrapped bodies ({"line_items": [...]}) return 400, not 422
  * unit_price as a float returns 422; it must be a decimal STRING
  * category as a flat string or category_id returns 422; it is an object

LINE ITEMS ARE CREATED BY VALUE
-------------------------------
There is no item_id on line-item creation. ScalePad confirmed this directly
(Jon Turner, 2026-08-23): "we do not allow existing catalog Items to be added,
just as ad-hoc Line Items."

So a line item is a free-standing copy of an item's values, with no link back
to the catalog record. That is why Bundles, Item Options and parent/child
items all fail to survive an API write (Chapter 3 section 7.12) — each needs a
reference that does not exist. Described as a known limitation likely to be
updated, so worth re-testing after a significant API release.

QUANTITY CANNOT BE ZERO
-----------------------
quantity_decimal must be greater than zero at write time; 0, blank and null all
return ERR_LINE_ITEM_QUANTITY_INVALID. The UI is more permissive and allows
both afterwards, which is what makes the seed-at-1 scaffold pattern work
(Chapter 3 sections 7.3-7.5).
"""

import os

QUOTER_PREFIX = "/quoter/v1"


class ScalePadQuotes:
    """Resource wrapper for quotes, sections and line items."""

    def __init__(self, client=None):
        if client is None:
            from scalepad_v2 import ScalePadV2Client
            client = ScalePadV2Client()
        self.client = client

    # ---- quotes ----------------------------------------------------------

    def get_quote(self, quote_id):
        """Full quote. `sections` is embedded, each with its `line_items`.

        Note GET /quotes/{id}/sections returns 403 — that path is POST-only.
        Sections are read from the quote itself.
        """
        r = self.client.get(f"{QUOTER_PREFIX}/quotes/{quote_id}")
        return (r or {}).get("data", r)

    def create_quote(self, template_id=None, contact_email=None,
                     client_name=None, custom_number=None, **extra):
        """Create a draft.

        client_id may be null; the Client is resolved from client_name
        (confirmed with ScalePad, and live 2026-08-19). custom_number is
        settable at create time on v2 — it was not on legacy.

        The response always carries sections: null, even with a template_id.
        A template contributes no line items via the API and ScalePad confirms
        that is intended (Chapter 3 section 6.2.1). Content is composed by the
        caller.
        """
        body = {}
        if template_id:
            body["template_id"] = template_id
        contact = {}
        if contact_email:
            contact["email"] = contact_email
        if client_name:
            contact["client_name"] = client_name
        if contact:
            body["contact"] = contact
        if custom_number:
            body["custom_number"] = custom_number
        body.update(extra)
        r = self.client.post(f"{QUOTER_PREFIX}/quotes", data=body)
        return (r or {}).get("data", r)

    # ---- sections --------------------------------------------------------

    def create_sections(self, quote_id, names):
        """Create one or more sections. Body is a bare array of {"name": ...}.

        Multiple sections per quote are supported and they read back in
        creation order. The response is the whole quote, not just the new
        sections, so this returns its `sections` list.
        """
        if isinstance(names, str):
            names = [names]
        body = [{"name": n} for n in names]
        r = self.client.post(f"{QUOTER_PREFIX}/quotes/{quote_id}/sections",
                             data=body)
        d = (r or {}).get("data", r) or {}
        return d.get("sections") or []

    def sections_of(self, quote_id):
        return (self.get_quote(quote_id) or {}).get("sections") or []

    def find_section(self, quote_id, name):
        return next((s for s in self.sections_of(quote_id)
                     if (s.get("name") or "").strip() == name.strip()), None)

    # ---- line items ------------------------------------------------------

    @staticmethod
    def line_item(name, category_id, unit_price, quantity=1,
                  unit_cost=None, taxable=None, description=None):
        """Build one line-item payload in the confirmed shape.

        quantity defaults to 1 because the API rejects 0 — see the module
        docstring. Prune to zero or blank in the UI afterwards.
        """
        if float(quantity) <= 0:
            raise ValueError(
                "quantity must be greater than zero: the API rejects 0, blank "
                "and null. Seed at 1 and zero it in the UI (Chapter 3 7.5)."
            )
        item = {
            "name": name,
            "quantity_decimal": str(quantity),
            "unit_price_decimal": f"{float(unit_price or 0):.2f}",
            "category": {"id": category_id},
        }
        if unit_cost is not None:
            item["unit_cost_decimal"] = f"{float(unit_cost):.2f}"
        if taxable is not None:
            item["taxable"] = bool(taxable)
        if description is not None:
            item["description"] = description
        return item

    @staticmethod
    def line_item_from_catalog(catalog_item, quantity=1, unit_price=0,
                               use_catalog_price=False):
        """Copy a catalog item's values into a line-item payload.

        By value, not by reference — there is no item_id to send.

        PRICE DEFAULTS TO ZERO, DELIBERATELY. TLC re-prices per customer and
        per deal, so the catalog price is a reference point rather than the
        number that goes on a quote. Seeding it would produce a line that
        looks deliberately priced when nobody has priced it — and if the
        salesperson misses one, a wrong price ships. A $0.00 line is visibly
        unpriced and cannot be mistaken for a decision.

        Zero is safe here where a zero QUANTITY is not: the API rejects
        quantity 0, but accepts unit_price 0, and 1 x $0.00 renders as an
        exact $0.00 across the API response, admin preview, webview and PDF
        (verified, Chapter 3 7.5).

        Pass use_catalog_price=True for fixed-price items that genuinely do
        not vary by customer.
        """
        price = unit_price
        if use_catalog_price:
            price = catalog_item.get("price_decimal")
        return ScalePadQuotes.line_item(
            name=catalog_item.get("name"),
            category_id=catalog_item.get("category_id"),
            unit_price=price,
            quantity=quantity,
            unit_cost=catalog_item.get("cost_decimal"),
        )

    def add_line_items(self, quote_id, section_id, items):
        """POST a bare array of line items into a section.

        A 422 reports EVERY failing rule across EVERY item in the batch, each
        located as line_items[i].field. The underlying client raises on 4xx,
        so callers should catch and read the exception text rather than
        inspecting a return value.
        """
        if isinstance(items, dict):
            items = [items]
        r = self.client.post(
            f"{QUOTER_PREFIX}/quotes/{quote_id}/sections/{section_id}/line-items",
            data=items)
        return (r or {}).get("data", r)

    # ---- item groups (read side, for composition) ------------------------

    def group_item_ids(self, item_group_id):
        """item_ids assigned to an Item Group, following cursor pagination.

        Item Groups are a reseller access-control feature repurposed as a
        machine-readable lookup (Chapter 3 section 7.8). Valid only while no
        Resellers are configured — otherwise a lookup group silently becomes a
        grant of item visibility.
        """
        out, cursor, seen = [], None, set()
        base = (f"{QUOTER_PREFIX}/item-group-item-assignments"
                f"?filter[item_group_id]=eq:{item_group_id}&page_size=200")
        while True:
            path = base + (f"&cursor={cursor}" if cursor else "")
            r = self.client.get(path) or {}
            out.extend(a.get("item_id") for a in (r.get("data") or []))
            cursor = r.get("next_cursor")
            if not cursor or cursor in seen:
                break
            seen.add(cursor)
        return [i for i in out if i]

    def find_group(self, name):
        r = self.client.get(f"{QUOTER_PREFIX}/item-groups?page_size=200") or {}
        return next((g for g in (r.get("data") or [])
                     if (g.get("name") or "").strip().lower()
                     == name.strip().lower()), None)
