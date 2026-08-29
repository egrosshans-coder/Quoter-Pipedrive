# Kickoff Brief — Quoter/ScalePad, Next Sub-Chat

**Date:** 2026-08-28
**Predecessor:** "Quoter Item Group Build from Template", Aug 19–28 2026
**Canonical reference:** `docs/CHAPTER_3_QUOTER_SCALEPAD_AS_BUILT_2026-08-28.md`. Read it first — this is orientation, not a replacement, and Chapter 3 wins on any conflict. **Do not load older Chapter 3 versions**; several contain claims later versions retract.
**Governing discipline:** Verify, don't assume. Tag every claim **[Confirmed]** or **[Hypothesis]**.

---

## 1. Where things stand

**Running in production, on gunicorn.** A Pipedrive deal reaching *Send Quote/Negotiate* produces a composed Quoter quote, with Slack, email and a Pipedrive note firing unchanged.

Confirmed three times, most recently `quot_3IZJjUcbGE2bF8b2eftkdRBU1M8` under gunicorn.

**No hardcoded item lists anywhere in that path.** Change the catalog and the next quote is already correct, with no deploy.

**`USE_V2_COMPOSITION` is TRUE.** Every qualifying deal goes through v2. Setting it `false` in Render reverts instantly — no deploy, no rollback.

**A human still finishes the quote:** links it back to Pipedrive (§4, manual by design), corrects the contact if it arrived as a placeholder, prunes lines, writes the scope narrative, prices it.

---

## 2. The one job worth doing next

**Move webhook auth to HTTP Basic, and rotate `WEBHOOK_SECRET`.** Chapter 3 §16.5.

The secret currently travels as `?token=` in the URL, so it lands in **every access log** — structural, not accidental. It was also echoed in a log line during testing, so it needs rotating regardless.

`_is_authorized()` already accepts an `X-Webhook-Token` header, which looked like the fix. **It is not: Pipedrive's automated webhooks do not support custom headers.** They support **HTTP Basic Auth**, which travels in the `Authorization` header and never appears in a URL. The handler does not support that yet; `request.authorization` exposes it in Flask.

**Six steps, in this order:**

1. add Basic Auth to `_is_authorized()`, **keeping** the existing methods so nothing breaks mid-change
2. deploy
3. set username and password on the v3 webhook in Pipedrive, strip `?token=` from its URL
4. rotate `WEBHOOK_SECRET` — Render, plus `.env` on both machines
5. test with `test_render_webhook.sh`
6. remove the query-token path once nothing uses it

**Callers before Render**, or every caller 401s until you catch up. GitHub Actions is *not* affected — the dropdown sync talks to Quoter and Pipedrive directly, never to this endpoint.

**While in there:** `Ready-Quoter-Draft Quote Creation-v2` still exists, points at the same endpoint, carries **no token**, and is referenced by **4 automations**. Anything firing through it gets a 401. Confirm it is dead before removing.

---

## 3. Also open

**The Pipedrive data rules**, decided 2026-08-26, not built (§12.4): Organization required at the quote stage; a private client still gets an Organization named after the person; person email required.

**But the follow-on is now questionable.** §12.5 says the placeholder chain should then become a hard failure. Since a human already corrects contact details when linking the quote, failing a whole quote over a missing email may be the wrong trade. **Decide before building.**

**Where the bundled price sits.** TLC bundles — "$5,000 gets you balloons and Floating Video" — so the price is not per-section. The `Scope of Project` line is the obvious home. Cost tracking is unaffected either way; unit costs stay on the line items (§14.3).

**Rename the Summary block to "Notes"?** It appears automatically on any multi-section quote and cannot be moved (§14.5).

**Email to Jon at Quoter**, drafted not sent: section subtotals without the one-time/recurring split, whether Introductory Content can be written via API, that "Cost Breakdown" shows price rather than cost, and the backspace-vs-delete quantity bug.

**Pipedrive automation cleanup.** 27 automations, most disabled but cluttering. `Test Webhook`, `slack 1`, `Untitled 12/21/2024`, `(Copy) 2B-V2`, two ARCHIVE and two REMOVED are obvious candidates. A company-wide limit replaces the per-seat one on 2027-05-31 and the account is already over it — nine months out, so not urgent.

---

## 4. What is built and running

| | |
| :-- | :-- |
| **21 Item Groups** | membership from catalog code prefixes, defined as data in `item_group_defs.json` |
| **`quote_composer.py`** | deal in, composed quote out. No dependency on legacy `quoter.py` |
| **Webhook branch** | `USE_V2_COMPOSITION` in `webhook_handler.py`, one call site |
| **gunicorn** | 2 workers, 120s timeout |
| **`Standard` template** | `tmpl_3ITGNwiAtd8fvLEpiiaBK79Z1YP`, presentation only |
| **Two dropdowns** | synced daily by GitHub Actions, 13:00 UTC. **Nothing runs locally** |

**Field 90** Quote Template `enum` — presentation. Key `42ab0c919271cb24f3587f0b01ea2af166019c8d`
**Field 102** Quote Effects `set` — content. Key `118a5ce132f73d7fec1822e2a0431b51ac2a2994`

