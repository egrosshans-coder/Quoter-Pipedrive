"""
Unit tests for scalepad_items_maint.py — no network, no API key.
FakeClient records calls and returns canned responses.

Run:  PYTHONPATH=. python3 test_files/test_scalepad_items_maint.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scalepad_items as si
import scalepad_items_maint as sim


class FakeClient:
    def __init__(self, responses=None):
        self.calls = []
        self._responses = list(responses or [])
        self._i = 0
    def _next(self):
        r = self._responses[self._i] if self._i < len(self._responses) else {}
        self._i += 1
        return r
    def get(self, path, params=None):
        self.calls.append(("GET", path, params)); return self._next()
    def post(self, path, data=None):
        self.calls.append(("POST", path, data)); return self._next()
    def patch(self, path, data=None):
        self.calls.append(("PATCH", path, data)); return self._next()


def maint(responses=None):
    fc = FakeClient(responses)
    return sim.ItemMaintenance(api=si.QuoterItemsV2(client=fc)), fc


def test_find_by_code_uses_server_filter():
    m, fc = maint([{"data": [{"id": "item_1", "code": "BAL-FIL-001"}]}])
    res = m.find_by_code("BAL-FIL-001")
    method, path, params = fc.calls[0]
    assert path == "/quoter/v1/items", path
    assert params["filter[code]"] == "eq:BAL-FIL-001", params
    assert res[0]["id"] == "item_1"


def test_find_by_sku_uses_server_filter():
    m, fc = maint([{"data": [{"id": "item_x", "sku": "195"}]}])
    m.find_by_sku("195")
    assert fc.calls[0][2]["filter[sku]"] == "eq:195", fc.calls[0][2]


def test_scan_sku_collisions():
    page = {"data": [
        {"id": "a", "sku": "195"}, {"id": "b", "sku": "195"},
        {"id": "c", "sku": "794"}, {"id": "d", "sku": "794"},
        {"id": "e", "sku": "12"}, {"id": "f", "sku": ""},
    ], "next_cursor": None}
    m, fc = maint([page])
    col = m.scan_sku_collisions()
    assert set(col.keys()) == {"195", "794"}, col.keys()
    assert len(col["195"]) == 2 and len(col["794"]) == 2


def test_scan_empty_sku():
    page = {"data": [{"id": "a", "sku": "1"}, {"id": "b", "sku": ""}, {"id": "c", "sku": "  "}],
            "next_cursor": None}
    m, fc = maint([page])
    empty = m.scan_empty_sku()
    assert {i["id"] for i in empty} == {"b", "c"}, empty


def test_scan_dup_codes():
    page = {"data": [{"id": "a", "code": "X"}, {"id": "b", "code": "X"}, {"id": "c", "code": "Y"}],
            "next_cursor": None}
    m, fc = maint([page])
    dup = m.scan_dup_codes()
    assert set(dup.keys()) == {"X"}, dup


def test_scan_nonnumeric_sku():
    page = {"data": [{"id": "a", "sku": "407"}, {"id": "b", "sku": "N82E16820147743"}, {"id": "c", "sku": ""}],
            "next_cursor": None}
    m, fc = maint([page])
    bad = m.scan_nonnumeric_sku()
    assert {i["id"] for i in bad} == {"b"}, bad


def test_set_sku_dry_run_default():
    m, fc = maint()
    plan = m.set_sku("item_mb", 412)          # dry_run defaults True
    assert plan == {"action": "set_sku", "item_id": "item_mb", "sku": "412", "dry_run": True}, plan
    assert fc.calls == [], "dry-run must not call the API"


def test_set_sku_execute():
    m, fc = maint([{"id": "item_mb", "sku": "412"}])
    m.set_sku("item_mb", 412, dry_run=False)
    method, path, data = fc.calls[0]
    assert method == "PATCH" and path == "/quoter/v1/items/item_mb", (method, path)
    assert data == {"sku": "412"}, data


def test_set_sku_rejects_nonnumeric():
    m, fc = maint()
    try:
        m.set_sku("item_x", "NOT-A-PD-ID", dry_run=False)
        assert False, "should have raised"
    except ValueError:
        pass
    assert fc.calls == []


def test_clear_sku_dry_run_and_execute():
    m, fc = maint()
    plan = m.clear_sku("item_rent")
    assert plan["action"] == "clear_sku" and plan["sku"] == "" and plan["dry_run"] is True, plan
    assert fc.calls == []
    m2, fc2 = maint([{"id": "item_rent", "sku": ""}])
    m2.clear_sku("item_rent", dry_run=False)
    method, path, data = fc2.calls[0]
    assert method == "PATCH" and path == "/quoter/v1/items/item_rent", (method, path)
    assert data == {"sku": ""}, data     # empty string sent (the behavior we must verify live)


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t(); print(f"PASS  {t.__name__}"); passed += 1
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}"); failed += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}"); failed += 1
    print(f"\n{passed} passed, {failed} failed, {len(tests)} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
