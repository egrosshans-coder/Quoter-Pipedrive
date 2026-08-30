# Work Request — Chapter 3

**From:** the Chapter 4 session, 2026-08-29
**To:** whoever holds Chapter 3
**Read first:** `docs/CHAPTER_3_QUOTER_SCALEPAD_AS_BUILT_2026-08-28.md`, then `docs/CHAPTER_4_QUOTE_PRESENTATION_20260829.md`
**Governing discipline:** Verify, don't assume. Everything below is tagged **[Confirmed]** or **[Hypothesis]**.

This is a handoff, not a chapter. It records **what changed in production today**, **what that broke or exposed**, and **what Chapter 3 needs to do about it**. Chapter 4 owns the client-facing surface; every item below is integration mechanics and belongs to Chapter 3.

---

## 0. Read this before planning anything

### 0.1 The `USE_V2_COMPOSITION` rollback no longer exists — **[Confirmed]**

Chapter 3 §15.1 sells the flag as a free escape hatch: *"Reverting is a Render environment setting, not a deploy or a rollback."*

**That is no longer true.** As of 2026-08-29, ten of the eleven Pipedrive field 90 options were deleted, and `template_selection_logic.py` hard-codes all eleven option ids with no runtime lookup and no default fallback. Setting the flag to `false` now points the legacy path at options and templates that do not exist.

**Consequence:** the v2 path is the only path. Any plan that assumes a one-setting revert needs rewriting. If a rollback capability is wanted back, `template_selection_logic.py` must be migrated to `PipedriveFields.option_map(90)` first — which §18 already lists as migration work, now promoted from housekeeping to the thing standing between you and a rollback.

### 0.2 What changed in production today — **[Confirmed]**

| Change | Detail |
| :-- | :-- |
| Field 90 options | 13 → **2**. Only `441 Basic` and `528 Standard` remain. |
| Deleted options | 442, 443, 444, 451, 452, 453, 454, 455, 456, 457 — plus one leftover `XX-RET-*` from §11.8 testing |
| Quoter templates | ten item-named templates **renamed** `YY-<name>`, not deleted. All content intact. |
| `sync_quoter_to_pipedrive.py` | patched: `ARCHIVE_PREFIX = "YY-"`, `is_archived()`, an exclusion in `fetch_quoter()`, and an `--include-archived` diagnostic flag |
| Verified | 2 records, 2 options, `ADD 0 / ORPHAN 0`. The filter is inert until a record is renamed. |

**82 deals** stored one of the deleted options; **33 were open**. Their Quote Template field now reads blank. Composition is unaffected — `quote_composer.py` falls back to `DEFAULT_TEMPLATE_ID` (Standard) and logs a warning. This was scanned across all 1,772 non-deleted deals before the deletion, not assumed.

**The `YY-` filter applies to item groups as well as templates**, because `fetch_quoter()` is shared by both sources. A group named `YY-*` would drop out of field 102 the same way. Probably desirable; it was not a deliberate design decision.

---

## 1. Priority work

### 1.1 `_contact_from_webhook()` trusts the payload instead of the re-fetch — **[Confirmed, source read]**

**The problem.** The v2 branch already re-fetches the full deal (§15.2), but the contact is still built from the webhook payload:

```python
name  = (organization_data.get("{{deal.person_name}}")
         or organization_data.get("person_name") or "")
email = (organization_data.get("{{person.email}}")
         or organization_data.get("person_email") or "")
```

So §12.5's placeholder chain — `{deal_id}@gmail.com`, `Unknown` / `Contact`, `Address not provided` — fires when **the payload** lacks a field, **not** when Pipedrive lacks it. **[Confirmed — Eric]** every Pipedrive Person has an email address, so any placeholder that fires is a payload gap, not a data gap.

**Why now.** §12.5 has sat as a data-quality note for months. Chapter 4 §6 puts a cover letter on the quote, and a cover letter renders the contact record — so `Dear Unknown,` becomes client-visible rather than merely untidy. Nothing about the mechanism changed; the consequence did.

**The fix.** Read person details from `get_deal_by_id()` rather than the payload. The composer already holds that object. This is the same move §15.2 made once for field 102, and §13.4 already draws the general conclusion — *"the webhook is a trigger, not a data source… the payload can shrink substantially."*

**Do §13.7's phone item at the same time** — same function, same source, and `##CustomerWorkPhone##` currently renders empty on every v2 quote because the composer never passes it.

