"""
scalepad_items.py — ScalePad (Quoter) v2 resource wrappers for Items and Categories.

ADDITIVE MODULE. Builds on the existing transport client (ScalePadV2Client) per the
dual-client architecture (see docs/DECISIONS.md D-003/D-004). It intentionally does NOT
modify or import any of the running sync code (quoter.py, pipedrive.py,
quoter_to_qbo_sync.py), so it cannot affect production behavior.

ScalePad v2 (base https://api.scalepad.com), auth: x-api-key header (handled by the client):
  GET    /quoter/v1/items                 (list; cursor pagination; filter[record_updated_at])
  GET    /quoter/v1/items/{id}            (fetch)
  POST   /quoter/v1/items                 (create; requires name + category_id)
  PATCH  /quoter/v1/items/{id}            (update)
  GET    /quoter/v1/categories            (list)
  GET    /quoter/v1/categories/{id}       (fetch)

The client is imported lazily so this module (and its unit tests) can be used with a
fake/injected client without requiring the real API key or dotenv.
"""

ITEMS_PATH = "/quoter/v1/items"
CATEGORIES_PATH = "/quoter/v1/categories"

# ScalePad v2 caps page_size at 200.
MAX_PAGE_SIZE = 200


def _csv(value):
    """Accept a list/tuple or a pre-joined string for comma-separated params."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return ",".join(str(v) for v in value)
    return str(value)


class QuoterItemsV2:
    def __init__(self, client=None):
        # Lazy import so tests can inject a fake client with no key/network/dotenv.
        if client is None:
            from scalepad_v2 import ScalePadV2Client
            client = ScalePadV2Client()
        self.client = client

    # ---- Items ---------------------------------------------------------------

    def list_items(self, updated_since=None, page_size=MAX_PAGE_SIZE, cursor=None,
                   fields=None, extra_filters=None):
        """One page of items. `updated_since` is an ISO-8601/RFC3339 string; it becomes
        filter[record_updated_at]=gt:<ts>. Returns the raw response
        {data: [...], next_cursor: str|None, total_count: int}."""
        params = {"page_size": min(int(page_size), MAX_PAGE_SIZE)}
        if cursor:
            params["cursor"] = cursor
        if updated_since:
            params["filter[record_updated_at]"] = f"gt:{updated_since}"
        if fields:
            params["fields"] = _csv(fields)
        if extra_filters:
            params.update(extra_filters)
        return self.client.get(ITEMS_PATH, params=params)

    def iter_all_items(self, updated_since=None, page_size=MAX_PAGE_SIZE, **kw):
        """Yield every item across pages, following next_cursor until exhausted."""
        cursor = None
        while True:
            resp = self.list_items(updated_since=updated_since, page_size=page_size,
                                   cursor=cursor, **kw) or {}
            for item in (resp.get("data") or []):
                yield item
            cursor = resp.get("next_cursor")
            if not cursor:
                break

    def get_item(self, item_id, fields=None):
        params = {}
        if fields:
            params["fields"] = _csv(fields)
        return self.client.get(f"{ITEMS_PATH}/{item_id}", params=params or None)

    def create_item(self, name, category_id, **fields):
        """Create an item. Required: name + category_id. Extra v2 fields (code, sku,
        price_decimal, cost_decimal, description, taxable, ...) passed as kwargs."""
        body = {"name": name, "category_id": category_id}
        body.update({k: v for k, v in fields.items() if v is not None})
        return self.client.post(ITEMS_PATH, data=body)

    def update_item(self, item_id, **fields):
        """Patch an existing item with only the supplied fields."""
        body = {k: v for k, v in fields.items() if v is not None}
        return self.client.patch(f"{ITEMS_PATH}/{item_id}", data=body)

    # ---- Categories ----------------------------------------------------------

    def list_categories(self, page_size=MAX_PAGE_SIZE, cursor=None):
        params = {"page_size": min(int(page_size), MAX_PAGE_SIZE)}
        if cursor:
            params["cursor"] = cursor
        return self.client.get(CATEGORIES_PATH, params=params)

    def get_category(self, category_id):
        return self.client.get(f"{CATEGORIES_PATH}/{category_id}")


# ---- Read-only live smoke test (run locally where SCALEPAD_API_KEY + network exist) ----
# Usage:  python scalepad_items.py
# Does NOT write anything: lists 1 item and the categories, prints a short summary.
if __name__ == "__main__":
    api = QuoterItemsV2()
    print("== ScalePad v2 read-only smoke test ==")
    items = api.list_items(page_size=1)
    data = (items or {}).get("data", [])
    print(f"list_items ok: total_count={items.get('total_count')!r}, "
          f"returned={len(data)}, next_cursor={'yes' if items.get('next_cursor') else 'no'}")
    if data:
        it = data[0]
        print("  sample item:", {k: it.get(k) for k in
              ("id", "name", "code", "sku", "category", "price_decimal", "record_updated_at")})
    cats = api.list_categories(page_size=5)
    print(f"list_categories ok: returned={len((cats or {}).get('data', []))}")
    print("Smoke test complete (no data written).")
