"""
Unit tests for pipedrive_v2.py — no network, no token. FakeClient returns canned responses.
Run:  PYTHONPATH=. python3 test_files/test_pipedrive_v2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pipedrive_v2 as pv2


class FakeClient:
    def __init__(self, responses=None):
        self.calls = []
        self._responses = list(responses or [])
        self._i = 0
    def get(self, path, params=None):
        self.calls.append(("GET", path, params))
        r = self._responses[self._i] if self._i < len(self._responses) else {}
        self._i += 1
        return r


# canonical v2 search shape: {success, data:{items:[{item:{...}}]}}
def search_resp(*products):
    return {"success": True, "data": {"items": [{"item": p} for p in products]}}


def test_search_params():
    fc = FakeClient([search_resp()])
    pv2.PipedriveProductsV2(client=fc).find_product_by_code("HG-FVV-MBOX-001")
    method, path, params = fc.calls[0]
    assert method == "GET" and path == "/products/search", (method, path)
    assert params["term"] == "HG-FVV-MBOX-001", params
    assert params["fields"] == "code", params
    assert params["exact_match"] == "true", params


def test_find_by_code_parses_items_shape():
    fc = FakeClient([search_resp({"id": 412, "name": "FVV-MasterBox", "code": "HG-FVV-MBOX-001"})])
    res = pv2.PipedriveProductsV2(client=fc).find_product_by_code("HG-FVV-MBOX-001")
    assert len(res) == 1 and res[0]["id"] == 412, res


def test_find_by_code_filters_nonexact():
    # search returns a near-match with a different code; we must drop it
    fc = FakeClient([search_resp(
        {"id": 412, "code": "HG-FVV-MBOX-001"},
        {"id": 999, "code": "HG-FVV-MBOX-002"},
    )])
    res = pv2.PipedriveProductsV2(client=fc).find_product_by_code("HG-FVV-MBOX-001")
    assert [p["id"] for p in res] == [412], res


def test_product_id_for_code_single():
    fc = FakeClient([search_resp({"id": 412, "code": "HG-FVV-MBOX-001"})])
    assert pv2.PipedriveProductsV2(client=fc).product_id_for_code("HG-FVV-MBOX-001") == 412


def test_product_id_for_code_none():
    fc = FakeClient([search_resp()])  # no items
    assert pv2.PipedriveProductsV2(client=fc).product_id_for_code("NOPE") is None


def test_product_id_for_code_ambiguous_raises():
    fc = FakeClient([search_resp({"id": 1, "code": "DUP"}, {"id": 2, "code": "DUP"})])
    try:
        pv2.PipedriveProductsV2(client=fc).product_id_for_code("DUP")
        assert False, "should have raised on ambiguity"
    except ValueError:
        pass


def test_products_from_search_handles_flat_list():
    # defensive: some responses may be {data:[...]} instead of {data:{items:[...]}}
    resp = {"data": [{"id": 5, "code": "X"}]}
    out = pv2.products_from_search(resp)
    assert out == [{"id": 5, "code": "X"}], out


def test_products_from_search_empty():
    assert pv2.products_from_search({}) == []
    assert pv2.products_from_search(None) == []


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
