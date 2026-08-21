# Quoter Legacy (v1) → ScalePad (v2) — Migration Plan

**Purpose:** Decide whether, and how, to move the TLC quote-to-pipeline integration off the legacy Quoter API (`api.quoter.com/v1`) and onto the ScalePad v2 API (`api.scalepad.com/quoter/v1`). Written to answer four questions: what we run on v1 today, what v2 makes possible, whether we still need v1, and what it takes to implement v2.

**Status:** Planning draft.

> **Confidence tags:** **[v2-docs]** = verified from the current ScalePad OpenAPI (fetched this session). **[code]** = verified in the repo. **[verify-live]** = must be confirmed against the live API with a working key before relying on it. **[open]** = unresolved question.

---

## 1. What we have built on legacy (v1) today

Auth: **OAuth client-credentials** → `POST /v1/auth/oauth/authorize` → bearer token. **[code]**
Client: `quoter.py` (feature-rich, ~93 KB) + `scalepad_v2.py` (thin transport shell, unused for real work). **[code]**

Legacy endpoints in active use **[code]**:

| Area | Legacy endpoint | Used by |
|---|---|---|
| Items | `GET/PATCH /v1/items`, `/v1/items/{id}` | item sync, `update_quoter_sku` |
| Categories | `GET /v1/categories/{id}` | `category_manager.py` |
| Quotes | `POST/GET /v1/quotes`, `/v1/quotes/{id}` | quote creation |
| Line items | `POST /v1/line_items` | quote build |
| Templates | `GET /v1/quote_templates` | quote build |
| Contacts | `POST /v1/contacts` | quote build |

What the system does with these (from the Section 3 as-built):
- **Item sync (the triangle):** Quoter is source of truth; `sync_with_date_filter.py`→`pipedrive.py` seeds Pipedrive (A/B/C logic, four custom fields, Sync=Yes); `quoter_to_qbo_sync.py` create-only-seeds QBO; **SyncQ** reconciles PD↔QBO (no account refs). **[code]**
- **Quote automation:** `webhook_handler.py` (Render) creates draft quotes from Pipedrive org events and updates PD deals on Quoter quote-published events. **[code]**
- **Key linkage hack:** the Pipedrive product ID is stored back into the Quoter item's **`sku`** field. **[code]**

Known debt (Section 3.8): `Type` hardcoded to Service, income account hardcoded to 389, name-similarity matching in the QBO sync, two-cooks drift, create-only QBO path. **[code]**

`DECISIONS.md` D-001 keeps legacy alive **specifically because draft-quote creation wasn't available on ScalePad.** That premise is the crux of Section 3 below.

---

## 2. What v2 enables if rewritten

Base `https://api.scalepad.com/quoter/v1`; auth **`x-api-key`** header. **[v2-docs]**

1. **Full item + category CRUD.** `POST/GET/PATCH/DELETE /v1/items` and `/v1/categories`, plus Item Groups, Item Options, Item Tiers, Manufacturers, Suppliers, Data Feed Suppliers. The catalog is a first-class, fully-managed resource — not the read-mostly surface v1 gave us. **[v2-docs]**
2. **Clean incremental sync.** `GET /v1/items?filter[record_updated_at]=gt:{ISO}&sort=+record_updated_at&page_size=200` + `next_cursor` (base64) pagination (page size ≤ 200). Replaces the legacy dual `created_at[gt]`/`modified_at[gt]` fetch-and-dedupe. Also filterable by `category_id`, `manufacturer_id`, `supplier_id`, `code`, `sku`, `name`. **[v2-docs]**
3. **Richer, cleaner item model.** Required to create: only `category_id` + `name`. Distinct `code` (MPN) vs `sku` (inventory). First-class `cost_decimal`/`cost_type`, `pricing_scheme` (per_unit/flat/tiered_volume/tiered_stepped/percentage), `taxable`, `recurring`/`recurring_interval`, `manufacturer`/`supplier`, plus read-only `id`, `record_created_at`, `record_updated_at`. **[v2-docs]**
4. **Opaque string IDs everywhere** (`item_…`, `cat_…`, `manu_…`, `sup_…`). Permanently retires the "numeric vs long-string ID drift" fragility — nothing is numeric on v2. **[v2-docs]**
5. **Draft quote creation** (see Section 3). **[v2-docs]**
6. **Simpler auth** — one API key vs the OAuth client-credentials dance. **[v2-docs]**

