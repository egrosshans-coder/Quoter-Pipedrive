# Kickoff Brief — Quoter/ScalePad, Next Sub-Chat

**Date:** 2026-08-27
**Predecessor:** "Quoter Item Group Build from Template", Aug 19–27 2026
**Canonical reference:** `docs/CHAPTER_3_QUOTER_SCALEPAD_AS_BUILT_2026-08-27.md`. Read it first — this is orientation, not a replacement, and Chapter 3 wins on any conflict. **Do not load older Chapter 3 versions**; several contain claims later versions retract.
**Governing discipline:** Verify, don't assume. Tag every claim **[Confirmed]** or **[Hypothesis]**.

---

## 1. Where things stand

**It works in production.** A Pipedrive automation fires, Render composes the quote from Item Groups, and Slack, email and the Pipedrive note all fire unchanged.

Confirmed live 2026-08-27: deal 3101 → `quot_3IW7X5sqOsYm0zP1MJM2c8dKwf9`, quote number `03101-20260827`, three sections, ten line items, all at $0.00.

**No hardcoded item lists anywhere in that path.** Change the catalog and the next quote is already correct, with no deploy.

**`USE_V2_COMPOSITION` is currently TRUE**, so every deal reaching the readiness gate goes through v2. Setting it to `false` in Render reverts instantly — no deploy, no rollback.

---

## 2. Do these first

Small, and each is a real risk or a real annoyance.

**2.1 Rotate `WEBHOOK_SECRET`.** It travels as `?token=` in the request URL, so it lands in every access log, and it was echoed in a log line during testing. Rotate it, and switch callers to the `X-Webhook-Token` header afterwards — the handler already accepts both.

**2.2 Demote the retry 404 to a warning.** `add_line_items_retrying` recovers from it, but `scalepad_v2.py` logs it at ERROR first, on **every multi-section quote**. Whoever reads the logs next will chase it.

**2.3 Reconcile `render.yaml`.** It declares `plan: free` while the service runs on **Starter**, and omits `SCALEPAD_API_KEY` from `envVarsFrom` though it is set in the dashboard. A blueprint-driven redeploy could try to downgrade the plan.

---

## 3. Then: the Pipedrive data rules

Decided 2026-08-26, not yet built. All three are Pipedrive-side (Chapter 3 §12.4).

- **Organization required to reach the quote stage.** Everything downstream depends on it — the Quoter Client resolves from the org name, and Pipedrive creates the QBO customer from it. One rule, three consumers.
- **A private client still gets an Organization**, named after the person. Avoids a special case in three systems.
- **Person email required**, so the composer never invents one.

Then **remove the placeholder chain** (§12.5). Today a missing email becomes `{deal_id}@gmail.com` and a missing address becomes "Address not provided" — both reached the client-facing quote on deal 3101. Once Pipedrive enforces, the composer should **fail loudly** instead of fabricating an address a quote could be sent to.

---

## 4. Also open

**Review the Pipedrive automation payload.** With the re-fetch in place (§15.2), most of it is redundant for the v2 path — the deal id alone would do. **Do not slim it until the legacy path is retired**, since that path still needs the fat payload.

**Where the bundled price sits.** TLC bundles — "$5,000 gets you balloons and Floating Video" — so the price is not per-section. The `Scope of Project` line is the obvious home. Cost tracking is unaffected either way; unit costs stay on the line items (§14.3).

**Rename the Summary block to "Notes"?** It appears automatically on any multi-section quote, so on every composed quote, and cannot be moved (§14.5).

**Email to Jon at Quoter**, drafted but not sent: section subtotals without the one-time/recurring split, whether Introductory Content can be written via API, that "Cost Breakdown" shows price rather than cost, and the backspace-vs-delete quantity bug.

---

## 5. What is built and running

| | |
| :-- | :-- |
| **21 Item Groups** | membership from catalog code prefixes, defined as data in `item_group_defs.json` |
| **`quote_composer.py`** | deal in, composed quote out. No dependency on legacy `quoter.py` |
| **Webhook branch** | `USE_V2_COMPOSITION` in `webhook_handler.py`, one call site |
| **`Standard` template** | `tmpl_3ITGNwiAtd8fvLEpiiaBK79Z1YP`, presentation only, no default items |
| **Two dropdowns** | synced daily by GitHub Actions at 13:00 UTC. **Nothing runs locally** |

**Field 90** Quote Template `enum` — presentation. Key `42ab0c919271cb24f3587f0b01ea2af166019c8d`
**Field 102** Quote Effects `set` — content. Key `118a5ce132f73d7fec1822e2a0431b51ac2a2994`

Naming: **`SCO-`** scope · **`SFX-`** effects · **`SVC-`** generic services · **`STE-`** shipping/travel/expenses.

**`SCO-ScopeOfWork` is auto-appended** as the first section and excluded from the dropdown — offering it would let someone produce two Scope sections (§13.5).

---

