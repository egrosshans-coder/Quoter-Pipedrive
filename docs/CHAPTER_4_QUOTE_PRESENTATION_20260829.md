# Chapter 4 — Quote Presentation & the Commercial Layer (As-Built)

**Status:** Draft — first working version
**Date:** 2026-08-29
**Parent:** `docs/CHAPTER_3_QUOTER_SCALEPAD_AS_BUILT_2026-08-28.md`. Chapter 3 owns integration mechanics — how a quote is assembled. **Chapter 4 owns what the client reads and agrees to.**
**Companion:** `docs/TEMPLATE_REBUILD_20260829.md` — the Basic/Standard decision and the field 90 reference check.
**Governing discipline:** Verify, don't assume. Every claim tagged **[Confirmed]** or **[Hypothesis]**.

**Method.** Read directly from the Quoter admin in a supervised browser session on 2026-08-29, per `DECISIONS.md` **D-008 — Browser Investigation as an Engineering Tool**. Read-only except where §8 records a deliberate change. Deal data read via the Pipedrive API, read-only.

---

## 1. Purpose & Scope

Chapter 3 established that **a template contributes nothing to a quote's line items** (§6.2, vendor-confirmed §6.2.1). That finding emptied the template of content and left unexamined what a template actually *does* carry. This chapter answers that, and covers the rest of the client-facing surface.

**In scope:** the template object, cover page and content blocks, display flags, acceptance and payment terms, PDF and branding, and the archive mechanism that keeps unused templates without offering them.

**Out of scope:** composition, Item Groups, the API write path. Chapter 3 owns those.

---

## 2. How we got here — three phases

Recorded because the repository still contains code from phases 1 and 2, and reading it as current is the single easiest mistake to make. It was made twice during the session that produced this chapter.

### Phase 1 — templates named after effects

Templates were created named for what they sold: `Balloons`, `Robotics`, `LED Wristbands`. Line items were placed in them, and in some cases sections.

Then draft quotes were created from those templates via the API, and **the line items did not arrive**. Some template content reaches a draft quote; sections and line items do not. This was not understood at the time, and the templates were built before anyone understood Quoter well enough to build them differently.

### Phase 2 — hardcoded line items in Python

Since templates could not supply line items, the items were embedded in Python — `template_mapping_enhanced.py`, ~70KB, hundreds of lines. Clumsy, and the only available way to populate a draft quote during API creation.

**This file is phase 2. It is not live and must not be read as current.** Chapter 3 §8.1 records it as the thing the migration exists to remove.

### Phase 3 — Item Groups as sections — **current**

An Item Group is a **section of a quote, containing that section's line items**. Composing a quote means selecting the sections it needs:

```
Scope of Work   section 1   (auto-appended, never selected)
Balloons        section 2
Lasers          section 3
```

Pipedrive field 102 carries the selection; `quote_composer.py` resolves each group to its items and writes one section per group. **This is where the system is.**

### 2.1 What this means for the repository

| File | Phase | Status |
| :-- | :-: | :-- |
| `template_mapping_enhanced.py` | 2 | dead. Retained as a drift record only. |
| `template_selection_logic.py` | 1–2 | dead for composition; still holds the hardcoded enum map the legacy path uses |
| `quote_composer.py`, `item_group_defs.json`, `build_item_groups_v3.py` | 3 | live |
| `sync_quoter_to_pipedrive.py`, `pd_fields.py` | 3 | live |

**[Consequence]** Deleting the phase-1 templates cannot lose anything composition can reach, because composition never could read template contents. Their line items have been inert since phase 1 ended. See §8 for what was done instead, and why.

---

## 3. A template is a `quote_form`

### 3.1 Addresses

| | |
| :-- | :-- |
| List | `/admin/quote_forms` |
| Edit | `/admin/quote_forms/edit/{numeric_id}` |
| View · Copy · Delete | `/view/{id}` · `/add/quoteForm:{id}` · `/delete/{id}` |
| New | `/admin/quote_forms/add` |
| New quote from template | `/admin/quotes/create/{slug}` |

### 3.2 A fourth identifier scheme — **[Confirmed]**

