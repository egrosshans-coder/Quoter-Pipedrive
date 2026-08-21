"""
Unit tests for scalepad_items.py — no network, no API key.

Uses a FakeClient that records calls and returns canned responses, so we verify:
  - correct endpoint paths
  - the incremental filter param (filter[record_updated_at]=gt:...)
  - cursor pagination follow-through in iter_all_items
  - create/update request bodies
  - response parsing against the documented v2 shape {data, next_cursor, total_count}

Run:  PYTHONPATH=. python3 test_files/test_scalepad_items_v2.py
"""
import os, sys

# Make the repo root importable regardless of where this is run from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scalepad_items as si


class FakeClient:
    """Records (METHOD, path, params_or_data) and returns queued responses in order."""
    def __init__(self, responses=None):
        self.calls = []
        self._responses = list(responses or [])
        self._i = 0

    def _next(self):
        if self._i < len(self._responses):
            r = self._responses[self._i]
            self._i += 1
            return r
        return {}

    def get(self, path, params=None):
        self.calls.append(("GET", path, params))
        return self._next()

    def post(self, path, data=None):
        self.calls.append(("POST", path, data))
        return self._next()

    def patch(self, path, data=None):
        self.calls.append(("PATCH", path, data))
        return self._next()


# ---- tests -------------------------------------------------------------------

def test_list_items_builds_incremental_params():
    fc = FakeClient([{"data": [], "next_cursor": None, "total_count": 0}])
    api = si.QuoterItemsV2(client=fc)
    api.list_items(updated_since="2026-01-15T00:00:00Z", page_size=200)
    method, path, params = fc.calls[0]
    assert method == "GET", method
    assert path == "/quoter/v1/items", path
    assert params["page_size"] == 200, params
    assert params["filter[record_updated_at]"] == "gt:2026-01-15T00:00:00Z", params
    assert "cursor" not in params, params


def test_list_items_caps_page_size_at_200():
    fc = FakeClient([{"data": []}])
    si.QuoterItemsV2(client=fc).list_items(page_size=1000)
    assert fc.calls[0][2]["page_size"] == 200, fc.calls[0][2]


def test_list_items_no_filter_when_no_updated_since():
    fc = FakeClient([{"data": []}])
    si.QuoterItemsV2(client=fc).list_items()
    params = fc.calls[0][2]
    assert "filter[record_updated_at]" not in params, params


def test_iter_all_items_follows_cursor():
    page1 = {"data": [{"id": "item_1"}, {"id": "item_2"}], "next_cursor": "CUR2", "total_count": 3}
    page2 = {"data": [{"id": "item_3"}], "next_cursor": None, "total_count": 3}
    fc = FakeClient([page1, page2])
    api = si.QuoterItemsV2(client=fc)
    ids = [it["id"] for it in api.iter_all_items(updated_since="2026-01-15T00:00:00Z")]
    assert ids == ["item_1", "item_2", "item_3"], ids
    # first call has no cursor; second call carries the cursor from page1
    assert fc.calls[0][2].get("cursor") is None, fc.calls[0][2]
    assert fc.calls[1][2]["cursor"] == "CUR2", fc.calls[1][2]


def test_get_item_path_and_fields():
    fc = FakeClient([{"id": "item_9"}])
    si.QuoterItemsV2(client=fc).get_item("item_9", fields=["name", "sku", "price_decimal"])
    method, path, params = fc.calls[0]
    assert method == "GET" and path == "/quoter/v1/items/item_9", (method, path)
    assert params["fields"] == "name,sku,price_decimal", params


def test_create_item_body():
    fc = FakeClient([{"id": "item_new"}])
    api = si.QuoterItemsV2(client=fc)
    api.create_item(name="Balloon air filler", category_id="cat_x",
                    code="BAL-FIL-001", price_decimal="10.00", sku=None)
    method, path, data = fc.calls[0]
    assert method == "POST" and path == "/quoter/v1/items", (method, path)
    assert data["name"] == "Balloon air filler" and data["category_id"] == "cat_x", data
    assert data["code"] == "BAL-FIL-001" and data["price_decimal"] == "10.00", data
    # None-valued kwargs are dropped
    assert "sku" not in data, data


def test_update_item_body():
    fc = FakeClient([{"id": "item_1"}])
    si.QuoterItemsV2(client=fc).update_item("item_1", price_decimal="12.00")
    method, path, data = fc.calls[0]
    assert method == "PATCH" and path == "/quoter/v1/items/item_1", (method, path)
    assert data == {"price_decimal": "12.00"}, data


def test_categories_paths():
    fc = FakeClient([{"data": []}, {"id": "cat_1"}])
    api = si.QuoterItemsV2(client=fc)
    api.list_categories()
    api.get_category("cat_1")
    assert fc.calls[0][:2] == ("GET", "/quoter/v1/categories"), fc.calls[0]
    assert fc.calls[1][:2] == ("GET", "/quoter/v1/categories/cat_1"), fc.calls[1]


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {len(tests)} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
