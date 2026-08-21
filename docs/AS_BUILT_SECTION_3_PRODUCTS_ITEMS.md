# TLC Quote-to-Pipeline — As-Built

## Section 3: Products / Items Flow

**Owner:** Eric Grosshans (TLC Creative)
**Scope:** Item/product creation and its synchronization across Quoter, QuickBooks Online (QBO), and Pipedrive (PD).
**Status of this document:** Draft for review.
**Stack:** Pipedrive, QuickBooks Online, Quoter/ScalePad, SyncQ, Render.

> **How to read the confidence tags in this section.** Every material claim is tagged:
> - **[code]** — verified directly in the current repository source (`/quoter_sync` root-level files).
> - **[doc]** — stated in the project's own docs or the official ScalePad/Quoter documentation.
> - **[ops]** — operational knowledge from the team; **not** currently evidenced in code or docs and flagged for confirmation.
> - **[confirm: SyncQ]** — depends on SyncQ dashboard configuration, which lives outside the repo and could not be inspected.

---

### 3.1 Source-of-truth principle

**Quoter is the source of truth for items.** Item content (name, code/SKU, category, unit price, description, cost) is authored in Quoter. QBO items and Pipedrive products are downstream representations of that Quoter item. **[doc]** (`README.md`, "Quoter should be the source of truth"; `products_quoter_pipedrive_analysis.md`.)

The reason PD cannot be the master is structural: a CRM has no place to hold the income/expense account references QBO requires on every item. Those accounts only exist in QBO. **[doc/ops]**

#### 3.1.1 Catalog origin — Goodshuffle migration (one-time) **[ops]**

Goodshuffle is the **legacy quoting system being replaced by Quoter**. The Quoter item catalog was seeded by a one-time migration: all Goodshuffle quotes were exported, their line items extracted and sorted, then de-duplicated and consolidated into a complete inventory of **equipment, services, and fees**, which was loaded into Quoter as items. `csv_files/csv_analysis.py` is a support utility from this migration — it QA's the cleaned export (`Cleaned_Goodshuffle_Line_Items - Sheet1.csv`) by checking the three Quoter-import required fields (`*Item Name`, `*Category`, `*USD Price`) for completeness and flagging duplicate item names before import. **[code + ops]**

This is **historical, one-time seeding**, not an ongoing intake path — new items are now authored directly in Quoter. Goodshuffle is being retired. It also relates to the CSV-era workflow that `docs/QBO_INTEGRATION_SETUP.md` describes as "problematic" (CSV export → manual import); that manual path has since been superseded by the sync mechanisms in §3.3. **[doc]**

---

### 3.2 Architecture: a triangle, not a chain

The earlier framing of a single one-way chain (Quoter → QBO → PD) is **not** the as-built. The real topology is a **fan-out from Quoter followed by SyncQ reconciliation** — a triangle:

```
                         Quoter  (source of truth)
                        /        \
        (seeds QBO)    /          \   (seeds PD: 4 custom fields + Sync=Yes)
                      v            v
              QuickBooks  <------>  Pipedrive
                          SyncQ
                     (bidirectional reconcile)
```

Neither Quoter-out leg produces a *complete* record on its own. Quoter seeds QBO with a certain subset of fields and seeds PD with a different subset; **SyncQ, running bidirectionally, brings both sides into full synchronization** — completing both the PD product and the QBO item. **[code + doc + ops]**

Why the fan-out is necessary today: **SyncQ transfers only partial data across the QBO↔PD boundary in each direction.** Quoter therefore has to seed PD directly with the fields SyncQ will not reliably carry from QBO (and seed QBO with what it needs), and SyncQ then reconciles the rest. If SyncQ's QBO→PD direction ever became complete, the direct Quoter→PD sync could be retired. **[ops]** (Consistent with `DECISIONS.md` D-005, incremental migration.)

---

### 3.3 The four mechanisms that create/populate items

There are **four** distinct mechanisms. Understanding *which fires when* is the core of this section.

