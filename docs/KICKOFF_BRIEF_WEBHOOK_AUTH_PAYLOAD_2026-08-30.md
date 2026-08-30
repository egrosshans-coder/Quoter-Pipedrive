# Kickoff Brief — Webhook Auth and Payload

**Date:** 2026-08-30
**Predecessor:** "Quoter Item Group Build from Template", Aug 19–30 2026
**Canonical reference:** `docs/CHAPTER_3_QUOTER_SCALEPAD_AS_BUILT_2026-08-30B.md` — **revision B**, which supersedes the earlier 2026-08-30 file. Read it first; Chapter 3 wins on any conflict. **Do not load older Chapter 3 versions**; several contain claims later versions retract.
**Governing discipline:** Verify, don't assume. Tag every claim **[Confirmed]** or **[Hypothesis]**.

---

## 1. Scope of this session

Two related jobs on the Pipedrive → Render webhook. **Do them in this order** — the second depends on a code change the first does not need.

**A. Move authentication to HTTP Basic and rotate `WEBHOOK_SECRET`.** Self-contained, ~20 minutes, removes a live exposure.

**B. Slim the payload from 17 keys to 4.** Blocked on `_contact_from_webhook()` in `quote_composer.py`, which must read from the re-fetched deal before any Pipedrive key is deleted.

Everything else is out of scope. The composition path works and is in production; do not refactor it.

---

## 2. Where things stand

**Production is healthy.** A deal reaching *Send Quote/Negotiate* produces a composed quote — Scope of Work, the selected effects, then shipping and travel — with Slack, email and a Pipedrive note firing. Running on gunicorn, two workers, 120s timeout.

**The legacy path is gone** as of 2026-08-30. 859 lines removed from `quoter.py`; `template_mapping_enhanced.py`, `verify_bundles.py` and `create_draft_quote.py` archived; `USE_V2_COMPOSITION` removed from Render. **There is one path and no flag** (§18).

**A human still finishes each quote:** links it to Pipedrive (§4, manual by design), prunes lines, writes the scope narrative, prices it.

---

## 3. Job A — authentication

### The problem

`WEBHOOK_SECRET` travels as `?token=` in the URL, so it lands in **every access log**. It was also echoed in a log line pasted during testing, so it needs rotating regardless of anything else.

### Why the obvious fix does not work

`_is_authorized()` already accepts an `X-Webhook-Token` header as well as the query param. That looked like the answer. **It is not: Pipedrive's automated webhooks do not support custom headers.**

They support **HTTP Basic Auth** — username and password fields on the webhook definition itself — which travels in the `Authorization` header and never appears in a URL. Flask exposes it as `request.authorization`. The handler does not support it yet.

### Steps, in order

1. add Basic Auth to `_is_authorized()`, **keeping** the existing methods so nothing breaks mid-change
2. deploy and confirm the service starts
3. set username and password on the **v3** webhook definition in Pipedrive, and strip `?token=` from its URL
4. rotate `WEBHOOK_SECRET` — Render, plus `.env` on both machines
5. test with `./test_render_webhook.sh` (which will need updating to send Basic Auth)
6. remove the query-token path once nothing uses it

**Callers before Render**, or everything 401s in the gap. GitHub Actions is unaffected — the dropdown sync talks to Quoter and Pipedrive directly, never to this endpoint.

**One webhook definition covers both automations** (§19.2), so step 3 is a single edit.

---

## 4. Job B — the payload

### What is sent today

Both `2B-V3` (step 19) and `2C-V1` (step 9) send an **identical 17 keys** to the same webhook. `2C-V1` is a clone of `2B-V3` with the earlier steps deleted, verified field by field (§19.2).

```
{{organization.id}}                  Org-ID
{{organization.454a3767...}}         HID-QBO-Status
{{organization.name}}                Organization name
{{deal.42ab0c91...}}                 Quote Template        <- field 90 only
{{deal.title}} · {{deal.id}}
{{deal.person_name}} · {{person.email}}
7 x organization.address_*
{{person.phones}}
{{organization.6b425330...}}         Parent Organization - ID
```

**Field 102 (Quote Effects) is absent**, which is why the v2 branch re-fetches the deal (§15.2).

### What is actually used

Four: `{{deal.id}}` to re-fetch · `{{organization.name}}` for `client_name` · `{{person.email}}` for the contact · and the handler's readiness gate needs `{{organization.id}}` plus HID-QBO-Status.

The other twelve feed `_contact_from_webhook()` for address, and `{{person.phones}}` is **not passed through at all**.

### The order that matters

**`_contact_from_webhook()` reads name, email and address from the payload, not from the re-fetched deal.** Change that first. Delete the Pipedrive keys first and contact resolution breaks — no name, no email, no address, and `billing_address` is required to create a contact (§12.2).

So: change the code, deploy, test, *then* slim both automations.

### Why bother

Those keys hardcode field hashes like `454a3767...` that break silently if a field is renamed. And a payload that disagrees with the API is a second source of truth about a deal.

---

## 5. Six things that will bite