## 6. Six things that will bite

**6.1 Create the contact before the quote.** `createQuote` *resolves* a contact by email; it does not create one. Unknown email → `422 ERR_CONTACT_NOT_FOUND` (§12.1).

**6.2 Read the write schema off a real record.** It mirrors the read schema every time — `category: {id}`, `billing_address: {address_line_1, ...}`, bare arrays for sections. Guessing the contact schema cost three round trips; one `GET /contacts` settled it. **A 422 is about the body's CONTENTS, a 400 about its SHAPE.**

**6.3 Section reads are eventually consistent.** An id read straight after a write can 404. Only appears on multi-section quotes. `add_line_items_retrying()` handles it — do not substitute a longer sleep (§9).

**6.4 Address sections by index, never by name.** Both wristband groups render as "LED Wristbands" and one quote may carry both.

**6.5 Lowercase `x-api-key` is mandatory.** The gateway matches case-sensitively; `urllib` capitalises header names. `scalepad_v2.py` uses `requests` with a literal lowercase key (§2.1.1).

**6.6 A webhook 200 does not mean a quote was created.** `not_ready_for_quotes` and `already_processed` both return 200 with a reason. `processed_organizations.txt` lives on Render's disk and persists (§15.4).

---

## 7. Reference

**Catalog:** 292 items. `code` is the unique part number — **resolve by `filter[code]=eq:`**. `sku` is a numeric foreign key, very likely a Pipedrive product id.

**Pagination:** cursor-based, `cursor` and `page_size` (max 200). Unrecognised params are ignored silently — **always compare fetched count to `total_count`.**

**Retirement is encoded in the code prefix:** `LED-WBT-` current / `LED-WBX-` legacy · `LED-LYT-` / `LED-LYX-` · `HG-FVV-` / `HG-FVH-`. Groups take only the current prefix.

**Four Quoter mechanisms are UI-only** — Bundles, template line items, parent/child items, Item Options. ScalePad: *"we do not allow existing catalog Items to be added, just as ad-hoc Line Items."* A known limitation likely to change; re-test after a significant API release (§7.12).

**Line item descriptions DO render; catalog item descriptions do not.** Two different fields. The composer copies one to the other (§14.1).

**Pruning: blank the quantity, do not zero it.** `1` shows the line and price · `0` shows it at $0.00 · **blank** removes it. **Backspace does not clear the field — delete does** (§14.2).

**"Cost Breakdown" shows PRICE, not cost.** Verified with cost 1000 / price 600 — it reported 600 (§14.4).

---

## 8. Repo and environments

`github.com/egrosshans-coder/Quoter-Pipedrive`, cloned as `quoter_sync` on Mac Mini and MacBook Air.

**`./retrieve.sh` before `./sync.sh`, always.** The dropdown-sync workflow commits state files to `main` on its own schedule, so a push can be rejected on a stale ref. `git config pull.rebase true` avoids a merge commit each time. `sync.sh` now pushes when the tree is clean but the branch is ahead.

**Markdown goes to `docs/`. Code to the repo root.**

| File | |
| :-- | :-- |
| `scalepad_v2.py` | transport |
| `scalepad_items.py` | items + categories. **`iter_all_items()` already does the catalog pull** |
| `scalepad_quotes.py` | quotes, sections, line items, contacts, `add_line_items_retrying()` |
| `quote_composer.py` | the v2 quote path |
| `webhook_handler.py` | Flask entry point, the `USE_V2_COMPOSITION` branch |
| `build_item_groups_v3.py` + `item_group_defs.json` | group membership as data |
| `pd_fields.py`, `sync_quoter_to_pipedrive.py` | dropdown sync |
| `.github/workflows/pipedrive-dropdown-sync.yml` | the scheduler |
| `pd_option_map_*.json` | state files — committed by the workflow |
| `test_render_webhook.sh` | fires the deployed webhook and reads the outcome |
| `*_probe_*.py`, `section_diag_v1.py` | diagnostics. Evidence, not code to build on |

**Three separate secret stores that do not see each other:** local `.env` on two machines, the Render dashboard, GitHub Actions secrets.

`docs/DECISIONS.md` governs where code goes: D-003/D-004 transport and resource wrappers separate from business logic; D-006 verify endpoints before wrapping; D-010 Investigate → Understand → Design → Document → Implement → Test → Commit.

---

## 9. Process notes

Three failure modes recurred over the week. All three are cheap to avoid and expensive to repeat.

**Asserting a mechanism instead of measuring one.** Three theories about a section 404 before a diagnostic answered it in one pass. **Instrument before theorising.**

**Guessing a write schema instead of reading one.** The contact schema took three failed attempts before anyone ran `GET /contacts`. **One read replaces three round trips.**

**Documenting a flaw instead of fixing it.** The local-cron scheduling was known to be fragile the day it was built — the limitation went into a code comment and a "known gap" — and then sat there while the job silently never ran. **A note is not a mitigation.**
