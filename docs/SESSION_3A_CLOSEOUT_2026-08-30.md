# Session 3A Close-Out — Webhook Auth and Payload

**Date:** 2026-08-30
**Kickoff:** `docs/KICKOFF_BRIEF_WEBHOOK_AUTH_PAYLOAD_2026-08-30.md`
**Reference:** `docs/CHAPTER_3_QUOTER_SCALEPAD_AS_BUILT_2026-08-30B.md`
**Commit:** `2f9dcdc` — *webhook: accept HTTP Basic Auth, support dual secret during rotation*
**Governing discipline:** verify, don't assume. Claims below are **[Confirmed]** or **[Hypothesis]**.

---

## 1. Job A — done, with one item pending

Webhook authentication now runs on HTTP Basic Auth. `WEBHOOK_SECRET` has been rotated and no longer appears in any URL Pipedrive holds.

### 1.1 What changed in the repo

`_is_authorized(req)` in `webhook_handler.py` (was lines 61–75) now accepts three methods in order of preference: **HTTP Basic Auth**, `X-Webhook-Token`, `?token=`. The last two are retained until step 6.

Four changes beyond adding Basic Auth, each deliberate:

- **`hmac.compare_digest` replaces `==`.** The original leaked timing information.
- **`WEBHOOK_SECRET_PREV`** is honoured alongside `WEBHOOK_SECRET`. Both are accepted while it is set.
- **The auth method is logged at INFO** — `🔑 webhook auth: basic (user=…)`, `header-token`, `query-token`, and `🚫` on rejection. This is the instrument step 6 depends on.
- **Basic Auth returns early on failure.** A caller presenting wrong Basic credentials is rejected rather than falling through to the query token. Consequence seen live: a misconfigured v3 with an old password 401'd even though its URL still carried a token the server would have accepted.

**Fail-open behaviour was preserved, not changed.** When no secret is configured the function still returns `True`. Changing this to fail-closed is a separate two-line edit and a separate decision — see §5.

### 1.2 Why the brief's step 4 was not followed as written

The brief says "callers before Render, or everything 401s in the gap." That holds for a single-secret design but does not close the gap — it moves it. Set the new password in Pipedrive first and Render still validates the old one; rotate Render first and Pipedrive still sends the old one. Either way a deal crossing into *Send Quote/Negotiate* during the window gets a 401 and no quote.

`WEBHOOK_SECRET_PREV` removes the window entirely and makes the order irrelevant. **[Confirmed]** — the rotation was performed Render-first with no interruption.

### 1.3 Pipedrive could not be edited; v4 was created

**[Confirmed]** The webhook manager offers **Review** and **Delete** only. There is no edit affordance on a saved webhook definition. Review shows which automations use it; it exists to explain why Delete is blocked.

So `Ready-Quoter-Draft Quote Creation-v4` was created:

- URL `https://quoter-webhook-server.onrender.com/webhook/pipedrive/organization/` — trailing slash, **no token**
- HTTP Auth username `pipedrive`, password = the rotated secret

Both automations were then repointed: **2C-V1 step 9** first (fires on demand via field 100, so failures are contained), then **2B-V3 step 19**.

This diverges from §19.2's "one edit applied twice" — that held for the *payload*, but the auth change required a new definition and two separate repoints.

### 1.4 Pipedrive's Basic Auth fields work — **[Confirmed, live, 23:37 UTC]**

The one claim in this job that nothing had tested. A field-100 toggle fired 2C-V1 through v4 and produced:

```
🔑 webhook auth: basic (user=pipedrive)
```

No `?token=` on the request. The access log records the username and nothing else — compare the query-token line from the same session, which recorded the full secret.

### 1.5 State after the session

| | |
| :-- | :-- |
| Render `WEBHOOK_SECRET` | rotated, 64 chars |
| Render `WEBHOOK_SECRET_PREV` | **set** — old 43-char value, deliberately retained |
| Pipedrive v4 | live, both automations repointed |
| Pipedrive v3 | now zero automations; delete guard has cleared |
| Pipedrive v2 | untouched; four automations, all inactive (§19.4) |
| `.env` MacBook Air | updated |
| `.env` Mac Mini | **not yet updated** |
| GitHub Actions | not touched, correctly (never calls this endpoint) |

