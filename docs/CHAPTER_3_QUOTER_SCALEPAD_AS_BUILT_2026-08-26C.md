# Chapter 3 — Quoter / ScalePad Integration (As-Built)

**Status:** Draft — in progress
**Date:** 2026-08-26
**Supersedes:** all prior Chapter 3 versions (2026-08-18-C/D/E/F/G, 2026-08-21-B/C/D/E/F/G/H, 2026-08-23, 2026-08-24, 2026-08-25) and the 2026-08-20 addenda (A/B/C). Those are superseded in full, not amended — several contain claims this version retracts (see §2.2.2, §2.2.7, §2.3.1, §7.8). Archive them; do not hand more than one Chapter 3 to a new session.
**Governing discipline:** Verify, don't assume. Every claim below is tagged **[Confirmed]** (backed by a live test, a documented API response, or a direct vendor statement) or **[Hypothesis]** (a reasonable inference not yet independently verified). Nothing here should be treated as fact if tagged Hypothesis.

---

## 1. Purpose & Scope

This chapter documents how TLC's Pipedrive → Render → Quoter draft-quote pipeline actually behaves, with a focus on what was previously undocumented or misunderstood:

1. The **hybrid API architecture** — legacy Quoter API and ScalePad v2 running side by side, and exactly where each is ahead of or behind the other.
2. **Authentication and transport mechanics** — including a case-sensitivity defect that reports itself as an invalid credential (§2.1).
3. The mechanics of the **Quoter "Client" object** — a distinct entity from a Contact, whose creation trigger was not obvious from outside the system.
4. The **manual linking step** (Pipedrive Person + Deal) that a salesperson performs on every draft quote, why it exists, and why it can't currently be automated.
5. **Template line-item access** — the problem this migration was started to solve (§6).
6. **What Item Groups and Bundles actually are**, as opposed to what they were assumed to be (§7.8, §7.9) — and the **line-item write schema** that had never been established (§7.10).
7. **Pipedrive dropdown synchronisation** (§11) — built and running: a Quoter template or Item Group created, renamed, or deleted now propagates to the Pipedrive custom field automatically, with option ids preserved.

**Scope note.** Sections 1–7 and 11 are as-built behaviour. §8 records a proposed architecture that follows from those findings but has not been built; it is design, not as-built, and is marked accordingly. Catalog organisation, naming conventions, and template restructuring belong to a future chapter — they are product-model decisions, not integration mechanics.

---

## 2. Architecture: Hybrid API

TLC runs two API generations concurrently during the v1→v2 migration:

| | **Legacy Quoter API** (`api.quoter.com`, OAuth) | **ScalePad v2** (`api.scalepad.com/quoter/v1`, `x-api-key`) |
| :-- | :-- | :-- |
| Owns today | Quote creation, line items (production) | New-endpoint surface being migrated onto |
| Sections | **Not supported** — flat line items only | **[Confirmed]** `POST /quotes/{id}/sections` documented |
| Custom quote number | Blocked — 403 on PATCH, not settable at create | **[Confirmed]** `custom_number` is a create-time field on `POST /quotes` |
| Line item edits post-creation | Not supported | **[Confirmed]** PATCH line item endpoint (added per Jon Turner, Jul 16 2026) |
| Quantity on line items | Allows `qty: 0` at API-write time | **[Confirmed]** API rejects zero/blank/null at write (§7.3) — but UI permits editing to zero or blank afterward (§7.4), so the scaffold pattern survives, relocated to a post-creation human step (§7.5) |
| Client/Contact model | Identifies by `contact_id` directly — no Client concept | **[Confirmed]** Requires resolving a `client_id`, or a Client name (§5) |
| Line item creation | By reference — `item_id` accepted | **[Confirmed]** **By value only** — no `item_id`; fields are copied in (§7.10) |
| Template → line items | **[Confirmed]** Never surfaced/seeded via API | **[Confirmed, re-verified Aug 19–20]** Same — see §6 |
| Pipedrive Deal/Org link | No field | No field |

**Net effect:** v2 is not a strict superset of legacy. It gained sections, create-time numbering, post-create line item edits, cursor pagination, and server-side filtering. It also introduced a Client-matching requirement legacy never had, and it **removed** by-reference line item creation — a change with real consequences for how quotes get assembled (§7.9, §7.10).

### 2.1 Authentication mechanics

#### 2.1.1 The `x-api-key` header is matched case-sensitively — **[Confirmed, live, Aug 19 2026]**

ScalePad's gateway (Kestrel) rejects `X-api-key` with **HTTP 401**:

```json
{"errors":[{"code":"UNAUTHORIZED","title":"Invalid API credentials",
"detail":"Invalid API credentials provided. Please check your API credentials and try again."}]}
```

The same key, same URL, same session, sent with lowercase `x-api-key`, returns **200**.

**Why this matters more than it appears.** Python's `urllib.request.Request.add_header()` normalises header names via `.capitalize()` — verified directly: adding `x-api-key` stores it as `X-api-key`. Any client built on `urllib` will silently send the capitalised form and be told its **credentials are invalid**. The error message points at the key; the actual fault is the header name.

This cost roughly two hours of misdirected debugging — chasing key rotation, Render env vars, and account billing status — before `curl` (which sends headers verbatim) returned 200 with the identical key and isolated the fault.

**Mitigation:** use `http.client` with `putheader()`, which writes the name byte-for-byte. Confirmed by capturing raw wire bytes off a local socket:

```
GET /test HTTP/1.1
Host: ...
x-api-key: <redacted>
```

**[Resolved, Aug 23 2026]** Render is unaffected: `scalepad_v2.py` uses `requests.Session()` with a literal lowercase `"x-api-key"`, and `requests` transmits header names as written. See §2.2.5. The hazard is confined to newly written tooling — any new script must use `requests` with an explicit lowercase key, or `http.client` with `putheader()`.

**[Hypothesis]** RFC 7230 specifies header field names as case-insensitive, so this is a gateway defect on ScalePad's side rather than intended behaviour. Worth reporting; it will affect other API consumers.

#### 2.1.2 Render environment variable names do not describe their contents — **[Confirmed]**

| Render var | Actually holds | Authenticates against |
| :-- | :-- | :-- |
| `QUOTER_API_KEY` | legacy OAuth **client_id** (`cid_...`, 31 chars) | `api.quoter.com` |
| `QUOTER_CLIENT_SECRET` | legacy OAuth client secret | `api.quoter.com` |
| `SCALEPAD_API_KEY` | v2 API key (52 chars) | `api.scalepad.com/quoter/v1` |

`QUOTER_API_KEY` is misnamed: it holds a client ID, not a key. This directly caused a failed authentication attempt during testing. Neither legacy credential authenticates against v2 under any header.

**Recommendation:** document this before renaming. A rename requires updating every reference in Render's codebase, so documentation-first is the safer order.

### 2.2 Collection endpoints, pagination, and filtering

#### 2.2.1 Confirmed endpoint inventory — **[Confirmed, live, Aug 19–20 2026]**

| Path | Status | Notes |
| :-- | :-- | :-- |
| `GET /items` | 200 | `total_count: 297` pre-test; 298 after a Bundle was created (§7.9) |
| `GET /categories` | 200 | `total_count: 313` |
| `GET /item-groups` | 200 | `total_count: 1` |
| `GET /item-group-item-assignments` | 200 | confirms the §7.1 retraction |
| `GET /quote-templates` | 200 | `total_count: 11` (§7.7) |
| `GET /quotes` | 200 | `total_count: 207` |
| `GET /contacts` | 200 | `total_count: 131` |
| `GET /quotes/{id}` | 200 | sections + line items nested — see §6.4 |
| `POST /quotes/{id}/sections/{sid}/line-items` | 201 | schema in §7.10 |
| `GET /quotes/{id}/sections` | **403** | `ERR_PERMISSION_DENIED` — POST-only |
| `GET /line-items` | **403** | `ERR_PERMISSION_DENIED` |
| `GET /catalog-items`, `/products` | non-JSON | do not exist |

**Note on 403s:** per the §7.1 retraction, a 403 on a *guessed* URL is not evidence of a plan restriction. `GET /quotes/{id}/sections` returning 403 while POST on the same path is documented and works is consistent with method-scoped permissions, not account tier.

#### 2.2.2 Pagination is cursor-based; the page-size parameter is `page_size` — **[Confirmed]**

Collections return `next_cursor` (base64; `WyIyIl0=` decodes to `["2"]`) alongside `total_count`. The cursor parameter is **`cursor`**. The page-size parameter is **`page_size`**, capped at 200.

**Correction to an earlier claim.** An earlier draft of this chapter stated that page-size parameters were "accepted without error and ignored." That was wrong, and the error is instructive: the test probed `page[size]`, `limit`, and `per_page` — never `page_size`. Three wrong guesses produced a false generalisation about the API. The parameter works; the guesses did not.

**[Confirmed]** from TLC's own `test_scalepad_items_v2.py`, which asserts `page_size=200` with a hard cap, and `test_get_items.py`, which calls `/items?page_size=200` directly.

**The genuine hazard remains, in a narrower form.** An *unrecognised* parameter is accepted silently and ignored, returning the full default page of 200 with HTTP 200 and no warning. A client using the wrong parameter name fetches 200 of 297 records with no indication it is short. **Always compare returned count against `total_count`.** An ignored *cursor* parameter fails the same way — it returns page 1 again, indistinguishable from success unless the returned IDs are compared.

#### 2.2.3 Server-side filtering and field projection — **[Confirmed]**

From TLC's `scalepad_items.py` test suite, verified against the documented shape:

| Parameter | Form | Use |
| :-- | :-- | :-- |
| `filter[code]` | `eq:BAL-FIL-001` | resolve a single item by code |
| `filter[sku]` | `eq:195` | resolve by SKU |
| `filter[billing_email]` | `eq:...` | resolve a contact |
| `filter[item_group_id]` | `eq:igrp_...` | scope assignments |
| `filter[record_updated_at]` | `gt:2026-01-15T00:00:00Z` | **incremental sync** |
| `fields` | `name,sku,price_decimal` | comma-separated projection |

**Two consequences worth stating.** Name/code→ID resolution does not require pulling the whole catalog. And `filter[record_updated_at]` means any sweep can run incrementally rather than full-scan — relevant to whatever keeps a mirror current (§8).

#### 2.2.4 SKU carries a numeric foreign key, catalog-wide — **[Confirmed, full-catalog scan 2026-08-23]**

Every one of the 297 catalog items has `sku` populated. All values are numeric. **Zero collisions and zero blanks**, range 1–1210.

TLC's `scalepad_items_maint.py` enforces this client-side: `set_sku()` raises `ValueError` on a non-numeric value *before any API call is made* (its test asserts `fc.calls == []`), `clear_sku()` writes an empty string, and `scan_nonnumeric_sku()` / `scan_empty_sku()` / `scan_sku_collisions()` report violations without correcting them. All three scans would return clean against the current catalog.

**Important distinction:** this is a **TLC convention enforced by TLC's own code**, not an API constraint. ScalePad has not been observed to reject a non-numeric SKU; the guard fires locally. An earlier draft of this chapter implied the API enforced it — that was wrong.

**[Hypothesis]** The field holds Pipedrive **product** IDs. Supporting: values are small integers, Pipedrive record IDs are numeric, the maintenance module's own failing-test fixture is the string `"NOT-A-PD-ID"`, and the real-world offender it scans for (`N82E16820147743`) is a supplier SKU. Not yet confirmed against Pipedrive itself — worth verifying that, say, sku `195` resolves to the corresponding Pipedrive product.

**Practical rule:** treat `sku` as a foreign key, never as a supplier part number. The human-readable part number lives in `code` (§2.2.6).

#### 2.2.5 An existing client already implements this — do not reimplement — **[Confirmed via test suite]**

`scalepad_items.py` exposes a `QuoterItemsV2` class that already covers the catalog surface. Confirmed from `test_files/test_scalepad_items_v2.py`, whose assertions pin the real call signatures:

| Method | Behaviour asserted by tests |
| :-- | :-- |
| `list_items(updated_since, page_size)` | `GET /quoter/v1/items`; `page_size` capped at 200; adds `filter[record_updated_at]=gt:` when `updated_since` given, omits it otherwise |
| `iter_all_items(updated_since)` | follows `cursor` across pages — verified across a two-page fixture |
| `get_item(id, fields=[...])` | `GET /items/{id}` with `fields` comma-joined |
| `create_item(**kw)` | `POST /items`; `None`-valued kwargs dropped |
| `update_item(id, **kw)` | `PATCH /items/{id}` |
| `list_categories()`, `get_category(id)` | `GET /categories`, `GET /categories/{id}` |

`scalepad_items_maint.py` adds an `ItemMaintenance` layer over it: `find_by_code` / `find_by_sku` using server-side `filter[...]=eq:` rather than client-side scanning, collision and duplicate scans, and `set_sku` / `clear_sku` with **dry-run defaulting to True**.

**Implication:** the throwaway probes written on 2026-08-19–21 (`quoter_recon.py`, `quoter_recon_v2.py`) reimplemented cursor pagination and the catalog pull that `iter_all_items()` already provides. Those scripts should be treated as **evidence of how the API facts were established, not as code to build on.** New work belongs in `scalepad_items.py` / `scalepad_v2.py`.

**[Confirmed — source read 2026-08-23]** Both previously-open questions are now answered.

**1. The header casing hazard does NOT affect production code.** `scalepad_v2.py` defines `ScalePadV2Client` on `requests.Session()` and sets its headers as literal lowercase:

```python
self.session.headers.update({
    "accept": "application/json",
    "content-type": "application/json",
    "x-api-key": self.api_key,
})
```

`requests` transmits header names as written (unlike `urllib`, which capitalises — §2.1.1). Render is therefore safe as built. **The hazard is real but confined to newly written tooling**, which is exactly where it bit on Aug 19. Any new script must use `requests` with an explicit lowercase key, or `http.client` with `putheader()`.

**2. No line-item write path exists yet.** `ScalePadV2Client` is transport only — `get`/`post`/`put`/`patch`/`delete` over a base of `https://api.scalepad.com`, with full paths (`/quoter/v1/...`) supplied by the caller. `QuoterItemsV2` covers Items and Categories only. **The §7.10 schema has no home yet** and should go into a sibling resource wrapper (e.g. `scalepad_quotes.py`) following the same pattern, not into another standalone script.

Two implementation notes for whoever writes it:

- `client.post(path, data=body)` forwards as `json=data`, so a **bare JSON array** body (§7.10) passes through correctly with no changes to the transport layer.
- `_request()` calls `raise_for_status()`, so a 422 raises `RuntimeError` rather than returning the body. The message does embed `response.text`, so the field-level `line_items[i].field` detail survives — but callers must catch and parse the exception rather than inspect a return value.

**[Confirmed] `iter_all_items()` does exactly what the probes reimplemented.** From source: `list_items()` sends `page_size` (capped at `MAX_PAGE_SIZE = 200`), `cursor`, `filter[record_updated_at]=gt:<ts>`, `fields`, and an `extra_filters` passthrough; `iter_all_items()` loops on `next_cursor` until exhausted. This predates and supersedes the pagination logic in `quoter_recon_v2.py`.