#### (A) Native Quoter↔QBO integration — quote-triggered, incidental
The official ScalePad/Quoter QBO integration is a **quote-to-estimate** integration, not a catalog integration. When a Quoter Quote is created, it automatically creates a QuickBooks **Estimate including its line items**; if a referenced item does not already exist in QBO, it is created at that point. It also matches customers and can pull existing QBO products into quotes via Product Search. **[doc]** (Official ScalePad article "Integrating with QuickBooks Online.")

**Shortcoming that drove the custom code:** an item reaches QBO through this path **only if it lands on a quote**, and only to the extent the estimate requires. Items authored in Quoter but never quoted never appear in QBO by this route. The internal note in `docs/QBO_INTEGRATION_SETUP.md` claiming "Automatic item sync from Quoter to QBO" **overstates** what the native integration actually does — it is estimate-level, not catalog-level. **[doc]**

> Because this mechanism is quote-driven, its *primary* documentation home is Section 4 (Quote Building). It is included here only to explain the gap the item-sync code fills.

#### (B) `quoter_to_qbo_sync.py` — catalog completion, create-only
Purpose: guarantee that **every** Quoter item has a matching QBO item, whether or not it has ever been quoted. This is the answer to "we added a new item in Quoter without writing a quote" — the native link never fires in that case, so this script is the only path that gets the item into QBO (and, via SyncQ, into PD). **[code + ops]**

Verified behavior **[code]** (`quoter_to_qbo_sync.py`):
- Runs as the daily batch's Step 2 (see 3.6).
- Fetches Quoter items (with category hierarchy) and existing QBO items.
- Matches Quoter→QBO **by item name similarity** (not by SKU), using a scored matcher.
- **Creates only the unmatched items.** Matched (already-existing) items are skipped — no update is pushed.
- This "create-only" behavior is **by design**: updates to already-quoted/synced items flow through the native link and SyncQ, so this script deliberately only fills the net-new gap.

#### (C) `sync_with_date_filter.py` → `pipedrive.py` — Quoter → Pipedrive
Purpose: seed the PD product directly with the descriptive/commercial fields plus the four control fields, because SyncQ's QBO→PD direction only carries partial data. **[code + ops]**

Verified behavior **[code]** (`sync_with_date_filter.py`, `pipedrive.py`, `category_manager.py`):
- Date-filtered: syncs Quoter items created/modified since `last_sync_date.txt` (defaults to 7 days back if absent).
- Uses **A/B/C logic** to decide create vs. update (see 3.5).
- Writes the four PD custom fields and sets **Sync-to-QuickBooks = Yes** (the SyncQ trigger).
- Writes the resulting **PD product ID back into the Quoter item's `sku` field** — this becomes the durable linkage between the Quoter item and the PD product on subsequent runs.

#### (D) SyncQ — bidirectional PD↔QBO reconciliation
Purpose: the external SaaS that reconciles Pipedrive products and QBO items in **both** directions, completing whatever each Quoter-out leg left partial. **[doc + confirm: SyncQ]**
- PD → QBO: SyncQ pushes Pipedrive products into QBO items. **[doc]** (`docs/QBO_SYNC_ERROR_FIX.md`: "the error occurs when SyncQ tries to sync Pipedrive products to QuickBooks Online.")
- QBO → PD: SyncQ writes back into PD — most importantly the **QuickBooks ID** custom field on the PD product (blank at creation, filled by SyncQ once QBO mints the item). **[doc/confirm: SyncQ]** (`docs/QBO_INTEGRATION_SETUP.md` "New Workflow": "SyncQ detects QBO items → Syncs all items to Pipedrive.")
- Trigger: SyncQ acts on a PD product once its **Sync-to-QuickBooks** field is set to **Yes** (option 83).

---

### 3.4 Field mappings

#### 3.4.1 Quoter item → QBO item (via `quoter_to_qbo_sync.py`) **[code]**

| Quoter field | QBO field | Notes |
|---|---|---|
| `name` | `Name` | Also the matching key (name similarity) |
| `code` | `Sku` | |
| `price_decimal` | `UnitPrice` | cast to float |
| `description` | `Description` | HTML-stripped; fallback "Imported from Quoter: {name}" |
| — | `IncomeAccountRef.value = "389"` | **Hardcoded** (Rental Income) — see risks |
| — | `Type = "Service"` | **Hardcoded for all items** — see risks |
| — | `Active = true`, `TrackQtyOnHand = false`, `PurchaseCost = 0` | |

