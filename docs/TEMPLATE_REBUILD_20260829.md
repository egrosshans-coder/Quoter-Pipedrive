# Template Rebuild — Basic and Standard

**Date:** 2026-08-29
**Parent chapter:** `docs/CHAPTER_3_QUOTER_SCALEPAD_AS_BUILT_2026-08-28.md` — Chapter 3 wins on any conflict.
**Governing discipline:** Verify, don't assume. Claims tagged **[Confirmed]** or **[Hypothesis]**.

**Sources read for this document:** Chapter 3 (08-28) and the 08-28 kickoff brief; `quote_composer.py`, `pd_option_map_templates.json` and `pd_option_map_item_groups.json` from `gdrive:projects/quoter_sync`; and a live read-only scan of **1,772 Pipedrive deals** via the Pipedrive MCP (§3).

**Decided:**

| | |
| :-- | :-- |
| Template set | **Basic** and **Standard** only. Proposal deferred. |
| What a template carries | Presentation only. **No sections, no line items** — they cannot be retrieved from a template anyway (§6.2), so they are dead weight that misleads anyone building manually in the UI. |
| Basic | The quote and nothing else. No cover letter, no Introductory Content. |
| Standard | Basic plus **one static credibility page**, zero fill-in slots. |
| The ten item-named templates | Deleted in Quoter, retired on field 90 by the existing sync. |

**Correction to an earlier draft of this document.** It raised "does Basic keep its Scope of Work section?" as an open question. That conflated two things. `SCO-ScopeOfWork` is composed onto the quote by `quote_composer.py` and has nothing to do with the template. Scope of Work is **critical to the quote and irrelevant to the template**, and stays on every quote regardless of which template is selected. There is no decision here.

---

## 1. The v2 path is safe. The legacy path is the one-way door.

### 1.1 Field 90 degrades gracefully — **[Confirmed, source read 2026-08-29]**

From `quote_composer.py`:

```python
DEFAULT_TEMPLATE_ID = os.getenv("QUOTER_DEFAULT_TEMPLATE_ID",
                                "tmpl_3ITGNwiAtd8fvLEpiiaBK79Z1YP")  # "Standard"

template_id = DEFAULT_TEMPLATE_ID
if template_labels:
    wanted = template_labels[0]
    for t in (...quote-templates...):
        if (t.get("title") or "").strip() == wanted.strip():
            template_id = t["id"]; break
    else:
        logger.warning(f"⚠️ Template {wanted!r} selected in Pipedrive but "
                       f"not found in Quoter; using the default")
```

Both failure modes land in the same safe place:

| What happens on the deal | Path through the code | Result |
| :-- | :-- | :-- |
| Option **retired** to `XX-RET-Balloons` | label resolves, no template titled that | warning → **Standard** |
| Option **deleted** from field 90 | `_resolve_labels` finds no label, returns `[]` | warning → **Standard** |

**So composition never breaks on a missing template.** Field 90 is a soft dependency.

**Field 102 is the hard one**, and it is worth knowing the asymmetry:

```python
if not group_names:
    logger.error("❌ No Quote Effects selected on the deal. Nothing to compose …")
    return None
```

That is the correct split — presentation can fall back to a default, content cannot be guessed — and it means this entire rebuild touches only the forgiving half.

### 1.2 What genuinely does not survive

`USE_V2_COMPOSITION=false` is sold as a free escape hatch (§15.1: *"a Render environment setting, not a deploy or a rollback"*). **That stops being true once the ten templates are deleted.** The legacy path resolves through `template_selection_logic.py`, which hard-codes the eleven option ids and their slugs — no runtime lookup, no default fallback. Flip the flag back afterwards and legacy points at templates that no longer exist.

Walk through the door knowingly. Two ways to keep it open if you want it: delete the ten templates last, after Basic and Standard have run for a while; or migrate `template_selection_logic.py` to `option_map(90)` first, which §18 already lists.

---

## 2. What "only the quote" cannot strip

**The Summary block is structural.** §14.5 — it appears on any quote with more than one section, cannot be removed or moved, and only its header text is editable, at `/admin/localizations`, **account-wide**. Composition always produces more than one section, so it is on every Basic quote. Renaming it to "Notes" is the only lever, and that is already an open item.

Everything else does strip.

---

## 3. Field 90: the reference check, run

**[Confirmed, live read-only scan, 2026-08-29]** All 1,772 non-deleted deals across `open`, `won` and `lost`, cursor exhausted (`next_cursor: None` on the final page). 133 carry a field 90 value; 1,639 do not, which is expected — the field is only Required from the Send Quote stage onward and most deals never reach it.

