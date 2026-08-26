# Kickoff Brief — Quoter/ScalePad, Next Sub-Chat

**Date:** 2026-08-26
**Predecessor:** "Quoter Item Group Build from Template", Aug 19–26 2026
**Canonical reference:** `CHAPTER_3_QUOTER_SCALEPAD_AS_BUILT_2026-08-26.md`. Read it first — this is orientation, not a replacement, and Chapter 3 wins on any conflict.
**Governing discipline:** Verify, don't assume. Tag every claim **[Confirmed]** or **[Hypothesis]**.

---

## 1. Where things stand

**A Pipedrive deal now produces a fully composed Quoter quote.** Confirmed end to end on deal 3101: two Pipedrive fields resolved at run time, contact created, quote created, two sections, nine line items, all at $0.00.

Nothing is hard-coded in that path. No `enum_mapping`, no `TEMPLATE_BUNDLES`. Change the catalog and the next quote is already correct, with no deploy.

**But it is not wired to the webhook yet.** `quote_composer.py` runs from the command line; `webhook_handler.py` still calls the legacy function. Production is untouched.

---

## 2. The task: Phase 3, wire the webhook

Three steps, roughly an hour.

**2.1 Branch in `webhook_handler.py`** behind `USE_V2_COMPOSITION`:

```
flag true  -> quote_composer.create_quote_v2(org_data, deal_data)
flag false -> quoter.create_comprehensive_quote_from_pipedrive(...)
```

Reverting is then a Render environment setting, not a deploy. That is the point of the flag.

**2.2 Add `SCALEPAD_API_KEY` to `render.yaml`** under `envVarsFrom`. It is set in the Render dashboard but **not declared in the blueprint**, so a blueprint redeploy might not carry it.

**2.3 Deploy and smoke test.** Push, Render redeploys, move a test deal to the trigger stage, confirm the quote appears.

**Free plan spins down when idle**, so the first webhook after a quiet period pays a cold start. Allow for a slow first response rather than assuming failure.

### 2.4 Then: enforce the three data rules in Pipedrive

Decided, not built. All three are Pipedrive-side (Chapter 3 §12.4):

- **Organization required to reach the quote stage.** Everything downstream depends on it — the Quoter Client resolves from the org name, and Pipedrive creates the QBO customer from it. One rule, three consumers.
- **A private client still gets an Organization**, named after the person. Avoids a special case in three systems.
- **Person email required**, so the composer never invents one.

Then **remove the placeholder chain** (§12.5) so the composer fails loudly instead of fabricating an email a quote could be sent to.

---

## 3. What is built and working

| | |
| :-- | :-- |
| **21 Item Groups** | membership from catalog code prefixes, defined as data in `item_group_defs.json` |
| **Composition** | `compose_quote.py --groups A,B,C --write`, and `quote_composer.py --deal N --write` |
| **Standard template** | `tmpl_3ITGNwiAtd8fvLEpiiaBK79Z1YP`, slug `standard` — presentation only, no default items |
| **Two Pipedrive dropdowns** | synced daily by GitHub Actions; nothing runs locally |

**Field 90** Quote Template `enum` — presentation. Key `42ab0c919271cb24f3587f0b01ea2af166019c8d`
**Field 102** Quote Effects `set` — content. Key `118a5ce132f73d7fec1822e2a0431b51ac2a2994`

Naming: **`SFX-`** effects · **`SVC-`** generic services · **`STE-`** shipping/travel/expenses. Group name and Pipedrive label must stay identical — the sync matches on them. The client-facing section name comes from `item_group_defs.json` and is free.

---

## 4. Five things that will bite

### 4.1 Create the contact before the quote

`createQuote` **resolves** a contact by email; it does not create one. An unknown email returns `422 ERR_CONTACT_NOT_FOUND`. Chapter 3 §5.1 reads as though createQuote materialises a contact — it does, but only for an email that already exists. §12.1.

### 4.2 Read the write schema off a real record

The write schema mirrors the read schema **every time** — `category: {id}` on line items, `billing_address: {address_line_1, city, ...}` on contacts, bare arrays for sections. Guessing the contact schema cost three round trips; one `GET /contacts` settled it.

**And read the error grammar:** a **422** is about the body's CONTENTS, a **400** about its SHAPE.

### 4.3 Section reads are eventually consistent

A section id read *immediately after a write* can 404. **Only shows up on multi-section quotes** — a single section never performs a second write. `add_line_items_retrying()` handles it; do not substitute a longer sleep. §9.

### 4.4 Address sections by index, never by name

Section names need not be unique — both wristband groups render as "LED Wristbands", and one quote may carry both.

### 4.5 Lowercase `x-api-key` is mandatory

The gateway matches case-sensitively; `urllib` capitalises header names automatically. `scalepad_v2.py` uses `requests` with a literal lowercase key and is safe. New tooling must be too. §2.1.1.

---

## 5. Reference

**Catalog:** 292 items. `code` is the unique part number — **resolve by `filter[code]=eq:`**. `sku` is a numeric foreign key, very likely a Pipedrive product id.

