# Kickoff Brief — Quoter/ScalePad, Next Sub-Chat

**Date:** 2026-08-30
**Predecessor:** "Quoter Item Group Build from Template", Aug 19–30 2026
**Canonical reference:** `docs/CHAPTER_3_QUOTER_SCALEPAD_AS_BUILT_2026-08-30.md`. Read it first — this is orientation, not a replacement, and Chapter 3 wins on any conflict. **Do not load older Chapter 3 versions**; several contain claims later versions retract.
**Governing discipline:** Verify, don't assume. Tag every claim **[Confirmed]** or **[Hypothesis]**.

---

## 0. Read this before planning anything

**The `USE_V2_COMPOSITION` rollback no longer exists.** Chapter 3 §15.1 and the 2026-08-28 brief both describe it as a free escape hatch. It is not, as of 2026-08-29.

Ten of the eleven field-90 options were deleted, and `template_selection_logic.py` still hard-codes all eleven with no runtime lookup and no default. Setting the flag `false` now points legacy at options and templates that do not exist.

**v2 is the only path.** Restoring a rollback means migrating `template_selection_logic.py` to `PipedriveFields.option_map(90)` first (§17.1).

**There is also a second document set.** A parallel Cowork session produced `CHAPTER_4_QUOTE_PRESENTATION_20260829.md`, `TEMPLATE_REBUILD_20260829.md`, `WORK_REQUEST_CHAPTER_3_20260829.md` and `KICKOFF_BRIEF_20260830.md`, in a different date format. Chapter 4 owns the **client-facing surface**; Chapter 3 owns **integration mechanics**. Two of the work request's claims are corrected in §17.5–17.6 — check there before acting on it.

---

## 1. Where things stand

**Running in production on gunicorn.** A deal reaching *Send Quote/Negotiate* produces a composed quote, with Slack, email and a Pipedrive note firing unchanged. Confirmed repeatedly, most recently under gunicorn.

**The catalog architecture is done.** 21 Item Groups from code prefixes; two Pipedrive dropdowns synced daily by GitHub Actions; `SCO-ScopeOfWork` auto-appended as the first section.

**Templates are down to two** — `Basic` and `Standard`. The other ten are archived `YY-` and filtered out of the sync (§17.3).

**A human still finishes each quote:** links it to Pipedrive (§4, manual by design), prunes lines, writes the scope narrative, prices it.

---

## 2. The work queue

### 2.1 Retire `template_mapping_enhanced.py` — **ready to do**

**[Confirmed]** the file is dead. `TEMPLATE_BUNDLES` is superseded by Item Groups; the 11 `appended_content` variants are a prose restatement of the catalog that appended the entire product line to every quote; and at `quoter.py:1769` the write is **commented out**, so none of it has reached a quote for months (§17.5–17.6).

The cover letter text is already salvaged — `docs/COVER_LETTER_SALVAGE_2026-08-30.md` — and confirmed rendering from `Standard` → Cover Page.

**Steps:** delete the file · retire `verify_bundles.py`, its only real consumer · remove the orphaned calls at `quoter.py:1748` and `:2003`.

### 2.2 Migrate `template_selection_logic.py` to `option_map(90)`

This is what restores a rollback. Same move `quote_composer.py` already makes. Until it is done, §0 stands.

### 2.3 Webhook auth: HTTP Basic, and rotate `WEBHOOK_SECRET`

§16.5. The secret travels as `?token=` so it lands in every access log, and it was echoed in a log during testing. **Pipedrive supports HTTP Basic Auth but not custom headers**, so `X-Webhook-Token` is a dead end for that caller.

Six steps, callers **before** Render, or everything 401s. GitHub Actions is unaffected.

### 2.4 Decide the org-name leak

`Aim Games-3097` now appears twice on a client-facing cover page (§17.7). `##CustomerOrganization##` reads the same field the Quoter Client resolves from, so stripping the suffix is a behavioural change, not a cosmetic one. Cheapest option needing no code: drop the token from the cover page.

### 2.5 `SFX-LEDDisplays`

**[Confirmed, computed]** 286 real items, 213 in a group, 73 in none. About 12 are deliberately unquotable retired lines; **~22 are a genuine gap** — the LED display line plus `HG-TBL-001`, `HG-SLT-MCH`, `HG-VRT-STAGE-001`. Current products, not quotable through the automated path.

When sales cannot find an LED wall, the likely response is a free-text line at a made-up price — no `code`, no `sku`, no Pipedrive linkage, and a hole in margin analysis. §7.12.4 warns about exactly that.

### 2.6 The Pipedrive data rules

Decided 2026-08-26, not built (§12.4): Organization required at the quote stage; a private client still gets an Organization named after the person; person email required.