Chapter 3 §7.6 recorded three id schemes for a quote. Templates add a fourth: **the admin UI addresses a template by numeric id, the API by `tmpl_`.** Nothing maps between them except the title.

| Template (title as at 2026-08-29) | numeric | `tmpl_` | slug |
| :-- | :-: | :-- | :-- |
| **Basic** | 50826 | `tmpl_30O6JTDIbApan1B5gh9hF2w1tfL` | `test` |
| **Standard** | 56760 | `tmpl_3ITGNwiAtd8fvLEpiiaBK79Z1YP` | `standard` |
| YY-Balloons | 51512 | `tmpl_32CqUL7Iloih2Xgx68JvjptGYXy` | `balloons` |
| YY-LED Wristbands | 51457 | `tmpl_329ZyWvDiEV9fA41C33QIisOeq1` | `led-wristbands` |
| YY-LED Lanyards | 51460 | `tmpl_329mwOURxx9hmgNuQmfkM4L8Xxw` | `led-lanyards` |
| YY-Robotics | 51462 | `tmpl_329qcsv6mx0upqqLkXFkEZZi92O` | `robitics` |
| YY-Confetti/Streamers | 51474 | `tmpl_32A0sbTQSxRN0d6K5pHenlaqUlD` | `confetti` |
| YY-Floating Video | 51475 | `tmpl_32A1eLVDiKYi3PBlIiAv0w1UgLG` | `floating-video` |
| YY-CO2/Smoke/Upright Foggers | 51478 | `tmpl_32A8f3F2d7dQF7NsDIqCQSVLatF` | `co2smokeupright-foggers` |
| YY-Fireworks/pyro/fire | 51480 | `tmpl_32ACJvG7U2tHAmiKzxhXXx3Pnns` | `fireworkspyro` |
| YY-Low level fog | 51495 | `tmpl_32CORYSQ1OgAJVjA5EmY8YfXpCq` | `low-level-fog` |
| YY-Tank Delivery | *(not captured)* | `tmpl_31vLnIjRObApRldxGd7V3LSuEd8` | `quick-quote` |

**Slugs must be read from `GET /quote-templates`, never generated** (Chapter 3 §7.7). `Robotics → robitics` is misspelled at source and `Tank Delivery → quick-quote` was repurposed. **[Untested]** whether the 2026-08-29 renames regenerated the slugs; irrelevant to composition, which resolves by `tmpl_` id, but it would break bookmarked `/admin/quotes/create/<slug>` links.

**The three ZZ lifecycle-test templates are gone** from the admin list, confirming that options 503/504/505 in `pd_option_map_templates.json` are stale pairings for deleted records.

### 3.3 The eight panels — **[Confirmed]**

A template edit page is one form with eight anchored panels, all present in the DOM simultaneously:

| Panel | Anchor | Carries |
| :-- | :-- | :-- |
| Default Items | `#default-line-items` | sections, line items, recurring fee frequency |
| Cover Page | `#cover-page` | Title, Subtitle, rich-text Content, background image |
| **Content Blocks** *(NEW)* | `#content-blocks` | attach blocks from the shared library (§5) |
| Cover Letter | `#cover-letter` | the deprecated predecessor to Content Blocks |
| Appended Content | `#appended-content` | content rendered after the line items |
| **Acceptance & Payments** | `#acceptance-payments` | electronic acceptance, online payment (§7) |
| Contracts | `#automations` | contract automation |
| **Settings** | `#settings` | display flags, PDF, branding, notifications (§4) |

**Cover Letter and Content Blocks both exist.** Content Blocks is badged NEW; Chapter 3 §14.6 recorded Cover Letter as Deprecated. Use Content Blocks.

### 3.4 Recurring fees are a template-level constraint — **[Confirmed]**

> "Note that a Template can only utilize one recurring billing frequency. If any of your included Items contain recurring fees, their billing frequencies will be adjusted in your Quotes to match the billing frequency set below."

Per template: **Recurring Fee Billing Frequency** (Monthly / Quarterly / Semi-annually / Annually), **N payment(s) upfront**, **N day grace period**. All 12 templates read Monthly / 0 upfront / 0 grace.

**[Hypothesis]** Irrelevant to TLC — event work is one-time. Recorded because *"payments upfront"* is the nearest native thing Quoter has to a deposit schedule, and §7 needs to establish whether a deposit belongs there or elsewhere.

