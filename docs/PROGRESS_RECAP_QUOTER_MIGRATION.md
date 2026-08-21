# Progress Recap — Products/Items As-Built & Quoter→ScalePad Migration

**What this is:** a single status snapshot of the work across these sessions — what's done, what's decided, what we're waiting on, and the short list of what's next. Written because the recent stretch ended on "wait for a vendor fix," which feels like a stall but isn't: it closed off dead ends and produced a clear plan.

---

## 1. What we accomplished (concrete)

**Documented the Products/Items flow as a code-verified as-built.** Produced `AS_BUILT_SECTION_3_PRODUCTS_ITEMS.md` (+ `.docx`), with every claim tagged as verified-in-code, from-docs, or operational-knowledge.

**Corrected the core architecture model.** Moved from the original "one-way chain, Pipedrive dormant" framing to the *verified* picture: a **fan-out-then-reconcile triangle** — Quoter is the source of truth and seeds both QBO and Pipedrive; **SyncQ** reconciles PD↔QBO in both directions to complete both records.

**Verified the actual running code** (not just the docs): the A/B/C create/update logic in `pipedrive.py`, the create-only `quoter_to_qbo_sync.py`, the four PD custom fields, the `Sync=Yes` trigger, and the field mappings — including the durable linkage (Quoter `sku` = PD product ID).

**Verified the SyncQ mapping from the dashboard** (mapping `LQ-7604`, Products→Item). Key finding: SyncQ maps **no income/expense account references** — which is precisely *why* the custom code and the fan-out exist. Also resolved that `LQ-####`/`LQB-####` are SyncQ mapping IDs, not Quoter item codes.

**Traced the catalog origin:** items were seeded into Quoter by a one-time **Goodshuffle** export/clean/import migration; Goodshuffle is being retired.

**Cataloged the technical debt** honestly: `Type` hardcoded to Service, income account hardcoded to 389, name-similarity matching, the "two cooks" drift, and the create-only QBO path.

**Produced a v1→v2 migration plan** (`QUOTER_V1_TO_V2_MIGRATION_PLAN.md`) and an agenda (`PRODUCTS_ITEMS_NEXT_SESSION_AGENDA.md`).

**Researched the ScalePad v2 API directly from its OpenAPI** and established:
- v2 now has **full item + category CRUD** (the old "no parity" assumption is outdated for items).
- **Clean incremental sync** exists: `filter[record_updated_at]=gt:…` + cursor pagination.
- **No webhooks anywhere** → the item service must be scheduled/polling, not event-driven.
- IDs are **opaque strings** (`item_…`, `cat_…`) → the "numeric ID drift" fragility is permanently moot on v2.

**Found and corrected a wrong conclusion:** v2 *has* a Create Quote endpoint, but it's **blocked for us** — it requires a `client_id` that only exists via ScalePad's Lifecycle Manager product, which we don't use (confirmed by ScalePad's Jon Turner). A fix is in progress to use the Quoter **Client name** instead.

**Pinned down template line items:** they're not on the template resource; the supported way to read them is **create a draft from the template, then fetch it** (probe: `test_files/test_template_seeds_lineitems.py`) — and that path is gated on the same `client_id` fix.

**Ruled out three fragile paths** (this is progress — it saves you from building the wrong thing):
- **Item Groups mirror** — ScalePad says Item Groups aren't supported on our Standard plan (Enterprise feature); also can't carry quantities/structure.
- **Web scraping** the admin UI — unsupported, breaks on any UI change, contrary to your "don't automate the UI" goal.
- **GraphQL endpoint** (`api.quoter.com/gql/query`, which powers the admin UI) — real, but undocumented, web-session-locked, and it *refuses backend replay* (`ERR_PERMISSION_DENIED`). Fallback only, not a production path.

---

## 2. Decisions locked

1. **Two dedicated services**, sharing one library: keep `webhook_handler.py` for quotes; build a separate service for products/items.
2. **Build the item service on ScalePad v2**, **scheduled** (Render cron job, not an internal timer), driven off `record_updated_at`.
3. **Refactor shared modules first** (`quoter`/`scalepad`, `pipedrive`, `qbo`, `category`) so both services call one core — this also fixes the "two cooks" drift.
4. **Keep legacy for quote creation** until the Client-name fix ships and is verified.
5. **Do not** build on Item Groups, scraping, or GraphQL. Keep the hard-coded template definitions as a **monitored cache** (bundle verification flags drift) until a supported template-read exists.

---

## 3. What everything is waiting on

**One vendor fix unblocks the two hardest items at once:** ScalePad's switch from `client_id` to **Client name** on Create Quote (target: ~this week). It unblocks:
- v2 **quote creation**, and
- the **create-from-template → fetch** read that gives us template line items with almost no code.

Also outstanding: **SyncQ's reply** on whether their PD↔QBO product/item integration has improved (could shrink the custom QBO work).

---

## 4. What's next (low effort — no DevTools required)

1. **Wait for Jon's confirmation** that the Client-name update is live. When it lands, I'll help you write the small `create-from-template → fetch → read line items` routine and test it against the Balloons template.
2. **Optional email to Jon** (drafted previously) to (a) get the fix timeline, (b) confirm whether Standard-plan Item Group API use is supported, (c) ask if GraphQL access is supported for backends and the roadmap for direct template line-item retrieval.
3. **When ready to build:** start the shared-module refactor and the v2 item wrappers in `scalepad_v2.py` — independent of the quote-side fix, so it can proceed now.
4. **Parked:** GraphQL query capture — noted as a fallback, not pursued.

---

## 5. Deliverables produced (in `docs/`)

- `AS_BUILT_SECTION_3_PRODUCTS_ITEMS.md` and `.docx` — the code-verified Products/Items as-built.
- `QUOTER_V1_TO_V2_MIGRATION_PLAN.md` — the migration plan (updated for the `client_id` blocker and the template/Item-Groups findings).
- `PRODUCTS_ITEMS_NEXT_SESSION_AGENDA.md` — research threads and open questions.
- `PROGRESS_RECAP_QUOTER_MIGRATION.md` — this document.

---

## 6. Honest assessment

The system is stable and running; it does not need a rewrite. It needs a **scoped, phased migration** to v2 plus a hardening pass on the known debt. The single biggest lever right now is outside our control — the ScalePad Client-name fix — so the productive work available today is the **shared-module refactor** and the **v2 item wrappers**, both of which are unblocked. Everything quote- and template-related becomes straightforward the moment that fix ships.
