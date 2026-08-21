"""
link_item_by_code.py — DERIVE-then-link: given a product Code, look up its Pipedrive
product id dynamically (no hardcoding), find the matching Quoter item, and set the
Supplier SKU so they're linked. Reusable for any item; idempotent.

Behaviour:
  - Resolves the PD product id from the code via Pipedrive v2 search.
  - Finds the Quoter item by the same code.
  - If the item's sku is empty        -> links it (writes the derived id).
  - If the item's sku already == id    -> reports "already linked" (no change).
  - If the item's sku != id (conflict) -> aborts and shows both, does nothing.

Run:  python link_item_by_code.py "HG-FVV-MBOX-001"
"""
import sys
from scalepad_items_maint import ItemMaintenance
from pipedrive_v2 import PipedriveProductsV2


def read(api, item_id):
    r = api.get_item(item_id, fields=["id", "name", "code", "sku"]) or {}
    return r.get("data", r) if isinstance(r, dict) else {}


def main():
    code = sys.argv[1] if len(sys.argv) > 1 else "HG-FVV-MBOX-001"
    m = ItemMaintenance()
    pd = PipedriveProductsV2()

    # 1) DERIVE the PD product id from the code (no hardcoding)
    print(f"Resolving Pipedrive product for code {code!r} ...")
    try:
        pd_id = pd.product_id_for_code(code)
    except ValueError as e:
        print(f"ABORT: {e}")
        return
    if pd_id is None:
        print("No Pipedrive product found for that code — this item is genuinely new "
              "(let the sync create it). Nothing to link.")
        # show raw search to help debug the response shape if unexpected
        print("raw search:", pd.search_products(code))
        return
    print(f"   Pipedrive product id = {pd_id}")

    # 2) find the Quoter item by the same code
    matches = m.find_by_code(code)
    if len(matches) != 1:
        print(f"ABORT: expected exactly 1 Quoter item for code {code!r}, found {len(matches)}.")
        for i in matches:
            print(f"   id={i.get('id')} name={i.get('name')!r} sku={i.get('sku')!r}")
        return
    item = matches[0]
    item_id = item["id"]
    cur = str(item.get("sku") or "").strip()

    # 3) act
    if cur == str(pd_id):
        print(f"Already linked: {item.get('name')!r} sku={cur} == PD {pd_id}. No change.")
        return
    if cur:
        print(f"CONFLICT: {item.get('name')!r} already has sku={cur!r}, but code resolves to "
              f"PD {pd_id}. Not overwriting — resolve manually.")
        return
    print("Plan:", m.set_sku(item_id, pd_id, dry_run=True))
    m.set_sku(item_id, pd_id, dry_run=False)
    after = read(m.api, item_id)
    ok = str(after.get("sku")) == str(pd_id)
    print("after:", {k: after.get(k) for k in ("name", "code", "sku")})
    print("✅ Linked." if ok else f"⚠️ sku did not stick (got {after.get('sku')!r}).")


if __name__ == "__main__":
    main()