Naming: **`SCO-`** scope · **`SFX-`** effects · **`SVC-`** generic services · **`STE-`** shipping/travel/expenses.

**`SCO-ScopeOfWork` is auto-appended** as the first section and excluded from the dropdown (§13.5).

---

## 5. Eight things that will bite

**5.1 Create the contact before the quote.** `createQuote` *resolves* a contact by email; it does not create one. Unknown email → `422 ERR_CONTACT_NOT_FOUND` (§12.1).

**5.2 Read the write schema off a real record.** It mirrors the read schema every time — `category: {id}`, `billing_address: {address_line_1, ...}`, bare arrays for sections. **A 422 is about the body's CONTENTS, a 400 about its SHAPE.**

**5.3 Section reads are eventually consistent.** An id read straight after a write can 404. Only on multi-section quotes. `add_line_items_retrying()` handles it; the 404 now logs at WARNING (§16.3). Do not substitute a longer sleep.

**5.4 Address sections by index, never by name.** Both wristband groups render as "LED Wristbands" and one quote may carry both.

**5.5 Lowercase `x-api-key` is mandatory.** The gateway matches case-sensitively; `urllib` capitalises header names (§2.1.1).

**5.6 A webhook 200 does not mean a quote was created.** `not_ready_for_quotes` and `already_processed` both return 200 with a reason (§15.4).

**5.7 `processed_organizations.txt` does not survive a deploy.** Duplicate protection resets every time (§16.2).

**5.8 `render.yaml` is inert.** The start command that runs is in **Render → Settings**. The file is documentation (§16.4).

---

## 6. Reference

**Catalog:** 292 items. `code` is the unique part number — **resolve by `filter[code]=eq:`**. `sku` is a numeric foreign key, very likely a Pipedrive product id.

**Pagination:** cursor-based, `cursor` and `page_size` (max 200). Unrecognised params are ignored silently — **always compare fetched count to `total_count`.**

**Retirement is encoded in the code prefix:** `LED-WBT-` current / `LED-WBX-` legacy · `LED-LYT-` / `LED-LYX-` · `HG-FVV-` / `HG-FVH-`.

**Four Quoter mechanisms are UI-only** — Bundles, template line items, parent/child items, Item Options. ScalePad: *"we do not allow existing catalog Items to be added, just as ad-hoc Line Items."* A known limitation likely to change (§7.12).

**Line item descriptions DO render; catalog item descriptions do not.** The composer copies one to the other (§14.1).

**Pruning: blank the quantity, do not zero it.** `1` shows line and price · `0` shows it at $0.00 · **blank** removes it. **Backspace does not clear the field — delete does** (§14.2).

**"Cost Breakdown" shows PRICE, not cost.** Verified with cost 1000 / price 600 (§14.4).

---

## 7. Repo and environments

`github.com/egrosshans-coder/Quoter-Pipedrive`, cloned as `quoter_sync` on Mac Mini and MacBook Air.

**`./retrieve.sh` before `./sync.sh`, always.** The dropdown-sync workflow commits to `main` on its own schedule. `git config pull.rebase true` avoids a merge commit each time.

**Markdown goes to `docs/`. Code to the repo root.**

| File | |
| :-- | :-- |
| `scalepad_v2.py` | transport, `expect_statuses` |
| `scalepad_items.py` | **`iter_all_items()` already does the catalog pull** |
| `scalepad_quotes.py` | quotes, sections, line items, contacts, retries |
| `quote_composer.py` | the v2 quote path |
| `webhook_handler.py` | Flask entry point, the `USE_V2_COMPOSITION` branch |
| `build_item_groups_v3.py` + `item_group_defs.json` | group membership as data |
| `pd_fields.py`, `sync_quoter_to_pipedrive.py` | dropdown sync |
| `.github/workflows/pipedrive-dropdown-sync.yml` | the scheduler |
| `test_render_webhook.sh` | fires the deployed webhook, reads the outcome |
| `*_probe_*.py`, `section_diag_v1.py` | diagnostics. Evidence, not code to build on |

**Three separate secret stores that do not see each other:** local `.env` on two machines, the Render dashboard, GitHub Actions secrets.

`docs/DECISIONS.md` governs where code goes: D-003/D-004 transport and resource wrappers separate from business logic; D-006 verify endpoints before wrapping; D-010 Investigate → Understand → Design → Document → Implement → Test → Commit.

---

## 8. Working notes

**Present files under their final names.** Repeated `_v2`/`_v3` suffixes cost the user several manual renames.

**No trailing `#` comments on shell commands** — this zsh parses them as arguments.

**Three failure modes recurred over the week.** All cheap to avoid, expensive to repeat.

**Asserting a mechanism instead of measuring one.** Three theories about a section 404 before a diagnostic answered it in one pass. **Instrument before theorising.**

**Guessing a write schema instead of reading one.** The contact schema took three failed attempts before anyone ran `GET /contacts`. **One read replaces three round trips.**

**Documenting a flaw instead of fixing it.** The local-cron scheduling was known fragile the day it was built, went into a comment and a "known gap", then sat there while the job silently never ran. **A note is not a mitigation.**
