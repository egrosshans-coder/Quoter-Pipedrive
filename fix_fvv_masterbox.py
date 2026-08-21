"""
fix_fvv_masterbox.py — op 3: link the FVV-MasterBox item to its existing PD product 412
by writing the missing Supplier SKU. Reversible (clear it again if ever wrong).

Guards: aborts unless exactly one item matches the code AND its sku is currently empty,
so it can't overwrite a real link or hit the wrong item.

Run:  python fix_fvv_masterbox.py
"""
from scalepad_items_maint import ItemMaintenance

CODE = "HG-FVV-MBOX-001"   # FVV-MasterBox
PD_ID = "412"

def read(api, item_id):
    r = api.get_item(item_id, fields=["id", "name", "code", "sku"]) or {}
    return r.get("data", r) if isinstance(r, dict) else {}

def main():
    m = ItemMaintenance()
    matches = m.find_by_code(CODE)
    print(f"Items matching code {CODE!r}: {len(matches)}")
    for i in matches:
        print(f"   id={i.get('id')}  name={i.get('name')!r}  sku={i.get('sku')!r}")

    if len(matches) != 1:
        print("ABORT: expected exactly 1 match. Fix manually / tell Claude.")
        return
    item = matches[0]
    if str(item.get("sku") or "").strip():
        print(f"ABORT: item already has a sku ({item['sku']!r}); not overwriting.")
        return

    item_id = item["id"]
    print("\nPlan:", m.set_sku(item_id, PD_ID, dry_run=True))
    print("Executing...")
    m.set_sku(item_id, PD_ID, dry_run=False)
    after = read(m.api, item_id)
    print("after:", {k: after.get(k) for k in ("name", "code", "sku")})
    if str(after.get("sku")) == PD_ID:
        print(f"\n✅ Linked {after.get('name')!r} -> PD product {PD_ID}.")
    else:
        print(f"\n⚠️  sku did not stick (got {after.get('sku')!r}). Paste output to Claude.")

if __name__ == "__main__":
    main()