**Verify:** compose on a deal whose payload deliberately omits person name and email, and confirm the contact resolves correctly from the API rather than falling back.

### 1.2 Decide whether the composer writes cover letter and appended content — **[Confirmed gap]**

**The finding.** `get_template_info()` in `template_mapping_enhanced.py` returns per-template `cover_letter` and `appended_content` HTML. Its only call sites are `quoter.py:1748` and `:2003`, both inside the legacy `create_comprehensive_quote_from_pipedrive`. With `USE_V2_COMPOSITION` true, **neither runs.**

**[Confirmed, browser 2026-08-29]** the `Standard` template carries no Cover Page, no Content Blocks, no Cover Letter and no Appended Content. So **v2 quotes currently ship with none of it, and there is no fallback.**

**Scale of the loss, measured:**

| | |
| :-- | :-- |
| `cover_letter` | **2 distinct variants across 11 templates.** Ten are byte-identical (978 chars); only Floating Video differs. Never per-product. |
| `appended_content` | **11 distinct variants**, 951–1791 chars — power, space, setup/strike timings, next steps, per effect type. Genuinely per-product. |

**The architectural question for Chapter 3:** should the composer write this content at all, or does it come from the template? If from the template, it is static and Chapter 4's problem. If from the composer, it can be per-quote and Chapter 3 owns it — and the only per-quote text v2 writes today is the **line item description**, which §14.1 confirms renders and §4.1 of Chapter 4 confirms can never be hidden.

**Not urgent in one specific sense:** `USE_V2_COMPOSITION` went true 2026-08-27 and sales is not on this path yet. **But check `Quote for Aim Games-3097`** (draft, 2026-08-27, $0) — it reads like a real customer org rather than a `zz` test. If it is real, a live composed quote already exists with none of this content. Still a draft, so nothing has reached a client.

### 1.3 Resolve the `{{...}}` substitution question — **[Unresolved]**

Two templating syntaxes coexist in `template_mapping_enhanced.py`:

- `##CustomerOrganization##`, `##QuoteExpiryDate##` — Quoter mail merge, resolved at render
- `{{deal.id}}`, `{{deal.title}}`, `{{deal.owner_name}}`, `{{person.first_name}}`, `{{quote.url}}` — **Pipedrive webhook payload token syntax**, the same family `_contact_from_webhook` uses as dict keys

The shared cover letter opens `<p>Hi {{person.first_name}},</p>`.

**[Hypothesis]** Render substituted the `{{...}}` tokens before sending, making this a two-stage scheme: Render resolves Pipedrive-shaped tokens, Quoter resolves its own. **Unverified** — nobody has read `quoter.py` around lines 1748 and 2003 to confirm the substitution exists.

**Two outcomes, both worth knowing:**

- **It substitutes** → that logic dies with the legacy path, and any content carrying `{{...}}` cannot move to a Quoter template unchanged.
- **It does not** → published quotes have been shipping with literal `{{person.first_name}}` visible to clients, which is a live defect in existing documents.

**Cheapest check:** open one published legacy quote and read the cover letter. If it says a name, it substituted.

**Note for the record.** Quoter's merge tokens read **Quoter's own contact record**, not Pipedrive. **[Confirmed — Eric, and consistent with the mail-merge picker, which lists only `Business*` / `Customer*` / `Quote*` / `User*` and no Pipedrive-shaped variables.]** Pipedrive data reaches those tokens because Render writes it onto the contact at creation. The Person/Deal link of §4 is for the **return leg** (§4.2), not for pulling fields forward. This corrects a claim made and retracted during the Chapter 4 session.

### 1.4 `WEBHOOK_SECRET` — unchanged and still open

§16.5, and the 2026-08-28 brief's *"one job worth doing next."* The secret still travels as `?token=` in every access log and was echoed in a log during testing, so it needs rotating regardless. Nothing about it changed today. Flagged only so it is not lost under newer items — it is the only item here with an adversary.

---

## 2. Secondary work

### 2.1 `SFX-LEDDisplays` and the unassigned catalog — **[Confirmed, computed]**

**286 real items: 213 in at least one Item Group, 73 in none.** Two categories:

