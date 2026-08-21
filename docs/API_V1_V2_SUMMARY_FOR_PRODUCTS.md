# API v1 → v2 — Summary & Plan for the Products/Items Work

**Purpose:** a self-contained brief for the Products/Items chat. Covers the two API migrations that affect products (Quoter/ScalePad and Pipedrive), what's ready, and the recommended order of work with rationale. You can act on this without the quote-chat context.

---

## The two API migrations in play

There are **two independent vendor API migrations**, and products sit in both:

1. **Quoter → ScalePad** — where item content is authored (source of truth).
2. **Pipedrive v1 → v2** — where products land for sales (and feed SyncQ → QBO).

They share one code foundation (`pipedrive.py`, the Quoter client, `category_manager.py`), so both are done as part of the same shared-module refactor rather than as separate projects.

---

### 1. Quoter / ScalePad (item catalog = source of truth)

| | Legacy Quoter API (v1) | ScalePad API (v2) |
|---|---|---|
| Base URL | `api.quoter.com/v1` | `api.scalepad.com/quoter/v1` |
| Auth | OAuth client-credentials → bearer | `x-api-key` header |
| Client in repo | `quoter.py` (in use) | `scalepad_v2.py` (thin shell) |
| Items | read + PATCH | **full CRUD** (create/list/fetch/update/delete) |
| Incremental | `created_at[gt]`/`modified_at[gt]` (dual fetch) | `filter[record_updated_at]=gt:…` + cursor |
| IDs | numeric + opaque mix | **opaque strings** (`item_…`, `cat_…`) |
| Webhooks | quote events only | **none** (poll/scheduled) |

**Status for products:** v2 item + category APIs are **ready and unblocked**. (The v2 *quote-creation* blocker — the Lifecycle Manager `client_id` issue — does **not** affect items; ignore it for products.)

**v2 item fields:** `name`, `code` (MPN), `sku` (inventory), `category`/`category_id`, `cost_decimal`/`cost_type`, `price_decimal`, `pricing_scheme`, `taxable`, `recurring`, `manufacturer`/`supplier`, `description`, `internal_note`, read-only `id`/`record_created_at`/`record_updated_at`. Only `category_id` + `name` are required to create.
**Note:** in v1 the code hijacks the item `sku` field to store the Pipedrive product ID. In v2, `code` and `sku` are distinct with real meaning — pick a cleaner place for the PD-ID linkage before building.

---

### 2. Pipedrive (where products land for sales, and feed SyncQ)

| | Pipedrive v1 | Pipedrive v2 |
|---|---|---|
| Base | `api.pipedrive.com/v1` | `api.pipedrive.com/api/v2` |
| Products | in use | **GA** (create/update/list/search/variations) |
| Custom fields | top-level 40-char hash keys | **nested `custom_fields` object** |
| Pagination | `start`/`limit` offset | **cursor** (limit ≤ 500) |
| Incremental | — | `updated_since`/`updated_until` (RFC3339) |
| Org address | flat fields | **structured object** (`address.value`, `.locality`, …) |
| Webhooks | v1 | **Webhooks v2** (separate migration) |

**Status:** the entities we use (Products, Organizations, Persons, Deals, Fields, Search) are **GA v2 — not beta.** There is **no announced v1 sunset** (only the unrelated Channels API is deprecated); the "discontinued this summer" forum claim is uncorroborated and appears to be about Make, not Pipedrive. So **no deadline pressure** — migrate opportunistically.

**v2 is better plumbing, not a new paradigm:** you still push products from your code; v2 just makes it cleaner/faster (lower rate cost, cursor, better validation).

---

## Why Products first (lowest risk)

- The **product catalog sync is backend** — your nightly item service, not something a sales rep touches while quoting. Migrating it changes **no sales workflow**.
- A bug affects a product's **metadata** (caught by bundle verification / the daily report), **not** live quote creation or deal updates. Low, reversible blast radius.
- Products v2 is **GA**, and this is the **same work as standing up the item service** (already the unblocked next step).
- By contrast, the quote-flow PD calls (Deals, Organizations, inbound org webhook) are on the **live sales path** — migrate those **later and carefully**.

