# Kickoff Brief — Quoter/ScalePad, Next Chat

**Date:** 2026-08-30
**Predecessor:** the Chapter 4 session, 2026-08-29
**Canonical references, in this order:**
1. `docs/CHAPTER_3_QUOTER_SCALEPAD_AS_BUILT_2026-08-28.md` — integration mechanics
2. `docs/CHAPTER_4_QUOTE_PRESENTATION_20260829.md` — the client-facing layer
3. `docs/WORK_REQUEST_CHAPTER_3_20260829.md` — what Chapter 3 needs to do next

**Do not load older Chapter 3 versions** — several contain claims later versions retract. One Chapter 3 per session.
**Governing discipline:** Verify, don't assume. Tag every claim **[Confirmed]** or **[Hypothesis]**.

---

## 1. What changed on 2026-08-29 — read this first

Production changed. A session that does not know this will plan against a system that no longer exists.

| | |
| :-- | :-- |
| **Field 90 options** | 13 → **2**. Only `441 Basic` and `528 Standard`. |
| **Deleted options** | 442, 443, 444, 451, 452, 453, 454, 455, 456, 457, plus one stale `XX-RET-*` |
| **Ten item-named templates** | **renamed `YY-<name>`, not deleted.** All content intact in Quoter. |
| **`sync_quoter_to_pipedrive.py`** | patched — `ARCHIVE_PREFIX = "YY-"`, `is_archived()`, an exclusion in `fetch_quoter()`, an `--include-archived` flag |
| **Verified** | 2 records, 2 options, `ADD 0 / ORPHAN 0` |

### 1.1 The `USE_V2_COMPOSITION` rollback is gone — **[Confirmed]**

Chapter 3 §15.1 calls the flag a free escape hatch. **It is not one any more.** `template_selection_logic.py` hard-codes eleven field 90 option ids with no runtime lookup and no fallback; ten of those options no longer exist. Setting the flag `false` points legacy at templates and options that are gone.

**The v2 path is the only path.** Restoring a rollback means migrating `template_selection_logic.py` to `PipedriveFields.option_map(90)` first.

### 1.2 82 deals lost their Quote Template label

They stored the deleted options; **33 were open**. Composition is unaffected — `quote_composer.py` falls back to `DEFAULT_TEMPLATE_ID` (Standard) with a warning. Scanned across all 1,772 non-deleted deals before deletion, not assumed.

---

## 2. The one job worth doing next

**Open a composed v2 quote and read it as the client will.**

Everything verified so far is API-level or admin-level — 201s, section counts, warning lines. **Nobody has opened the webview or the PDF of a composed quote and read it end to end.** Scope of Work first, two or three effect sections, Shipping/Travel & Expenses, everything at $0.00.

It costs ten minutes and it answers, by inspection, several questions currently being reasoned about abstractly:

- Do three sections at $0.00 read as deliberate or broken?
- Does the Scope of Work placeholder text look like an invitation to write, or like an error?
- Does the Summary block (§14.5, automatic and unremovable) read sensibly?
- Does `LED Wristbands` appearing twice confuse, or read correctly?
- Is the missing cover letter and appended content (§3.2) actually noticeable?

**Start with `Quote for Aim Games-3097`** — draft, 2026-08-27, $0. It reads like a real customer rather than a `zz` test. If it is real, a live composed quote already exists with no cover letter and no appended content. Still a draft, so nothing has reached a client.

---

## 3. Also open

### 3.1 `WEBHOOK_SECRET` — still the security item

Carried unchanged from the 2026-08-28 brief, where it was "the one job worth doing next," and still not done. The secret travels as `?token=` in the URL, so it lands in **every access log** — structural, not accidental — and it was echoed in a log during testing, so it needs rotating regardless.

Pipedrive's automated webhooks **do not support custom headers**, so the existing `X-Webhook-Token` path is a dead end for that caller. They support **HTTP Basic Auth**. `request.authorization` exposes it in Flask.

Six steps, in order: add Basic Auth to `_is_authorized()` keeping the existing methods → deploy → set username/password on the v3 webhook and strip `?token=` → rotate `WEBHOOK_SECRET` in Render and both `.env` files → test with `test_render_webhook.sh` → remove the query-token path. **Callers before Render**, or everything 401s until you catch up.

Also: `Ready-Quoter-Draft Quote Creation-v2` still exists, points at the same endpoint, carries **no token**, and is referenced by **4 automations**. Confirm it is dead before removing.

### 3.2 Cover letter and appended content are not applied on v2 — **[Confirmed]**

`get_template_info()` returns per-template `cover_letter` and `appended_content` HTML. Its only call sites are `quoter.py:1748` and `:2003`, both inside the legacy path — which does not run. **[Confirmed, browser]** the `Standard` template carries none of it either, so there is no fallback.

Measured: `cover_letter` has **2 distinct variants across 11 templates** (ten byte-identical) — it was never per-product. `appended_content` has **11 distinct variants**, 951–1791 chars, genuinely per-product — power, space, setup/strike timings, next steps.

