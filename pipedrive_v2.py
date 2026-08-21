"""
pipedrive_v2.py — minimal Pipedrive API v2 READ wrapper for products.

ADDITIVE + READ-ONLY. Does not touch the running sync (pipedrive.py). Lets us look up a
Pipedrive product by code (or name) and get its id — so linkage fixes DERIVE the PD id
instead of hardcoding it.

Auth: PIPEDRIVE_API_TOKEN as an api_token query param (same token pipedrive.py uses).
Base: https://api.pipedrive.com/api/v2
Find-by-code uses GET /api/v2/products/search?term=<code>&fields=code&exact_match=true
(the v2 Products list has no code filter; search is the supported path).

The client is imported/instantiated lazily so unit tests can inject a fake with no token/network.
"""
import os

BASE_URL_V2 = "https://api.pipedrive.com/api/v2"


class PipedriveV2Client:
    def __init__(self, api_token=None, base_url=BASE_URL_V2):
        import requests
        self.api_token = api_token or os.getenv("PIPEDRIVE_API_TOKEN")
        if not self.api_token:
            raise ValueError("Missing PIPEDRIVE_API_TOKEN")
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def get(self, path, params=None):
        p = dict(params or {})
        p["api_token"] = self.api_token
        r = self.session.get(f"{self.base_url}/{path.lstrip('/')}", params=p, timeout=30)
        r.raise_for_status()
        return r.json() if r.text else None


def products_from_search(resp):
    """Normalize a v2 products/search response into a flat list of product dicts.
    Handles {data:{items:[{item:{...}}]}} and {data:[...]} shapes defensively."""
    if not isinstance(resp, dict):
        return []
    d = resp.get("data", resp)
    out = []
    if isinstance(d, dict):
        for it in (d.get("items") or []):
            out.append(it.get("item", it) if isinstance(it, dict) else it)
    elif isinstance(d, list):
        out = d
    return out


class PipedriveProductsV2:
    def __init__(self, client=None):
        if client is None:
            client = PipedriveV2Client()
        self.client = client

    def search_products(self, term, fields="code", exact=True):
        params = {"term": term, "fields": fields}
        if exact:
            params["exact_match"] = "true"
        return self.client.get("/products/search", params=params)

    def find_product_by_code(self, code):
        prods = products_from_search(self.search_products(code, fields="code", exact=True))
        return [p for p in prods if str(p.get("code") or "") == str(code)]

    def find_product_by_name(self, name):
        prods = products_from_search(self.search_products(name, fields="name", exact=True))
        return [p for p in prods if str(p.get("name") or "") == str(name)]

    def get_product(self, product_id):
        r = self.client.get(f"/products/{product_id}")
        return (r or {}).get("data", r) if isinstance(r, dict) else r

    def product_id_for_code(self, code):
        """The single PD product id for a code, None if none, ValueError if ambiguous."""
        matches = self.find_product_by_code(code)
        if not matches:
            return None
        if len(matches) > 1:
            raise ValueError(f"Multiple PD products with code {code!r}: "
                             f"{[m.get('id') for m in matches]}")
        return matches[0].get("id")


if __name__ == "__main__":
    # read-only smoke: resolve a code to a PD product id
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "HG-FVV-MBOX-001"
    pd = PipedriveProductsV2()
    print(f"Searching Pipedrive for product code {code!r} ...")
    matches = pd.find_product_by_code(code)
    for p in matches:
        print(f"   id={p.get('id')}  name={p.get('name')!r}  code={p.get('code')!r}")
    print("resolved id:", pd.product_id_for_code(code))
