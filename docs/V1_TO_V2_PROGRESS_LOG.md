# V1 → V2 Migration — Progress Log

A running, dated log of the Quoter→ScalePad and Pipedrive v1→v2 migration work. Newest entry on top. Add a new dated block at the top each session.

**Status legend:** ✅ done · 🔨 in progress · ⏳ waiting (vendor/external) · 🅿️ parked

---

## 2026-07-24 (cont.) — Fix toolkit built + first real repairs ✅

**Built** (all additive, no running-sync code touched; all unit-tested, no network):
- `pipedrive_v2.py` — read-only Pipedrive v2 wrapper: `find_product_by_code` / `by_name`, `product_id_for_code`. 8/8 tests. Live-verified (resolved a code/name to the right PD product).
- `scalepad_items_maint.py` — audits (`scan_empty_sku`, `scan_sku_collisions`, `scan_dup_codes`, `scan_nonnumeric_sku`) + guarded `set_sku` / `clear_sku` (dry-run default). 10/10 tests.
- `link_item_by_code.py` / `relink_item_by_name.py` — derive-then-(re)link; **no hardcoded ids**.
- `verify_writes.py` / `fix_fvv_masterbox.py` — one-shot runnable helpers.

**Live-verified & repaired:**
- Writes work; `clear_sku` genuinely empties the field (reversible ZZZ round-trip).
- **FVV-MasterBox** → linked to existing **PD 412** (was a half-synced item: product existed, sku write-back had failed).
- **Rental fan** → relinked to its own **PD 1210** (resolved by *name* — code was ambiguous), code set to `HG-FVV-080-002`. Base fan keeps **PD 195** / `…-001`.

**Findings:**
- The rental fan already had its own PD product (1210); the Quoter sku wrongly pointed at the base (195). Checking PD *before* acting prevented creating a duplicate — validates "reconcile by match, heal don't duplicate."
- **Code is not reliably unique** (PD 195 & 1210 shared `HG-FVV-080-001`) → code-as-key is ambiguous unless uniqueness is enforced; name disambiguated.
- **Supplier SKU is editable on the Quoter item form** and **copied on item duplication** → fumble/copy risk confirmed. It's hidden from the list view + search index, so such damage is invisible.
- Corrected the earlier hardcoded `412` → now **derived** dynamically via `pipedrive_v2`.

**Remaining cleanup:** delete old nitrogen regulator (`CNF-NIT-REG`, PD 794) in the Quoter UI; item `EQP-NTR-001` keeps 794.

---

## 2026-07-24 — First v2 code brick: ScalePad items wrapper (built, tested, live-verified) ✅

**Did:** Added `scalepad_items.py` — a ScalePad v2 resource wrapper (`list_items` with `record_updated_at` incremental filter + cursor pagination, `iter_all_items`, `get_item`, `create_item`, `update_item`, `list/get categories`) built on the existing `ScalePadV2Client`. **Additive only — no existing production code touched** (`quoter.py`, `pipedrive.py`, `quoter_to_qbo_sync.py` unchanged).

**Tested:**
- Unit tests `test_files/test_scalepad_items_v2.py` — **8/8 passing** (paths, incremental filter param, page-size cap, cursor follow-through, create/update bodies, category paths). No network/key needed.
- Live **read-only** smoke test (`python scalepad_items.py`) run by Eric — **success**.

**Evidence / findings from the live read:**
- `list_items` returned `total_count = 298`, `next_cursor = yes` → pagination works against the real catalog.
- Sample item: `id=item_2zvQahvtdYRKfPz3av3B5Ife2nm`, `name="Horizon Managed Services"`, `code="MGS"`, `sku="407"`, `category="Service"`, `price_decimal="101"`, `record_updated_at="2025-09-06T21:18:11Z"`.
- **Confirmed: the `sku` field holds a Pipedrive product ID** (`sku="407"`), i.e. the linkage hijack is real → must choose a cleaner PD-ID home before writing items via v2. (Open item.)
- `record_updated_at` is populated → incremental sync (`filter[record_updated_at]=gt:`) is viable.
- IDs are opaque strings (`item_…`) → no numeric-ID assumptions.

**Impact:** none to production. First verified building block of the item-service migration (plan step 2).

**Next brick (read-only, no writes):** a small `iter_all_items(updated_since=…)` loop that reports "N items changed since <date>" — watch the incremental sync work on real data before touching any write path.

---

## Through 2026-07-24 — Investigation & planning (foundation) ✅

Grouped summary of the work that got us to the first code brick:

- ✅ **Products/Items as-built** documented and code-verified (`AS_BUILT_SECTION_3_PRODUCTS_ITEMS.md/.docx`). Corrected the architecture to the **fan-out + SyncQ-reconcile triangle** (Quoter = source of truth).
- ✅ **SyncQ mapping verified** from the dashboard (`LQ-7604` Products→Item); confirmed SyncQ maps **no income/expense accounts** — the reason the custom code/fan-out exists.
- ✅ **ScalePad v2 researched** from OpenAPI: full item/category CRUD, incremental (`record_updated_at`+cursor), **no webhooks**, opaque string IDs, richer model. → item domain builds on v2, scheduled.
- ✅ **Pipedrive v1→v2 researched**: Products/Orgs/Persons/Deals/Fields/Search are **GA v2 (not beta)**; custom fields move to a nested `custom_fields` object; cursor pagination; `updated_since`; structured org address; Webhooks v2. **No announced v1 sunset** (only the unrelated Channels API) → no deadline; migrate opportunistically with the refactor.
- ✅ **Migration plan** written (`QUOTER_V1_TO_V2_MIGRATION_PLAN.md`) + **Products-first brief** (`API_V1_V2_SUMMARY_FOR_PRODUCTS.md`).
- ⏳ **Quote creation on v2** blocked by ScalePad `client_id` (Lifecycle Manager) dependency; ScalePad shipping a **Client-name fix** (~this week). Quote-flow migration waits on it.
- ⏳ **SyncQ** improvement reply awaited.
- 🅿️ **Parked:** template Item-Groups mirror (not entitled on Standard plan), admin-UI/GraphQL scraping (undocumented, session-locked), Pipedrive Projects API (unused).

---

## Current status snapshot

- **Buildable now (no blockers):** shared-module refactor; ScalePad v2 item/category wrappers (started ✅); read-only incremental item loop.
- **Waiting on vendors:** ScalePad Client-name fix (unblocks quote creation + supported template read); SyncQ roadmap reply.
- **Do last / carefully:** quote-flow Pipedrive calls (Deals/Orgs/webhooks) — live sales path.
- **Immediate next step:** read-only `iter_all_items(updated_since=…)` loop to demonstrate incremental sync on real data.