| Option | Template | Deals | Open | Won | Lost | Disposition |
| :-: | :-- | :-: | :-: | :-: | :-: | :-- |
| 444 | LED Wristbands | **31** | 9 | 8 | 14 | retire — do not delete |
| 457 | Robotics | **27** | 9 | 7 | 11 | retire — do not delete |
| 454 | Floating Video | **13** | 9 | 1 | 3 | retire — do not delete |
| 442 | Confetti/Streamers | 4 | 2 | 2 | — | retire — do not delete |
| 451 | Balloons | 4 | 3 | — | 1 | retire — do not delete |
| 453 | Fireworks/pyro/fire | 2 | 1 | 1 | — | retire — do not delete |
| 443 | LED Lanyards | 1 | — | — | 1 | retire — do not delete |
| 452 | CO2/Smoke/Upright Foggers | **0** | — | — | — | **unreferenced — safe to delete** |
| 455 | Low level fog | **0** | — | — | — | **unreferenced — safe to delete** |
| 456 | Tank Delivery | **0** | — | — | — | **unreferenced — safe to delete** |
| | **total** | **82** | 33 | 19 | 30 | |

Kept: **441 Basic** (50 deals) · **528 Standard** (1 deal).

### 3.1 What this means

**Three options can be deleted outright today** — 452, 455, 456 — at zero cost. Nothing references them.

**Seven should be retired, not deleted.** Per §1.1 deleting them would not break composition, so the reason is not operational: it is that **the stored option is the only record of what those 82 quotes were built from.** Field 102 did not exist when most of them were created, so option 457 *is* the history of "this deal was a Robotics quote." Retiring keeps the id and a readable label; deleting throws that away for a tidier picker.

**The 33 open deals need no action.** They will compose on Standard with a warning line. If you would rather they carry a deliberate choice, re-pick Basic or Standard on each — but nothing fails if you do not.

**Six deals in that set are test data** — `zz51`, `zz30`, `zz31`, `zz32`, `zz52`, `zz52-deal2`, plus `Test for Quota` and the `zz-Gotham City` deal 3007 already listed in §18's cleanup. Worth discounting when reading the open count.

### 3.2 Three unexplained entries in the state file

`pd_option_map_templates.json` holds **15** pairings, not the 14 §11.10 records. Three do not appear in Chapter 3's §7.7 inventory:

| Option | Template id |
| :-: | :-- |
| 503 | `tmpl_3IKtZJCVSfO2qdb7GJwwt8Tm3KN` |
| 504 | `tmpl_3IKun1uqGXO1vRP9RqkkuzZYaB7` |
| 505 | `tmpl_3IKwYt07pjtRAtnsxhYFTz2E7gq` |

**[Hypothesis]** These are the `ZZ Test Template` / `ZZ Renamed Template` / `ZZ TEST3 Template` artifacts from the §11.8 lifecycle testing. **No deal references any of them** — the scan found only 441, 528 and the ten above. Confirm and clear them while you are in there.

---

## 4. The Standard cover letter

### 4.1 Why this one gets used

The appendage risk has a specific cause, and it is not the wording. A per-deal cover letter **competes with `SCO-WORK-001` "Scope of Project"** — a $0.00 line whose description the salesperson already rewrites every deal (§10.7), and the leading candidate to carry the bundled price (§14.3). Ask for a deal-specific narrative in a cover letter too and sales writes the same story twice, in two editors. The one further from the price loses.

**So this letter is deliberately not deal-specific.** Nothing to write, nothing to keep current, and no `[EVENT NAME]` placeholder that can reach a client — the same failure class as §12.5's fabricated email, except client-visible.

**The adoption mechanism is that sales does nothing.** It lives in the template and is never edited. Its last line hands off to the Scope of Work section, so the two complement rather than duplicate.

### 4.2 Mechanics

Cover Letter is **Deprecated** in Quoter in favour of **Introductory Content** (§14.6), so this is an Introductory Content block, and each such block **starts its own page** — correct for a letter, and why it cannot sit as a paragraph above the line items.

**[Untested]** Whether content blocks can be written via API or seeded from a template (§14.6). Assume this is built once by hand on Standard.

### 4.3 The copy