Category hierarchy (`Parent:Child`) is computed for matching/display but **not** written to QBO — items are created flat. **[code]**

#### 3.4.2 Quoter item → Pipedrive product (via `pipedrive.py`) **[code]**

Standard fields: `name`, `code`, `description`, `price` (nested under `prices`), `cost`, plus category and subcategory (below).

Custom fields written:

| Field | PD custom field key | Value logic |
|---|---|---|
| CatSub (QBO Category:Subcategory) | `9c636133839b978b686bbc952fbd5dc41d5cd087` | `"Category:Subcategory"` |
| QBO Item Type | `b65439db55a0f1d772dc1570c8818f3b8a188b25` | Service **74** if code starts `SVC`, else NonInventory **71** |
| Product / Service | `b82ad04a30171b69c4649e6f66f956ade0a51886` | Service **248** / NonInventory **435** (same rule) |
| Sync to QuickBooks | `98ec4970ff4f9f9cc17926d27675eee823a4eb86` | Yes = **83** (the SyncQ trigger) |
| Subcategory (text) | `ae55145d60840de457ff9e785eba68f0b39ab777` | subcategory name |
| QuickBooks ID : SyncQ | `1213a9ae4c45178ff7c81bde38c3cdfbdc71bbd4` | **Read, not written** — populated later by SyncQ |

Category mapping is done with **live API lookups** (no hardcoded map): Quoter `category_id` → Quoter `/v1/categories/{id}` → `parent_category` → `"Parent / Child"`, then split and mapped to the PD Category option ID and Subcategory field. **[code]** (`category_manager.py`.)

#### 3.4.3 Pipedrive product → QBO item (via SyncQ) **[SyncQ dashboard — verified]**

Confirmed from the SyncQ dashboard (SyncQ – Pipedrive QuickBooks Automation, account **TLC Creative Special Effects**). SyncQ's object mapping **LQ-7604** maps Pipedrive **Products → QuickBooks Item** with the following field mappings:

| Map ID | Pipedrive Product field (type) | QuickBooks Item field (type) |
|---|---|---|
| LQB-41342 | Name (VARCHAR) | Name (STRING) |
| LQB-41343 | Price (DOUBLE) | UnitPrice (DECIMAL) |
| LQB-42387 | Description (TEXT) | Description (STRING) |
| LQB-42405 | QuickBooks Item Type (ENUM) | Type (ITEMTYPEENUM — **required**) |
| LQB-42406 | Product code (VARCHAR) | Sku (STRING) |
| LQB-42410 | Tech-Specs (TEXT) | PurchaseDesc (STRING) |
| LQB-44918 | Category (ENUM) | ItemCategoryType (STRING) |

**Key finding — accounts are NOT mapped by SyncQ.** There is no `IncomeAccountRef` or `ExpenseAccountRef` in this mapping. This matches `README.md`'s guidance to "avoid SyncQ for account reference fields due to format limitations." Consequence: SyncQ can create/update the descriptive shell of a QBO item but **cannot set the income/expense accounts** QBO requires. That gap is exactly why the accounts must be set by the native link or by `quoter_to_qbo_sync.py` (which hardcodes income account 389). This is the concrete "partial data" limitation that justifies the whole fan-out topology in §3.2. **[SyncQ dashboard + doc]**

**The Type loop closes here.** The `QuickBooks Item Type` PD custom field written by `pipedrive.py` (`b65439db…`, Service 74 / NonInventory 71) is exactly the field SyncQ reads (LQB-42405) to populate QBO's required `Type`. So the Quoter→PD write and the PD→QBO reconcile connect through that custom field. **[code + SyncQ dashboard]**

Corrections to the earlier reconstruction: the `QBO_SYNC_ERROR_FIX.md` guess of `PurchaseCost ← cost` is **not** in the live mapping (no cost mapping exists); instead `Tech-Specs → PurchaseDesc` and `Category → ItemCategoryType` are present.

Payload constraints (from `docs/QBO_SYNC_ERROR_FIX.md`, still valid): PD `unit` must be a QBO-standard value (e.g. "each"), and Pipedrive-only fields (`tax`, `visible_to`) must be stripped or QBO rejects the payload with "failed to parse json object." **[doc]**