**Unresolved and gating:** two templating syntaxes coexist. `##CustomerOrganization##` is Quoter mail merge. `{{deal.title}}`, `{{person.first_name}}` are **Pipedrive webhook payload token syntax** — the same family `_contact_from_webhook` uses as dict keys. **[Hypothesis]** Render substituted them before sending. Nobody has read `quoter.py:1748` / `:2003` to confirm. **If it did not substitute, published quotes have been shipping with literal `{{person.first_name}}` visible to clients.** Cheapest check: open one published legacy quote and read the cover letter.

### 3.3 `_contact_from_webhook()` trusts the payload

The v2 branch re-fetches the full deal (§15.2) but still builds the contact from the webhook payload. So §12.5's placeholder chain fires on **payload** gaps, not Pipedrive gaps. **[Confirmed — Eric]** every Pipedrive Person has an email, so any placeholder that fires is a payload problem.

Matters more now: a cover letter renders the contact record, so `Dear Unknown,` becomes client-visible. Fix is to read person details from `get_deal_by_id()`. Do §13.7's phone item at the same time — `##CustomerWorkPhone##` currently renders empty on every v2 quote.

### 3.4 ~22 current products cannot be quoted at all — **[Confirmed, computed]**

286 real items: **213 in at least one Item Group, 73 in none.** Of those 73, ~12 are deliberately retired by prefix (§10.4, working correctly). The other ~22 are a genuine gap — the LED display line (walls, tubes, floor, screens, panels, mesh, letters, costumes, signage, sphere) plus Holographic Table, Slot Machine, Virtual Stage.

`item_group_defs.json`'s own `_unassigned` block already names **`SFX-LEDDisplays`** as the fix. When sales cannot find an LED wall, the likely response is a free-text line at a made-up price — no `code`, no `sku`, so no Pipedrive linkage and a hole in margin analysis (§7.12.4 warns about exactly this).

### 3.5 Decisions waiting on a human

- **Display flags per tier** (Ch4 §4.4) — Basic and Standard both inherit the account default; nothing configured.
- **The Standard cover letter** (Ch4 §6) — copy drafted, block not created. Two sentences need sign-off: the "base in Los Angeles" reach claim, and "we hold our own inventory and crew it ourselves," which is inferred and not verified.
- **Payment: QBO or Quoter** (Ch4 §7). TLC is ACH-only. **ConnectBooster is the only US gateway with card and ACH as independent toggles.** Quoter's Stripe integration is card-only. All ACH options need their own merchant contract.
- **Where the bundled price sits** (Ch3 §14.3) — `Scope of Project` line is the leading candidate.
- **Rename the Summary block to "Notes"?** Account-wide.

---

## 4. What is built and running

| | |
| :-- | :-- |
| **22 Item Groups** | membership from catalog code prefixes, defined as data in `item_group_defs.json` |
| **`quote_composer.py`** | deal in, composed quote out. No dependency on legacy `quoter.py` |
| **Webhook branch** | `USE_V2_COMPOSITION` in `webhook_handler.py`, one call site, **currently true** |
| **gunicorn** | 2 workers, 120s timeout |
| **Templates** | `Basic` (`tmpl_30O6JTDIbApan1B5gh9hF2w1tfL`) and `Standard` (`tmpl_3ITGNwiAtd8fvLEpiiaBK79Z1YP`), presentation only |
| **Two dropdowns** | synced daily by GitHub Actions, 13:00 UTC. **Nothing runs locally** |

**Field 90** Quote Template `enum` — presentation. Key `42ab0c919271cb24f3587f0b01ea2af166019c8d`
**Field 102** Quote Effects `set` — content. Key `118a5ce132f73d7fec1822e2a0431b51ac2a2994`

Group naming: **`SCO-`** scope · **`SFX-`** effects · **`SVC-`** generic services · **`STE-`** shipping/travel/expenses. `SCO-ScopeOfWork` is auto-appended first and excluded from the dropdown.

---

## 5. Things that will bite

**5.1 The rollback is gone.** §1.1. Do not plan around `USE_V2_COMPOSITION=false`.

**5.2 The `YY-` filter applies to item groups too**, because `fetch_quoter()` is shared by both sources. A group named `YY-*` drops out of field 102 the same way. Probably desirable; not a deliberate decision.

**5.3 Archiving `Standard` would not break composition** — `DEFAULT_TEMPLATE_ID` is hardcoded to its `tmpl_` id, so the composer would keep building on a template nobody can select. Worth a guard.

**5.4 Quoter's merge tokens read Quoter's own contact record, not Pipedrive.** Pipedrive data reaches them because Render writes it onto the contact at creation. The Person/Deal link of §4 serves the **return leg**, not merge-field recall. A merge token can only show what Render wrote.

**5.5 Create the contact before the quote.** `createQuote` *resolves* a contact by email; it does not create one. Unknown email → `422 ERR_CONTACT_NOT_FOUND`.

**5.6 Section reads are eventually consistent.** An id read straight after a write can 404, only on multi-section quotes. `add_line_items_retrying()` handles it. Do not substitute a longer sleep.

**5.7 Address sections by index, never by name.** Both wristband groups render as "LED Wristbands" and one quote may carry both.