**[Confirmed — `docs/DECISIONS.md` v1.0, 2026-06-30, read Aug 23 2026]** The architectural decision record governs where new code belongs, and three entries bear directly on this workstream:

- **D-003 — Separate transport from business logic.** `scalepad_v2.py` contains only authentication, HTTP transport, and resource-wrapper methods. Business logic belongs in higher-level service modules.
- **D-004 — SDK evolution.** `scalepad_v2.py` becomes TLC's internal ScalePad SDK: generic HTTP, resource wrappers, common request handling. Business workflows stay outside it.
- **D-006 — Investigation before implementation.** Endpoints are investigated and verified *before* wrapper methods are written.

**Consequence for §7.10.** A line-item resource wrapper is exactly what D-003/D-004 sanction, and D-006's precondition is now satisfied — the endpoint was verified live before any wrapper existed. `scalepad_items.py` establishes the pattern for a resource module built over the shared client, so a sibling (e.g. `scalepad_quotes.py`) is the architecturally consistent home. **Quote-composition logic — deciding which items belong on a quote — is business logic and belongs in a service module above the SDK, not inside it.**

Also relevant: **D-005** (legacy functionality removed only after equivalent ScalePad functionality is *verified*) and **D-010** (Investigate → Understand → Design → Document → Implement → Test → Commit). This chapter is the Document step; implementation is next.

#### 2.2.6 `code` is the human-readable part number, and it already encodes manufacturer — **[Confirmed, 2026-08-23]**

Two identifier fields exist and they are not interchangeable:

| Field | Holds | Example |
| :-- | :-- | :-- |
| `code` | TLC part number | `BAL-BLW-001`, `HG-FVV-080-001`, `T&E-FLY-001` |
| `sku` | numeric foreign key (§2.2.4) | `195`, `412`, `1210` |

**Zero code collisions across all 297 items.** Both fields are unique catalog-wide, so either resolves a single item — but `filter[code]=eq:` is the right lookup for a part number, and it is one server-side call rather than a client-side scan.

**Manufacturer is already encoded in the code prefix.** The Floating Video line makes this explicit:

| Code | Item | Manufacturer |
| :-- | :-- | :-- |
| `HG-FVH-L30-001` | FV-30 Fan Holographic | **FVH** — Hypervsn |
| `HG-FVH-M22-001` | FV-22 Fan Holographic | FVH |
| `HG-FVH-HH-001` | FV-HoloHuman | FVH |
| `HG-FVH-HH-002` | FV-HoloHuman-Case | FVH |
| `HG-FVH-MBOX-001` | FV-MasterBox | FVH |
| `HG-FVV-180-001` | FV-6FT-180 Fan Holographic | **FVV** — Vdisplay |
| `HG-FVV-150-001` | FV-5FT-150 Fan Holographic | FVV |
| `HG-FVV-100-001` | FV-40in-100 Fan Holographic | FVV |
| `HG-FVV-080-001` | FV-32in-80 Fan Holographic | FVV |
| `HG-FVV-080-002` | FV-32in-80 / Rental Only / No Technician | FVV |
| `HG-FVV-MBOX-001` | FVV-MasterBox | FVV |
| `HG-FV-Graph-001/2/3` | Standard / Advanced / Ultimate Graphics Pkg | neutral |

**This matters for the phase-out.** Item *names* carry no manufacturer marker, so a salesperson reading a quote cannot tell a Hypervsn unit from a Vdisplay one. The *codes* can, unambiguously: everything `HG-FVH-*` is the line being retired. Attribution does not need to be reconstructed — it already exists, and the retirement set is selectable by prefix.

**Correction to an earlier draft.** A previous version of this chapter stated the FV items "carry no manufacturer marker at all" and flagged attributing them as a prerequisite data task. That was wrong; the task is already done.

#### 2.2.7 Correction: the July export's `-001`/`-002` pair is not a collision

An earlier draft read a diff between the two July 24 CSV exports as a weight correction plus a code collision being resolved — `FV-32in-80` moving from `HG-FVV-080-001` to `-002`, with a value changing `195 → 1210`.

Both readings were wrong, and the live catalog shows why:

- `HG-FVV-080-001` (sku 195) and `HG-FVV-080-002` (sku 1210) are **two distinct items** — the standard unit and a *Rental Only / No Technician* variant. Neither supersedes the other.
- The column read as "Weight" was holding **SKU** values. `195`, `1210`, and `412` are exactly the SKUs of the affected items.

There is no unresolved collision, and `-002` is the previously-unexplained 13th `FV` item (§2.3).

### 2.3 Catalog taxonomy

#### 2.3.1 The category hierarchy exists; the API reports only the leaf — **[Confirmed, corrected Aug 20 2026]**

**Correction to an earlier claim.** An earlier draft stated that Quoter "flattened TLC's two-level taxonomy on import, discarding the top-level Category." That was wrong. The Add Bundle form's category picker renders a genuine parent/child tree:

```
T&E
  » Baggage
  » Buyout
  » Flights
  » Ground
  » Meals
  » Parking
  » PerDiem
  » Rooms
```

The hierarchy is intact. What is true is narrower: **`GET /items` returns only the leaf name in its `category` string field.** An item in `T&E / Flights` reports `category: "Flights"`. The parent is not present in the item payload, though `category_id` presumably resolves to it via `GET /categories/{id}` (untested).

Item-for-item confirmation that the API's `category` is the leaf, not the parent:

| API `category` | API count | Source-catalog subcategory count |
| :-- | :-: | :-: |
| `Latex` | 12 | 12 |
| `Flame` | 7 | 7 |
| `Truss` | 6 | 6 |
| `GlowBalls` | 6 | 6 |

#### 2.3.2 Leaf names collide across parents — **[Confirmed]**

Because only the leaf is reported, 16 leaf names are ambiguous in the item payload:

| API `category` | Items | Distinct parents |
| :-- | :-: | :-- |
| `Technician` | 6 | Pyro, Robotics, Service |
| `Cables` | 6 | DMX, Electrical, Laser |
| `Repair` | 3 | CO2, Tanks |
| `Helium` | 3 | Balloons, Tanks |
| `Fogger` | 2 | CO2, Fog |

*(11 further collisions of the same kind.)*

**Practical implication:** selecting items by the `category` string from `GET /items` is **unsafe**. A rule matching `Technician` would pull Pyro and Service technicians alongside Robotics ones. Selection must key on `category_id`, or on an explicit item list.

#### 2.3.3 There are also duplicate flat category records — **[Confirmed]**

Alongside the tree, the picker lists literal flat entries: `T&E / Baggage`, `T&E / Buyout`, `Balloons / Drop`, `Robotics / Arm`, and many more. These appear to be separate category records whose *names* contain the parent path.

**[Hypothesis]** These are import artifacts — created when a source export's `Category / Subcategory` pair was written as a single category name. This plausibly explains 313 category records against a catalog of 286 real items. Worth an audit; duplicate categories mean the same real grouping can be referenced by two different `category_id` values.

Also present in the picker but holding **no items**: `Template Bundle Demo`, `Rental Items`, `Services - Labor`, `Robot Dog`, `Robot (Not Dog)`, `Robot Branding`, `Robot packages`, `Per Diem`, `Fans`, `Product`, `Instructions`, `Test`. **[Confirmed — Eric Grosshans]** these are remnants of earlier exploratory work on template bundling, predating this project.

#### 2.3.4 The catalog count includes 11 test items — effective catalog is 286 — **[Confirmed]**

`GET /items` reported `total_count: 297` before this session's testing. Eleven of those are `zz-test item…` fixtures (codes `ZZZ-BAL-LT*`), all in `Balloons / Latex`. That subcategory holds 12 items, of which exactly **one** — "Balloons per package" — is real.

**Consequence:** any process selecting items by the `Latex` category would produce 92% test data. See §10 for removal.

---

## 3. The Quoter "Client" Object

### 3.1 Client vs. Contact

A **Contact** (person: name, email, phone) and a **Client** (the billing/organisation entity a quote is prepared for) are two separate objects in Quoter's data model. This section is about the Client.

### 3.2 Three-source selector — **[Confirmed]**

The "Prepared For" search box on a draft quote is not hardwired to one system. It has a dropdown with three lookup sources: **Quoter** (native People/Client list), **Pipedrive**, and **QuickBooks Online**.