Sibling object mappings in the same SyncQ config: **LQ-7780** Organization ↔ Customer (Section 1) and **LQ-7781** Deals ↔ Invoice (Section 4). **[SyncQ dashboard]**

---

### 3.5 Create-vs-update logic (A/B/C) and the Sync ordering **[code]**

`pipedrive.py` decides what to do with each Quoter item based on its `sku` field:

- **A — Quoter `sku` present:** treat `sku` as the PD product ID, look it up directly, and **update** it.
- **B — no `sku`, name matches an existing PD product that already has a QuickBooks ID:** that product originated from QBO via SyncQ — **update** it (do not duplicate), and write the PD ID back to Quoter's `sku`.
- **C — no `sku`, and no match (or a match without a QuickBooks ID):** **create** a new PD product and write its ID back to Quoter's `sku`.

**Sync-field ordering (race avoidance):** on the **update** path the three metadata fields are written first, then **Sync = Yes** is set in a *separate* second call, so SyncQ only wakes after the metadata is populated. **Inconsistency:** on the **create** path all four fields (including Sync = Yes) are sent in a *single* POST — SyncQ can therefore be triggered before the record is otherwise settled. **[code]** (See risks.)

**Two-step PD lookup:** because the PD `/products/search` endpoint omits custom fields, the code matches by name via search, then re-fetches the product by ID to read custom fields (e.g. the QuickBooks ID). **[code]**

---

### 3.6 Triggers and scheduling **[code]**

- **Daily batch — `.github/workflows/complete-sync.yml`**, cron `0 14 * * 1-6` (Mon–Sat, 2 PM UTC ≈ 6 AM Pacific):
  - Step 1: `sync_with_date_filter.py` (Quoter → Pipedrive).
  - Step 2: `quoter_to_qbo_sync.py` (Quoter → QBO), runs after Step 1.
  - Step 3: notification.
- **Real-time — `webhook_handler.py` on Render** handles **quotes and organizations only** (Pipedrive org → draft quote; Quoter quote-published → update PD deal). **It does not run item/product sync.** Item sync is daily-batch only. **[code]**
- SyncQ runs continuously/independently against PD products flagged Sync = Yes. **[doc]**

---

### 3.7 Key identifiers and linkage

- **Quoter `sku` field = Pipedrive product ID.** This is the verified, durable link between a Quoter item and its PD product, written back by `pipedrive.py` after first sync. **[code]**
- **QuickBooks ID** on the PD product (`1213a9ae…`) links the PD product to its QBO item; populated by SyncQ. **[doc/confirm: SyncQ]**
- **QBO ↔ Quoter items are matched by name.** **[code]**
- **`LQ-####` / `LQB-####` are SyncQ mapping IDs, not Quoter item codes.** `LQ-####` identifies a SyncQ **object mapping** (`LQ-7604` = Products→Item; `LQ-7780` = Organization→Customer; `LQ-7781` = Deals→Invoice). `LQB-####` identifies a **field-level** mapping inside an object mapping (e.g. LQB-42406 = Product code→Sku within LQ-7604). **[SyncQ dashboard — verified]**
- **Deal number** as the universal key operates primarily at the quote/organization level (Section 1 / Section 4), not on the item records themselves. **[ops]**

---

### 3.8 Known issues, risks, and fragilities