### 1.6 Step 6 — blocked, and should stay blocked

Do not unset `WEBHOOK_SECRET_PREV` or remove the legacy code paths until:

1. **A real deal has fired 2B-V3 through v4.** 2C-V1 is proven; 2B-V3's step-19 edit is not. Recreating the full chain (deal, org, person, QBO customer, QBO sub-customer) for a synthetic test costs more than waiting. If step 19 did not save, v3's `?token=` with the old secret still works via `PREV` — so the deal would succeed and the fault would stay hidden. Remove `PREV` before that and an unsaved edit becomes a failed quote on a live deal.
2. **The Mini's `.env` is updated.** A stale `.env` works today via `PREV` and starts failing the moment it is unset.
3. **The debug endpoints are mapped.** `_is_authorized()` gates four call sites — lines 137 and 750 carry the "require shared secret" comment; **1064 and 1101 do not**. The original comment names "Pipedrive + Quoter (and any debug caller)" as senders, so Pipedrive may not be the only user of the query token. Run `grep -n "@app.route" webhook_handler.py` and confirm what those two are before deleting the path.

The log lines from §1.1 are the evidence: step 6 proceeds when nothing but `basic` has appeared for long enough to cover every caller.

---

## 2. Job B — not started, but the scope is now known

The brief describes Job B as blocked on `_contact_from_webhook()` reading the address from the payload. **That understates it.** A probe tonight established the composer reads **four things** from the payload and none from the API.

### 2.1 The probe

The webhook payload was made to disagree with Pipedrive: `ORG_NAME=zz-CLIENTSRC-PROBE` against org 4343, whose real name is different. The resulting quote's Prepared For panel read:

| Field | Value | Source |
| :-- | :-- | :-- |
| Organization | `zz-CLIENTSRC-PROBE` | **payload** |
| First / Last name | `Unknown` / `Contact` | placeholder — payload had no name key |
| Email | `3094@gmail.com` | placeholder — payload had no email key |
| Address | `Address not provided` | placeholder |

**[Confirmed]** The composer reads the payload, not the API, for all four.

The email finding is the sharper one: **deal 3094's Person has `zz52@gmail.com` in Pipedrive.** A correct address existed and was reachable by API. The composer did not look — it read the payload, found nothing, and invented one. This is not a missing-data problem; it is the composer not asking.

One request answered what the brief had listed as a code-reading exercise. **Instrument before theorising.**

### 2.2 What must move before any key is deleted

| Field | Available from | Status |
| :-- | :-- | :-- |
| org name | `get_organization_by_id()` → `name` | **[Confirmed]** live in tonight's logs |
| address (12 components) | `get_organization_by_id()` | **[Confirmed]** all twelve returned, including `address_country_code` |
| email | the deal's linked Person | **[Hypothesis]** — unverified |
| first / last name | the deal's linked Person | **[Hypothesis]** — unverified |

The handler **already calls `get_organization_by_id()` twice per request**, so the org half needs no new API call — only a repoint.

### 2.3 The one open question

Does `get_deal_by_id()` return `person_id` expanded with name and email, or a bare integer? The automation pulls `{{person.email}}` and `{{deal.person_name}}` from the Person record, not from deal fields, so this is not answerable from the UI.

**[Hypothesis]** A parallel session concluded that `full_deal` carries `person_id` only, so email and phone require a second call:

```
deal_id  →  get_deal_by_id()   →  person_id, org_id, field 90, field 102
         →  get_person(...)    →  email, phone, name
```

That is very likely right, but it was asserted rather than measured, and this project's own §9 lists "asserting a mechanism instead of measuring one" as a recurring failure mode. One read settles it:

```
python3 -c "from pipedrive import get_deal_by_id; import json; d=get_deal_by_id(3094); print(json.dumps(d.get('person_id'), indent=2))"
```

Expanded → Job B is a repoint with no new calls. Bare integer → the hypothesis holds and a person fetch is needed.