**The follow-on is questionable.** §12.5 says the placeholder chain should then become a hard failure — but a human already corrects contact details when linking the quote, so failing a whole quote over a missing email may be the wrong trade. **Decide before building.**

---

## 3. Six things that will bite

**3.1 Create the contact before the quote.** `createQuote` *resolves* a contact by email; it does not create one (§12.1).

**3.2 Read the write schema off a real record.** It mirrors the read schema every time. **A 422 is about the body's CONTENTS, a 400 about its SHAPE.**

**3.3 Section reads are eventually consistent.** An id read straight after a write can 404, on multi-section quotes only. `add_line_items_retrying()` handles it; the 404 logs at WARNING (§16.3).

**3.4 Address sections by index, never by name.** Both wristband groups render as "LED Wristbands".

**3.5 A webhook 200 does not mean a quote was created.** `not_ready_for_quotes` and `already_processed` both return 200 with a reason. `processed_organizations.txt` also **does not survive a deploy** (§16.2).

**3.6 `render.yaml` is inert.** The start command that runs is in **Render → Settings** (§16.4).

---

## 4. Reference

**Prefixes, three systems, three meanings:**

| | | |
| :-- | :-- | :-- |
| `XX-RET-` | Pipedrive option | retired, id kept so old deals resolve |
| `YY-` | Quoter template | archived, hidden from the sync |
| `zz-` / `ZZZ-` | Quoter items, quotes | test artifact, safe to delete |

**Group naming:** `SCO-` scope · `SFX-` effects · `SVC-` generic services · `STE-` shipping/travel/expenses.

**Field 90** Quote Template `enum` — presentation. Key `42ab0c919271cb24f3587f0b01ea2af166019c8d`
**Field 102** Quote Effects `set` — content. Key `118a5ce132f73d7fec1822e2a0431b51ac2a2994`

**Catalog:** ~292 items. `code` is the unique part number — **resolve by `filter[code]=eq:`**. `sku` holds the Pipedrive **product id** — now **[Confirmed]** from Eric's own 2025 letter to Jon Turner, not merely inferred.

**Retirement is encoded in the code prefix:** `LED-WBT-` current / `LED-WBX-` legacy · `HG-FVV-` / `HG-FVH-`.

**Line item descriptions DO render; catalog item descriptions do not.** The composer copies one to the other (§14.1).

**Pruning: blank the quantity, do not zero it.** **Backspace does not clear the field — delete does** (§14.2).

**Cover Page:** rich-text editor, **no HTML source view** — paste plain text and format with the toolbar. Title and Subtitle are separate fields and accept merge tokens (§17.7).

---

## 5. Repo and environments

`github.com/egrosshans-coder/Quoter-Pipedrive`, cloned as `quoter_sync` on Mac Mini and MacBook Air.

**`./retrieve.sh` before `./sync.sh`, always.** The dropdown-sync workflow commits to `main` on its own schedule.

**Markdown goes to `docs/`. Code to the repo root.**

**`./sync-gdrive-quoter_sync.sh`** pushes the repo folder to Drive — scoped to `quoter_sync` deliberately, because `rclone sync` mirrors and the wider `~/projects` is not Git-managed. `~/.rclone-exclude` is **per-machine and not in the repo**; the Air excludes `.git`, `__pycache__`, `.env` and backups, **the Mini does not yet**. Worth moving that list into the repo.

**Three separate secret stores that do not see each other:** local `.env` on two machines, the Render dashboard, GitHub Actions secrets.

`docs/DECISIONS.md` governs where code goes: D-003/D-004 transport and resource wrappers separate from business logic; D-006 verify endpoints before wrapping; D-010 Investigate → Understand → Design → Document → Implement → Test → Commit.

---

## 6. Working notes

**Present files under their final names.** Repeated `_v2`/`_v3` suffixes cost several manual renames.

**No trailing `#` comments on shell commands** — this zsh parses them as arguments.

**Three failure modes recurred.** All cheap to avoid, expensive to repeat.

**Asserting a mechanism instead of measuring one.** Three theories about a section 404 before a diagnostic answered it in one pass. **Instrument before theorising.**

**Guessing a write schema instead of reading one.** The contact schema took three failed attempts before anyone ran `GET /contacts`. **One read replaces three round trips.**

**Documenting a flaw instead of fixing it.** The local-cron scheduling was known fragile the day it was built, went into a comment and a "known gap", then sat there while the job silently never ran. **A note is not a mitigation.**

**And one from 2026-08-30:** the work request's §1.2 and §1.3 both rested on the assumption that legacy wrote cover letter and appended content. Ten seconds reading `quoter.py:1769` showed the write commented out, which closed one item and reframed the other. **Read the call site before planning around what a function returns.**