---

## 4. Display settings: per-template, over an account default — **[Confirmed, verbatim]**

**This resolves the question Chapter 3 left open**, and it is what makes a Basic/Standard split meaningful rather than cosmetic.

`/admin/quote_columns`:

> "Set the default data shown in your Quote's pricing table. Changes will be applied to newly generated Quotes. **If per-Template Pricing Table display settings have been set at the Template level, the Template Pricing Table display settings will take priority.** Item title and description cannot be hidden."

The template's own Settings panel carries the override as an explicit choice:

- ○ **Use Account Pricing Table display settings**
- ○ **Customize Pricing Table display for this Template**

> "Customizing Pricing Table display for this Template will take priority over the Account-level Pricing Table display settings."

### 4.1 What is controllable, and where

| Setting | Account default | Per-template |
| :-- | :-: | :-: |
| Pricing Table columns — Category, Manufacturer/Code, Quantity, Unit Price, Line Total | ✓ | override |
| Cost Breakdown | — | ✓ |
| Calculate Margins | — | ✓ |
| Restrict Discounting | — | ✓ |
| Separate One-time/Recurring Prices | — | ✓ |
| Free Shipping Threshold | — | ✓ |
| Calculate Tax | — | ✓ |
| Hide total information | — | ✓ |

**Item title and description can never be hidden.** This is why Chapter 3 §14.1 — that line-item descriptions render — is load-bearing rather than incidental: the description column is the one guaranteed channel to the client.

### 4.2 Two behaviours carried from Chapter 3 that constrain the choice

**A per-section subtotal appears only when *Separate One-time/Recurring Prices* is on** (§14.3), and it arrives with a "One-Time Fees" header. There is no combination giving line items without prices *and* a section subtotal.

**"Cost Breakdown" shows PRICE, not cost** (§14.4) — verified with unit cost 1000 against unit price 600, which reported 600. It groups by **full category path** (`Balloons / Wall-Flying`), unlike `GET /items`, which returns only the leaf name (§2.3.1). So it is safe client-facing and works as a per-category rollup.

### 4.3 Also in the per-template Settings panel

Quote tags · Auto CC · Auto BCC · Order Notification Recipients · default-vs-custom PDF filename · a separate Accepted PDF filename · **up to three file attachments** (max 10 MB each) automatically included with the quote · header and footer background images for all pages · *Show Standard Page Header*.

A Cover Page background image takes priority over the all-pages header image.

### 4.4 **[Open]** which flags each tier sets

A commercial decision, not a technical one. Basic can hide Cost Breakdown and margins and run a minimal column set; Standard can show the fuller picture. Neither has been configured — both currently inherit the account default.

---

## 5. Content Blocks, Cover Page, and mail merge

### 5.1 Content Blocks are a shared library — **[Confirmed]**

`/admin/content_blocks`. Blocks are authored once and attached to templates rather than written into each one.

| Block | Editable on Quote? | Last edited |
| :-- | :-: | :-- |
| **Quote Scope** | Yes | Aug 26, '26 |
| **Proposal** | Yes | Jan 29, '26 |

**A `Proposal` block already exists**, predating this work by seven months. Read it before designing any Proposal template.

**"Editable on Quote?" is the control that decides whether a block is boilerplate or a per-deal surface.** Set to **No**, a block is fixed presentation sales cannot touch or forget to update. Set to **Yes**, it is a drafting surface on every quote. Both existing blocks are Yes; **[Open]** whether that is deliberate.

### 5.2 Mail merge — **[Confirmed]**

The Cover Page and content editors expose **Add Mail Merge**, resolved at render time:

