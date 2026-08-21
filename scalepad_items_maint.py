"""
scalepad_items_maint.py — maintenance helpers for the Quoter (ScalePad v2) item catalog.

ADDITIVE. Builds on QuoterItemsV2 (scalepad_items.py). Provides the linkage-integrity
operations the Quoter UI CANNOT do (set/clear the Supplier SKU), plus read-only audits.
Touches no running sync code.

Fixes it enables (from the catalog audit):
  - op 2  "create 2nd product": clear_sku() on the copy so the next sync creates its own PD product.
  - op 3  "link missing sku":   set_sku() to point a valid item at an existing PD product (e.g. FVV-MasterBox -> 412).
  (op 1 "delete real dup" is intentionally NOT here — do deletes in the Quoter UI, which warns on quote usage.)

WRITES ARE GUARDED: every write defaults to dry_run=True and returns the intended change
without sending it. Pass dry_run=False to execute.

VERIFY LIVE BEFORE USING ON REAL ITEMS (run on a throwaway ZZZ item):
  1. v2 writes work with the API key at all (set a field, re-read, confirm).
  2. clear_sku() actually EMPTIES the field (PATCH sku="" clears vs is ignored).
Use verify_plan()/the runbook in the project docs; do not trust these on real items until confirmed.
"""

from scalepad_items import QuoterItemsV2


class ItemMaintenance:
    def __init__(self, api=None):
        self.api = api or QuoterItemsV2()

    # ---------- find (server-side filters; ScalePad v2 supports eq: on code/sku/name) ----------

    def find_by_code(self, code):
        resp = self.api.list_items(extra_filters={"filter[code]": f"eq:{code}"}) or {}
        return resp.get("data", []) or []

    def find_by_sku(self, sku):
        resp = self.api.list_items(extra_filters={"filter[sku]": f"eq:{sku}"}) or {}
        return resp.get("data", []) or []

    def find_by_name(self, name):
        resp = self.api.list_items(extra_filters={"filter[name]": f"eq:{name}"}) or {}
        return resp.get("data", []) or []

    # ---------- audits (read-only, whole catalog) ----------

    def _all(self, items):
        return items if items is not None else list(
            self.api.iter_all_items(fields=["id", "name", "code", "sku", "category"]))

    def scan_empty_sku(self, items=None):
        """Items with no Supplier SKU — candidates for op 3 (link) or op 2 (new)."""
        return [i for i in self._all(items) if not str(i.get("sku") or "").strip()]

    def scan_sku_collisions(self, items=None):
        """{sku: [items]} where >1 item shares a Supplier SKU (the copy problem)."""
        by = {}
        for i in self._all(items):
            s = str(i.get("sku") or "").strip()
            if s:
                by.setdefault(s, []).append(i)
        return {s: v for s, v in by.items() if len(v) > 1}

    def scan_dup_codes(self, items=None):
        """{code: [items]} where >1 item shares a Code (blocks code-as-key)."""
        by = {}
        for i in self._all(items):
            c = str(i.get("code") or "").strip()
            if c:
                by.setdefault(c, []).append(i)
        return {c: v for c, v in by.items() if len(v) > 1}

    def scan_nonnumeric_sku(self, items=None):
        """Items whose Supplier SKU is present but not a numeric PD id (likely a real SKU typed in)."""
        out = []
        for i in self._all(items):
            s = str(i.get("sku") or "").strip()
            if s and not s.isdigit():
                out.append(i)
        return out

    # ---------- guarded writes (the parts the Quoter UI cannot do) ----------

    def set_sku(self, item_id, pd_id, dry_run=True):
        """op 3 — link an item to an existing PD product id."""
        pd_id = str(pd_id).strip()
        if not pd_id.isdigit():
            raise ValueError(f"pd_id must be a numeric Pipedrive product id, got {pd_id!r}")
        if dry_run:
            return {"action": "set_sku", "item_id": item_id, "sku": pd_id, "dry_run": True}
        return self.api.update_item(item_id, sku=pd_id)

    def clear_sku(self, item_id, dry_run=True):
        """op 2 (step) — unlink so the next sync creates a fresh PD product."""
        if dry_run:
            return {"action": "clear_sku", "item_id": item_id, "sku": "", "dry_run": True}
        return self.api.update_item(item_id, sku="")