One is set as the account-level default (TLC's is Pipedrive), but a user can switch per-quote. This is a **UI convenience setting only** — it has no bearing on API automation (§4).

### 3.3 Client creation — mechanism confirmed by ScalePad Support

**[Confirmed]** A Quoter Client can exist before any human has touched the draft quote. Verified directly: `Images by Lighting-3036` (Deal 3036) existed as a Client the moment the associated draft was opened — its Person/Deal link had not yet been confirmed (search icons still present, no "associated with…" banner) — meaning Client creation does **not** depend on the manual linking step.

**[Confirmed — Jon Turner, ScalePad Support, Aug 2026]** Asked directly whether Client creation is tied to Contact-write behaviour or to the QBO connector:

> "Yes, if you create a Contact in Quoter via the API it will be added as a Client as well. We do not sync the data from QBO so it would be created once the contact is added, whether manually or via the API :)"

This rules out the QBO-connector hypothesis and confirms the mechanism: **creating a Contact — manually or via API, on either API generation — automatically mints a matching Client.** Jon's framing ("via the API," without distinguishing legacy from v2) means this is not a legacy-only behaviour at risk of disappearing on full migration.

**Practical implication:** the Client's identity is entirely a function of whatever value is passed as the Contact's `billing_organization` at creation time. There is no separate sync process to reason about — it is a direct, deterministic input → Client mapping.

### 3.4 Confirmed fragmentation, and why it's expected

**[Confirmed]** Two separate Quoter Clients exist for the same real customer: `Images by Lighting-2710` and `Images by Lighting-3036`, from two deals seven months apart.

This is the **expected consequence** of the current configuration, not a defect:

- The default lookup source is Pipedrive.
- TLC's Pipedrive sub-organisations are created **per deal** (one org = one deal, by design — see Chapter 2, provisioning automations 2A/2B).
- Therefore every new deal's quote resolves against a brand-new Pipedrive org name → a brand-new Quoter Client, every time, even for repeat customers.

**Supporting evidence:** the Client detail page has a built-in **"Merge duplicate Clients"** tool. Quoter's own product design anticipates this fragmentation pattern and expects periodic manual consolidation — this is not a TLC-specific quirk.

### 3.5 Three possible target models — an input-side decision

| Option | Client = | Consequence today |
| :-: | :-- | :-- |
| 1 | Pipedrive Organization (per-deal) | **[Confirmed current behaviour]** New Client every deal, even for repeat customers |
| 2 | QuickBooks Customer | If sub-customer (per-deal): same fragmentation. If parent customer: one Client per real company — untested |
| 3 | Quoter native Client, deduplicated by company | **[Confirmed not currently true]** — the 2710/3036 fragmentation rules this out |

Per §3.3 this is not a question of which upstream system syncs into Quoter — there is no sync. **Whatever string is passed as `billing_organization` on Contact creation becomes the Client.** Today that string is the per-deal Pipedrive sub-org name, which is why fragmentation happens.

**This makes Option 3 directly achievable without new architecture:** if Render resolved a canonical, deal-independent company name (stripping the `-DealID` suffix, or looking up a stable identifier) and passed that instead, every deal for the same customer would resolve to the same Client. A deliberate decision about what to pass — not a bug fix, and not blocked on ScalePad.

---

## 4. Manual Linking Requirement (Pipedrive Person + Deal)

### 4.1 What the link actually does — **[Confirmed]**

Confirming a match in the "Prepared For" search does two things, observed on a live draft:

1. Stamps the quote's Contact with an actual **Pipedrive Person ID** (e.g. "This Quote is associated with Jessica Mak (ID 5727) from Pipedrive").
2. Reveals a **Deal / Opportunity Selection** section below, scoped to that Person's Pipedrive Organization, where a specific Deal is picked.

This is materially different from the Client match in §3 — the Client is a name-based billing entity; this link is a hard reference to specific Pipedrive record IDs. Without it, a quote has no real pointer back to Pipedrive, regardless of whether the Client name looks right.

### 4.2 Why it's necessary, not vestigial

Required for **bidirectional sync** — one of the reasons Quoter was selected. Without the Person/Deal reference there is nothing for a return-leg process to read or write against. The "Organization Appears Correct but Is Not Linked" failure mode in the Overview/Runbook is exactly the case where the name matches but this reference was never set.

### 4.3 Bidirectional capability exists but is unused by design

The Deal/Opportunity Selection section can **create a new Deal in Pipedrive directly from Quoter**. TLC does not use this: the architecture is strictly 1:1 (one Pipedrive Organization = one Deal) and the deal always originates in Pipedrive. A deliberate non-use of an available capability, not a gap.

### 4.4 Confirmed: cannot be set via API, on either version

**[Confirmed]** Checked every relevant v2 endpoint (Create Quote, Create/List Contacts, Create Sections, Create/Patch Line Items, Publish Quote) — none expose a field for a Pipedrive Person ID, Organization, or Deal reference. This matches ScalePad Support's written guidance from Aug 11 2025 (legacy-era): *"our recommendation here would be to create the Drafts via the API and manually associate the Deals/contacts after the Drafts are created."*

**This has not changed with v2.** The "default source = Pipedrive" setting affects only which tab a human lands on first — it does not make the link API-settable. A required human action regardless of API generation.

---

## 5. The `client_id: null` Fix — Confirmed Live Against Production

**[Confirmed — Jon Turner, Jul 27 2026]** `client_id` can be set to null on v2 `createQuote`; the Client name is what resolves the match instead.

**[Confirmed — live test, Aug 19 2026]** Ran a real `POST /quoter/v1/quotes` against production with a zz-tagged test Contact/Client (no real customer data touched). Result: **201 Created**, with `client.name` resolved from the passed `client_name`, `client.id` staying null (expected — no Lifecycle Manager UUID exists for TLC), and `custom_number` set exactly as passed, `draft: true`, no PATCH required.

Two things settled:

- **`client_name` resolution works exactly as Jon described** — the actual resolution of the original blocker.
- **`custom_number` is settable at create time** — the value passed came back verbatim.

**Doc-accuracy note.** The public docs describe the template ID prefix as `qtpl_`; the live API returns and expects `tmpl_` (confirmed via `GET /quote-templates`). This is now the **third** instance of the reference lagging the real API — see also §2.2.2 (the body-params block on the Create Quote Line Items page renders empty) and §7.10 (the write schema had to be derived from error responses). **Treat the docs as directionally correct, not verbatim-reliable.**

### 5.1 Contact record and quote-embedded contact do not stay in sync

Running `createContact` standalone, then separately referencing that same `billing_email` inside `createQuote`, surfaced a reproducible split — not a caching artifact (confirmed by re-querying after a delay with identical timestamps):

- **`POST /contacts` (standalone)** creates a real, persistent record (confirmed via `GET /contacts?filter[billing_email]=eq:...`, `total_count: 1`) — but that record's own `id` and `client` fields remain **permanently null**. The record is inert on its own.
- **`createQuote`**, given the same email plus a `client_name`, materialises a **fully-resolved** contact — real `cont_...` ID, resolved client object — but only visible embedded inside the quote's response. It is never written back to the standalone `/contacts` resource.

Corroborated by the artifact sweep (§10): both `zz-test-chapter3@tlciscreative.com` and `myles@tlciscreative.com` return `id: null` from `GET /contacts`.

**Practical implication:** Jon's statement that creating a Contact "will be added as a Client as well" is true in effect, but the linkage lives on the **quote's view of the contact**, not on the contact record. Render likely does not need a standalone `createContact` call — `createQuote` appears to do all the resolution in one call, provided the referenced `billing_email` exists in some form first.

---

## 6. Template Line-Item Access

**This was the original reason the migration project exists.** TLC's June 2026 email to Jon stated the goal plainly: eliminate ~200 lines of hard-coded Python per template, because there was no way to read a template's line items at quote-creation time.

As of this chapter, **the API still cannot read template line items** — but see §7.8: the reason this blocked the Item Group work was not what it appeared to be.

### 6.1 Confirmed history, verified against Gmail

- **Legacy API never had this.** Jon, Sept 11 2025, in writing: *"A reminder that any Line Items set on the Template level are not supported by the API, so they will be ignored."*
- **v2 was explicitly scoped not to add it.** Jon, Jul 9 2026: *"I don't believe as part of the new API updates… that we will be surfacing the Line Items that exist on the Templates."*
- **The Item Group mirror idea's sticking point was assumed to be this same problem, one layer removed.** TLC proposed (Jun 26 2026) nightly-syncing each Template into an Item Group. Jon flagged Item Groups as Enterprise-only for a Standard-plan account (Jul 2 2026) — but Item Groups had already been created and retrieved via API before that correction landed. **Both of those objections turn out to be beside the point; see §7.8.**
- **An unanswered question sits at the centre of this, since June 30 2026.** TLC asked: *"is there a supported way to authenticate to the Quoter web application programmatically so we can retrieve the same template payload that the browser receives?"* Jon's reply addressed Item Groups and release timelines — it never answered this question. Re-sent Aug 19 2026, ~15:37 PT. No reply as of this writing.

### 6.2 Live re-confirmation, Aug 19–20 2026 — tested on a stronger claim

The earlier draft recorded that `POST /quotes` with a real `template_id` returns `sections: null`. That is a fact about the **create response**. It is not the same claim as *the created quote has no sections* — an API can create a populated resource and return a thin representation of it. That second claim had never been tested.

**[Confirmed, live, Aug 19 2026]** It has now been tested directly. A draft was created from the Balloons template (`tmpl_32CqUL7Iloih2Xgx68JvjptGYXy`), producing `quot_3I9uJGP7vY89JWM9IqRpYTOtcSN` (201 Created), then read back after a settle delay:

- `POST /quotes` response → `sections: null` (as previously documented)
- `GET /quotes/{id}` read-back → **`sections: null`**

**The template's line items do not materialise server-side.** §6's conclusion stands on firmer evidence than before: this is not an artifact of a thin create response, it is a genuine absence. **This closes the last supported-API avenue.**

### 6.2.1 CLOSED — vendor confirmation, 2026-08-23

**[Confirmed — Jon Turner, ScalePad, 2026-08-23]** The question first raised 2026-06-30 and re-sent twice is now answered:

> "Yes, regarding the template lists of Items, we don't have an endpoint for this yet so that is intended. The short answer is that the use case for templates having Items makes sense for manual Quotes but for API Quotes, Items can be added automatically anyway. The API also doesn't support third-party Items yet, which don't have prices at the time of being added to the template so those Items would not necessarily contain pricing info even if we were to list them on the Template."

Three things follow.

**It is intended, not an oversight.** No endpoint exists and none is described as planned. §6 is closed.

**A second reason we had not considered.** Third-party Items carry no price at the point they are added to a template, so even a template-contents endpoint would return incomplete pricing. That is an argument against the feature existing at all, not merely against its priority.

**[Hypothesis]** *"For API Quotes, Items can be added automatically anyway"* reads as an expectation that an API-driven quote populates itself rather than inheriting from a template. That is consistent with §8, but it is a justification for the missing endpoint, not a statement about how quotes should be architected. Do not cite it as vendor endorsement.

**Consequence for §6.3:** the `/admin` scrape route is no longer needed for the production path, because templates are not the content source. It retains value only for one-off reference — reading what a template currently contains when defining an Item Group by hand.

### 6.3 The undocumented browser route, and why the distinction matters

**[Confirmed, re-verified Aug 20 2026]** Opening `https://tlciscreative.quoter.com/admin/quotes/create/<template-slug>` in an authenticated session returns a fully-populated Rails form with real item names, categories, costs, and prices, embedded server-side in the HTML at request time (`<input name="title" value="Balloon air filler">`).

All 11 templates were read this way on Aug 20 (§7.7). The data has always been technically retrievable from Quoter's backend. It has never been retrievable through anything ScalePad has documented, supported, or blessed.

**Why the distinction matters.** Scraping the internal route works today. It would also mean trading a documented, API-key-authenticated integration for session/cookie auth against an undocumented route that could change with any UI redesign, with no notice.

**Recommended distinction, refined:**

- **Prohibited pending Jon's answer:** any unattended, scheduled, or Render-embedded process that depends on the `/admin` route. An automated sync that breaks silently on a UI change is the real risk.
- **Permitted as stopgap:** one-time, human-supervised reads, provided the results are stored as reviewable data rather than as an automated pipeline. The kickoff brief explicitly sanctioned this: *"it's reasonable to start manual/one-off Item Group population as a stopgap while waiting."*

The Aug 20 sweep of all 11 templates was performed under the second heading.

**[Confirmed — this is already TLC policy.]** `docs/DECISIONS.md` **D-008 — Browser Investigation as an Engineering Tool** states that Chrome DevTools is *"the preferred method for understanding undocumented Quoter behavior,"* covering network traffic, XHR/Fetch, embedded payloads, HTML, and JavaScript, because *"browser behavior represents the authoritative implementation when public APIs do not expose required functionality."*

So browser investigation is not a grey area requiring vendor permission — it is the established, documented approach. The distinction above therefore narrows to something sharper: **D-008 sanctions investigation; it does not sanction unattended production dependency.** Reading templates in a supervised session is squarely within policy. Wiring Render to scrape `/admin` on a schedule is a different commitment, and that is what §6's open question actually gates.

### 6.4 Quote reads expose full nested line items — **[Confirmed]**

`GET /quotes/{id}` returns `sections`, each containing a fully populated `line_items` array. Confirmed against the test quote: section `Balloons` (`3I9d4lOPLC1mH88I9TntKgwRbUd`) with 2 line items.

Line item schema:

```
attachments, bundle, bundle_line_item_id, bundle_publicly_visible,
category, code, custom_fields, description, discount_input_decimal,
discount_input_type, id, images, manufacturer, name, optional,
optional_group_id, optional_selected, options, quantity_decimal,
sku, supplier, taxable, totals, unit_cost_decimal,
unit_margin_decimal, unit_margin_percentage, unit_price_decimal
```

Note `bundle` (boolean, "True when this line item is a product bundle") and `bundle_line_item_id` ("ID of the parent bundle line item when this line item belongs to a bundle") — bundle structure exists on quotes even though it cannot be created via API (§7.9).

This reads *quotes*, not templates. It does not solve §6.

---

## 7. Item Groups, Bundles, Line Items, and the Scaffold-Quantity Design

### 7.1 Retraction: an earlier "Item Groups are permission-blocked" claim was wrong

An initial test hit a **guessed, unverified URL** (`/item-groups/{id}/assignments`) and got `ERR_PERMISSION_DENIED`, reported as confirmation of Jon's Enterprise-only warning. **That was a mistake — the guessed URL was simply wrong, not evidence of a restriction.** The documented endpoint (`GET /quoter/v1/item-group-item-assignments?filter[item_group_id]=eq:...`) returns a clean 200 on the same Item Group (`igrp_3Fgct9Xz5Uwu03SUmOoNP6RmZ9o`). **No access restriction exists.**

### 7.2 Item Group Assignments cannot carry quantity — **[Confirmed]**

An Item Group Assignment is `{id, item_group_id, item_id, record_created_at, record_updated_at}`. **No quantity field exists.** An Item Group can only ever represent "these items belong together," never "how many of each." Any design using them must treat them as pure membership lists and source quantity elsewhere.

### 7.3 `quantity_decimal` rejects zero, blank, and null — **[Confirmed]**

| Payload | Result |
| :-- | :-- |
| `quantity_decimal: "0"` | `ERR_LINE_ITEM_QUANTITY_INVALID` — "must be greater than zero" |
| Field omitted entirely | `ERR_LINE_ITEM_QUANTITY_INVALID` — "must be a non-negative decimal" |
| `quantity_decimal: null` | `ERR_LINE_ITEM_QUANTITY_INVALID` — identical to omitted |

**There is no way to create a line item with a zero, blank, or null quantity via the API.** A real, positive decimal is required at write time.

### 7.4 The UI enforces looser rules than the API — **[Confirmed]**

Hands-on testing on a line item created via API at `quantity_decimal: 1`:

- **Editing quantity down to `0` in the UI succeeds**, no error. The line stays visible with a genuine $0.00 total.
- **Clearing the field entirely (blank) succeeds**, and the item **disappears from the customer-facing preview and webview** while remaining in the underlying draft (shown as `—` in the Total column, distinguishing it from a real $0.00 line).

The API and UI enforce **genuinely different validation on the same field on the same resource** — two separate code paths. The API's `>0` constraint governs only what Render can *write*.

### 7.5 Resolved scaffold design

Given 7.3 and 7.4, full legacy-equivalent scaffold behaviour is achievable on v2, relocated:

1. **Render seeds every candidate item at `quantity_decimal: 1`** — the minimum the API accepts.
2. **The salesperson reviews the draft and, per item:** leaves it as-is, sets quantity to 0 (a deliberate, visible $0.00 record), or blanks the quantity (removes it from the customer view) — the same three-way decision legacy supported, now post-creation.

**Anti-pattern, considered and rejected: seeding at a tiny non-zero quantity (e.g. `0.000001`).** Appealing since the API rejects true 0, but unsound. `0.000001 × $5,000.00 = $0.005`, which rounds to a visible $0.01 — a real charge on an item meant to be irrelevant, with no warning.

This is not merely a matter of picking a smaller epsilon. **TLC's pricing varies customer to customer** — the same catalog item is re-priced per deal, per markup. There is no stable ceiling to design an epsilon around, because the thing a safe epsilon depends on — a fixed maximum price — does not exist in this business. An epsilon safe for one customer could produce a visible charge for another, with no way to know which quotes are affected.

**True zero has no such dependency:** `0 × any price = exactly 0`, unconditionally. Epsilon-quantity is a rounding artifact that works only below a threshold that itself is not fixed; zero is a guarantee.

**Visual confirmation, four independent surfaces:** a genuine $0.00 line was checked in (a) the raw API response, (b) the admin Preview Quote modal, (c) the public webview link, and (d) the downloadable PDF. All four rendered it identically and correctly with accurate totals.

### 7.6 Three distinct identifiers exist for the same quote

The same test quote was addressable via **three separate ID schemes** — the v2 API's `quot_3I9UCyBcqZJ39soTFYS5SodFzlW`, the legacy internal numeric ID `8940983` (used in `/admin/quotes/draft/balloons/8940983` and `/admin/quotes/get_pdf/8940983`), and the public webview token (`2778-5c366108-4771-48da-b7a4-3770e7081511`). None are interchangeable; each is scoped to a specific endpoint family.

### 7.7 Template inventory — **[Confirmed, Aug 19–20 2026]**

11 templates exist. Slugs are required for the `/admin/quotes/create/<slug>` route.

| Title | ID | Slug | Line items |
| :-- | :-- | :-- | :-: |
| Basic | `tmpl_30O6JTDIbApan1B5gh9hF2w1tfL` | `test` | 1 |
| Tank Delivery | `tmpl_31vLnIjRObApRldxGd7V3LSuEd8` | `quick-quote` | 12 |
| LED Wristbands | `tmpl_329ZyWvDiEV9fA41C33QIisOeq1` | `led-wristbands` | 25 |
| LED Lanyards | `tmpl_329mwOURxx9hmgNuQmfkM4L8Xxw` | `led-lanyards` | 22 |
| Robotics | `tmpl_329qcsv6mx0upqqLkXFkEZZi92O` | `robitics` | 40 |
| Confetti/Streamers | `tmpl_32A0sbTQSxRN0d6K5pHenlaqUlD` | `confetti` | 23 |
| Floating Video | `tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG` | `floating-video` | 21 |
| CO2/Smoke/Upright Foggers | `tmpl_32A8f3F2d7dQF7NsDIqCQSVLatF` | `co2smokeupright-foggers` | 11 |
| Fireworks/pyro/fire | `tmpl_32ACJvG7U2tHAmiKzxhXXx3Pnns` | `fireworkspyro` | 25 |
| Low level fog | `tmpl_32CORYSQ1OgAJVjA5EmY8YfXpCq` | `low-level-fog` | 9 |
| Balloons | `tmpl_32CqUL7Iloih2Xgx68JvjptGYXy` | `balloons` | 14 |

**Two slugs do not match their titles** and will break any slug-derived-from-title logic: `Robotics → robitics` (misspelled at creation) and `Tank Delivery → quick-quote` (evidently repurposed). **Slugs must be read from `GET /quote-templates`, never generated.** Slug generation also strips `/` without inserting a separator (`Fireworks/pyro/fire → fireworkspyro`).

**Shared-block drift is measurable and real — [Confirmed].** The full T&E set is 8 items. Five templates carry all 8; **Balloons is missing `T&E-Per Diem`** and **LED Wristbands is missing `T&E - accommodations Buyout`**. Three templates (Tank Delivery, CO2/Smoke, Low Level Fog) carry no T&E at all. Three generic Service items (`Labor/Technician for Setup, Test and Strike`, `Second Technician Option`, `Labor Overtime & Per-Diem`) each appear on 6 templates in inconsistent combinations.

This is the concrete cost of maintaining shared content by copy: 11 independent copies, already diverged.

### 7.8 **Item Groups are a reseller access-control feature** — **[Confirmed, Aug 20 2026]**

The `/admin/item_groups/add` form contains exactly three things: a Name field, an **Associated Resellers** picker, and an **Accessible Items** table. Its own help text:

> Associated Resellers — The Resellers selected below will be able to access the Items selected below.
> Accessible Items — The Items selected in the table below will be accessible by the Resellers selected above.

**That is the entire object.** Item Groups do not appear in the quote builder, do not create quote sections, and do not organise the item picker for internal users. They answer one question: *which items may this reseller see.*

**What this corrects.** The kickoff brief's premise — one Item Group per template, mirroring its contents, named identically — was building against an assumed behaviour the object does not have. And §6's template-read blocker was not, in fact, what prevented that design from working: even with complete template contents, an Item Group would have nothing to do with them, because its membership is determined by reseller permissions. This also explains why `TEST-Balloons` has sat empty since June 2026 with nothing breaking — an empty ACL group is indistinguishable from a working one until a reseller uses it.

**What survives, and this is the important part.** An Item Group is still **a named, arbitrary, API-readable and API-writable set of item IDs**. Nothing else in Quoter is all four of those things. So while its *product purpose* is reseller ACL, it remains structurally fit for the purpose TLC actually wants: a machine-readable lookup that answers *"Pipedrive said Balloons — which item IDs is that?"* — getting the hard-coded item lists out of Render's Python and into the system of record.

**[Hypothesis]** Repurposing an ACL object as a lookup table is sound while TLC has no resellers, but the two uses would collide if reseller functionality is ever enabled: a group created as a lookup would silently become a grant of item visibility. Worth confirming TLC has no resellers configured, and worth noting the coupling in whatever documentation Render carries.

#### 7.8.1 Relationship to D-009 — the decision holds, its premise needs amending

`docs/DECISIONS.md` **D-009 — Quoter is the Source of Truth for Templates** states:

> Quote templates will not be maintained manually in Python. Quoter Templates become the authoritative source. ScalePad Item Groups become the synchronized operational mirror.

**The decision is correct and this session's findings support it.** Hard-coded templates in `template_mapping_enhanced.py` are the problem; an API-readable mirror is the fix; and Item Groups remain the only Quoter object that is simultaneously named, arbitrary, API-readable, and API-writable.

**What D-009 did not know is what an Item Group is.** Written 2026-06-30, it treats Item Groups as a neutral grouping primitive. They are a reseller access-control feature (§7.8). That does not invalidate the decision, but it changes its risk profile in two ways worth recording:

1. The mirror repurposes an ACL object. Safe only while no resellers are configured.
2. "Synchronized" is doing heavy lifting. The API cannot read template line items (§6.2), so synchronisation depends on either Jon's answer or the `/admin` route — neither of which D-009 anticipated needing.

Per the Decision Lifecycle ("if a decision changes, do not delete it — record a new decision, reference the superseded one, explain why the architecture evolved"), **this warrants a new entry rather than an edit to D-009.** A proposed D-011 is drafted in §8.5.

### 7.9 Bundles: real objects, but not usable by the API — **[Confirmed, Aug 20–21 2026]**

A **Bundle** is Quoter's genuine multi-item construct — the thing Item Groups were mistaken for. The `/admin/bundles/add` form posts `data[Item][title]`, `data[Item][item_type_id]`, `data[Item][recurring]`, `data[Item][bundle_visibility_type]` — i.e. **a Bundle is an Item that contains Items.**

Its capabilities exceed Item Groups in exactly the ways that matter:

- **`Qty per Bundle`** per member — the quantity that Item Group Assignments lack entirely (§7.2).
- **Price computed from members** — "The Bundle Unit Price and Unit Cost will be calculated using the included Items."
- **`Bundle Display`** with three options: *Show Bundle only*, *Show Line Items only*, *Show Bundle and Line Items (exclude Line Item prices)*. This is the `bundle_visibility_type` field, and it is the direct control for whether a client sees one rolled-up number or itemised detail.

TLC had **zero Bundles** on the account before this test.

**Live test.** A Bundle `zz-TEST-Bundle-TE` was created (category `Test`, display *Show Line Items only*) containing `T&E-Flights` and `T&E-Rooms`, each qty 1. Findings:

1. **It appears in `GET /items` with a real `item_id`** (`item_3ICkQSZwDX0Oa1mA7mLP77fuMyj`), and `total_count` moved 297 → 298. **Bundles and catalog items share one namespace**, so a Bundle *can* be assigned to an Item Group.
2. **Its API record is indistinguishable from an ordinary item.** No member list, no bundle flag, and `price_decimal: null` / `pricing_scheme: ""` despite the UI computing $1,399 from its members. Nothing in `GET /items` reveals that this record is a Bundle or what it contains.
3. **Posting it as a line item produces one ordinary line, with no expansion.** Result: 201, one line item, `bundle: false`, `bundle_line_item_id: null`. The created line was merely *named* `zz-TEST-Bundle-TE`; its price came from the payload, not from the Bundle's members.

**Conclusion: Bundles are UI-only.** Because v2 creates line items **by value** (§7.10), there is no item reference for a Bundle to expand from. Bundles are genuinely useful to a person assembling a quote in the UI, and invisible to Render.

Bundles are one of four such mechanisms; see §7.12 for the pattern and its common cause.

**[Hypothesis — untested]** The probe stopped at the first accepted payload shape, so a variant carrying both by-value fields *and* an `item_id` was never sent. It is possible `item_id` is accepted and triggers expansion. Given the singular `POST /line-items` documents no `item_id` at all, this is unlikely — but it is the one remaining thread if certainty is needed.

### 7.10 The line-item write schema — **[Confirmed, Aug 21 2026]**

This had never been established, and the documentation does not supply it: the Create Quote Line Items reference page renders its Body Params block empty. The schema below was derived by reading successive error responses, each of which named its failing field.

**The working call:**

```
POST https://api.scalepad.com/quoter/v1/quotes/{quote_id}/sections/{section_id}/line-items

[
  {
    "name": "T&E-Parking",
    "quantity_decimal": "1",
    "unit_price_decimal": "99.00",
    "category": { "id": "cat_..." }
  }
]
```

→ **201 Created.** Response body matches `GET /quotes/{quote_id}`, with line, section, and quote totals recomputed and persisted.

**Derivation, for the record** — each step is a confirmed error response:

| Payload attempted | Response | What it established |
| :-- | :-- | :-- |
| `{"item_id":…, "quantity_decimal":"1"}` flat | 400 `ERR_REQUEST_FORMAT_INVALID` | wrong shape (also wrong endpoint initially) |
| `{"line_items":[…]}` wrapper | 400 `ERR_REQUEST_FORMAT_INVALID` | not wrapped |
| `[{…}]` bare array | 422 `ERR_LINE_ITEM_NAME_REQUIRED` — `line_items[0].name` | **body is a bare array**, and `name` is required |
| `[{"name":…, "unit_price": 99.0}]` | 422 `ERR_LINE_ITEM_UNIT_PRICE_INVALID` — `unit_price_decimal` must be a non-negative decimal | field is `unit_price_decimal`, a decimal **string** |
| `[{…, "category_id": "cat_…"}]` | 422 `ERR_LINE_ITEM_CATEGORY_REQUIRED` — `line_items[0].category.id` | `category` is a **nested object**; flat `category_id` does not satisfy it |
| `[{…, "category": {"id": "cat_…"}}]` | **201** | confirmed |

**Three findings of consequence:**

1. **The write schema mirrors the read schema** — `*_decimal` string fields, nested `{category: {id}}` object. Not the flat/scalar shape legacy used.
2. **Line items are created by value, not by reference.** The singular `POST /line-items` documents `category`, `name`, `quantity`, `quote_id` as required and accepts **no `item_id`**. Render must fetch an item's values and copy them into the line item.
3. **Validation accumulates.** Per the docs, a 422 returns *every* failing rule across *every* item in the batch, each located as `line_items[i].field`. Callers should iterate `errors[]` rather than reading only the first.

**Legacy field conventions do not survive the migration.** TLC's `enhanced_quote_creator.py` posts `{quote_id, item_id, name, category, quantity, unit_price}` to `api.quoter.com/v1/line_items` — flat body, `category` as a string, `item_id` by reference, `unit_price` as a float. Every one of those conventions changed. That file remains a useful record of *intent*; none of its payload shape is reusable.

### 7.11 Section creation, and the full write chain — **[Confirmed, live, 2026-08-23]**

`POST /quotes/{id}/sections` accepts a **bare JSON array**, mirroring the line-item convention (§7.10). `name` is the only field that needs supplying:

```
POST https://api.scalepad.com/quoter/v1/quotes/{quote_id}/sections

[ { "name": "Balloons" } ]
```

→ **201 Created.** The response body is the whole quote, not just the new section.

Accepted on the first shape tried, so no error-driven derivation was needed. The four fallback shapes (bare array with `position`, flat object, `{"sections": [...]}` wrapper, empty object) were never reached and remain untested.

**Multiple sections per quote work.** Two were created in succession on the same draft and both persisted with distinct IDs, reading back in creation order:

```
[0] id=3IKjeMYoKK3rqQVzyOsRgw22FtM  name='Balloons'
[1] id=3IKjeLlzclWYKABtJ6WbjTl4URw  name='Travel & Expenses'
```

This matters more than the bare fact of creation: the §8 design needs one section per Item Group, so a one-section-per-quote limit would have forced everything into a single flat section and lost the layout entirely.

#### 7.11.1 The complete write chain

Verified end to end in a single run against production:

| Step | Call | Result |
| :-: | :-- | :-- |
| 1 | `POST /quotes` with `template_id`, `contact`, `custom_number` | 201 — `sections: null`, as always (§6.2) |
| 2 | `POST /quotes/{id}/sections` — `[{"name": "Balloons"}]` | 201 |
| 3 | `POST /quotes/{id}/sections` — `[{"name": "Travel & Expenses"}]` | 201 |
| 4 | `POST /quotes/{id}/sections/{sid}/line-items` — bare array, §7.10 schema | 201, line item present on read-back |

**Nothing in the composition path is now unverified.** Render can create a draft from one default template, add a section per Item Group, and populate each section by value. Section read-back confirmed `line_items` counts moving from 0 to 1 as expected.

#### 7.11.2 Section fields, from a live read

A section object carries: `id`, `name`, `line_items`, `optional_group_id`, `optional_selected`, four `discount_*` fields, and a server-computed `totals`.

Only `name` is caller-supplied. `id` and `totals` are computed; the discount and optional-group fields default to null.

`totals` breaks down by billing frequency — `one_time`, `monthly`, `quarterly`, `semi_annual`, `annual`, `upfront`, plus `taxes`. **[Hypothesis]** this is how a quote mixing one-time equipment with recurring services would separate them, which may matter if TLC ever quotes recurring line items. Nothing in the current design depends on it.

### 7.12 Four catalog mechanisms exist in Quoter and none are reachable from the API — **[Confirmed, 2026-08-23]**

Quoter offers several ways to relate catalog items to one another or to offer a choice within one item. Each was investigated as a way to avoid seeding several mutually-exclusive line items and having a human delete the surplus. **All four failed the same way, for the same underlying reason.**

| Mechanism | What it does in the UI | Via the API |
| :-- | :-- | :-- |
| **Template line items** | items attached to a template | never materialise (§6.2) |
| **Bundles** | one Item containing Items, with per-member qty and computed price | posts as one ordinary line, `bundle: false`, no expansion (§7.9) |
| **Parent / Child items** | a child cannot be picked from the item list; only its parent | relationship not exposed; children contribute nothing |
| **Item Options** | one item carries a priced choice (Standard/Advanced/Ultimate) | not exposed on read; no selector on an API-created line |

#### 7.12.0 Vendor confirmation — **[Confirmed, Jon Turner, 2026-08-23]**

The cause inferred below was put to ScalePad and confirmed:

> "Currently the API does not allow Single-Select Items/Groups or Bundles to be created, just single Line Items. This is a known limitation of the API and will likely be updated at some point. Similarly, we do not allow existing catalog Items to be added, just as ad-hoc Line Items."

Two points of substance.

**"Ad-hoc Line Items" is Quoter's own term** for what this chapter calls by-value creation. A line item is not a reference to a catalog record; it is a free-standing set of values. That is the vendor's stated design, not a gap in our understanding.

**It is a known limitation expected to change.** *"Will likely be updated at some point."* So §7.12 documents a current-state constraint rather than permanent architecture. If catalog-item references are added later, Bundles, Item Options and Single-Select Groups all become reachable at once, and the seed-and-prune approach (§7.12.4) could be revisited. Worth re-testing after any significant API release.

#### 7.12.1 The common cause

Line items are created **by value** (§7.10): `name`, `quantity_decimal`, `unit_price_decimal`, nested `category`. There is no `item_id` in the write schema, so **an API-created line item has no link back to the catalog record it was copied from.**

Every one of these four mechanisms depends on that link. A bundle needs to know which bundle to expand; an option selector needs to know which item's options to draw. With no reference, there is nothing to resolve.

The consistent rule: **anything requiring a reference to a catalog item is lost on an API write.** Only literal field values survive.

#### 7.12.2 Parent / Child — tested and inert

A scratch parent (`ZZ Parent Item`, category `Balloons / Drop`) and two children (`ZZ Child1`, `ZZ Child2`, category `Additional Options`, $1.00 each) were created in the UI.

- Children are **not selectable from the item list** — only parents appear.
- With the parent on a quote at qty 2, the preview showed a single line: `ZZ Parent Item`, 2 × $1.00 = $2.00. Children were absent and contributed nothing.
- There was **no way to select a child** once the parent was on the quote.

**[Resolved — §7.12.0]** ScalePad confirms Single-Select Items/Groups cannot be created via the API. Whatever the UI behaviour depends on, it is not reachable from the write path.

#### 7.12.3 Item Options — tested and UI-only

`FV-Standard Graphics Pkg` (`HG-FV-Graph-001`, sku 4, base price $500) was configured with an option `OptS` carrying three values: Standard $500, Advanced $1500, Ultimate $3000, with **REQUIRE SELECTION = Yes** and **ALLOW MULTIPLE = No**.

Note the modelling: the values are *resulting* prices, not increments — Standard matches the item's own $500 base. **[Hypothesis]** the option replaces the price rather than adding to it; not separately verified.

Results:

- `GET /items` exposes only `show_option_prices` (a boolean display flag). The configured values are **not returned**.
- `GET /items/{id}` returns **no additional keys** over the collection record. The single-record endpoint carries nothing extra.
- Posted by value into a section: 201, and the line read back with `options: null`, `bundle: false`, `optional: false`, `optional_group_id: null`.
- **Decisive check — the quote editor showed no selector.** The line rendered as name, category, qty, unit cost, price modifier, unit price, discount. No Standard/Advanced/Ultimate control anywhere.

This matters more than the others because **REQUIRE SELECTION = Yes**. An API-created line for an option-bearing item is one nobody can complete — strictly worse than seeding the three separate items.

#### 7.12.4 Consequence: seed generously, prune manually

No mechanism collapses mutually-exclusive variants into a single selectable line. So the design is:

- variants stay as **separate catalog items** (three graphics packages, four FV sizes, three wristband LED counts)
- Render **seeds all candidates** at `quantity_decimal: 1` (§7.5)
- the salesperson deletes, zeroes, or blanks what does not apply — the three-way pruning already verified across API response, preview, webview, and PDF (§7.4, §7.5)

**This is the right outcome for a reason independent of the API limits.** A quote seeded with real catalog items teaches the catalog: the salesperson sees what exists, what it is called, and what it costs. A blank template invites invention — a free-text line at a made-up price, with no `code`, no `sku`, and therefore no Pipedrive product linkage (§2.2.4, §2.2.6) and a hole in margin analysis. Pruning a seeded quote is a smaller act than knowing what to create.

#### 7.12.5 One lead not yet followed

The quote editor offers **`+ Add Single Select Section Group`** alongside `+ Add Section`. That is a mutually-exclusive group of *sections* — a Good/Better/Best structure where the client picks one — which is close to what Item Options would have given, one level up.

Both the section and line-item schemas carry `optional_group_id` and `optional_selected`, null in everything read so far. **[Resolved — §7.12.0]** ScalePad confirms Single-Select Items/Groups are not creatable via the API. This was the last remaining candidate for API-driven choice, and it is closed for now — though listed among the limitations expected to be updated.

Also noted in the editor: a per-line **Price Modifier** column with a markup/margin dropdown. Worth understanding before Render sets prices, since a modifier may interact with the `unit_price_decimal` it posts.

---

Everything above is verified behaviour. This section is a design that follows from it. **As of 2026-08-23 it has no unverified prerequisites** (§7.11) — but it has not been built yet.

**[Hypothesis — our reading, not the vendor's claim]** Asked why templates do not expose their line items, ScalePad's answer included *"for API Quotes, Items can be added automatically anyway"* (§6.2.1). That is offered as a justification for the absent endpoint, and it is consistent with this design — but it does not establish that ScalePad intends or endorses it. The sentence supports "the API has a line-items endpoint, so you can populate quotes"; reading it as "composing quotes from your own content model is the intended pattern" is our inference and should not be recorded as vendor guidance.

## 8. Proposed Architecture — **DESIGN, NOT AS-BUILT**

Everything above is verified behaviour. This section is a design that follows from it. **As of 2026-08-23 it has no unverified prerequisites** (§7.11) — but it has not been built yet.

**[Hypothesis — our reading, not the vendor's claim]** Asked why templates do not expose their line items, ScalePad's answer included *"for API Quotes, Items can be added automatically anyway"* (§6.2.1). That is offered as a justification for the absent endpoint, and it is consistent with this design — but it does not establish that ScalePad intends or endorses it. The sentence supports "the API has a line-items endpoint, so you can populate quotes"; reading it as "composing quotes from your own content model is the intended pattern" is our inference and should not be recorded as vendor guidance.

### 8.1 The problem being solved

Render currently holds each template's line items as hard-coded Python (`template_mapping_enhanced.py`), on the legacy API. Two consequences: a template edited in Quoter leaves Render writing stale items until a developer redeploys, and the shared T&E/Shipping/Labor blocks exist as 11 independent copies, already measurably diverged (§7.7).

### 8.2 Composition instead of template mirroring

Because a template contributes **nothing** to a quote's line items via the API (§6.2), the automated path gains nothing from choosing among 11 templates. A template supplies cover page, content blocks, and branding only. **One default template is sufficient for API-created drafts.**

That reframes what Pipedrive should pass. Instead of a single `Template` name, it passes a set of Item Group names:

```
Pipedrive:  Groups = [ Balloons, Services-Technician, Shipping, Travel-Expenses ]
    ↓
Render: for each group → GET /item-group-item-assignments → item_ids
    ↓
        → GET /items (filter[code] or fields=) → name, price_decimal, category_id
    ↓
        → POST /quotes/{id}/sections            (one section per group)
        → POST …/sections/{sid}/line-items      (bare array, §7.10)
```

**Why this is attractive:** the shared blocks exist exactly once, so drift becomes structurally impossible rather than something a sweep has to police. Adding a new product line means one new group, not a new template plus copies of every shared block. And since Render must create sections anyway (a template-created quote has none), naming each section after its group produces the section layout for free.

**The dependency is now verified.** `POST /quotes/{id}/sections` was untested when this design was written. It was tested live on 2026-08-23 and works — see §7.11. The design has no remaining unverified prerequisites.

### 8.2.1 Group membership is derived from `code` prefix, not from a swept list — **[2026-08-23]**

An earlier draft of this section assumed each Item Group would be populated from a template sweep. That is superseded.

**Membership resolves from three inputs**, defined in `item_group_defs.json` rather than in Python:

| Input | Purpose |
| :-- | :-- |
| `code_prefixes` | derivable baseline — every item whose `code` starts with e.g. `BAL-` |
| `include_codes` | cross-family items a prefix cannot capture |
| `exclude_codes` | prefix matches that do not belong |

**Why prefix rather than category.** The API returns only a category's leaf name and 16 leaf names collide across parents (§2.3.2), so category selection is ambiguous. It also sweeps in test data: `Balloons / Latex` holds 11 `zz-test` fixtures, so a category-derived Balloons group resolves to 20 items, 11 of them junk. The `ZZZ-` prefix excludes them for free — 8 items, all real.

**Why prefix rather than the template sweep.** The template is an incomplete view of the catalog. The Balloons template carries 6 balloon items; the catalog holds 8 — `Balloon- 12 ft` and `Balloon- 8 ft` were never added. A template-derived group could not offer them, and under seed-and-prune (§7.12.4) the point is to show the salesperson what exists.

**The property that matters: the baseline is derivable, not maintained.** Add a `BAL-` item to the catalog and it joins `XRN-Balloons` by construction. No sweep, no list to update, no drift. This is a materially stronger position than a mirrored list, which is what §7.8/§11 were built to keep in sync.

**`include_codes` exists because prefixes cannot express dependency.** An exploding balloon wall is a pyro effect and may require `PYR-LIC-TEC` (licensed pyrotechnician) and `PYR-PRM-001` (permit). No prefix rule captures that; it is a judgement call and must be stated explicitly. **[Open]** whether those specific pyro items belong on balloon quotes has not been decided — seeding a pyrotechnician onto every balloon quote would be wrong, and omitting one where it is legally required is worse.

#### 8.2.2 Prefix discipline is now load-bearing

A mistyped prefix silently drops an item from its group, with no error. Known offenders as of 2026-08-23:

| Code | Problem |
| :-- | :-- |
| `BAL-FLY` | missing the `-NNN` suffix |
| `BAL-HEL-08F`, `BAL-HEL-12F` | non-numeric suffix |
| `PYRO-FIR-REAL` | `PYRO-` rather than `PYR-`, so a `PYR-` filter misses it |
| `MGS` | Quoter demo item, no prefix at all |

`scalepad_items_maint.py` already has `scan_dup_codes()`; a scan for codes not matching the `XXX-YYY-NNN` shape would catch the rest. Worth running before more groups are defined.

**Catalog prefixes present, by count (2026-08-23):** LED 40, HG 29, ROB 27, SVC 26, PYR 17, LSR 15, PRO 14, TNK 13, SHP 11, ZZZ 11, CNF 9, FOG 9, EQP 9, DRN 8, BAL 8, T&E 8, WTR 7, FIN 6, AI 4, DMX 4, SNO 3, SPH 2.

That taxonomy is already disciplined enough to drive group membership, which resolves much of the naming-convention question: **it is largely already answered in the `code` field.**

### 8.3 Known trade-off

A single dropdown becomes a multi-select, and correctness moves to whoever fills it in. Worth considering a named "profile" — a stored set of groups — so sales still picks one thing. **[Hypothesis]** that mapping could live in Pipedrive, or be implied by a naming convention. Not designed.

### 8.4 Key on IDs, not names

If Pipedrive's field must match an Item Group name for Render to resolve it, the two must stay locked forever. `Robotics`/`robitics` (§7.7) shows how that drifts. Prefer keying on stable IDs, with names as display only.

### 8.5 Proposed D-011 — draft for `docs/DECISIONS.md`

Per the Decision Lifecycle, D-009 should not be edited. The following is offered as a new entry for Eric's review, not as a decision already taken.

> **D-011 — Item Groups are Repurposed, Not Purpose-Built**
>
> *Supersedes the premise of D-009; the decision itself stands.*
>
> **Decision**
>
> ScalePad Item Groups remain the operational mirror of Quoter Templates, as established in D-009. This entry records that Item Groups are a **reseller access-control feature**, not a general grouping primitive, and that TLC's use of them is a deliberate repurposing.
>
> Two conditions attach:
>
> 1. The repurposing is valid only while no Resellers are configured on the account. If reseller functionality is ever enabled, every mirror group silently becomes a grant of item visibility, and the mirror must be relocated before that happens.
> 2. Item Group Assignments carry no quantity field. The mirror can express membership only. Quantity is supplied at quote-composition time.
>
> **Reason**
>
> D-009 was written 2026-06-30, before the Item Group object had been inspected. Verification on 2026-08-20 established its actual product purpose from the `/admin/item_groups/add` form. Nothing else in Quoter is simultaneously named, arbitrary, API-readable and API-writable, so the mirror has no better host — but the coupling to an unused permissions feature is a real dependency and should be recorded rather than discovered later.
>
> **Amendment note, 2026-08-23:** the maintenance concern behind this entry has narrowed. §11 establishes that a Pipedrive dropdown can be kept in step with Item Groups automatically, so repurposing an ACL object no longer implies hand-maintaining two lists. The reseller-collision condition in (1) still stands.
>
> **Also recorded:** Quoter Bundles were evaluated as an alternative and rejected for this purpose. A Bundle is a genuine multi-item construct with per-member quantity and computed pricing, but v2 creates line items **by value** with no item reference (§7.10), so a Bundle cannot expand via the API. Bundles remain useful for humans composing quotes in the UI and are invisible to Render.

---

## 9. Section Writes Are Eventually Consistent — **[Confirmed, live, 2026-08-24]**

The single most expensive finding of the build, because it is invisible until a quote has more than one section, and it is not documented anywhere.

### 9.1 The symptom

Composing a quote with several sections fails partway. The first section fills; posting line items into the second returns:

```
404 {"errors":[{"code":"ERR_NOT_FOUND","title":"Not Found","detail":"Record not found"}]}
```

— on a section id that was read back **moments earlier** and that demonstrably exists.

### 9.2 What it is not

Three explanations were proposed and each was wrong. They are recorded because each is a plausible-sounding theory that a future reader might arrive at independently:

| Theory | Tested how | Result |
| :-- | :-- | :-- |
| Creating a second section invalidates the first | created three in one call, read back | all three stable, all valid |
| Posting line items regenerates the other sections' ids | filled section 0, re-read all | ids unchanged |
| Section ids are not durable handles at all | read twice with no write between | identical both times |
| Multi-section composition never worked | inspected an earlier quote | it had worked — two populated sections |

**Section ids are stable. Writes do not regenerate them. Both creation patterns — all-at-once and one-at-a-time — work.** A diagnostic exercising every one of those paths passed cleanly.

### 9.3 What it is

**A race.** The API is eventually consistent on section reads: immediately after a write, a read can return section ids from a replica that has not caught up, and posting to one of those ids returns 404.

The evidence is timing, not schema:

- the diagnostic used ~1.5s pauses between operations and passed every time
- `compose_quote.py` used 0.2–0.5s and failed on the second section
- the failing run created a quote at 17:37:22 and hit the 404 at 17:37:24 — the whole sequence inside two seconds

**Why it hid for so long:** a single-section quote never performs a second write, so it never exposes the race. Every earlier successful run used one Item Group.

### 9.4 The fix, and why not just sleep longer

`ScalePadQuotes.add_line_items_retrying()` re-reads the section list before **every** attempt and retries on 404, five times, 1.5s apart.

Retrying rather than sleeping matters: a longer sleep only makes the race less likely, and picks an arbitrary number that will be wrong under different load. A retry is correct regardless of how long the replica takes.

Confirmed live 2026-08-24 — a three-section quote where sections 2 and 3 each 404'd once and succeeded on the second attempt:

```
+ Balloon Effects              8 line item(s)
+ Services                     5 line item(s)   (after 2 attempts)
+ Shipping, Travel & Expenses  1 line item(s)   (after 2 attempts)
VERIFIED: 3 section(s), 14 line item(s)
```

**Render must do the same.** Any multi-section quote will hit this.

### 9.5 Address sections by index, never by name

A second constraint, independent of the race. Section names need not be unique — `SFX-Wristbands-Zone` and `SFX-Wristbands-Pixel` both render as "LED Wristbands" (§10.3), and a quote may legitimately carry both. A name-based lookup would write both groups' items into whichever section it found first.

So sections are addressed by position, with the name checked only as a guard that raises rather than writing into the wrong section.

### 9.6 Process note

This took four attempts to diagnose. The first three were theories asserted without measurement, each producing a code change that did not fix it. What settled it was a throwaway diagnostic script that printed the section list at every step and tried each pattern in isolation — written only after the third failure.

The general lesson matches §7.1 and §2.2.2: **when an API misbehaves, instrument before theorising.** Every wrong turn in this chapter came from inferring a mechanism instead of observing one.

---

## 10. The Item Group Catalog — **[Confirmed, built, 2026-08-24]**

22 Item Groups now exist, resolved from catalog code prefixes rather than from template contents. §8.2.1 gives the reasoning; this records what was built.

### 10.1 Naming — three names, three audiences

| | Example | Audience |
| :-- | :-- | :-- |
| group key | `SFX-Balloons` | maintenance, Render's lookup, the Pipedrive dropdown label |
| `section_name` | `Balloon Effects` | the **client**, as the section heading on the quote |
| code prefix | `BAL-` | determines membership |

Group key and Pipedrive option label **must** stay identical — the sync matches on them. The section name is referenced by nothing and supplied at write time, so it is free.

**This split is forced, not stylistic.** Quoter has **no setting to hide section headings** — Display Settings covers pricing table, cost breakdown, margins, discounting, one-time/recurring split, shipping, tax and totals, and nothing else. Whatever a section is called appears on the customer's quote, so internal taxonomy must not leak into it. An earlier composed quote shipped with `XRN-Balloons` as the client-facing heading, which is what surfaced this.

The convention: **`SFX-`** effects (feature) · **`SVC-`** generic services · **`STE-`** shipping, travel and expenses.

### 10.2 The 22 groups

| Group | Section name | Prefixes | Items |
| :-- | :-- | :-- | :-: |
| `SCO-ScopeOfWork` | Scope of Work | `SCO-` | 1 |
| `SFX-Balloons` | Balloon Effects | `BAL-` | 8 |
| `SFX-FloatingVideo` | Floating Video | `HG-FVV-`, `HG-FV-Graph-` | 10 |
| `SFX-HoloPortal` | Holographic Displays | `HG-HP-` | 16 |
| `SFX-Wristbands-Zone` | LED Wristbands | `LED-WBT-2LED-`, `LED-WBT-TX158-` | 10 |
| `SFX-Wristbands-Pixel` | LED Wristbands | `LED-WBT-4LED-`, `LED-WBT-TX305-`, `LED-WBT-TX306-` | 12 |
| `SFX-Lanyards` | LED Lanyards | `LED-LYT-`, `LED-LAN-` | 9 |
| `SFX-GlowBalls` | LED Glow Balls | `LED-GLOBAL-`, `LED-GLOTX-` | 7 |
| `SFX-GlowOrbs` | LED Glow Orbs | `LED-GLOORB-` | 2 |
| `SFX-Robotics` | Robotics | `ROB-` | 30 |
| `SFX-Lasers` | Laser Effects | `LSR-` | 16 |
| `SFX-Pyro` | Pyrotechnics | `PYR-`, `PYRO-` | 19 |
| `SFX-Confetti` | Confetti & Streamers | `CNF-` | 10 |
| `SFX-Fog` | Atmospherics | `FOG-`, `CO2-` | 12 |
| `SFX-Tanks` | Gas & Tanks | `TNK-` | 14 |
| `SFX-Projection` | Projection | `PRO-` | 15 |
| `SFX-Drones` | Drones | `DRN-` | 8 |
| `SFX-Water` | Water Effects | `WTR-` | 7 |
| `SFX-Snow` | Snow Effects | `SNO-` | 3 |
| `SVC-General` | Services | *(explicit)* | 5 |
| `STE-All-In` | Shipping, Travel & Expenses | `SHP-`, `T&E-` | 19 |
| `STE-After-Bill` | Shipping, Travel & Expenses | *(explicit)* | 1 |

Definitions live in `item_group_defs.json`; `build_item_groups_v3.py` applies them, dry run by default.

### 10.3 Two groups may share a section name — deliberately

`SFX-Wristbands-Zone` and `SFX-Wristbands-Pixel` both render as "LED Wristbands". The two systems are incompatible — zone is 433MHz with 10 group-level zones by demographic; pixel is individual control with up to 100 groups, Excel-driven with real-time selection — but a salesperson unsure which the show needs picks **both** and prunes in the quote. The client then sees two sections under one heading, which reads correctly.

This is why sections are addressed by index rather than name (§9.5).

### 10.4 Retirement is handled by prefix, not by exclusion

The catalog already encodes current versus legacy in the code itself:

| Current | Legacy |
| :-- | :-- |
| `LED-WBT-*` TLC wristbands | `LED-WBX-*` Xylobands |
| `LED-LYT-*` TLC lanyard | `LED-LYX-*` Xylo lanyard |
| `HG-FVV-*` Vdisplay | `HG-FVH-*` Hypervsn |

Groups take only the current prefix, so legacy items **stay in the catalog** for servicing kit in the field but **cannot be newly quoted**. No exclusion list to maintain, and nothing silently reappears when someone adds an item.

### 10.5 Specialist labour goes in its feature group; generic labour is shared

`SVC-` holds both kinds, so a blanket `SVC-` prefix rule would put a robot handler on a balloon quote. Hence:

- **specialist** — `SVC-ROB-HDLR/SUP/TECH`, `SVC-LSR-TECH`, `SVC-WBT-TECH`, `SVC-PGM-WB-LY-*`, `SVC-RPR-CO2`, `SVC-TNK-TEC`, `SVC-LAB-HP`, `SVC-PROJ-TECH-001` — `include_codes` on the relevant `SFX-` group
- **generic** — `SVC-LAB-001`, `SVC-TEC-001/002`, `SVC-LAB-OVR`, `SVC-STF-001` — the shared `SVC-General` block, which has **no** `code_prefixes` and explicit membership only

### 10.6 `STE-After-Bill`

`STE-All-In` and `STE-After-Bill` cover the same scope; only the billing timing differs. All-In itemises 19 priced lines. After-Bill is **one** $0.00 line stating the cost is invoiced separately.

That required a new catalog item — `STE-AFTER-001`, "T&E - Billed After Event", category `T&E / Terms`, price 0.00, non-taxable.

**The code is deliberately not `T&E-AFTER-001`.** `STE-All-In` takes every `T&E-` prefixed item, so a `T&E-` code would sweep the explanatory line onto itemised quotes as well. A different prefix keeps the groups disjoint with no exclusion to maintain.

**[Superseded by §14.1 — 2026-08-26.]** This section originally recorded that item descriptions do not render client-facing. That is true of the CATALOG item's description, but a LINE ITEM has its own description field which does render. Once the composer copied one to the other, the wording below appeared correctly and this problem resolved itself.

The description was written to carry the terms — *"Travel and expenses are not included in this quote. Airfare, lodging, meals, per diem, ground transport and shipping will be invoiced at actual cost following the event."* The rendered quote shows only Category, Item, Qty, Price, Total. The client sees `Terms | T&E - Billed After Event | 1 | $0.00`.

So **anything the client must read has to be in the item NAME.** The Category column does render, which is why `Terms` was a useful choice.

**[Open]** The current line tells a client that T&E is billed later, but not what it covers or that it is at actual cost. Either lengthen the name, or put the terms in the template's Appended Content or a Content Block. A commercial decision, not a technical one.

### 10.7 Auto-appended groups — `SCO-ScopeOfWork` — **[Built 2026-08-26]**

A group marked `auto_append: true` in `item_group_defs.json` is added to every quote by the composer and is **excluded from the Pipedrive dropdown**. `position: "first"` puts it ahead of the selected groups.

Currently one: **`SCO-ScopeOfWork`**, section name **Scope of Work**, holding a single item `SCO-WORK-001` "Scope of Project" at $0.00, whose description carries placeholder text the salesperson rewrites per deal.

**Why automatic rather than selectable.** Every quote should describe what is being sold, so leaving it to a dropdown choice means someone can forget. Auto-appending removes that failure mode and keeps the Quote Effects list shorter.

**Why excluded from the sync.** An option sales should never pick would only invite a duplicate Scope section. `sync_quoter_to_pipedrive.py` filters auto-append groups out of the dropdown; the composer also de-duplicates, so selecting it would be harmless if it ever appeared.

**It works only because line item descriptions render** (§14.1). Before that fix a Scope section would have shown a bare item name and nothing else.

`SVC-General` stays **selectable** by contrast. Generic labour is on most quotes but not all — a dry hire where the client provides crew genuinely needs none — so it remains a judgement call.

**Naming.** The `X` prefix is gone; every group now starts with `S`:

| | |
| :-- | :-- |
| `SCO-` | scope of work |
| `SFX-` | effects |
| `SVC-` | generic services |
| `STE-` | shipping, travel, expenses |

### 10.8 Also confirmed

**Line items are seeded at $0.00, not at catalog price.** TLC re-prices per customer and per deal, so a seeded catalog price reads as a decision nobody made, and a missed one ships wrong. `$0.00` is unmistakably unpriced. `--catalog-price` opts in where an item genuinely does not vary. Zero price is safe where zero *quantity* is not: the API rejects quantity 0 but accepts `unit_price_decimal: "0.00"` (§7.3, §7.5).

**Unit cost is carried through**, so the margin column works in the editor while the client-facing price stays blank.

**Items appear in code order, not group order.** Assignment order is not preserved. If presentation order ever matters commercially, `compose_quote.py` must sort explicitly.

**Quoter greys out the Price Modifier on items with no unit cost**, so those can only be priced by entering a number, not by markup.

---

## 11. Pipedrive Dropdown Synchronisation — **[Confirmed, built and running]**

**Updated 2026-08-25:** two fields are synced, by a **GitHub Actions workflow**, not by local cron. See §11.11.

| Field | Dropdown | Type | Source |
| :-: | :-- | :-- | :-- |
| 90 | Quote Template | `enum` | Quoter quote templates — presentation |
| 102 | Quote Effects | `set` | Quoter Item Groups — content |

Field 102's key is `118a5ce132f73d7fec1822e2a0431b51ac2a2994`; it is Required from the *Send Quote/Negotiate* stage onward. Its 20 options (507–526) were created by the sync on 2026-08-24 from the groups in §10; the initial placeholder was retired to `XX-RET-Option1 Placeholder` rather than deleted.

Being a `set` rather than an `enum` is the point: a show using lasers, floating video and fog selects three effects, and Render composes one section per selection.


The composition design (§8) depends on Pipedrive telling Render what to build. That only works if what Pipedrive offers stays in step with what exists in Quoter. This section documents the mechanism, which is now built, tested against every lifecycle case, and scheduled.

### 11.1 The problem, stated precisely

Two halves, and only the first is obvious.

**Adding an option** so a new Quoter template or Item Group becomes selectable.

**Resolving it afterwards.** A Pipedrive deal stores a custom-field option's **numeric ID**, not its label. A webhook carries `"42ab0c91…": "451"`, so something must map `451 → "Balloons"`. Historically that map was built by hand: create the options in Pipedrive's UI, look up their IDs, hardcode them into Python. Every new template meant a code change.

### 11.2 `POST /dealFields/{id}/options` does not exist — **[Confirmed]**

```
POST /v1/dealFields/90/options
→ 404 {"error": "Route POST:/v1/dealFields/90/options not found"}
```

**Consequence: `sync_templates_to_pipedrive.py` (Jan 2026) has never worked.** Every write it makes goes through that route. It is dead code and should be deleted or clearly marked; leaving it in place invites someone to trust it.

### 11.3 `PUT /dealFields/{id}` works, and preserves ids — **[Confirmed]**

The supported path replaces the entire options array. Existing options must be sent **with their `id`**; new ones carry only `label`.

The hazard is that omitting an existing option's id lets Pipedrive reassign it — silently repointing every deal that stored it. So the behaviour was verified on a **scratch field**, not on production:

| | Before | After |
| :-- | :-- | :-- |
| 499 | `zz-alpha` | `zz-alpha` |
| 500 | `zz-beta` | `zz-beta` |
| 501 | — | `zz-added-153006` |

Ids preserved, one added. Then confirmed on the real field: option 452 was relabelled `Co2/smoke/upright foggers` → `CO2/Smoke/Upright Foggers` **keeping id 452**, and `ZZ Test Template` was added as 502 — with all eleven pre-existing options untouched.

**Renaming is therefore safe**, and it is what makes the whole scheme workable: a Quoter rename becomes a label change on the same id, and deals keep resolving.

### 11.4 The Quote Template field — **[Confirmed]**

| | |
| :-- | :-- |
| numeric id | `90` |
| key | `42ab0c919271cb24f3587f0b01ea2af166019c8d` |
| type | `enum` (single option) |
| flags | Required, Important, all pipelines, all users |
| field group | Quoter |

Its 11 options (441–457) mapped one-to-one onto the 11 Quoter templates. Ids are assigned in creation order, not alphabetically — 441–444 are the original batch, 451–457 added later.

`GET /api/v2/dealFields` also returns 200, so v2 exposes fields; v1 was used because the options write is documented there and because `pipedrive.py` already authenticates that way.

### 11.5 What was built

Split per D-003 — transport and resource wrappers separate from business logic.

**`pd_fields.py`** — resource wrapper over `PipedriveV1Client`. `set_options()` refuses to write if any pre-existing option is missing from the array, and after writing verifies that no id changed meaning, raising `OptionIdDrift` if one did. `option_map(field_id)` returns `{id: label}` — the runtime lookup that retires the hardcoded map.

**`sync_quoter_to_pipedrive.py`** — diff and apply. Sources are `--source templates` (`/quoter/v1/quote-templates`) and `--source item-groups` (`/quoter/v1/item-groups`), both read through `ScalePadV2Client`. Dry run by default.

**`.github/workflows/pipedrive-dropdown-sync.yml`** — the scheduler. Runs both fields daily at 13:00 UTC (06:00 PT), plus manual dispatch with `dry_run` and `retire_orphans` inputs. See §11.11.

**`sync_dropdowns.sh`** — retained for manual local runs only. **No longer the scheduler.** Resolves `venv/bin/python3` explicitly, sources `.env`, logs to `logs/`.

### 11.6 Why there is a state file

Matching Quoter records to Pipedrive options **by label cannot distinguish a rename from a delete-plus-create.** Rename "Robotics" to "ROB-Robotics" and a label-matcher adds a new option and orphans the old one — while every existing deal still points at the old id.

So `pd_option_map_templates.json` holds `{quoter_id: pipedrive_option_id}`. With it, a rename is a label change on a known id. On first run the map is empty and existing options are adopted by case-insensitive label match.

**This file must persist and be committed.** Lose it and every rename degrades into an orphan plus a duplicate. Render's disk does not survive a redeploy, so a repo-committed file is the current answer.

### 11.7 Deletion is never automatic

A deleted Quoter record does **not** delete its Pipedrive option. With `--retire-orphans` the option is relabelled `XX-RET-<name>`:

- the **id survives**, so any deal storing it still resolves to a readable label
- the prefix sorts to the bottom of Pipedrive's A-Z list and reads as not-for-selection
- retired options are **excluded from future orphan reports**, so the orphan list stays meaningful rather than becoming noise people learn to ignore
- if a record with that name returns, the retired option's id is **reused** rather than a duplicate created

Actual removal stays a human decision in the UI, taken only after confirming nothing references the option. This preserves the instinct in the older script — *"These won't be automatically removed for safety"* — which was right even though its endpoint never existed.

### 11.8 Lifecycle, all verified live

| Case | Behaviour | Verified |
| :-- | :-- | :-- |
| **Adopt** | first run pairs 11 templates to options 441–457 by label | ✓ |
| **Create** | `ZZ Test Template` → option 502, existing ids untouched | ✓ |
| **Rename** | 502 relabelled `ZZ Renamed Template`, **id preserved** | ✓ |
| **Casing** | 452 normalised to Quoter's casing, id preserved | ✓ |
| **Retire** | orphan → `XX-RET-ZZ TEST3 Template`, id kept | ✓ |
| **Ignore** | retired options no longer reported as orphans | ✓ |
| **Recreate** | option deleted in Pipedrive → recreated on next run | ✓ |
| **Un-retire** | returning record reuses the retired id | unit test |

**No option id has been renumbered at any point, and nothing has been deleted.**

### 11.9 Consequences for the wider design

**It removes the maintenance objection to Item Groups.** §7.8 established that Item Groups are a reseller ACL repurposed as a lookup table, with no friendly editor. The counter-argument was that someone would have to hand-maintain both the groups and the Pipedrive dropdown. The dropdown half is now automatic, and `--source item-groups` already exists.

**It retires the hardcoded option map.** Render can call `option_map(90)` at runtime rather than carrying `{451: "Balloons", …}` in Python.

**It is the first piece of this workstream running on ScalePad v2 in an operational role** — not a probe. The Quoter side reads v2; the Pipedrive side is Pipedrive v1, unrelated to the Quoter v1/v2 split (D-001/D-002).

### 11.10 Known gaps

~~**Cron runs on the Mac Mini**, so it only fires when that machine is awake.~~ **[Resolved 2026-08-25 — see §11.11.]** It did not fire at all. Moved to GitHub Actions.

**No pruning of stale state.** Mappings whose Quoter record is gone stay in the file — currently 14 pairings against 11 templates. Harmless, but it accumulates.

**`--retire-orphans` runs unattended** in the scheduled workflow, so a template deleted in Quoter is relabelled without review. Acceptable because it is non-destructive and reversible, but it is an automatic write to a production field.

~~**`sync.sh`'s workflow validator produces false positives.**~~ **[Fixed 2026-08-26.]** It counted quote characters per line including inside `#` comments, so any apostrophe in prose failed validation with "Unclosed single quotes". It now skips comment-only lines, and still catches unbalanced quotes in actual YAML values.

~~**`sync.sh` misreports a pending push.**~~ **[Fixed 2026-08-26.]** It exited on "nothing to commit" without checking whether the branch was ahead of origin, so a failed push read as "everything is already synced". It now fetches, counts unpushed commits, and pushes them. This recurs by design: the dropdown-sync workflow commits state files to `main` on its own schedule, so a local push can be rejected on a stale ref. **`./retrieve.sh` before `./sync.sh` is now the habit**, and `git config pull.rebase true` avoids a merge commit each time.

**Untested:** whether ScalePad's `/quote-templates` returns the same set the legacy endpoint did. Both reported 11, but they have never been diffed directly. If they drift, the sync mirrors the wrong list.

---

### 11.11 Scheduling: local cron was the wrong host — **[Corrected 2026-08-25]**

The sync was first installed as a `crontab` entry on the Mac Mini at `0 6 * * *`. **It never fired.** The log contained only the manual run from the day it was set up.

**Why.** cron does not run while the machine is asleep. A workstation is the wrong host for scheduled work — it sleeps, it travels, it gets rebooted, and a missed run is silent.

**This was a known flaw that was documented instead of fixed.** The limitation was written into the script as a comment and into this chapter as a "known gap" on the day it was built, and then never raised again. Recording a defect is not the same as flagging one; the note simply sat there while the job quietly did not run.

**What it should have been from the start.** The repository already had the pattern: `.github/workflows/` contains `smart-template-sync.yml`, `complete-sync.yml` and `daily-bundle-verification.yml`, all scheduled GitHub Actions with `workflow_dispatch` for manual triggering — and `sync.sh` validates them on every commit. Render was also considered and ruled out: `render.yaml` defines a single free-plan web service (`quoter-webhook-server` running `webhook_handler.py`) and no cron service, and a free-plan service spins down when idle.

#### 11.11.1 `.github/workflows/pipedrive-dropdown-sync.yml`

| | |
| :-- | :-- |
| Schedule | `0 13 * * *` — 13:00 UTC, 06:00 PT |
| Manual | `workflow_dispatch` with `dry_run` and `retire_orphans` inputs |
| Secrets | `SCALEPAD_API_KEY`, `PIPEDRIVE_API_TOKEN` (GitHub Actions secrets — separate from Render's, which are not visible to a runner) |
| Python | 3.11 |

Steps: checkout → Python → deps → env → **verify credentials** → build flags → field 90 → field 102 → **commit state files** → report.

**Credential verification fails fast** rather than producing a run of 401s. It prints lengths only, never values, and rejects a `cid_`-prefixed key outright — the legacy Quoter client_id that has been mistaken for the ScalePad key before (§2.1.2).

**Field 102 runs `if: always()`**, so it still syncs when field 90 fails. They are independent dropdowns and a failure in one says nothing about the other.

#### 11.11.2 The state files must be committed by the workflow

`pd_option_map_*.json` are what make a rename distinguishable from a delete-plus-create (§11.6). A GitHub Actions runner is ephemeral, so a file written during a run is lost unless committed.

The workflow therefore commits them back to the repo, under `permissions: contents: write`. **This is not housekeeping — it is what makes rename detection work at all.** Without it, every rename would degrade into a new option plus an orphan, while existing deals continued pointing at the old id.

Confirmed live on the first real run: `STE-AllIn` → `STE-All-In` renamed with option id 526 preserved, `STE-After-Bill` added as option 527, state written to 21 pairings, and committed as `930e159..9074e19`.

#### 11.11.3 Notes

The other three workflows are currently **Disabled**, with their last runs in November 2025. Deliberate, per Eric — they had nothing left to update.

**[Hypothesis]** GitHub auto-disables scheduled workflows after 60 days of repository inactivity. If so, this workflow is subject to the same rule, and a quiet period would silently stop the sync. Worth verifying rather than assuming, since the failure is silent either way.

`actions/checkout@v4` and `actions/setup-python@v4` raise a Node 20 deprecation warning. Cosmetic now; bumping to `@v5` avoids a future break. The other three workflows use v4 as well.

---
## 12. The Contact Dependency, and the Contact Schema — **[Confirmed, 2026-08-26]**

### 12.1 `createQuote` resolves a contact; it does not create one

An email with no contact record returns:

```
422 {"errors":[{"code":"ERR_CONTACT_NOT_FOUND",
                "detail":"contact.email not found"}]}
```

**This corrects a misreading of §5.1.** That section records that `createQuote`, given an email plus a `client_name`, materialises a fully-resolved contact with a real `cont_...` id. True — but only for an email that **already exists as a contact**. Every earlier v2 test used `zz-test-chapter3@tlciscreative.com`, created beforehand by a standalone `POST /contacts`, which hid the dependency entirely.

So the sequence is the same as legacy: **create or find the contact first, then create the quote.** `quoter.py` has always done this — `create_or_find_contact_in_quoter()` runs before `POST /v1/quotes`. Only the endpoint and field names change.

### 12.2 The contact schema

Read off a live record rather than guessed, after three failed attempts cost three round trips:

| Field | |
| :-- | :-- |
| `billing_email` | required — **this is the handle**, not the id |
| `billing_first_name` | required |
| `billing_last_name` | required |
| `billing_address` | required, and a **nested object** |
| `billing_organization` | optional |
| `billing_work_phone`, `billing_mobile_phone` | optional |
| `title`, `website` | optional |
| `shipping_*` | optional, mirrors billing |

```json
"billing_address": {
  "address_line_1": "30 Rockefeller Plaza",
  "address_line_2": null,
  "address_line_3": null,
  "city": "New York",
  "state_prov_code": "NY",
  "postal_code": "10124",
  "country_code": "US"
}
```

**There are no flat address fields.** `billing_city`, `billing_country_iso`, `billing_region_iso` and `billing_postal_code` do not exist; sending them returns `400 ERR_REQUEST_FORMAT_INVALID`.

Note the error grammar, which is consistent across this API and worth reading carefully: **a 422 is about the CONTENTS of the body, a 400 about its SHAPE.** The 422 naming three required fields meant those names were right; the 400 that followed meant something added afterwards was structurally wrong.

### 12.3 The write schema mirrors the read schema — every time

Three separate endpoints now follow the same rule:

| Endpoint | Nested structure |
| :-- | :-- |
| line items | `category: {id}` |
| contacts | `billing_address: {address_line_1, city, ...}` |
| sections | bare array, matching how sections read back |

**So when a write shape is unclear, `GET` a real record.** Three guesses at the contact schema cost three round trips; reading one record settled it immediately. The same shortcut would have solved the line-item schema (§7.10) faster than deriving it from successive 422s.

### 12.4 Required Fields is an account setting, and it governs the API

**Settings → Required Fields** — *"Indicate which fields are required for a Person when creating a Quote or Person."*

Four are locked **Mandatory** and cannot be unticked: **First Name, Last Name, Email, Country**. The rest are toggles: Phone, Organization, Title, Street Address, Street Address 2, Region, City, Postal Code.

**Unlike the quantity validation of §7.3/§7.4, this setting governs both the UI and the API.** Unticking Street Address, Region, City and Postal Code removed `billing_address is required` from the 422.

**[Confirmed — Eric, 2026-08-26]** TLC's position: enforce data quality **in Pipedrive**, at the stage gate, rather than in Quoter. A salesperson can fix a missing field on the deal in front of them; they never see a webhook fail. So Quoter's requirements were relaxed to Organization and the four mandatory fields, and Pipedrive becomes the gatekeeper.

Three rules follow, and all three are Pipedrive-side work not yet done:

- **Organization is required to reach the quote stage.** Everything downstream depends on it — the Quoter Client resolves from the org name (§3.3), and Pipedrive creates the QBO customer from it too. One rule serves all three consumers.
- **A private client still gets an Organization**, named after the person. Avoids a special case in three separate systems.
- **Person email is required**, so the composer never has to invent one.

### 12.5 The placeholder chain, and why it should be temporary

Where Pipedrive data is missing, the composer currently invents values, matching legacy behaviour:

| Missing | Placeholder |
| :-- | :-- |
| person email | `{deal_id}@gmail.com` |
| person name | `Unknown` / `Contact` |
| street address | `Address not provided` |

**This is right for a test deal and wrong for production.** A fabricated email is an address a quote could be sent to. Once Pipedrive enforces §12.4's rules, the composer should **fail loudly** instead — a visible failure beats a quote addressed to a made-up mailbox.

---

## 13. `quote_composer.py` — Pipedrive to Quote, End to End — **[Confirmed live, 2026-08-26]**

The v2 replacement for `quoter.create_comprehensive_quote_from_pipedrive()`. Business logic; sits above the SDK per D-003/D-004. **Does not touch the legacy path** — nothing changes in production until `webhook_handler.py` is pointed at it.

### 13.1 What it replaces

| legacy | v2 |
| :-- | :-- |
| `enum_mapping` — 11 hard-coded option ids in `template_selection_logic.py` | `option_map()` read at run time |
| `TEMPLATE_BUNDLES` — line items in a Python dict | Item Groups read from Quoter |
| prices baked into the dict | `$0.00`, priced by the salesperson |
| `POST /v1/contacts`, then pass its id | contact resolved by email (§12.1) |
| flat line items, no sections | one section per Item Group |
| `api.quoter.com`, legacy OAuth | `api.scalepad.com`, `x-api-key` |

### 13.2 The flow

```
deal
 ├─ option_map(90)   -> template title -> tmpl_ id     presentation
 ├─ option_map(102)  -> Item Group names               content
 ├─ item_group_defs.json -> client-facing section name
 ├─ ensure_contact(email)                              §12.1
 ├─ POST /quotes
 ├─ POST /sections            all in one call
 └─ POST .../line-items       per section, with retry  §9
```

### 13.3 Confirmed run

Deal 3101 (`zz53-org-3101`), Quote Template `Standard`, Quote Effects `SFX-Balloons` + `STE-After-Bill`:

```
Template: ['Standard'] -> tmpl_3ITGNwiAtd8fvLEpiiaBK79Z1YP
Effects:  SFX-Balloons, STE-After-Bill
Plan:     2 sections, 9 line items
  SFX-Balloons   -> 'Balloon Effects'                8 items
  STE-After-Bill -> 'Shipping, Travel & Expenses'    1 item
Contact 3101@gmail.com: created
Created draft quot_3ITPDbwn7eMug2hZXl4ZhXHTRO4
  + Balloon Effects: 8 item(s)
  + Shipping, Travel & Expenses: 1 item(s) (after 2 attempts)
```

The retry on section two is §9's eventual consistency, caught and handled.

**Two things the response confirms.** `contacts[0].id` is a real `cont_...` while the standalone record's `id` stays null — §5.1's split, seen from the other side. And `client: {id: null, name: "zz53-org-3101"}` shows the Client resolving from the org name, as §3.3 describes.

### 13.4 The webhook is a trigger, not a data source

Worth stating plainly, because it was a live question: **reading a deal never required a webhook.** `pipedrive.py:get_deal_by_id()` fetches any deal with the API token, which is what the composer does and what the legacy code falls back to.

The webhook answers *when* — "deal 3101 just moved to Send Quote/Negotiate." Without it you would poll, or a human would run a command.

**This means the payload can shrink substantially.** The legacy handler needs a fat payload because it builds a contact from scratch: name, email, work phone, mobile, six address fields, and elaborate fallbacks for unreliable webhook phone data. The v2 path needs the deal id and little else — everything else is one API call away. In the limit the payload becomes a trigger carrying an id.

**[Not yet done]** Both shapes must work during the transition, since the legacy handler still needs its fat payload. So the v2 branch should ignore what it does not need rather than the webhook template changing.

### 13.5 `SCO-ScopeOfWork` — an auto-appended group

Every quote should describe what is being sold, so leaving that to a dropdown choice means someone can forget. `SCO-ScopeOfWork` is therefore **added by the composer to every quote and never offered in Pipedrive**.

```json
"SCO-ScopeOfWork": {
  "section_name": "Scope of Work",
  "code_prefixes": ["SCO-"],
  "auto_append": true,
  "position": "first"
}
```

Three parts, and all three are needed:

- **`item_group_defs.json`** marks it `auto_append: true, position: "first"`.
- **The composer** prepends it and de-duplicates, so a stray selection cannot produce two Scope sections.
- **`sync_quoter_to_pipedrive.py` excludes it** from the dropdown. An option sales should never pick would only invite that duplicate.

It holds one item — `SCO-WORK-001` "Scope of Project", $0.00, `T&E / Terms` — whose description carries placeholder text the salesperson rewrites per deal.

**It only works because of §14.1.** Without line-item descriptions rendering, a Scope section would be an empty heading.

Naming convention now: **`SCO-`** scope · **`SFX-`** effects · **`SVC-`** generic services · **`STE-`** shipping, travel, expenses.

**`SVC-General` stays selectable** by contrast. Generic labour is on most quotes but not all — a dry hire where the client supplies crew needs none — so it remains a judgement call rather than an automatic one.

### 13.6 Quote numbering is unconditional on v2

`ENABLE_CUSTOM_NUMBER_PATCH` is **gone**.

It existed because the **legacy** API could not set a quote number reliably: the post-publish PUT to `custom_number` did not stick, so numbering fell to a human and the flag defaulted off. **v2 sets `custom_number` at create, and it holds.** The constraint the flag guarded no longer exists, and keeping the switch only invited quotes falling back to Quoter's own counter — which produced "Quote #46" on the first deal-3101 run.

Format unchanged: `dealID-YYYYMMDD`, zero-padded to five digits, Pacific date — `03101-20260826`.

`generate_sequential_quote_number()` was **ported rather than imported**, so `quote_composer.py` carries no dependency on legacy `quoter.py` at all.

### 13.7 Not yet carried over from legacy

- **Phone.** The webhook carries work and mobile; `create_contact` accepts `billing_work_phone` / `billing_mobile_phone`; the composer does not pass them yet.
- **Address PATCH onto the quote.** Legacy PATCHes billing and shipping onto the quote after creation. Whether v2 accepts an address at create is untested; the composer sets it on the contact only.
- ~~**Quote numbering.**~~ Done — see §13.6.

---

## 14. Client-Facing Rendering — **[Confirmed, 2026-08-26]**

Everything a customer actually reads. Settled by inspection of the rendered preview rather than from documentation.

### 14.1 Line item descriptions render; catalog item descriptions do not

**These are two different fields, and conflating them cost most of an afternoon.**

- A **catalog item** has a `description`. It does **not** reach the quote by itself.
- A **line item** has its own `description`. It **does** render, beneath the item name.

Proven both ways. `STE-AFTER-001` carried its explanatory wording in the catalog description and the client saw only the name. Once `line_item_from_catalog()` copied that description onto the line, the sentence appeared.

**296 of 297 catalog items carry a description and `GET /items` returns it** — the composer was reading it and discarding it. One line fixed that.

Mixed formats in the catalog are harmless: some descriptions are HTML (`<p>Air filer for balloons</p>`), some plain text. Quoter parses both, so no normalising is needed.

**This resolved the `STE-After-Bill` wording problem for free** (§10.6). That section now reads:

> **T&E - Billed After Event**
> Travel and expenses are not included in this quote. Airfare, lodging, meals, per diem, ground transport and shipping will be invoiced at actual cost following the event.

### 14.2 Pruning: blank the quantity, do not zero it

| Quantity | Client sees |
| :-- | :-- |
| `1` | the line, with its price |
| `0` | the line, at $0.00 — included but not charged |
| **blank** | nothing — the line drops out |

**Backspace does not clear the field; the delete key does.** A salesperson using backspace leaves the field in a state Quoter still treats as zero, so a line they believe they removed stays on the quote. Worth telling sales explicitly.

### 14.3 Section subtotals and the one-time/recurring split

A per-section subtotal renders **only** when Display Settings → *Separate One-time/Recurring Prices* is on, and it arrives as "One-Time Subtotal" beneath a "One-Time Fees" header.

| Split setting | Line prices | Section total | "One-Time Fees" header |
| :-- | :-: | :-: | :-: |
| **Yes** | shown | shown | shown |
| **No** | shown | — | — |
| price toggles off | — | — | — |

The Pricing Table toggles (Category, Manufacturer/Code, Quantity, Unit Price, Line Total) control columns only; turning Unit Price and Line Total off removes **every** dollar figure including the grand total.

**There is no combination giving line items without prices AND a section subtotal.** The subtotal is a by-product of the split.

**[Confirmed — Eric]** This matters less than it first appeared, because **TLC bundles**: "$5,000 gets you balloons and Floating Video." The price is not per-section, so splitting it across sections would be arbitrary. What is wanted is **one number for the quote**, with sections showing what is included — which the current configuration already produces.

**[Open]** Where the bundled price sits. Putting it on the `Scope of Project` line keeps one price on the line describing the whole project, with everything below as scope at $0.00. Cost tracking is unaffected either way: unit costs stay on the line items and the margin column reads them regardless of where revenue sits.

Note the editor **does** show a per-section `Total One-Time` on the section header row even with the split off. It simply is not rendered client-facing.

### 14.4 "Cost Breakdown" shows PRICE, not cost

Despite the name. Confirmed by setting unit cost 1000 and unit price 600 on the same line: the breakdown reported **600**.

It groups by **full category path** — `Balloons / Wall-Flying`, `T&E / Terms` — and totals at the bottom. Notably it shows the parent, unlike `GET /items`, which returns only the leaf name (§2.3.1).

So it is safe client-facing and works as a per-category rollup, which is close to the section total the split cannot provide without its header.

### 14.5 The "Summary" block appears automatically

**Localization** — *"When a Quote has more than 1 Section, this is the header text of the Summary block."*

So it is structural, not removable, and appears on **every composed quote**, since composition always produces more than one section. Only the header text is editable, at `/admin/localizations`. It cannot be moved; it renders after the sections.

The block carries the non-taxable footnote and the closing message. **[Open]** whether renaming it to "Notes" reads correctly once lines are actually priced and it may also carry the grand total.

### 14.6 Introductory Content blocks start a new page

The quote editor offers **Introductory Content** blocks that render before the line items — but each **creates its own page**. That rules them out for a short scope paragraph, which would sit alone on a page, separated from the sections it describes.

Appropriate for content that *should* be its own page: a cover letter, terms and conditions, a capabilities overview. Consistent with Cover Letter now being marked **Deprecated** in favour of Introductory Content.

**[Untested]** whether Render can write content blocks via the API, and whether they can be seeded from the template.

---


## 15. Open Questions for ScalePad / Jon Turner

1. Is a Quoter Client created automatically from Contact-write behaviour, or tied to the QBO connector? **[Resolved — Jon Turner, Aug 2026]** Contact-creation creates the Client. No QBO sync. §3.3.
2. Is there any API-triggerable path — now or on the roadmap — for setting a Pipedrive Person/Deal reference on a quote, or will this remain permanently manual? §4.4.
3. What is the exact request shape for `client_id: null` / Client-name resolution on `createQuote`? **[Resolved — live test, Aug 19 2026]** `contact.client_name`. §5.
4. Is Quoter's native "Quoter" source (§3.2) deduplicated by company, or does it inherit the same per-deal fragmentation when fed Pipedrive-sourced names?
5. Why does a standalone `POST /contacts` record keep `id: null` / `client: null` permanently, while the same contact referenced inside `createQuote` materialises with a real `cont_...` ID and resolved client? §5.1.
6. **[RESOLVED — Jon Turner, Aug 23 2026]** ~~Is there a supported way to read a Quote Template's line-item contents via the API?~~ **No, and it is intended.** No endpoint exists; none is planned. Rationale: templates-with-items serves manual quoting, whereas API quotes are expected to add items themselves — and third-party Items carry no price at template-add time, so a contents endpoint would return incomplete pricing regardless. See §6.2.1. Open since 2026-06-30, asked three times.
7. **[ACKNOWLEDGED — Aug 23 2026]** Case-sensitive `x-api-key` matching (§2.1.1). Jon: *"I will make a note with our team regarding the case sensitivity for the x-api-key header."* Reported; no fix committed. Assume the lowercase requirement stands until proven otherwise. Original question: RFC 7230 specifies header names as case-insensitive, and the 401 attributes the failure to credentials rather than to the header — actively misleading for any client that capitalises headers by default.
8. **[RESOLVED — Jon Turner, Aug 23 2026]** ~~Is there any way to reference a catalog Item when creating a line item?~~ **No.** *"We do not allow existing catalog Items to be added, just as ad-hoc Line Items."* This is the confirmed cause of all four dead ends in §7.12. **But it is described as a known limitation that "will likely be updated at some point"** — so this is current-state, not permanent. Re-test after any significant API release.
9. **[RESOLVED — Jon Turner, Aug 23 2026]** ~~Is `Add Single Select Section Group` creatable via the API?~~ **No.** *"The API does not allow Single-Select Items/Groups or Bundles to be created, just single Line Items."* Same known-limitation caveat as item 8.
10. **New.** When catalog-item references do arrive, which of Bundles / Item Options / Single-Select Groups become usable, and is there a migration note? Worth asking ahead of adopting seed-and-prune permanently (§7.12.4).
11. **New.** `GET /items` returns only the leaf category name, and leaf names collide across parents (§2.3.2). Is there a documented way to retrieve an item's full category path, or must `category_id` be resolved separately via `GET /categories/{id}`?

---

## 16. Next Steps

### Done 2026-08-23

- Section creation verified; full write chain confirmed (§7.11).
- Pipedrive dropdown sync built, tested on every lifecycle case, and scheduled at 06:00 daily (§11).

### Immediate — build

- **[Done, 2026-08-23]** ~~Test `POST /quotes/{id}/sections`.~~ Confirmed working, multiple sections per quote, full write chain verified (§7.11). **No blocking unknowns remain.**
- **[Done 2026-08-24]** ~~Build the vertical slice.~~ 21 Item Groups built (§15), multi-section composition working (§9), all 20 synced to Pipedrive field 102, `STE-After-Bill` created.
- **[Done 2026-08-26]** ~~Migrate `quoter.py`.~~ `quote_composer.py` does it (§13), confirmed end to end on deal 3101. Written as a new module alongside the legacy path, so nothing changes in production yet.
- **Wire the webhook.** Branch in `webhook_handler.py` behind `USE_V2_COMPOSITION`, so reverting is a Render env setting rather than a deploy. Add `SCALEPAD_API_KEY` to `render.yaml` `envVarsFrom` — it is set in the dashboard but not declared.
- **Decide where the bundled price sits** (§14.3). TLC quotes a single figure for the whole show, so per-section subtotals are the wrong target. Putting the price on the `Scope of Project` line is the leading candidate.
- **Enforce the three data rules in Pipedrive** (§12.4): Organization required at the quote stage; a private client still gets an Organization named after the person; person email required. Then remove the placeholder chain (§12.5) so the composer fails loudly instead of inventing an email.
- ~~**Migrate `quoter.py`.**~~ Replace the hard-coded `enum_mapping` in `template_selection_logic.py` with `PipedriveFields.option_map(102)`, and `add_template_line_items_to_quote()` with the `compose_quote` path. `get_template_info()` at lines 1748 and 2003 stays — cover letters are unaffected, though note Quoter now marks Cover Letter *Deprecated* in favour of Introductory Content.
- **Fix the CO2 mapping bug** while migrating: `template_selection_logic.py` maps `'CO2/Smoke/Upright Foggers'` to `'low-level-fog'`, so CO2 deals get fog items. A `co2-smoke-foggers` bundle exists and is orphaned. Not urgent — sales is not using this path yet.
- ~~**Build the vertical slice:**~~ create `XRN-Balloons` (8 items, resolved by `BAL-` code prefix — see §8.2.1 and `build_item_groups_v3.py` / `item_group_defs.json`) → write `scalepad_quotes.py` → compose one quote end to end → delete the Balloons block from `template_mapping_enhanced.py`. Proves the whole path on one product line before repeating.
- **Decide whether pyro items belong in `XRN-Balloons`** (§8.2.1). An exploding balloon wall may legally require `PYR-LIC-TEC` and `PYR-PRM-001`. Left out of the definition pending a human answer.
- **Run a code-prefix hygiene scan** before defining more groups (§8.2.2) — prefix discipline is now load-bearing.
- **[Resolved — Jon Turner, Aug 23]** ~~Send a payload carrying both by-value fields and an `item_id`.~~ Unnecessary: ScalePad confirms catalog items cannot be referenced, only ad-hoc line items created (§7.12.0).

### Migration work

- **Write the line-item resource wrapper.** §7.10's schema has no home: `QuoterItemsV2` covers Items and Categories only. Add a sibling (e.g. `scalepad_quotes.py`) over the existing `ScalePadV2Client` — this is what D-003/D-004 sanction, and D-006's "verify before wrapping" precondition is now met. Keep quote-composition logic in a service module above the SDK, not inside it.
- **Review proposed D-011** (§8.5) and add it to `docs/DECISIONS.md` if accepted. Per the Decision Lifecycle, D-009 is referenced, not edited.
- **Confirm no Resellers are configured** on the Quoter account. The whole Item Group mirror depends on it (§7.8.1).
- **[Resolved]** ~~Audit Render's HTTP client for the §2.1.1 header-casing hazard.~~ `scalepad_v2.py` uses `requests` with a literal lowercase `x-api-key`; `requests` preserves header case. Production is unaffected. The hazard applies only to newly written tooling (§2.2.5).
- **Document (before renaming) the Render env var naming** per §2.1.2.
- **Verify the `sku` → Pipedrive **product** mapping** (§2.2.4). The convention is confirmed live and clean catalog-wide (297/297, numeric, no collisions); what remains unverified is that a given SKU resolves to the corresponding Pipedrive product. Check one — e.g. sku `195` — before any process writes to the field.
- Decide whether Render's create flow should drop the standalone `createContact` call, given `createQuote` appears to handle full resolution in one step (§5.1) — pending Jon on whether that behaviour is guaranteed.
- Decide whether to pursue Client consolidation (§3.5) — an input-side change, not a system limitation.
- **Scaffold design is resolved (§7.5)** — build item-seeding against `quantity_decimal: 1`, relying on the existing UI zero/blank workflow for pruning. No further design needed.

### Data cleanup

**Consolidated 2026-08-23.** Earlier drafts appended to this list session by session; restated here in full. Nothing below has been removed yet.

**Quotes (5)** — all **[Confirmed test data — Eric Grosshans]**

| ID / tag | State |
| :-- | :-- |
| `quot_3EjnxxiDSUXEK7DHjolvg9jqyiG` — client `zz-Wayne Industries-3007` | **`draft: false`, number 45**, Jun 5 — issued, not a draft |
| `quot_3I9UCyBcqZJ39soTFYS5SodFzlW` — `TEST-CH3-2026-08-19` | draft; carries test line items from the §7.10 derivation |
| `quot_3I9uJGP7vY89JWM9IqRpYTOtcSN` — `zz-TEMPLATE-PROBE-20260819-182350` | draft |
| `quot_3IKjeLMuYNN2YJ1FgwhZ5kZe2rJ` — `zz-SECTION-PROBE-20260823-142407` | draft; two probe sections, one line item |
| `quot_3IL8khK3vNkCR5TtXyVgfOweH86` — `zz-OPTIONS-PROBE-20260823-175032` | draft; one section, one line item |

The first is **not a draft** — a numbered, issued quote. Deleting it may leave a gap in the number sequence and carries audit implications the others do not. Handle separately. The `-3007` suffix follows the per-deal org naming of §3.4.

**Catalog items (14)**

- 11 × `zz-test item*`, codes `ZZZ-BAL-LT*`, all in `Balloons / Latex` — **highest priority.** That subcategory holds 12 items of which exactly one is real (§2.3.4). The `BAL-` prefix rule (§8.2.1) excludes them, but they distort any category-based view. Numbering skips 4 and 10, so item deletion is supported and has been exercised before.
- `ZZ Parent Item`, `ZZ Child1 of ZZ Parent`, `ZZ Child2 of Parent ZZ` — from the §7.12.2 test. Catalog moved 298 → 301.

**Configuration to revert**

- The `OptS` option on `FV-Standard Graphics Pkg` (`HG-FV-Graph-001`) — **remove before that item is quoted.** `REQUIRE SELECTION = Yes` means an API-created line for it cannot be completed (§7.12.3).
- Empty category `Additional Options`, created for the parent/child test.
- Bundle `zz-TEST-Bundle-TE` (`item_3ICkQSZwDX0Oa1mA7mLP77fuMyj`) and its `Test` category.
- Item group `TEST-Balloons` (`igrp_3Fgct9Xz5Uwu03SUmOoNP6RmZ9o`), 0 members — delete, or rename if it becomes a production group.

**Contacts (2)**

| Email | Organisation |
| :-- | :-- |
| `zz-test-chapter3@tlciscreative.com` | `zz-Chapter3-CustomNumber-Test` |
| **`myles@tlciscreative.com`** | `zz-Wayne Industries-3007` |

The second is a **real colleague's address on a test organisation** — a stand-in from the June test. **Correct the organisation; do not delete the contact record.** Both show `id: null`, consistent with §5.1.

**Pipedrive**

- Scratch dealField **101** `zz-PROBE-20260823-152852`, options `zz-alpha` / `zz-beta` / `zz-added-153006` — from the §11.3 id-preservation test. Delete the field.
- Any `XX-RET-*` options on field 90 left from sync testing. Safe to leave (§11.7), but created by probes rather than by real retirements.
- Stale entries in `pd_option_map_templates.json`: 14 pairings against 11 live templates. Harmless; nothing prunes them (§11.10).

**Repo**

- `logs/sync_dropdowns.log` was committed before `logs/` was gitignored — `git rm -r --cached logs`.
- `sync_templates_to_pipedrive.py` targets a route that does not exist and has never worked (§11.2). Delete or clearly mark.

### Deferred to a future chapter

Catalog naming conventions, category-record deduplication (§2.3.3), template restructuring, and the shared-block organisation are product-model decisions rather than integration mechanics. They depend on the §8.2 verification and should be documented separately once that resolves.