| Group | Variables |
| :-- | :-- |
| Business | `BusinessName` `BusinessAddress` `BusinessCity` `BusinessPostalCode` `BusinessPhone` `BusinessFax` `BusinessWebsite` `BusinessEmail` `BusinessLogo` |
| Customer | `CustomerOrganization` `CustomerTitle` `CustomerFirstName` `CustomerLastName` `CustomerStreetAddress`(`2`) `CustomerCity` `CustomerPostalCode` `CustomerCountry` `CustomerWorkPhone` `CustomerEmail` `CustomerRegionShortName`/`LongName`, plus a full `CustomerShipping*` mirror |
| Quote | `QuoteFormName` `QuoteNumber` `QuoteLink` `QuoteWebViewURL` `QuotePDFURL` `QuoteTotal` `RawQuoteTotal` `QuoteUpfrontTotal` `RawQuoteUpfrontTotal` `QuoteRecurringTotal` `RawQuoteRecurringTotal` `QuoteCreatedDate` `QuoteCreatedDateTime` `QuoteExpiryDate` `RecurrenceIntervalAdjective` `RecurrenceInterval` `UpfrontPayments` `GracePeriod` |
| User | `UserFirstName` `UserLastName` `UserEmail` `Signature` |

There is also an **Insert page break for Quote PDF** control — the mechanism behind Chapter 3 §14.6's "each Introductory Content block starts its own page".

**The limit is precise and worth stating.** Quoter knows the *client*; it does not know the *show*. There is no event name, date or venue variable — those live in the Pipedrive deal title, not in Quoter. So a template can open *"Prepared for {CustomerOrganization}"* but cannot name the event. Anything show-specific belongs in the Scope of Work section.

---

## 6. The Standard cover letter

### 6.1 Why a per-deal letter fails

The risk is that sales treats it as an unnecessary appendage, and the cause is specific. A per-deal cover letter **competes with `SCO-WORK-001` "Scope of Project"** — a $0.00 line whose description the salesperson already rewrites every deal (Chapter 3 §10.7), and the leading candidate to carry the bundled price (§14.3). Ask for a deal-specific narrative in a cover letter as well and sales writes the same story twice, in two editors. The one further from the price loses.

### 6.2 The design

**Static, no fill-in slots, mail-merged for identity only.** Nothing for sales to write, nothing to keep current, and no placeholder that can ship unfilled — the failure class Chapter 3 §12.5 warns about cannot occur, because no human fills anything in.

The adoption mechanism is that **sales does nothing**. It lives in the template and is never edited. Its last line hands off to the Scope of Work section so the two complement rather than duplicate.

Mechanically it is an **Introductory Content block** (Cover Letter being deprecated, §14.6), which starts its own page — correct for a letter.

### 6.3 The copy

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

~180 words, one page.

### 6.4 Provenance of the claims

Every factual claim is drawn from the catalog — the effect list is Chapter 3 §10.2's group list, the itemisation claim is what composition produces. **No credentials were invented:** no years in business, no client names, no productions, no crew size, no certifications, no awards.

**Two require sign-off before it ships:**

1. **"from our base in Los Angeles"** — LA is confirmed; the sentence implies reach beyond it. Deal titles show New York, Miami, Denver, Las Vegas, San Diego and Boise, so the implication appears sound.
2. **"We hold our own inventory and crew it ourselves"** — inferred from the catalog carrying rental items and TLC's own technician lines (`SVC-LSR-TECH`, `SVC-ROB-HDLR`, `SVC-WBT-TECH`). **[Hypothesis]**, not verified. If any of it is subcontracted this sentence must change; it is the paragraph doing the most work and the one a client could hold TLC to.

**[Open]** Whether to add `{CustomerOrganization}` and `{QuoteExpiryDate}` per §5.2. It costs nothing and makes the letter read as addressed.

**[Not built]** The block has not been created. §6.3 is copy awaiting a decision, not a deployed asset.

---

## 7. Acceptance & Payments — **[Confirmed current state]**

### 7.1 Nothing is enabled

The panel's own text:

> "Enable online payments, deposits, or electronic acceptance with Acceptance & Payments. Allow customers to formally agree to purchase the contents of their Quotes according to your terms of sale. To enable online payments during checkout, create a **Payment Gateway**."

> ⚠️ "If you enable electronic acceptance, existing Quotes will not be affected by the change."

**Electronic Acceptance on `Standard`: Disabled.** So no quote surfaces a payment or signature step, and payment terms are handled entirely outside Quoter — on the QBO invoice after publish, which Chapter 3 deliberately scoped out.

### 7.2 Acceptance and payment are separable