**5.1 Create the contact before the quote.** `createQuote` *resolves* a contact by email; it does not create one (§12.1). `billing_address` is a **nested object**, and there are no flat address fields (§12.2).

**5.2 Read the write schema off a real record.** It mirrors the read schema every time. **A 422 is about the body's CONTENTS, a 400 about its SHAPE.**

**5.3 Section reads are eventually consistent.** An id read straight after a write can 404, on multi-section quotes only. `add_line_items_retrying()` handles it and the 404 logs at WARNING (§16.3). Do not substitute a longer sleep.

**5.4 A webhook 200 does not mean a quote was created.** `not_ready_for_quotes` and `already_processed` both return 200 with a reason. `processed_organizations.txt` also **does not survive a deploy** (§16.2).

**5.5 `render.yaml` is inert.** The start command that runs is in **Render → Settings**. Render uses Python 3.13.4 while the file declares 3.14.6 (§18.4).

**5.6 `test_render_webhook.sh` gives stale advice** — it tells you to check the logs for `USE_V2_COMPOSITION=true`, a flag that no longer exists. Fix it while you are in there.

---

## 6. Two-machine discipline — read this before committing

**Three deploys failed in a row on 2026-08-29** because a commit removed `gunicorn==23.0.0` from `requirements.txt`. Nobody meant to.

**`sync.sh` runs `git add -A` and commits whatever is on disk. Git cannot distinguish a deliberate revert from a stale file.** An older `requirements.txt` from the Air was committed over the Mini's newer one and looked like an intentional edit.

The likely mechanism was an **`rclone copy` from Drive into the repo** — Drive's copies were two days old, and rclone preserves mtime.

**So: never `rclone copy` into a Git working directory.** Pull to a scratch folder and move deliberately. And run `git status` after any rclone operation, before `sync.sh`.

`./retrieve.sh` before `./sync.sh`, always.

---

## 7. Reference

**Prefixes, three systems, three meanings:**

| | | |
| :-- | :-- | :-- |
| `XX-RET-` | Pipedrive option | retired, id kept so old deals resolve |
| `YY-` | Quoter template | archived, hidden from the sync |
| `zz-` / `ZZZ-` | Quoter items, quotes | test artifact, safe to delete |

**Group naming:** `SCO-` scope · `SFX-` effects · `SVC-` generic services · `STE-` shipping/travel/expenses.

**Field 90** Quote Template `enum` — presentation. Key `42ab0c919271cb24f3587f0b01ea2af166019c8d`
**Field 102** Quote Effects `set` — content. Key `118a5ce132f73d7fec1822e2a0431b51ac2a2994`
**Field 100** `Run 2C Manual SubCust Repair` — triggers the repair automation

**Catalog:** ~292 items. `code` is the unique part number — **resolve by `filter[code]=eq:`**. `sku` holds the Pipedrive product id.

**Line item descriptions DO render; catalog item descriptions do not** (§14.1).

---

## 8. Repo

`github.com/egrosshans-coder/Quoter-Pipedrive`, cloned as `quoter_sync` on Mac Mini and MacBook Air. **Markdown goes to `docs/`. Code to the repo root.**

| File | |
| :-- | :-- |
| `webhook_handler.py` | Flask entry point, `_is_authorized()` — **Job A lives here** |
| `quote_composer.py` | the quote path, `_contact_from_webhook()` — **Job B lives here** |
| `scalepad_quotes.py` | quotes, sections, line items, contacts, retries |
| `scalepad_items.py` | **`iter_all_items()` already does the catalog pull** |
| `quoter.py` | now OAuth, contacts and helpers only |
| `test_render_webhook.sh` | fires the deployed webhook — needs updating for Basic Auth |

**Three separate secret stores that do not see each other:** local `.env` on two machines, the Render dashboard, GitHub Actions secrets. Rotating `WEBHOOK_SECRET` touches the first two plus Pipedrive; **not** GitHub.

`docs/DECISIONS.md` governs where code goes: D-003/D-004 transport and resource wrappers separate from business logic; D-006 verify endpoints before wrapping.

---

## 9. Working notes

**Present files under their final names.** Repeated `_v2`/`_v3` suffixes cost several manual renames.

**No trailing `#` comments on shell commands** — this zsh parses them as arguments.

**Four failure modes recurred over the week.** All cheap to avoid, expensive to repeat.

**Asserting a mechanism instead of measuring one.** Three theories about a section 404 before a diagnostic answered it in one pass. **Instrument before theorising.**

**Guessing a write schema instead of reading one.** The contact schema took three failed attempts before anyone ran `GET /contacts`. **One read replaces three round trips.**

**Documenting a flaw instead of fixing it.** The local-cron scheduling was known fragile the day it was built, went into a comment and a "known gap", then silently never ran. **A note is not a mitigation.**

**Planning around what a function returns without reading its call site.** Two items in a handoff document rested on the assumption that legacy wrote cover-letter content. Ten seconds reading `quoter.py:1769` showed the write commented out — closing one item and reframing the other.