**Either way, check whether `pipedrive.py` already has a person getter.** That determines whether Job B is a few lines or a new function:

```
grep -n "def get_person\|def get_.*person" pipedrive.py
```

**Ordering is not a constraint.** The re-fetch is the first thing the v2 branch does, and everything runs inside one request — auth, gate, `get_deal_by_id()`, then `create_quote_v2()` with `ensure_contact()` inside it. So any data the re-fetch obtains is available at the moment the contact needs it. Nothing arrives late. (This single-request shape is also why gunicorn runs a 120s timeout rather than the 30s default.)

### 2.4 The test that makes slimming safe

Because 2C-V1 fires on demand via field 100, it is the only path that can be exercised without building a full deal chain. Order:

1. change `_contact_from_webhook()` to read from the re-fetched deal and the org API
2. deploy
3. fire 2C-V1 **with the fat payload still in place** — the new code should ignore those keys entirely
4. only then slim 2C-V1 step 9, fire again, confirm nothing changed
5. slim 2B-V3 step 19 last

Step 3 is what makes this safe: if the code sources everything from the API, the payload keys are dead weight *before* they are deleted, so deleting them cannot break anything.

Rename the function while it is open. `_contact_from_webhook()` reading the deal is a name that lies.

### 2.5 The right test for each key

Better than "which keys are used," which is an observation about today's code:

> **What does the API need in order to start, before handing off to the composer?**

By that test the payload collapses to:

- `{{deal.id}}` — which deal. Nothing else answers this. Also generates the quote number (`03094-20260830`).
- `{{organization.id}}` — which org. **[Hypothesis]** possibly derivable from the deal fetch.
- HID-QBO-Status — not data but a *signal*: the readiness gate runs before the composer. **[Hypothesis]** could be re-read from the org, reducing the payload to two keys.

Everything else is a copy of something one API call away. This is §13.4's "the webhook answers *when*" taken to its endpoint.

**Why the re-fetch beats widening the payload**, restating §15.2 with tonight's evidence: editing the payload means editing two automations in a UI, and those edits carry hardcoded field hashes (`454a3767…`, `42ab0c91…`) that break silently on a field rename. Editing a fetch means editing code in git. A payload that disagrees with the API is a second source of truth, and its failure mode is quiet.

### 2.6 Job B is optimisation, not repair

**The current webhook works.** In production the payload carries the correct values, so quotes come out right. What Job B retires is not a present fault but a latent one: a field rename or automation edit could make the payload wrong without anything failing loudly.

Against that, it is a real code change touching four fields on a path with no staging environment. Waiting for the 2B-V3 confirmation before touching the composer is the conservative order.

---

## 3. Quoter Client creation — settled

**[Confirmed, live tonight]** A Quoter Client existed for a quote created by API that no human had touched. This reproduces §3.3's August observation on a fresh quote.

The hypothesis under test — that the Client is minted when the human backspaces over the name and links the Pipedrive Org — is **wrong**. Two different objects:

| | |
| :-- | :-- |
| **Client** | name-based billing entity, minted from `billing_organization` at contact creation, exists before the draft is opened |
| **Person / Deal link** | hard reference to specific Pipedrive record ids, only after the human confirms, **not settable by API** (§4.4) |

What looks like Client creation during the backspace is the **Pipedrive lookup** — the three-source selector of §3.2, TLC's default source being Pipedrive, querying Pipedrive live. The Client with that name was already in Quoter. The give-away is that the Deal dropdown only appears *after* the Person is confirmed, because it is scoped to that Person's org; Client creation has no such sequencing.

**Consequence for Job B:** the human step is a safety net for the *link*, not for the *Client name*. A wrong or empty org name mints a Client that persists whether or not the human later links correctly — and per §3.4 those accumulate.

### 3.1 `client_name` is unvalidated — **[Confirmed, live tonight]**

The probe passed `zz-CLIENTSRC-PROBE`, a string with no corresponding Pipedrive organization. Quoter accepted it and minted a Client. There is no validation against Pipedrive, or against anything else.