**The one thing to validate:** the PD product custom fields — `Sync to QuickBooks` (`98ec4970…` = Yes/83), `CatSub` (`9c636133…`), `QBO Item Type` (`b65439db…`, Service 74 / NonInventory 71), `Product/Service` (`b82ad04a…`, 248/435) — are what **trigger SyncQ → QBO**. In v2 they move into the nested `custom_fields` object, so the migration must still write them correctly or **SyncQ stops firing**. Test this explicitly.

---

## Suggested steps (ordered, with why)

1. **Shared-module refactor.** Pull `quoter`/`scalepad`, `pipedrive`, `qbo`, `category` into clean importable modules with no work-on-import.
   *Why:* prerequisite for everything; kills the "two cooks" drift; where both v2 migrations land.
2. **Build ScalePad v2 item + category wrappers** in `scalepad_v2.py`.
   *Why:* v2 is the item source-of-truth target; wrappers are reusable and testable.
3. **Read Quoter items via ScalePad v2** (`filter[record_updated_at]` + cursor) in the item service.
   *Why:* clean incremental sync; retires the legacy dual-fetch/dedupe.
4. **Decide the PD-ID linkage** (replace the `sku` hijack) before writing back.
   *Why:* `sku` has real inventory meaning in v2; avoid corrupting it.
5. **Migrate PD product writes to Pipedrive v2** — `POST/PATCH /api/v2/products`, custom fields under `custom_fields`, cursor pagination.
   *Why:* modernizes the product leg on the safe (backend) surface; no sales impact.
6. **Validate SyncQ still triggers** — create/update a product via v2, confirm the four custom fields land and SyncQ picks it up into QBO.
   *Why:* this is the single failure mode that matters; prove it before rollout.
7. **Fold in the known code fixes** while you're in there: `Type` hardcoded to Service, income account hardcoded to 389, name-matching → use durable IDs.
   *Why:* cheap to fix during the rewrite; already documented as debt.

**Keep the item service isolated** (its own scheduled Render service over shared modules) so none of this can touch live quote creation.

---

## Reference (keys / endpoints / auth)

- **ScalePad v2:** `https://api.scalepad.com/quoter/v1/items`, `/categories`; header `x-api-key`; incremental `?filter[record_updated_at]=gt:{ISO}&sort=+record_updated_at&page_size=200` + `next_cursor`.
- **Pipedrive v2:** `POST/PATCH https://api.pipedrive.com/api/v2/products`; custom fields nested under `custom_fields`; cursor pagination.
- **PD product custom-field keys:** CatSub `9c636133839b978b686bbc952fbd5dc41d5cd087`; QBO Item Type `b65439db55a0f1d772dc1570c8818f3b8a188b25` (Service 74 / NonInventory 71); Product/Service `b82ad04a30171b69c4649e6f66f956ade0a51886` (248 / 435); Sync to QuickBooks `98ec4970ff4f9f9cc17926d27675eee823a4eb86` (Yes = 83); Subcategory `ae55145d60840de457ff9e785eba68f0b39ab777`; QuickBooks ID (SyncQ) `1213a9ae4c45178ff7c81bde38c3cdfbdc71bbd4`.
- **SyncQ** maps PD Product → QBO Item (mapping `LQ-7604`) but **not** income/expense accounts — accounts must be set by the native link or `quoter_to_qbo_sync.py`.

---

## Out of scope for the products chat (parked)

- **Quote creation on v2** — blocked by the ScalePad `client_id`/Lifecycle Manager issue; awaiting the Client-name fix. (Quote-flow work stays in the quote chat.)
- **Template line items / Item Groups / GraphQL scraping** — Item Groups aren't entitled on the Standard plan; the supported template read (create-from-template → fetch) is gated on the same `client_id` fix. Parked.
- **Pipedrive Projects API v2** — not used by TLC. Ignore.
- **Pipedrive quote-flow migration** (Deals/Organizations/webhooks) — live sales path; do after Products.