Practical upshot: an item service on v2 is simpler than today's — fewer moving parts, a real incremental cursor, and a clean data model. `scalepad_v2.py` grows the resource wrappers (D-004).

---

## 3. Do we still need v1?

### 3.1 The draft-quote question — endpoint exists, but is BLOCKED for us today
**v2 has a Create Quote endpoint, but it is not usable by TLC right now.** `POST /quoter/v1/quotes` creates a draft from a template, with the contact identified by `client_id` + `email`, cover-page fields, `custom_number`, `currency_iso`, `expired_at`, `owner`, `tax_codes`; sections and line items are added via their own endpoints and `Publish Quote` finalizes it. **[v2-docs]**

**The blocker:** the required `contact.client_id` is a **ScalePad Client UUID that originates in Lifecycle Manager** (a separate ScalePad product). TLC has **no Lifecycle Manager integration**, so there are no client IDs to supply and the create call fails. ScalePad confirmed this directly (Jon Turner, ScalePad Support, email): *"there are no client IDs to retrieve and the Quotes cannot be created… a significant limitation."* **[email]**

**Fix in progress:** ScalePad is updating the API (target: week of ~Jul 21, 2026) to accept the **Quoter Client name** instead of the ScalePad Client ID, which would bypass the Lifecycle Manager dependency. **[email]**

**Conclusion (corrects an earlier draft of this plan):** the D-001 rationale still holds — **legacy remains required for quote creation** until the client-name update ships and is verified. This is a different, narrower blocker than "v2 has no quote API," but the practical effect is the same today.

### 3.2 Everything else the code uses has a v2 equivalent
Items, categories, contacts, quotes, line items, and templates all exist on v2. **[v2-docs]** So on paper, v2 covers the full set of legacy endpoints the integration calls today.

### 3.3 What must be verified before trusting parity **[verify-live]**
- **Draft-quote field parity:** does the v2 quote/section/line-item chain reproduce what `create_comprehensive_quote_from_pipedrive` builds today (cover letter content, custom numbering, template seeding of line items, PDF/attachment behavior)?
- **Contact matching:** v2 keys contacts by `client_id`+`email`; confirm this matches how we resolve Pipedrive people today (labeled phones, dummy-email fallback).
- **Publish semantics & quote numbering:** confirm `Publish Quote` assigns numbers the way the current flow expects.

### 3.4 The real remaining v1/legacy dependency — events **[open]**
The v2 REST API has **no webhooks or events endpoints anywhere** (verified across the entire ScalePad index). But the live system is triggered by two webhooks: a **Pipedrive** org webhook (unaffected — Pipedrive side) and a **Quoter quote-published** webhook that updates the PD deal. **[code]**

Open question: is that Quoter quote-published webhook a *platform* feature (configured in Quoter settings, independent of which REST API version we call) or tied to legacy? If platform-level, it keeps working regardless and v2 migration is unaffected. If not, we need an alternative trigger (e.g. polling quote status, or the native Pipedrive integration). **This is the one thing that could force us to retain a legacy/native piece — resolve it early.**

### 3.5 Verdict
For **items and categories**, v2 can replace v1 today. For **quote creation**, **legacy is still required** until the client-name fix (3.1) ships and is verified. Residual dependencies to watch: the Lifecycle Manager `client_id` fix (3.1), event delivery (3.4), and field-level parity (3.3). Net: **migrate the item domain to v2 now; keep legacy for quote creation** until 3.1 is resolved.

