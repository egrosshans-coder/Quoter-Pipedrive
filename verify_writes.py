"""
verify_writes.py — one-shot, SAFE live check that ScalePad v2 writes work and that
clear_sku actually empties the Supplier SKU.

It does a REVERSIBLE round-trip on an existing throwaway ZZZ item:
    read sku -> clear it -> read (expect empty) -> restore original -> read (expect original)
No sync is run in between, so there is NO net change and NO PD/QBO ripple.
Nothing is created or deleted.

Run:  python verify_writes.py
"""
from scalepad_items_maint import ItemMaintenance


def read_sku(api, item_id):
    r = api.get_item(item_id, fields=["id", "sku"]) or {}
    d = r.get("data", r) if isinstance(r, dict) else {}
    return d.get("sku")


def main():
    m = ItemMaintenance()

    print("Scanning for a disposable ZZZ item with a numeric sku...")
    items = list(m.api.iter_all_items(fields=["id", "name", "code", "sku"]))
    zz = [i for i in items
          if (i.get("code") or "").upper().startswith("ZZZ") and str(i.get("sku") or "").isdigit()]

    if not zz:
        print("No ZZZ item with a numeric sku found. Candidates without sku:")
        for i in items:
            if (i.get("code") or "").upper().startswith("ZZZ"):
                print(f"   {i.get('code')}  sku={i.get('sku')!r}  {i.get('name')}")
        print("\nPick any ZZZ item, or tell me its code and I'll adapt the test.")
        return

    t = zz[0]
    item_id, orig = t["id"], str(t["sku"])
    print(f"Using: {t.get('name')!r}  code={t.get('code')}  id={item_id}  original sku={orig!r}\n")

    ok_clear = ok_restore = False
    try:
        print("before       :", read_sku(m.api, item_id))
        m.clear_sku(item_id, dry_run=False)
        after_clear = read_sku(m.api, item_id)
        print("after clear  :", repr(after_clear), "  (expect empty)")
        ok_clear = (after_clear in ("", None))
    finally:
        # Always attempt to restore, even if the check above raised.
        m.set_sku(item_id, orig, dry_run=False)
        after_restore = read_sku(m.api, item_id)
        print("after restore:", repr(after_restore), f"  (expect {orig!r})")
        ok_restore = (str(after_restore) == orig)

    print("\n---- RESULT ----")
    print(f"  writes work + clear empties the field : {'PASS' if ok_clear else 'FAIL'}")
    print(f"  set_sku restores the value            : {'PASS' if ok_restore else 'FAIL'}")
    if ok_clear and ok_restore:
        print("\n✅ Safe to use set_sku / clear_sku on real items (FVV-MasterBox, rent fan).")
    elif ok_restore and not ok_clear:
        print("\n⚠️  Writes work, but PATCH sku=\"\" did NOT empty the field.")
        print("   Paste this output to Claude — we'll switch clear_sku from \"\" to null.")
    else:
        print("\n⚠️  Something didn't round-trip cleanly. Paste this output to Claude before doing real fixes.")


if __name__ == "__main__":
    main()
