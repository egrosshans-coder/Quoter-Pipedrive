"""
relink_item_by_name.py — repoint a Quoter item's Supplier SKU to the PD product that is
*actually* its own, resolved by NAME (used when the code is ambiguous, e.g. a base and a
rental variant share a code).

Why by name: for the fan, PD 195 (base) and PD 1210 (rental) share code HG-FVV-080-001,
so code can't disambiguate — but the exact product NAME does.

SAFETY:
  - dry-run by default; pass --execute to actually write.
  - requires EXACTLY ONE PD product and EXACTLY ONE Quoter item matching the name.
  - verifies the PD product's name equals the item's name before touching anything.
  - leaves the old product alone (it stays owned by whatever item legitimately points at it).

Usage:
  python relink_item_by_name.py "FV-32in-80 Fan Holographic / Rental Only / No Technician"
  python relink_item_by_name.py "FV-32in-80 Fan Holographic / Rental Only / No Technician" --execute
"""
import sys
from scalepad_items_maint import ItemMaintenance
from pipedrive_v2 import PipedriveProductsV2


def read(api, item_id):
    r = api.get_item(item_id, fields=["id", "name", "code", "sku"]) or {}
    return r.get("data", r) if isinstance(r, dict) else {}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    execute = "--execute" in sys.argv
    if not args:
        print('Usage: python relink_item_by_name.py "<exact item name>" [--execute]')
        return
    name = args[0]

    m = ItemMaintenance()
    pd = PipedriveProductsV2()

    # 1) resolve the PD product by exact name
    print(f"Resolving Pipedrive product by name {name!r} ...")
    pd_matches = pd.find_product_by_name(name)
    for p in pd_matches:
        print(f"   PD id={p.get('id')}  name={p.get('name')!r}  code={p.get('code')!r}")
    if len(pd_matches) != 1:
        print(f"ABORT: expected exactly 1 PD product for that name, found {len(pd_matches)}.")
        return
    target = pd_matches[0]
    target_id = str(target.get("id"))
    if str(target.get("name") or "") != name:
        print("ABORT: PD product name does not exactly match — refusing to relink.")
        return

    # 2) find the Quoter item by exact name
    q_matches = m.find_by_name(name)
    for i in q_matches:
        print(f"   Quoter id={i.get('id')}  name={i.get('name')!r}  code={i.get('code')!r}  sku={i.get('sku')!r}")
    if len(q_matches) != 1:
        print(f"ABORT: expected exactly 1 Quoter item for that name, found {len(q_matches)}.")
        return
    item = q_matches[0]
    item_id = item["id"]
    cur = str(item.get("sku") or "").strip()

    # 3) decide
    print(f"\nCurrent link : sku={cur or '(empty)'}   Correct product: PD {target_id}")
    if cur == target_id:
        print("Already correctly linked. No change.")
        return
    verb = "RELINK" if cur else "LINK"
    print(f"Planned {verb}: set item {item_id} sku {cur or '(empty)'} -> {target_id}")

    if not execute:
        print("\n(dry-run) Re-run with --execute to apply. The old product is left untouched.")
        return

    m.set_sku(item_id, target_id, dry_run=False)
    after = read(m.api, item_id)
    ok = str(after.get("sku")) == target_id
    print("after:", {k: after.get(k) for k in ("name", "code", "sku")})
    print("✅ Relinked." if ok else f"⚠️ sku did not stick (got {after.get('sku')!r}).")
    if ok:
        print("Next: you can now safely change this item's Code to '…-002' in the Quoter UI; "
              "the next sync will apply it to the correct product.")


if __name__ == "__main__":
    main()
