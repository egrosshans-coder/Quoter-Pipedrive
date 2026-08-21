# Products / Items — Next Session Agenda

**Context:** Follow-up to the Section 3 (Products/Items Flow) as-built. Goal of this thread: decide whether the current fan-out architecture still fits, and design a dedicated **item service** ("second mothership") for the creation and maintenance of products/items — separate from `webhook_handler.py`, which stays dedicated to quotes.

**Guiding question that ties everything together:** *Given what Quoter, SyncQ, and Pipedrive can each do now, is the fan-out still the right shape — or is there a simpler path?*

---

## A. Start here — Quoter API for items

The first task, and the fork that decides the whole design.

1. **Does Quoter emit item webhooks** (create/update/delete)? This is the decision point:
   - **Yes** → the item service can be **event-driven** (always-on, reacts in real time), symmetrical to the quote chef.
   - **No** → the item service stays **scheduled** (Render cron job) with an optional thin control surface for on-demand syncs.
2. Item endpoints and semantics: create / update / read / list, pagination, and the date filters already in use (`created_at[gt]`, `modified_at[gt]`).
3. Full item field surface — confirm every field we map (name, code, `price_decimal`, `cost`, `category_id`, `description`, `sku`) and anything we're not yet using.
4. The Categories API hierarchy (`/v1/categories/{id}`, `parent_category`) — confirm it still behaves as `category_manager.py` assumes.
5. ScalePad API vs legacy Quoter API — per `DECISIONS.md` (D-001…D-005), check whether item operations have reached parity on ScalePad yet.

---

## B. Research threads (gather before committing to a design)

1. **Quoter items API** — as above (this session).
2. **SyncQ** — *awaiting their reply* on improvements to the PD↔QBO product/item integration. If the account-reference gap is closed, the custom code's job shrinks and the division of labor changes. (Recall: SyncQ currently maps 7 product→item fields but **no** income/expense accounts — that gap is the whole reason for the custom Quoter→QBO create path.)
3. **Pipedrive API (improved) + higher comfort level** — evaluate a cleaner Quoter↔PD channel; may let us rethink or retire the direct `sync_with_date_filter.py` → `pipedrive.py` sync.

> These interlock: strong answers to (2) and (3) could make the item service *simpler* than what runs today. Gather all three before locking the design.

---

## C. Architecture decisions pending

1. **Two-service split (confirmed direction):** keep `webhook_handler.py` for quotes; build a dedicated item service for products/items.
2. **Prerequisite refactor — shared library:** extract `quoter.py`, `pipedrive.py`, a real `qbo.py` (pulled out of `quoter_to_qbo_sync.py`), `category_manager.py`, and `notification.py` into pure importable modules with no work-on-import. Both services call the same core. This is the step that actually pays down the debt.
3. **Trigger model for the item service:** event-driven vs scheduled — decided by A.1. Leaning: primarily scheduled (Render cron job) + a thin always-on control surface (`/sync/incremental`, `/sync/item/{id}`, `/health`, `/report/daily`), upgradeable to event-driven if Quoter supports item webhooks.
4. **Platform:** Render (paid, always-on). Consolidate the "two cooks" (`complete-sync.yml` + `run_complete_sync.py`) into one batch entry point so there's a single recipe.
5. **Config drift to fix:** `render.yaml` still says `plan: free` — update to match the paid plan actually deployed.

---

## D. Hardening / tech-debt backlog (from §3.8)

Refactor, not rewrite — the architecture is sound; the implementation carries debt.

1. `Type` hardcoded to "Service" (dead `SVC` branch) — items mislabeled in QBO.
2. Income account hardcoded to `389`, no `ExpenseAccountRef` — see the chart-of-accounts project (E.3).
3. Dead duplicate `convert_quoter_to_qbo_item` (and duplicate `get_subcategory_field_key` in `category_manager.py`) — delete.
4. QBO items created flat — computed category hierarchy never written.
5. Create-path sends `Sync=Yes` in one POST vs. deferred on update path — align to avoid premature SyncQ trigger.
6. `main()` runs live (`dry_run=False`) while advertising dry-run — gate live writes behind an explicit flag; add a smoke test.
7. **Replace name-similarity matching** in the Quoter→QBO sync with the durable keys we already maintain (Quoter `sku` = PD id; QuickBooks ID). Highest-value fix.

---

## E. Open items from §3.10

1. Confirm the **native Quoter↔QBO integration is currently enabled** in the Quoter account.
2. Confirm/deny operational fragilities: QBO item-ID drift (numeric vs long-string), item-side Sync "toggle" workaround, QBO 3-custom-field API cap. (None currently evidenced in code/docs.)
3. **Scope the chart-of-accounts mapping project** — review/extend the QBO chart of accounts and design a category→account mapping, with a test-and-rollback plan to protect the three-way connectivity before any change to account references.
4. **Clarify the Quoter→QBO vs SyncQ overlap** — since SyncQ maps Products→Item (PD→QBO), decide whether `quoter_to_qbo_sync.py` still needs to create items, or whether its only unique job is setting the accounts SyncQ can't. Pick one authoritative creation path.

---

## F. Still queued

- **Section 4 — Quote Building** (native Quoter→QBO estimate flow, template/bundle assembly, Deals→Invoice mapping `LQ-7781`). Resume after the item-service design thread, or interleave as needed.