### 3.6 Template line items & Item Groups — supported ground vs. workaround
Goal: eliminate the ~200-lines-per-template hard-coded definitions (`template_mapping_enhanced.py`, the `BUNDLE_VERIFICATION_SYSTEM`) and let Quoter Templates be the single source of truth.

Two findings shape this:
- **Template resource exposes no line items directly — but the create-from-template path does.** The v2 `List Quote Templates` returns only `id`, `slug`, `title`, timestamps, and there is no template-detail endpoint. **[v2-docs]** The identified supported mechanism to read a template's contents: **`POST /quoter/v1/quotes` with `template_id` to create a draft, then `GET /quoter/v1/quotes/{id}` to fetch it and read `sections[].line_items[]`** — fields `name`, `code`, `sku`, `category`, `unit_price_decimal`, **`quantity_decimal`**, `description`. This is probed by `test_files/test_template_seeds_lineitems.py`. **[code]** Because it returns **quantities and full line-item detail**, it is strictly better than an Item Group mirror (which cannot carry quantities/structure). **Critically it is gated on the same `client_id` blocker (3.1)** — the probe quote can't be created without a Client UUID — so it can only run once the Client-name fix ships. **Empirical result pending [confirm]:** whether a fetched draft actually returns seeded line items has not been confirmed to run (create is blocked by `client_id`).
- **Item Groups are not entitled on our plan.** ScalePad states Item Groups are an **Enterprise / multi-tenant** feature; TLC is on a **Standard plan** that "doesn't actually support these currently." The API mechanically allowed create/retrieve/assign, but that is not the same as supported entitlement. **[email]** Building the template-mirror on Item Groups is therefore high-risk: it can be gated or changed without notice, and an Item Group (a catalog grouping) may not even represent template structure/quantities faithfully.

**Recommendation:** the **create-from-template → fetch** path (above) is the preferred supported mechanism — it needs no Enterprise entitlement and carries quantities. So do **not** build the template mirror on Item Groups (unentitled on Standard), and do **not** adopt web-scraping of the Quoter admin payload (unsupported, breaks on any UI change, contrary to the "don't automate the web UI" goal). Sequence: (a) once the Client-name fix (3.1) ships, run `test_template_seeds_lineitems.py` to confirm the draft returns seeded line items; (b) if confirmed, retire the hard-coded definitions in favor of create-throwaway-draft → fetch → read line items (and delete the draft); (c) until then, keep the hard-coded definitions but treat them as a **monitored cache** — let bundle verification flag drift so maintenance is "confirm a change," not "hand-maintain 200 lines." The Item Group work already validated can be shelved rather than extended.

---

## 4. What we need to implement v2

### 4.1 Prerequisites
- **Working `SCALEPAD_API_KEY`** (env var already referenced in `scalepad_v2.py`) with items/quotes scope. **[code]**
- **SyncQ's pending reply** on PD↔QBO product/item improvements — may shrink the custom QBO work.
- **Linkage decision (blocking):** stop hijacking `sku` for the Pipedrive product ID. Options: a dedicated custom/reference field, `internal_note`, or an external mapping table keyed on the v2 `item_…` id. Decide before building. **[open]**