**Electronic acceptance works without a gateway.** It is the client formally agreeing to scope and price — a signature. Payment *collection* is the part that needs a gateway. Most of the value may be in the signature alone, with none of the merchant setup.

### 7.3 Payment gateways — the ACH question — **[Confirmed]**

No gateway was configured before 2026-08-29. A **Test Gateway** (Quoter's sandbox type, no processor, no credentials) was created that day while surveying the form.

TLC accepts **ACH only, not credit cards.** Reading the gateway form's fields per type:

| Gateway type | ACH support |
| :-- | :-- |
| **ConnectBooster** | `ENABLE CREDIT CARD PAYMENTS` + `ENABLE E-CHECK (ACH) PAYMENTS` — **independent toggles** |
| **WisePay** | `ALLOW BANK DEBIT` |
| **Benji Pays** | `ALLOW BANK DEBIT` |
| Moneris | both toggles, but Canada only |
| Authorize.net · PayPal · PayPal Pro · **Stripe** · Alternative Payments · FlexPoint · Test Gateway | no ACH field |

**ConnectBooster is the only US option with card and ACH as separate switches**, so it is the only one confirmed able to run ACH-only. **[Untested]** whether WisePay or Benji Pays can fully disable cards.

**Quoter's Stripe integration is card-only**, despite Stripe itself supporting ACH Direct Debit. Worth knowing, because Stripe is the option most people would reach for first.

**[Commercial, not technical]** All three ACH-capable options are MSP payment platforms requiring their own merchant account and contract. Enabling ACH deposits in Quoter is a decision to sign up with a payment provider, not a settings toggle.

### 7.4 **[Not surveyed]** what the panel exposes when enabled

Deposit percentage or fixed amount, terms-of-sale text, signature fields — none read. The Test Gateway makes this safe to survey on a **throwaway copy of Standard**, never on Standard itself.

---

## 8. Archiving templates — **[Confirmed, built and verified 2026-08-29]**

### 8.1 The problem

Field 90 offered eleven item-named templates. Sales should see only presentation choices, not effects — effects are field 102's job. But the ten item-named templates could not simply be deleted: **Quoter has no archive**, deletion is permanent, and they hold roughly 202 curated line items encoding human judgements about what each kind of job needs. Those judgements were never transferred into `item_group_defs.json`, which derives membership from code prefixes instead (Chapter 3 §8.2.1).

**The deciding argument was cost asymmetry, not probability.** ScalePad describes the template-line-item gap as intended (§6.2.1) but describes the related catalog-reference limitation as one that *"will likely be updated at some point"* (§7.12.0). Keeping the templates costs a few lines of code. Deleting them costs days of reconstruction if the capability ever lands. That decides it without needing to estimate the odds.

### 8.2 Why renaming alone does not work — **[Confirmed in source]**

Two mechanisms defeat the obvious approaches:

`build_plan()` treats a renamed template as a label change on the same option id, so `YY-Balloons` in Quoter simply relabels the Pipedrive option — still selectable:

```python
elif current.strip() != rec["label"]:
    to_rename.append((oid, current, rec["label"]))
```

And deleting the option while the template still exists causes it to be **re-added on the next run**:

```python
if oid not in by_id:
    to_add.append(rec)          # mapped option deleted in Pipedrive
```

**So the exclusion has to happen at fetch time.** Nothing short of that keeps an option out of the dropdown.

### 8.3 What was built

`sync_quoter_to_pipedrive.py` gained an archive filter mirroring the auto-append exclusion that already existed for item groups:

```python
ARCHIVE_PREFIX = "YY-"

def is_archived(label):
    return (label or "").upper().startswith(ARCHIVE_PREFIX)
```

applied inside `fetch_quoter()` after the auto-append filter, plus an `--include-archived` diagnostic flag that the scheduled run must never pass.

**[Note]** `fetch_quoter()` is shared by both sources, so the filter applies to **item groups as well as templates**. A group named `YY-*` would drop out of field 102 the same way. Probably desirable; it falls out of where the code sits rather than from a deliberate decision.

### 8.4 Verified sequence

| Step | Result |
| :-- | :-- |
| Patch applied, before renaming | 12 records, 13 options, **ADD 0 / RENAME 0 / ORPHAN 0** — inert |
| Ten renamed `YY-*` in Quoter | 2 records, ten excluded by name, **ORPHAN 10**, RENAME **0** |
| Ten options deleted in Pipedrive UI | — |
| Final verification | 2 records, 2 options, **ADD 0 / ORPHAN 0** |

`RENAME: 0` at step 2 is the load-bearing observation: the sync never attempted to relabel the options `YY-*`, because the templates were filtered out before `build_plan()` saw them.

The leftover `XX-RET-*` option from §11.8 lifecycle testing was deleted at the same time, clearing a Chapter 3 §18 cleanup item. Field 90 went from 13 options to 2.

### 8.5 Un-archiving

Drop the `YY-` prefix in Quoter and the template reappears in the dropdown on the next run.

Because the ten options were **deleted** rather than retired, un-archiving creates **new option ids** via `to_add`. Had they been left retired, `to_unretire` would have restored the original label on the original id automatically:

```python
if is_retired(current):
    to_unretire.append((oid, current, rec))
```

That trade was made deliberately: retired options stay visible at the bottom of the picker, and the requirement was that sales not be able to select them.

**Consequence:** 82 historical deals now store option ids that no longer exist, and show a blank Quote Template. Composition is unaffected — `quote_composer.py` falls back to `DEFAULT_TEMPLATE_ID` (Standard) with a warning. The quotes themselves retain their contents; only the Pipedrive breadcrumb is gone.

### 8.6 Two edge cases

**Same-name recreation silently inherits the old option id.** `retired_by_label` matches on the stripped name, so a brand-new template named `Balloons` would be handed the id historical deals point at. Continuity, or a silent merge of two different templates, depending on intent.

**Archiving `Standard` would not break composition, which is itself the trap.** `DEFAULT_TEMPLATE_ID` is hardcoded to Standard's `tmpl_` id, so the composer would keep using it while it vanished from the dropdown — quotes building on a template nobody can select. Worth a guard.

---

## 9. Prefix conventions

Three two-letter prefixes now exist across two systems. None is self-explanatory, so this table is the key.

| Prefix | System | Means |
| :-- | :-- | :-- |
| `XX-RET-` | Pipedrive option label | **retired** — the Quoter record is gone; the option id is kept so old deals still resolve to a readable label. Written by the sync with `--retire-orphans`. |
| `YY-` | Quoter template (or item group) title | **archived** — kept in Quoter, deliberately hidden from the Pipedrive dropdown. Read by `is_archived()`. |
| `zz-` / `ZZZ-` | Quoter items, quotes, contacts, bundles | **test artifact** — safe to delete. See Chapter 3 §18. |

Also in use, on catalog **codes** rather than record names, per `item_group_defs.json`:

| | |
| :-- | :-- |
| `SCO-` | scope of work |
| `SFX-` | effects |
| `SVC-` | generic services |
| `STE-` | shipping, travel, expenses |

**A `YY-` record is not test data.** Anything sweeping for `zz-` must not also match `YY-`; `zz_artifact_sweep_v1.py` currently does not, and should not be loosened.

---

## 10. Resellers are locked — closes a Chapter 3 open item — **[Confirmed]**

Chapter 3 §18 carried: *"Confirm no Resellers are configured on the Quoter account. The whole Item Group mirror depends on it (§7.8.1)."*

`/admin/resellers/` returns a **locked upsell page**: 🔒 *"Ask your Account Owner to Unlock."* The feature is not merely unconfigured — **it is not available on TLC's plan.**

This does more than satisfy **D-011**'s condition. D-011 warns that repurposing Item Groups as a lookup table *"is valid only while no Resellers are configured… if reseller functionality is ever enabled, every mirror group silently becomes a grant of item visibility."* That risk is now gated behind an explicit account-owner plan unlock — it cannot happen by accident.

**[Recommended]** Record this against D-011 as the confirmation it was waiting for, noting the guarantee is a plan lock rather than an empty configuration.

---

## 11. Catalog coverage — a gap unrelated to templates

Computed 2026-08-29 from the Aug 19 catalog pull against `item_group_defs.json`. **[Note]** the pull is 297 items; the catalog is now 292, so treat the counts as indicative.

**286 real items (excluding 11 `ZZZ-` fixtures): 213 in at least one Item Group, 73 in none.**

The 73 split cleanly:

**Deliberately unquotable (~12).** `HG-FVH-*` Hypervsn, `LED-WBX-*` Xylobands, `LED-LYX-001` Xylo lanyard, and the HTX controller pair. Chapter 3 §10.4's retirement-by-prefix working as designed — retained in the catalog for servicing kit in the field, excluded from groups so they cannot be newly quoted.

**A genuine gap (~22).** The LED display line — walls, tubes, floor, screens, panels, mesh, letters, costumes, signage, sphere — plus `HG-TBL-001` Holographic Table, `HG-SLT-MCH` Holographic Slot Machine and `HG-VRT-STAGE-001` Virtual Stage. Current products in no group, therefore **not quotable through the automated path at all.** `item_group_defs.json`'s own `_unassigned` block already names `SFX-LEDDisplays` as the candidate fix.

Remainder: `EQP-` (9, support kit), `FIN-` (5–6, commercial terms including `FIN-ACH-DOM`), and ~12 single-item prefixes.

**This gap predates and is unaffected by the template archiving.** It is a live hole in phase 3.

---

## 12. Corrections made while writing this chapter

Recorded because each was asserted with more confidence than the evidence supported — the same discipline Chapter 3 §4 applies to itself.

| Claim | Reality |
| :-- | :-- |
| "The Pipedrive dropdown's deal references can't be checked from here" | They can. `getDeals` accepts `include_option_labels`; 1,772 deals scanned in five calls. |
| "Capture the template contents before deleting — `template_mapping_enhanced.py` is a record worth preserving" | Phase-2 reasoning. Item Groups supersede template contents and are *more* complete (§8.2.1). |
| "So there is nothing to capture" | Overcorrected. The templates encode **curation** — cross-family membership judgements — that the prefix-derived groups do not. That is what §8 preserves. |
| "Templates have no archive" | True as far as the UI shows, but an **inference** from View/Edit/Copy/Delete being the only actions. Not tested, and not worth testing by deleting one. |
| "Retiring the options is reversible" | Only the Pipedrive half. Deleting the Quoter template is as final as any other option. |
| "Display settings are per-template or account-wide — untested" | Now **[Confirmed]**: account default with per-template override (§4). |

---

## 13. Not yet surveyed

- **Acceptance & Payments panel with acceptance enabled** (§7.4) — deposit fields, terms-of-sale text, signature options.
- **Cover Page vs Content Blocks vs Appended Content** — three surfaces, no established rule for which content belongs where.
- **The two existing content blocks' actual content** — `Quote Scope` and `Proposal`.
- **Approval Policies and Quote Reminders** — whether either is configured, and whether either fires on API-created drafts.
- **Which display flags are currently set** on the account default and on each template.
- **[Untested, carried from §14.6]** whether content blocks are API-writable or seedable from a template.
- **Whether the 2026-08-29 renames regenerated the template slugs.**

---

## 14. Next steps

**Presentation**

- Decide the display-flag set for Basic and Standard (§4.4).
- Create the Standard cover letter block once §6.4's two sentences are signed off.
- Strip `Basic`'s one remaining line item (Chapter 3 §7.7). `Standard` is already clean.
- Decide whether to rename `Basic`'s slug from `test`.

**Commercial**

- Decide whether payment stays in QBO or moves into Quoter (§7). If it moves, ConnectBooster is the only confirmed ACH-only-capable US option.
- Survey the Acceptance panel on a throwaway copy of Standard, using the existing Test Gateway.
- Decide where the bundled price sits (Chapter 3 §14.3) — the `Scope of Project` line is the leading candidate.
- Decide whether to rename the Summary block to "Notes" (§14.5) — account-wide.

**Housekeeping**

- Delete the **Test Gateway** once the acceptance survey is done.
- Build `SFX-LEDDisplays` and decide the other ~22 orphans (§11).
- Prune options 503/504/505 from `pd_option_map_templates.json` — confirmed stale (§3.2).
- Add a guard against archiving `Standard` while it remains `DEFAULT_TEMPLATE_ID` (§8.6).
- Record the D-011 confirmation (§10).