**Pagination:** cursor-based, param `cursor`, page size `page_size` (max 200). Unrecognised params are ignored silently — **always compare fetched count against `total_count`.**

**Retirement is encoded in the code prefix:** `LED-WBT-` current / `LED-WBX-` legacy · `LED-LYT-` / `LED-LYX-` · `HG-FVV-` / `HG-FVH-`. Groups take only the current prefix.

**Four Quoter mechanisms are UI-only** — Bundles, template line items, parent/child items, Item Options. Confirmed by ScalePad: *"we do not allow existing catalog Items to be added, just as ad-hoc Line Items."* Described as a known limitation likely to change; worth re-testing after a significant API release. §7.12.

**Item descriptions do not render client-facing.** Anything the client must read has to be in the item **name**.

**Quoter Settings → Required Fields governs the API as well as the UI.** First Name, Last Name, Email and Country are locked Mandatory; the rest are toggles. Currently Organization is on and the address fields are off, because data quality is enforced in Pipedrive instead.

---

## 6. Repo and environments

`github.com/egrosshans-coder/Quoter-Pipedrive`, cloned as `quoter_sync` on Mac Mini and MacBook Air.

**`./retrieve.sh` before `./sync.sh`, always.** The dropdown-sync workflow commits state files to `main` on its own schedule, so a push can be rejected on a stale ref. `git config pull.rebase true` avoids a merge commit each time.

| File | |
| :-- | :-- |
| `scalepad_v2.py` | transport |
| `scalepad_items.py` | items + categories. **`iter_all_items()` already does the catalog pull** |
| `scalepad_quotes.py` | quotes, sections, line items, contacts, `add_line_items_retrying()` |
| `quote_composer.py` | **the v2 quote path** — deal in, quote out |
| `compose_quote.py` | compose from group names directly, for testing |
| `build_item_groups_v3.py` + `item_group_defs.json` | group membership as data |
| `pd_fields.py`, `sync_quoter_to_pipedrive.py` | dropdown sync |
| `.github/workflows/pipedrive-dropdown-sync.yml` | the scheduler, 13:00 UTC daily |
| `pd_option_map_*.json` | state files — committed by the workflow |
| `*_probe_*.py`, `section_diag_v1.py` | diagnostics. Evidence, not code to build on |

**Three separate secret stores that do not see each other:** local `.env` on two machines, the Render dashboard, GitHub Actions secrets. `SCALEPAD_API_KEY` is in all three — rotating it means updating all three, and it has been flagged for rotation since Chapter 3 began.

**Render** runs one free-plan web service, `quoter-webhook-server` → `webhook_handler.py`. No cron service.

`docs/DECISIONS.md` governs where code goes: D-003/D-004 transport and resource wrappers separate from business logic; D-006 verify endpoints before wrapping; D-010 Investigate → Understand → Design → Document → Implement → Test → Commit.

---

## 7. Known gaps and loose ends

**Not carried over from legacy into the composer:** phone (webhook has it, `create_contact` accepts it, composer does not pass it); the address PATCH onto the quote; quote numbering, still behind `ENABLE_CUSTOM_NUMBER_PATCH` though v2 can now set `custom_number` at create.

**CO2 mapping bug.** `template_selection_logic.py` maps `'CO2/Smoke/Upright Foggers'` to `'low-level-fog'`. Dead once v2 is live; do not port it forward.

**The webhook payload can shrink a lot.** The legacy handler needs a fat payload to build a contact from scratch; the v2 path needs the deal id and little else. Both shapes must work during the transition, so the v2 branch should ignore what it does not need rather than the webhook template changing. §13.4.

**Node 20 deprecation** on `actions/checkout@v4` and `actions/setup-python@v4`, all four workflows.

**[Hypothesis]** GitHub auto-disables scheduled workflows after 60 days of repo inactivity. The other three workflows are Disabled with last runs in November 2025 — deliberate. If the rule applies, the new workflow is subject to it and would stop silently.

**Unassigned catalog items** and **three unconfirmed calls** in `item_group_defs.json` — whether `LED-GLOBAL-*` is the beach balls, whether `LED-GLOTX-10` serves orbs, whether CO2 belongs with Fog.

**Cleanup** — Chapter 3 §15 has the full list. Now also includes the deal-3101 test quote and contact `3101@gmail.com`.

---

## 8. Process notes

Three failure modes recurred. All three are cheap to avoid and expensive to repeat.

**Asserting a mechanism instead of measuring one.** Three theories about the section 404 before a diagnostic answered it in one pass. **Instrument before theorising** — a throwaway script printing state at every step beats three plausible guesses.

**Guessing a write schema instead of reading one.** The contact schema took three failed attempts before anyone ran `GET /contacts`. The write schema mirrors the read schema every time. **One read replaces three round trips.**

**Documenting a flaw instead of fixing it.** The local-cron scheduling was known to be fragile the day it was built — the limitation went into a code comment and a "known gap" — and then sat there while the job silently never ran. **A note is not a mitigation.**