### 4.2 Build steps
1. **Grow `scalepad_v2.py` resource wrappers** (D-003/D-004): `items`, `categories`, `contacts`, `quotes`, `quote_sections`, `line_items`, `templates` — thin methods over the generic client.
2. **Shared-library refactor:** extract pure modules (`quoter`/`scalepad`, `pipedrive`, `qbo`, `category`) with no work-on-import, so both the quote service and the item service call the same core.
3. **Stand up the item service** (per the agenda's "second mothership"): scheduled/polling on v2 (`filter[record_updated_at]`), a single batch entry point (fold the two cooks), plus a thin manual-trigger endpoint. Render **cron job** (paid plan, always-on) rather than an internal timer.
4. **Fold in the Section 3.8 fixes** during the rewrite: correct `Type`, drive accounts from config/chart-of-accounts (not hardcoded 389), replace name-matching with durable IDs.
5. **Address the account gap** (SyncQ maps no `IncomeAccountRef`/`ExpenseAccountRef`): decide whether the item service sets accounts on the QBO side directly, or the chart-of-accounts mapping project handles it.

### 4.3 Migration approach (incremental — D-005)
- Run v2 **read-only alongside** legacy first: list items via v2, diff against legacy output, confirm the data matches.
- Migrate **item sync** to v2 (lower risk, clear incremental cursor), verify the triangle still completes.
- Then migrate **quote creation** to v2, gated on the 3.3 parity tests and the 3.4 event question.
- Retire legacy `quoter.py` paths only after each equivalent is verified in production (D-005). Keep `quoter.py` until then.

### 4.4 Test plan
- Wrapper unit tests against recorded v2 responses.
- A dry-run/read-only mode (fix the current always-live `main()`).
- End-to-end: create a test item in Quoter → v2 list picks it up → PD product created → SyncQ completes QBO → verify all three records.
- Draft-quote smoke test: create → add section → add line items → publish → confirm against a known-good legacy quote.

---

## 5. Open questions to resolve

1. **[open]** Is the Quoter quote-published webhook platform-level or legacy-tied? (Section 3.4 — resolve first.)
2. **[open]** Where does the Pipedrive-product-ID linkage live post-`sku`? (Section 4.1.)
3. **[verify-live]** Draft-quote field parity and publish/numbering behavior (Section 3.3).
4. **[open]** SyncQ's roadmap reply — does it change the QBO account-population responsibility?
5. **[open]** Does v2 expose the same category hierarchy (`parent_category`) `category_manager.py` relies on? (Confirm via `List/Fetch Category`.)
6. **[open]** Timeline for the Client-name fix that unblocks v2 quote creation (3.1) — resolve/track; it gates the quote-side migration.
7. **[verify-live]** What is the supported mechanism by which template line items are read? (3.6 — document it.)
8. **[open]** Is Standard-plan Item Group API use supported and durable, or a loophole that will close? (3.6.)

---

## 6. Recommendation

Proceed with a **phased migration to v2**, not a rewrite-in-place. Order: shared-module refactor → v2 item wrappers → item service (scheduled) → **quote-creation migration only after the Client-name fix ships and is verified (3.1)**. The item domain can move now; quote creation stays on legacy until ScalePad removes the Lifecycle Manager `client_id` dependency. Do **not** build the template layer on Item Groups (unentitled on Standard, 3.6) or on web-scraping; keep the hard-coded definitions as a monitored cache until a supported template line-item mechanism is confirmed. Keep legacy running until each piece is verified live.

---

## 7. Related migration: Pipedrive API v1 → v2

This is a **separate vendor migration** from the Quoter/ScalePad one, but it touches the same files, so it's folded into the same phased work rather than run as its own project.

**Urgency: none.** Pipedrive's official changelog shows **no blanket v1 sunset** — they are still actively *expanding* v2 (Projects API v2 landed May 2026; Fields API v2 Dec 2025). The only deprecation announced is the **Channels API** (Feb 2026), which we don't use. The dev-community "v1 discontinued this summer" claim is **uncorroborated** and appears to concern Make's modules, not the Pipedrive API. Official policy: deprecated v1 endpoints get **≥1 year** grace. **[verified — Pipedrive changelog + v2 overview]** (Subscribe to the changelog for the definitive signal.)

**Where our integration touches Pipedrive (all in scope, none blocking):**
- **Quote flow** (`webhook_handler.py`): inbound **Pipedrive org webhook** triggers quote creation; reads via `get_deal_by_id`/`get_organization_by_name`; writes via `update_deal_with_quote_info` (Deal) and `update_organization_address` (Organization). **[code]**
- **Item service** (`pipedrive.py`): creates/updates PD **Products** with the four custom fields + Sync trigger. **[code]**

**Key v1→v2 changes that hit the code:**
1. **Custom fields nest into a `custom_fields` object** (was top-level 40-char hash keys). Affects product writes (`9c63…`, `b654…`, `98ec…`) *and* any deal/org custom-field access. This is the biggest single change and is the through-line with the ScalePad work.
2. **Cursor pagination** replaces `start`/`limit` offset (limit up to 500).
3. **Incremental filter** `updated_since`/`updated_until` (RFC3339) — cleaner reads.
4. **Organization address is a structured object** in v2 (`address.value`, `.locality`, `.postal_code`, …) — directly affects `update_organization_address`.
5. **Webhooks v2** — the inbound org webhook migrates (separate Webhooks v2 guide).
6. Lower rate-limit cost + better performance + stricter validation.

**Note:** v2 is better *plumbing*, not a native Quoter↔PD bridge — the push pattern is unchanged.

**Plan:** migrate Pipedrive calls to v2 **opportunistically, as part of the shared-module refactor** — when `pipedrive.py` and `webhook_handler.py` are refactored into shared modules, point them at `/api/v2/…`, move custom-field access into `custom_fields`, adopt cursor pagination, and update the address write. No deadline; v1 keeps working meanwhile. Track the changelog in case a firm v1 date is ever announced.

---

## 8. Linkage integrity — findings & guardrails (from the live catalog audit)

The Quoter↔PD link is stored in the Quoter item's **Supplier SKU** (= PD product id). Auditing the live 297-item catalog and doing the first repairs surfaced how fragile that field is and what the sync/reconcile must do about it. **[code + live-verified]**

**Confirmed facts:**
- **Non-atomic write-back.** The link is set in two steps — create the PD product, then PATCH its id into Quoter. A failure between them leaves a PD product with **no Quoter link** (e.g. FVV-MasterBox: PD 412 existed, sku was empty).
- **The Supplier SKU field is user-editable on the item form AND copied on item duplication** — so it can be fumbled, cleared, or duplicated by normal use. It's hidden from the list view and search index, so such damage is **invisible** to users.
- **Code is not reliably unique** (base + rental fan both `HG-FVV-080-001`) — so `code` alone can't disambiguate; **name** can. Code-as-key requires enforcing uniqueness.
- The only **copy-proof, immutable** key is the Quoter item **`id`** (`item_…`).

**Clear-vs-keep rule** (when the sync sees an item with Supplier SKU `S`):
- **Keep → update** iff `S` is numeric, resolves to a live PD product, and is claimed by exactly one item.
- **Clear → create** if `S` is empty, non-numeric, or dangling (404 in PD).
- **Flag (don't auto-resolve)** if `S` is shared by >1 item (copy collision) — a human/rule picks the owner; the losers are re-created.

**Heal-don't-duplicate reconcile rule:** for an item with a missing/questionable sku, **match an existing PD product by name/code before creating**. If a match exists, relink (write its id); only create when no match exists. **Derive the id, never hardcode** (this prevented a duplicate on the rental fan — its product 1210 already existed).

**Toolkit built to support this** (all additive, unit-tested, no running-sync code touched): `pipedrive_v2.py`, `scalepad_items.py`, `scalepad_items_maint.py`, `link_item_by_code.py`, `relink_item_by_name.py`.

**Recommendation (reaffirmed):** because the linkage field is user-editable and copy-propagated, either enforce the guardrails above in the reconcile pass, **or move the linkage to an `id`-keyed external map** (immune to fumble/copy/clear). Guardrails are the minimum; the map is the durable fix.

**Data-integrity cleanups found** (fix in Quoter; two already done):
- ✅ FVV-MasterBox → linked to PD 412.
- ✅ Rental fan → relinked to PD 1210, recoded `…-002`.
- ⬜ Old nitrogen regulator `CNF-NIT-REG` (PD 794) → delete in UI; `EQP-NTR-001` keeps 794.