> ## TLC Creative
>
> TLC Creative designs and delivers live special effects for events, broadcast, and brand experiences, from our base in Los Angeles.
>
> We work across the full range of effect: lasers and projection, pyrotechnics and flame, CO2, fog and low-level atmospherics, confetti and streamers, snow, water features, drones, robotics, holographic and floating video displays, and LED audience engagement — wristbands, lanyards, and glow elements — at scales from a single room to an arena floor.
>
> That range is the point. Most effects work is subcontracted piece by piece, which means more vendors, more load-in windows, and more people who each know one part of your show. We hold our own inventory and crew it ourselves, so a show combining lasers, holographic displays and an LED audience moment is one contract, one site survey, one team on site, and one number to call when the run-of-show changes at four in the afternoon.
>
> Every quote we issue is itemised. Equipment, crew, and travel are listed separately, so you can see what is included and adjust scope without starting the conversation over.
>
> The pages that follow set out the scope of your project and what it covers.

~180 words. One page.

### 4.4 What I did and did not claim

Every factual claim is drawn from your own catalog — the effect list is the §10.2 group list, the itemisation claim is what composition produces. **I invented no credentials:** no years in business, no client names, no productions, no crew size, no certifications, no awards.

**Two need your confirmation:**

1. **"from our base in Los Angeles"** — LA is confirmed; the sentence implies reach beyond it. The deal titles in the scan show New York, Miami, Denver, Vegas, San Diego and Boise, so the implication looks right — but say if it should read differently.
2. **"We hold our own inventory and crew it ourselves"** — inferred from the catalog carrying rental items and your own technician lines (`SVC-LSR-TECH`, `SVC-ROB-HDLR`, `SVC-WBT-TECH`). Plausible, not verified. If any of it is subcontracted this sentence must change; it is the paragraph doing the most work and the one a client could hold you to.

**What would strengthen it, if you supply the facts:** years operating, a named production, crew size, a safety credential. Any beats the general case. Left out rather than guessed.

---

## 5. Runbook

**1. Strip both templates to presentation only.** Remove every section and line item from `Basic` (`tmpl_30O6JTDIbApan1B5gh9hF2w1tfL`) and `Standard` (`tmpl_3ITGNwiAtd8fvLEpiiaBK79Z1YP`). Chapter 3 §7.7 records Basic carrying 1 line item. This has **zero effect on the v2 path** — the composer passes `template_id` and never reads template contents — so the reason is that a stray line item misleads anyone building a quote manually in the UI.

Consider renaming Basic's slug from `test`. Cosmetic for the API path; §7.7's rule still holds — **slugs are read from `GET /quote-templates`, never generated.**

**2. Standard.** Add the §4.3 copy as an Introductory Content block.

**3. Verify before deleting.** Compose one draft on each and read the rendered preview. Expect the Summary block on both (§2) and a Scope of Work section on both (composer-side, by design).

**4. Delete the ten item-named templates in Quoter.** Ids in §7.7.

**5. Dry-run the sync.** Dispatch `pipedrive-dropdown-sync.yml` manually with `dry_run: true` and read the orphan report before it writes (§11.11.1). Do not wait for the nightly run and hope.

**6. Let it write.** Field 90 ends up holding `Basic`, `Standard`, and ten `XX-RET-*` options with ids preserved.

**7. Delete only the three unreferenced options** — 452, 455, 456 — in the Pipedrive UI. Leave the other seven retired: they are the history of 82 quotes (§3.1).

### 5.1 The overnight job already exists

Worth stating plainly, since it was the part that sounded like new work: **you do not need to build a timed update.** `.github/workflows/pipedrive-dropdown-sync.yml` runs daily at 13:00 UTC / 06:00 PT and already passes `--retire-orphans` unattended (§11.10, §11.11.1). The overnight behaviour you asked for is what it does. The decision was never whether to schedule it — it was what it should be allowed to do when it fires, and §3 answers that with evidence.

If 06:00 PT is later than you want the dropdown settled, the cron line is the only thing to change.

---

## 6. Left open

**Renaming the Summary block to "Notes"** — account-wide, affects both templates equally.

**Confirm and clear options 503/504/505** (§3.2) once verified as lifecycle-test artifacts.

**`pd_option_map_templates.json` gets staler** — 15 pairings against what will be 2 live templates. Harmless, and the file is what makes a rename distinguishable from a delete-plus-create (§11.6), so prune carefully or not at all.

**Untested, and now more load-bearing:** whether ScalePad's `/quote-templates` returns the same set the legacy endpoint did (§11.10). Never diffed. With two templates left, drift there is far more visible than it was with eleven.