**5.8 Lowercase `x-api-key` is mandatory.** The gateway matches case-sensitively; `urllib` capitalises header names.

**5.9 A webhook 200 does not mean a quote was created.** `not_ready_for_quotes` and `already_processed` both return 200 with a reason.

**5.10 `processed_organizations.txt` does not survive a deploy.** Duplicate protection resets every time.

**5.11 `render.yaml` is inert.** The start command that runs is in Render → Settings.

---

## 6. Reference

**Catalog:** 292 items. `code` is the unique part number — **resolve by `filter[code]=eq:`**. `sku` is a numeric foreign key, very likely a Pipedrive product id.

**Pagination:** cursor-based, `cursor` and `page_size` (max 200). Unrecognised params are ignored silently — **always compare fetched count to `total_count`.**

**Retirement by code prefix:** `LED-WBT-` current / `LED-WBX-` legacy · `LED-LYT-` / `LED-LYX-` · `HG-FVV-` / `HG-FVH-`.

**Prefix conventions across systems:** `XX-RET-` = retired Pipedrive option (id kept, deals still resolve) · `YY-` = archived Quoter template, hidden from the sync · `zz-`/`ZZZ-` = test artifact, safe to delete. **A `YY-` record is not test data.**

**Display settings are per-template over an account default** — **[Confirmed]**. Per-template: Cost Breakdown, Calculate Margins, Restrict Discounting, Separate One-time/Recurring Prices, Free Shipping Threshold, Calculate Tax, Hide total information. **Item title and description can never be hidden.**

**Templates are `quote_forms`.** Admin uses a numeric id, the API uses `tmpl_` — a fourth identifier scheme. Full map in Ch4 §3.2.

**Line item descriptions DO render; catalog item descriptions do not.** The composer copies one to the other.

**Pruning: blank the quantity, do not zero it.** `1` shows line and price · `0` shows $0.00 · **blank** removes it. **Backspace does not clear the field — delete does.**

**"Cost Breakdown" shows PRICE, not cost.**

**Resellers are plan-locked** — not merely unconfigured. Closes the D-011 condition more strongly than the decision assumed.

**Four Quoter mechanisms are UI-only** — Bundles, template line items, parent/child items, Item Options. A known limitation ScalePad expects to update.

---

## 7. Repo and environments

`github.com/egrosshans-coder/Quoter-Pipedrive`, cloned as `quoter_sync` on Mac Mini and MacBook Air.

**`./retrieve.sh` before `./sync.sh`, always.** The dropdown-sync workflow commits to `main` on its own schedule. `git config pull.rebase true` avoids a merge commit each time.

**Markdown goes to `docs/`. Code to the repo root.**

| File | |
| :-- | :-- |
| `scalepad_v2.py` | transport, `expect_statuses` |
| `scalepad_items.py` | `iter_all_items()` already does the catalog pull |
| `scalepad_quotes.py` | quotes, sections, line items, contacts, retries |
| `quote_composer.py` | the v2 quote path |
| `webhook_handler.py` | Flask entry point, the `USE_V2_COMPOSITION` branch |
| `build_item_groups_v3.py` + `item_group_defs.json` | group membership as data |
| `pd_fields.py`, `sync_quoter_to_pipedrive.py` | dropdown sync — **patched 2026-08-29** |
| `template_mapping_enhanced.py` | **phase 2, dead for line items.** Still the only store of the old cover letters. |
| `template_selection_logic.py` | **phase 1–2, hardcoded option ids, now stale** |
| `sync_quoter_to_pipedrive.py.bak`, `apply_archive_filter.py` | left over from the 08-29 patch, can be removed |

**Three separate secret stores that do not see each other:** local `.env` on two machines, the Render dashboard, GitHub Actions secrets.

`docs/DECISIONS.md` governs where code goes: D-003/D-004 transport and resource wrappers separate from business logic; D-006 verify endpoints before wrapping; D-008 browser investigation is the sanctioned tool for undocumented Quoter behaviour; D-010 Investigate → Understand → Design → Document → Implement → Test → Commit.

---

## 8. Working notes

**Present files under their final names.** Repeated `_v2`/`_v3` suffixes cost several manual renames.

**No trailing `#` comments on shell commands** — this zsh parses them as arguments.

**Write code, not memos about code.** The working pattern is: code is written, the user verifies it, the user runs it in terminal. A prose description of a change is a worse deliverable than the change.

**Instrument before theorising.** Every wrong turn in Chapter 3 came from inferring a mechanism instead of observing one. Three theories about a section 404 before a diagnostic answered it in one pass.

**Read the write schema off a real record.** It mirrors the read schema every time. **A 422 is about the body's CONTENTS, a 400 about its SHAPE.**

**A note is not a mitigation.** The local-cron scheduling was known fragile the day it was built, went into a comment and a "known gap", then sat there while the job silently never ran.

**Phase 1 and phase 2 code still exists in the repo.** `template_mapping_enhanced.py` and `template_selection_logic.py` are not live. Reading them as current was the single most repeated mistake of the 08-29 session — twice, by someone who had already been told. Check Ch4 §2 before trusting either.