- **~12 deliberately unquotable** — `HG-FVH-*`, `LED-WBX-*`, `LED-LYX-001`, the HTX pair. §10.4's retirement-by-prefix working correctly.
- **~22 a genuine gap** — the LED display line (walls, tubes, floor, screens, panels, mesh, letters, costumes, signage, sphere) plus `HG-TBL-001`, `HG-SLT-MCH`, `HG-VRT-STAGE-001`. Current products, in no group, **not quotable through the automated path at all.**

`item_group_defs.json`'s own `_unassigned` block already names `SFX-LEDDisplays` as the candidate fix.

**Why this matters more than it looks.** When sales cannot find an LED wall in Quote Effects, the likely response is a free-text line at a made-up price — no `code`, no `sku`, therefore no Pipedrive product linkage (§2.2.4) and a hole in margin analysis. §7.12.4 warns about exactly that behaviour. LED walls are not exotic; this is the gap most likely to be hit first.

Remainder to triage: `EQP-` (9, support kit), `FIN-` (5–6, commercial terms), ~12 single-item prefixes.

### 2.2 Guard `DEFAULT_TEMPLATE_ID`

`quote_composer.DEFAULT_TEMPLATE_ID` is hardcoded to Standard's `tmpl_` id. If `Standard` were ever archived `YY-`, it would vanish from the dropdown while the composer kept building on it — quotes on a template nobody can select. Add a check, or at minimum a note.

### 2.3 Housekeeping

- **Prune options 503/504/505** from `pd_option_map_templates.json`. **[Confirmed]** stale — those templates are absent from the Quoter admin list, and no deal references them.
- **Record the D-011 confirmation.** §18 asked to confirm no Resellers are configured. **[Confirmed]** `/admin/resellers/` is a locked upsell page — *"Ask your Account Owner to Unlock."* The feature is not on TLC's plan, so D-011's condition is guaranteed by a plan lock rather than by an empty configuration. Stronger than the decision assumed.
- **`sync_quoter_to_pipedrive.py.bak`** and `apply_archive_filter.py` are in the repo root from today's patch and can be removed.

---

## 3. What is already decided — do not re-litigate

| Decision | Where |
| :-- | :-- |
| Template set is **Basic** and **Standard**; Proposal deferred | Ch4 §3, `TEMPLATE_REBUILD_20260829.md` |
| Templates carry **presentation only** — no sections, no line items | Ch4 §2 |
| The ten item-named templates are **archived, not deleted** — the cost asymmetry argument, not a probability estimate | Ch4 §8.1 |
| `YY-` marks an archived Quoter record; `XX-RET-` marks a retired Pipedrive option; `zz-`/`ZZZ-` marks test data | Ch4 §9 |
| Display settings are **per-template over an account default** | Ch4 §4 |
| The Standard cover letter is **static, no fill-in slots** | Ch4 §6 |

Chapter 4 owns display flags, cover letter copy, where appended content lives, acceptance and payments, the Summary block rename, and where the bundled price sits. Do not absorb those.

---

## 4. Corrections to carry into Chapter 3's next revision

| Section | Correction |
| :-- | :-- |
| §15.1 | The `USE_V2_COMPOSITION` revert is no longer a rollback (§0.1 above) |
| §12.5 | The placeholder chain fires on **payload** gaps, not Pipedrive gaps. Every Pipedrive Person has an email. Priority raised because Ch4 §6 makes the contact client-visible. |
| §13.7 | Phone is still unpassed, and now has a visible consequence — `##CustomerWorkPhone##` renders empty |
| §18 | Reseller confirmation **resolved** (§2.3 above) |
| §11.10 | The three stale state pairings are **confirmed** stale, not hypothesised |
| §4 | Worth stating explicitly that the Person/Deal link serves the return leg and **not** merge-field recall — the distinction caused a wrong claim during the Ch4 session |

---

## 5. Suggested order

1. **§1.3** — read `quoter.py:1748` / `:2003`, or open one published legacy quote. Cheapest, and it determines whether §1.2 is a content-migration problem or a live defect in existing documents.
2. **§1.1 + §13.7 together** — one function, one change, closes the placeholder question before any cover letter ships.
3. **§1.2** — decide where cover letter and appended content come from. Needs §1.3 answered first.
4. **§1.4** — `WEBHOOK_SECRET`. Independent of everything above; do it whenever there is a deploy window.
5. **§2.1** — `SFX-LEDDisplays`, before sales starts using the path in anger.

**§0.1 is not a task but it gates planning.** Anything written on the assumption that the flag is a rollback needs revisiting first.