§3.3 said the mapping was "direct and deterministic"; watching it accept an invented name makes the consequence concrete. **A typo in the org name creates a new Client rather than failing.** Combined with §3.4's per-deal org naming, that is a path to Client proliferation that nothing would flag.

It also means the composer is the only guard. Whatever string it passes becomes a billing entity, permanently.

---

## 4. Required fields, and where discipline belongs

Quoter locks four as Mandatory and they govern the API, not just the UI (§12.4): **First Name, Last Name, Email, Country.** TLC additionally requires Organization.

**Organization needs no enforcement rule.** The sub-org is created by automation 2A/2B, not by a human, and Organization is required to reach the quote stage. It is therefore **guaranteed by the provisioning architecture** rather than by a validation. This is stronger than §12.4's framing of it as a rule to implement, and it means no placeholder for org name is ever justified.

**Person email is the field that actually needs discipline.** It is human-entered on the Person record; nothing creates it. Tonight's probe shows exactly what happens when it is absent from the payload — a fabricated mailbox on a live quote, with the API never complaining because the placeholders are shaped to satisfy the four mandatory fields.

**Sequencing:** the Pipedrive rule must land *before* the placeholder chain is removed. Remove placeholders first and a deal with a missing email fails at the webhook, which is the failure mode the whole "enforce in Pipedrive" argument exists to avoid.

---

## 5. Open decisions

**Fail-open vs fail-closed.** `_is_authorized()` returns `True` when no secret is configured. The stated reason — "so existing deployments keep working until the secret is configured on both senders" — has expired. It gates debug endpoints as well as the webhook, and its failure mode is silent: a typo'd env var name in Render does not break anything visibly, it opens the endpoint. Recommend fail-closed, as its own commit so a 401 during testing has one cause rather than two.

**Delete v3.** Zero automations now, so the guard has cleared. Deleting it removes the last Pipedrive-held copy of the `?token=` URL, though the secret in it is already dead.

**Canonical Client name (§3.5 Option 3).** Since `_contact_from_webhook()` is being opened anyway, the org-name source is where a deal-independent company name would be resolved. A deliberate decision, not blocked on ScalePad. Out of scope for Job B but adjacent to it.

**Unread ScalePad reply.** Neil, 2026-08-27, thread "Quote rendering questions — section subtotals, Summary block, content blocks." Bears on the §14.3 open item about where the bundled price sits.

---

## 6. Cleanup — for Chapter 3 §21 Data cleanup

**Quotes on deal 3101** (org 4351), from auth testing. `processed_organizations.txt` does not survive a deploy (§16.2), so the `already_processed` guard was empty after each restart and did not prevent these:

- `quot_3IehezOEMBMXZu2Z6emy51JKyVG` — 23:04 UTC, curl, 3 sections / 10 line items
- one further quote from the 23:37 UTC fire through 2C-V1

**Quote on deal 3094** (org 4343), from the client-source probe:

- `quot_3IepnbH4HxioZe9BBB2E7ro1jhS`

**Quoter Client** `zz-CLIENTSRC-PROBE` — minted by the probe. Persists independently of the quote; see §3 above.

**Quoter Contact** `3094@gmail.com` — fabricated by the placeholder chain. A mailbox a quote could be sent to.

---

## 7. Repo housekeeping

- `backups/` and `*.bak` added to `.gitignore`. Backups live in `backups/` inside the repo, machine-local.
- `patch_is_authorized.py` — the one-time anchor-based patch script, moved to `backups/`, deliberately not committed. `git revert 2f9dcdc` is the better undo and works from either machine.
- `test_render_webhook.sh` updated: Basic Auth modes (`basic`, `query`, `header`), an `authcheck` matrix asserting 401 vs not-401 across six cases, and the stale `USE_V2_COMPOSITION` advice removed (§18.2). The payload fixture is unchanged from the original. Executable bit restored — it had been lost in transit.
- **The fixture is thin.** Five keys, no email, no name, no address. It therefore exercises the placeholder path rather than the real one. Add `{{person.email}}` and `{{deal.person_name}}` before testing Job B, or the test will pass against placeholders and prove nothing.