**Code-level (verified) [code]:**
1. **`Type` hardcoded to "Service"** in the active Quoter→QBO converter — the `SVC`-prefix branch is dead (both sides return "Service"). Non-inventory/inventory items are mislabeled in QBO. *Remediation: restore the code-prefix branch and map to the correct QBO Type.*
2. **Income account hardcoded to `389`** and **no `ExpenseAccountRef`** sent. This was a deliberate expedient: when the sync was first built, QBO account structure was not yet well understood and the priority was to ship a working pipeline. *Remediation is a project, not a one-line change:* it requires reviewing the QBO **chart of accounts** (and adding accounts where necessary), then building an item-category → income/expense-account mapping. **Critical constraint:** any such mapping change must be rolled out carefully so it does **not** break connectivity between the three applications (Quoter ↔ QBO ↔ Pipedrive) — a changed or invalid account reference can cause SyncQ posts to fail. Treat this as a scoped, tested change with a rollback path, not an in-place edit. As an interim step, at least drive the accounts from the documented `QBO_INCOME_ACCOUNT_ID` / `QBO_EXPENSE_ACCOUNT_ID` env vars instead of a literal.
3. **Dead duplicate `convert_quoter_to_qbo_item`** — a second definition (Inventory type, env-var accounts, no SKU) that matches the docs but is never called. *Remediation: delete the dead function to remove the doc/behavior contradiction.*
4. **QBO items created flat** — computed category hierarchy is never written. *Remediation: set `FullyQualifiedName` / parent reference if hierarchy is required in QBO.*
5. **Create-path sends Sync = Yes in one POST** (vs. the deferred two-step on the update path) — possible premature SyncQ trigger. *Remediation: defer Sync = Yes on create as well.*
6. **`main()` runs live (`dry_run=False`)** despite advertising a safe dry-run mode. *Remediation: gate live writes behind an explicit flag.*

**Operational (from the team; not evidenced in code — confirm) [ops]:**
7. **QBO item-ID drift** (newer IDs are long alphanumeric strings while older ones are numeric, breaking numeric-ID assumptions). *No numeric-ID assumption for QBO items was found in the current code; the only numeric-ID rule in the repo applies to Pipedrive **Deal** IDs. Confirm whether this still affects any live process.*
8. **SyncQ "Line is missing" race** and the **toggle Sync No→Yes** workaround. *The repo documents a "Required parameter Line is missing" error, but its documented cause/fix is removing optional phone/email mappings and it concerns the **customer/organization** sync (Section 1), not item sync. No "Sync No", "toggle", or reset option exists in the code. Confirm whether the item-side race/toggle is real and, if so, capture it.*
9. **QBO 3-custom-field API cap** (inactive fields still counting). *Not referenced anywhere in code or docs. Confirm and document if live.*

**Architectural (verified/ops):**
10. **SyncQ carries only partial data** across QBO↔PD, which is the reason the direct Quoter→PD sync exists. Retire that sync only after SyncQ's QBO→PD direction is proven complete. **[ops]**

---

### 3.9 Integration points with other sections

- **Section 1 (Customer/Org spine):** the QBO↔PD reconciliation via SyncQ is the same mechanism §1 relies on for customers/sub-customers; the "Line is missing" fix documented in-repo belongs to that customer path. The products path is **one-way out of Quoter** on the seeding legs; the customer path is bi-directional and Pipedrive-initiated.
- **Section 4 (Quote Building):** the item structure defined here is what quotes assemble. The **native Quoter→QBO estimate creation** is a §4 mechanism; it is referenced here only because it incidentally creates QBO items.
- **Section 7 (Monitoring/Fragilities):** the `DAILY_PRODUCT_ITEM_REPORT` cross-checks Quoter items against PD products (`Quoter sku = PD id`) and QBO items (by name) each day; item-sync fragilities (3.8) are tracked there.

---

### 3.10 Open items to close this section

1. Confirm the **native Quoter↔QBO integration is currently enabled** in the Quoter account.
2. Confirm/deny operational fragilities 7–9 (item-ID drift, item-side Sync toggle, 3-field cap).
3. **Scope the chart-of-accounts mapping project** (risk #2): review/extend the QBO chart of accounts and design a category→account mapping, with an explicit test-and-rollback plan to protect the three-way connectivity before any change to account references.
4. **Clarify potential Quoter→QBO overlap:** since SyncQ maps Products→Item (PD→QBO), determine whether `quoter_to_qbo_sync.py` still needs to create items directly, or whether its remaining unique job is purely setting the income/expense accounts SyncQ cannot. Decide which mechanism is authoritative for item creation to avoid double-creation.

**Resolved during review:**
- SyncQ PD→QBO field mapping confirmed from the SyncQ dashboard — see §3.4.3.
- `LQ-####` / `LQB-####` identified as SyncQ mapping IDs — see §3.7.
- Confirmed SyncQ does **not** map income/expense accounts — see §3.4.3.
