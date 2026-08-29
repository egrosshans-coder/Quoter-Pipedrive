# TLC Quote-to-Pipeline — As-Built
## Section 2 — Pipedrive Provisioning Automation

**Organization Level · 2A · 2B · 2C**

TLC Creative (Special Effects, Los Angeles) · Author: Eric Grosshans

_Sources: 2A-V2 & 2B-V3 automation screenshots + design brief; live Pipedrive / SyncQ / QuickBooks inspection; Render deploy logs._

---

## At a Glance

**What this section documents:** the Pipedrive automations that provision organizations/customers at the Organization level — the 2A mothership (parent) → 2B child chain, and the status of the proposed 2C geocode step.

| # | Type | Action / Configuration |
|---|---|---|
| **2A** | Built | Create QBO-Parent Cust / PD-Parent Org (2A-V2). Live. Carries an If/Else canary at step 10. |
| **2B** | Built | Create Org(Deal) / QBO SubCust / Deal Update (2B-V3). Two If/Else gates (parent gate, child gate), both with canary branches. |
| **2C** | Exists, INACTIVE | "2C-V3 Run Webhook with Update Geocode Addresses" — the geocode path, disabled. Dormant because Pipedrive geocodes addresses natively at entry. See §5. |

**Bottom line:** The Organization level is closed. 2A and 2B are the whole provisioning chain; 2C exists but is inactive. The Quoter/Render service now has a split OK/alerts Slack signal and a shared-secret gate (`WEBHOOK_SECRET`) — see §12–§15. A live 2B stall investigated 7/27–8/27 traced to **two distinct failure modes** — legacy motherships not linked in SyncQ (Mode A) and an early-checking gate timing race (Mode B) — see §16. Remaining work is discipline and hardening, not new logic.

---

## 1. Scope & Shared Spine

The whole pipeline runs on one shared spine. This section is bound by it:

- **Entry vs. record:** Quoter is the entry point; QuickBooks Online (QBO) is the system of record.
- **Products:** flow one-way QBO → Pipedrive. Pipedrive Products are dormant.
- **Customer / org sync:** bi-directional but Pipedrive-initiated. The automation stamps Org (and later Sub-org) fields → that triggers SyncQ → SyncQ creates the QBO customer / sub-customer → QBO IDs are written back into Pipedrive custom fields.
- **Universal key:** the deal number.
- **Projects:** QBO sub-customers — a parent "mothership" and a child "Client-####". Provisioning builds the parent first, then the child.
- **Stack:** Pipedrive, QBO, Quoter/ScalePad, SyncQ, Render.

---

## 2. The Provisioning Mechanism (SyncQ Round-Trip)

These automations do not create the QBO customer directly. They initiate a round-trip and wait for it:

- **Stamp the trigger fields** on the org (Sub-org for the child), most importantly flipping `SyncQ: Sync to QuickBooks` to **Yes**.
- **SyncQ fires** and creates the QBO customer, then the sub-customer.
- **SyncQ writes back** the result into `QuickBooks Id: SyncQ` (the QBO ID) and `HID-QBO-Status` (the state).

So the automation's job is exactly: _"set the trigger fields, then wait for SyncQ to return the ID."_

**Terminal `HID-QBO-Status` values:** parent → **QBO-Cust**; child → **QBO-SubCust (289)**. The intermediate stamp on both is **QBO-Cust-Ready** ("trigger fields set, awaiting SyncQ").

---

## 3. Automation 2A — Create QBO-Parent Cust / PD-Parent Org (2A-V2)

**Purpose:** build the parent (mothership) QBO customer and PD parent organization.

| # | Type | Action / Configuration |
|---|---|---|
| 1 | Trigger | Deal updated — watched field: Deal stage. |
| 2 | Instant condition | Deal stage has changed to "Send Quote/Negotiate…" |
| 3 | Action | Update organization fields — Organization = Deal organization; Name = Deal organization name. |
| 4 | Instant condition | `QuickBooks Id: SyncQ is empty` (guard: only provision if not already synced). |
| 5 | Action | Update org fields — `SyncQ:Sync = No`; `HID-QBO-Status = QBO-Cust-Ready`; `Parent Organization = Organization`; `Parent_Org_ID = Organization ID`; `QuickBooks Company:SyncQ = TLC_Creative_Special_Effects_Inc`; `Org_ID = Organization ID`. |
| 6 | Delay | 1 minute. |
| 7 | Action | Update org fields — `SyncQ:Sync = Yes` (this flip is what fires SyncQ). |
| 8 | Action | Update org fields — `Company Revenue = "Verify Reset 2A"` (marker). |
| 9 | Delay | 1 minute. |
| 10 | If/Else gate | `QuickBooks Id: SyncQ is not empty` — "has SyncQ returned the parent ID?" |
| 13 | Met → Action | Update org fields — `HID-QBO-Status = QBO-Cust` (parent terminal state). |
| 14 | Met → Action | Add note — "Automation executed successfully. Parent Org Name / ID / Org ID." |
| 11 | Not met → Action | **CANARY:** Slack → `#d-pipedrive-automation-alerts` — "HALTED at step 10 — org not ready after delay." |
| 12 | Not met → Action | **CANARY:** email → eric@tlc.tech, myles@tlc.tech. |

Note the reference pattern: 2A sets `Sync = No` at step 5, settles, then flips `Sync = Yes` at step 7 — a **change** event. That "stamp → settle → enable" ordering matters (see §5).

---

## 4. Automation 2B — Create Org(Deal) / QBO SubCust / Deal Update (2B-V3)

**Purpose:** once the parent is confirmed in QBO, build the child org + QBO sub-customer, stamp the deal, and hand off to Quoter.

| # | Type | Action / Configuration |
|---|---|---|
| 1 | Trigger | Deal updated — watched field: Deal stage. |
| 2 | Instant condition | Deal stage has changed to "Send Quote/Negotiate…" |
| 3 | Delay | 3 minutes (give 2A / SyncQ time to return the parent ID). |
| 4 | Action | Update org fields — Organization = Deal organization; Name; `Company Revenue = "Verify-2B"`. |
| 5 | If/Else gate (PARENT) | `QuickBooks Id: SyncQ is not empty AND HID-QBO-Status is QBO-Cust` — the parent-completion gate. |
| 6 | Not met → Action | **CANARY:** Slack → `#d-pipedrive-automation-alerts` — "HALTED at step 5 — parent not ready." |
| 7 | Not met → Action | **CANARY:** email — "mothership not ready; sub-customer NOT created; Quoter draft NOT triggered." |
| 8 | Met → Action | Create organization (the child) — Name = Organization name + Deal; Address; Deal_ID; `SyncQ:Sync = Yes`; Parent Organization / Parent_Org_ID; `QuickBooks Company:SyncQ = TLC_Creative_Special_Effects_Inc`; plus company profile fields. |
| 9 | Action | Update person fields — link Deal contact person to the new Organization. |
| 10 | Action | Update org fields — `HID-QBO-Status = QBO-Cust-Ready`; `Org_ID = Organization`. |
| 11 | Delay | 1 minute. |
| 12 | If/Else gate (CHILD) | `QuickBooks Id: SyncQ is not empty` — "has SyncQ returned the child sub-customer ID?" |
| 15 | Met → Action | Update org fields — `HID-QBO-Status = QBO-SubCust`. |
| 16 | Met → Action | Update deal fields — QBO-SubCust-ID; QBO-Cust-ID; Org-ID; Parent Org-ID; Parent organization; Organization name; `EXP-Create Reports = Yes`. |
| 17 | Met → Action | Send webhook (POST) — "Ready-Quoter-Draft Quote Creation" (now tokenized v3). Payload carries org + parsed address components, deal, person, Parent Org ID. |
| 18 | Met → Action | Add note — "Organization Creation Successful!" |
| 19 | Met → Action | Slack SUCCESS → `#d-pipedrive-automation-ok` (provisioning complete). |
| 13 | Not met → Action | **CANARY:** Slack → `#d-pipedrive-automation-alerts` — "HALTED at step 12 — child org not ready." |
| 14 | Not met → Action | **CANARY:** email — "sub-customer status incomplete; Quoter draft NOT triggered." |

> **Live node numbers (reconciliation).** The step numbers above follow the original build screenshots; the current live 2B-V3 has since been restructured and renumbered. As of the 2026-08-19 run the child-gate cluster is: **node 12 = Delay** → **node 13 = Update org (HID = QBO-Cust-Ready)** → **node 14 = If/Else gate** (`QuickBooks Id: SyncQ is not empty`) → **node 15 = not-met canary** → **node 17 = met (HID = QBO-SubCust)**. Two changes: the QBO-Cust-Ready stamp now sits **after** the delay (node 13), and the child gate referred to throughout is **live node 14** (was step 12 in the screenshots).

---

## 5. Automation 2C — Update Geocode Addresses (exists, INACTIVE)

**Corrected status:** 2C does exist — as "2C-V3 Run Webhook with Update Geocode Addresses" — but it is currently **INACTIVE**. Confirmed via Pipedrive's Automated Webhooks manager: it is one of five automations that reference the shared "Ready-Quoter-Draft Quote Creation" webhook. (An earlier note said "2C does not exist"; that was wrong.)

**What it does:** fires the same webhook with a geocode-address update — the geocode path, currently switched off.

**Why it can stay dormant:** Pipedrive's native organization Address field is Google-geocoded at entry. When an address is set through Google autocomplete, Pipedrive stores the parsed subcomponents (street_number, route, subpremise, locality, admin_area_level, postal_code, country) — exactly the tokens 2B's step-17 webhook already reads. So the geocoding has already happened before any downstream step runs.

**Before or after SyncQ's first push?** Before. The parsed components exist by the time step 8 creates the child with `Sync = Yes`, so SyncQ's first push carries a clean structured address and `BillAddr.*` lands clean — no race, no corrective re-sync.

**When 2C earns reactivation:** if addresses arrive as free text (unparsed WPForms) rather than via Google autocomplete, the subcomponents are blank and `BillAddr.*` would push dirty. If reactivated, it must run **in-chain before `Sync = Yes`** (mirroring 2A's stamp → settle → enable), NOT standalone on address-change — a standalone geocode would race SyncQ. Because it uses the same webhook, reactivating it means pointing at the tokenized v3 webhook (see §13) or its calls 401 once `WEBHOOK_SECRET` is enforced.

---

## 6. The Canary — Silent-Quit Fix

**Problem fixed:** Pipedrive's native If/Else has an explicit "Condition not met" path. Left empty, that branch dead-ends and the automation silently quits with no signal. The canary is a notify action on the not-met branch so a stall is loud instead of silent. 2A (step 10) and 2B (steps 5 and 12/live-14) carry canary branches (Slack + email).

**Message = locator + cause.**

- Pretext (locator spine): `🚨 STALL 2B: Deal [11] · Org [6] · #[8] Org_ID · QBO-[10] QuickBooks Id:SyncQ`
- On a real stall the `QBO-` token renders blank — **that blank is the diagnosis** (SyncQ never returned the ID).
- Body (one line): what halted + `HID-QBO-Status` + "check 2A / mothership."

**Scope discipline:** narrow the not-met branch to the real stall case so the canary doesn't cry wolf on benign re-evaluations. Gate meanings: 2A step 10 = parent ID returned? · 2B step 5 = parent complete? · 2B child gate (live node 14) = child sub-customer ID returned?

---

## 7. Channel Convention (locked)

Paired taxonomy: each domain has a failure channel (-alerts) and a success channel (-ok). -alerts is failures-only (silence = healthy); -ok carries the positive confirmation.

- **`#d-pipedrive-automation-alerts`** (FAIL) — Pipedrive provisioning failures; the 2A/2B canaries fire here.
- **`#d-pipedrive-automation-ok`** (OK) — Pipedrive provisioning success (org / QBO customer created).
- **`#d-quoter-render-alerts`** (FAIL) — Quoter / Render failures; `webhook_handler`'s failure branches post here via `SLACK_ALERT_WEBHOOK_URL`.
- **`#d-quoter-render-ok`** (OK) — Quoter / Render success; the draft-created notification posts here via `SLACK_WEBHOOK_URL`.

Route by outcome, never post success into an -alerts channel. A customer-visible "quote ready" signal belongs on a Pipedrive deal notification in sales's workflow — the -ok channels are ops heartbeats.

---

## 8. Versioning & Swap Discipline

- **Current working build:** 2B-V3 is the live automation and carries the If/Else canary. Built by copying the proven prior version (2B-V2, stage-only trigger) and adding the canary branch.
- **One change per version:** only the If/Else canary branch differs from the proven prior version.
- **One armed at a time:** a new copy is tested with the original off, then swapped in.
- Version number must track recency — highest number is newest, only one live.
- **Housekeeping:** a dead Feb "2B-V3" also exists. Delete it so only the working V3 remains. (No "V4" is involved.)

---

## 9. Settled Decisions (recorded)

- `SyncQ: Sync = Yes` stays.
- `QBO → PD auto-sync = 0` is intentional.
- No compound trigger.
- No fan-in for one-shot provisioning.
- Triggers are change-only.
- **HID-QBO-Status terminal values:** parent → QBO-Cust; child → QBO-SubCust (289).

---

## 10. Integration Points

- **← §1 (org authority):** which system is the org record of truth is decided in Section 1; this section assumes QBO as record, Pipedrive-initiated.
- **→ 2A / mothership:** the canary's "parent not ready" message points back here.
- **→ §6 (writeback):** the post-publish writeback that stamps org fields is documented in Section 6.
- **→ Quoter / Render service:** 2B step-17 webhook (now the tokenized "Ready-Quoter-Draft Quote Creation-v3") is the handoff out of provisioning into the Render webhook service — see §12–§14.

---

## 11. Open Items & Flags

Inconsistencies found while mapping the screenshots against the brief. None block the chain; all are cleanup:

> **⚠ Duplicate 2B-V3 name (working build vs. dead Feb build).** Two automations are named "2B-V3": the working build (canary live) and a dead Feb build. Delete the dead one so only the working V3 remains.

> **⚠ 2A email subject says "STALL 2B".** The step-12 email inside Automation 2A carries the subject "🚨 STALL 2B — …". It should read 2A. Copy-paste carryover.

> **⚠ "3-minute delay" wording vs. actual delays.** See §16 — with the child-gate delay now raised to 3 minutes, node 15's "3-min delay" text is finally accurate; verify 2A's wording similarly.

> **Resolved — success post rerouted.** 2B step 19 previously posted success to a failure channel; it now routes to `#d-pipedrive-automation-ok`, and the field was relabeled QBO Sub-Cust ID.

> **⚠ Gate asymmetry between 2A and 2B.** 2A's parent gate (step 10) checks only "QuickBooks Id: SyncQ is not empty," while 2B's parent gate (step 5) checks "SyncQ not empty AND HID-QBO-Status = QBO-Cust." Consider aligning 2A to also require QBO-Cust.

---

## 12. Render Webhook Service — Quoter Draft Creation

The middleware that turns 2B's step-17 handoff into an actual Quoter draft.

- **Host / endpoint:** Render web service `quoter-webhook-server` at `https://quoter-webhook-server.onrender.com`, path `/webhook/pipedrive/organization/`. Entry point `webhook_handler.py` (Flask).
- **Flow:** 2B step-17 webhook POSTs the org/deal/address payload → handler guards (ignore empty_data; require `HID-QBO-Status = QBO-SubCust/289`; skip already-processed) → `create_comprehensive_quote_from_pipedrive` builds the Quoter draft → on success, `send_quote_created_notification` (Slack OK + email + Pipedrive note); on failure, `send_slack_alert` (render-side canary).
- **Notification wiring (`notification.py`):** `send_slack_notification` defaults to `SLACK_WEBHOOK_URL` → `#d-quoter-render-ok`; `send_slack_alert` uses `SLACK_ALERT_WEBHOOK_URL` → `#d-quoter-render-alerts`. The failure branches in `webhook_handler.py` call `send_slack_alert` with a "🚨 STALL Quoter/Render: Deal · Org · cause" locator.
- **Slack webhook constraint:** a Slack Incoming Webhook posts to exactly one channel, so OK vs. alerts requires two separate URLs (two env vars). The channel field in code is cosmetic — Slack ignores it.
- **Second inbound handler:** a Quoter-publish webhook endpoint also exists (updates Pipedrive when a quote is published) and is guarded by the same secret gate.

---

## 13. Inbound Authentication — WEBHOOK_SECRET Shared-Secret Gate

The endpoint is public, so a shared-secret gate protects it (`webhook_handler.py`, `_is_authorized`).

- **Mechanism:** callers send the secret as an `X-Webhook-Token` header OR a `?token=` query param. Fail-OPEN when `WEBHOOK_SECRET` is unset; fail-CLOSED once set. Read at startup, so setting it requires a restart/redeploy.
- **Rollout order (matters):** add the token to every sender FIRST, then set `WEBHOOK_SECRET` in Render — otherwise live provisioning 401s the moment the secret exists.
- **Pipedrive senders are immutable:** automated webhooks can't be edited, so a NEW webhook "Ready-Quoter-Draft Quote Creation-v3" was created with the URL `…/organization/?token=<secret>&` (Pipedrive requires the URL to end in `/ & ? =`, hence the trailing `&`), and 2B-V3 step 17 was repointed to it. The four inactive automations still on the v2 webhook must be swapped if reactivated.
- **Verified:** POST without token → 401; POST with token → 200.
- **Secret hygiene:** the value lives only in Render env vars and local `.env` (gitignored) — never committed. Local and prod secrets may differ (safer). `.env.example` documents the key names only.
- **Still to do:** add `?token=` to the Quoter-publish webhook (second inbound handler) so it doesn't 401 once the secret is enforced.

---

## 14. Deployment & Environment (Render)

> **⚠ `render.yaml` is IGNORED — service is dashboard-managed.** Prod runs Python 3.13.4 (confirmed via response headers and cp313 wheels) despite `render.yaml` pinning 3.14.6. This service was created manually, so it does NOT read `render.yaml`. Consequence: `PYTHON_VERSION` and all env vars (including `SLACK_ALERT_WEBHOOK_URL` and `WEBHOOK_SECRET`) must be set in the dashboard Environment tab, not the yaml. Treat `render.yaml` as documentation only for this service.

- **Auto-Deploy was OFF:** this was why pushes weren't deploying. Now set to On Commit, so `sync.sh` pushes deploy automatically. Env-var changes also auto-trigger a redeploy.
- **Local ↔ prod Python mismatch:** local venv is 3.14.6, prod is 3.13.4. Not urgent, but for parity set dashboard `PYTHON_VERSION` or build the local venv on 3.13.
- **Runtime server:** running Flask's built-in (Werkzeug) dev server — fine at current volume; gunicorn is the eventual production-hardening step.
- **Repo hygiene (done):** `.gitignore` now excludes `*_old.py`, `local_backup/`, `files.zip`, `*.zip`; `*_old.py` archived to `archive/obsolete_scripts/`; root `test_*.py` consolidated into `test_files/`; `files.zip` and `files/` removed; `venv_py39_backup` deleted.

---

## 15. Session Changelog — 2026-07-21

- **Slack OK/alerts split:** added `send_slack_alert` + failure-branch canaries in `webhook_handler.py`; renamed `#d-quoter-alerts` → `#d-quoter-render-ok` and created `#d-quoter-render-alerts` (+ its Incoming Webhook).
- **Inbound auth turned on:** `WEBHOOK_SECRET` set in Render; created tokenized webhook v3 and repointed 2B-V3 step 17. Verified 401/200.
- **Deploy fixed:** Auto-Deploy was off → enabled; discovered `render.yaml` is ignored and prod runs Python 3.13.4.
- **Repo cleanup + docs:** gitignore/backups/tests tidied; `.env.example` documents the Slack vars.
- **2C corrected:** exists but inactive.
- **Deferred (not blocking):** enrich the OK message with build data (quote #, total, deep link); align local↔prod Python; move to gunicorn; add `?token=` to the Quoter-publish webhook.

---

## 16. SyncQ Round-Trip Investigation — Root Causes

**Window: 2026-07-27 → 08-27.** A real 2B stall surfaced during documentation (the canary firing as designed). Investigation traced it through the SyncQ round-trip and landed on **two distinct failure modes**. Status: open with SyncQ (reviewing logs) on the Mode A side.

### Symptom

- **2B halted at the child gate (live node 14):** SyncQ's child sub-customer ID was not present when the gate checked, so the deal stalled. Monitoring showed 12 STALL alerts over ~45 days across ≥5 deals (Cotality, BizBash, Deutser, a zz-test org, Images by Lighting), at both parent gates (2A step 10 / 2B step 5) and the child gate.

### Two distinct failure modes (the stalls are not all the same bug)

API reads of two stalled deals show two different root causes that surface at the same gate:

- **Mode A — SyncQ genuinely didn't create (legacy-link).** Images by Lighting-2893 (Org 4319, parent **803**): no QBO sub-customer existed until a manual push; the parent is an unlinked **legacy mothership**. A controlled test — a fresh mothership + sub-customer (zz51 prefix) — ran the full chain successfully, so a parent provisioned through the current 2A flow is properly linked in SyncQ and its children sync. **Age is not the discriminator:** old org **817** ("Imprint Events") syncs fine while old org **803** fails — the operative difference is SyncQ link status (Pipedrive org ↔ QBO customer), not vintage. **The 803-vs-817 diff is the sharpest open diagnostic for SyncQ.** Fix is on SyncQ's side (link/repair the parent).
- **Mode B — SyncQ succeeded, our gate checked too early (timing).** Aim Games-3097 (Org **4358**, parent **3557**): API shows the QBO-id field = **5203** and Sync Status = **"Success"** — the writeback DID land — but `HID-QBO-Status` stuck at QBO-Cust-Ready because the automation had already taken the not-met branch. The 2026-08-19 run proves it: the 1-minute delay (node 12) finished **11:31:16** and the gate (node 14) evaluated **11:31:21**, before SyncQ wrote 5203. The parent (3557) is fully healthy (QBO-Cust, QBO-id 5196) — no legacy confound, pure early-check. The Pipedrive UI showed the field blank (staleness), which is why it first looked like a write-back failure. **RESOLVED:** the Quoter draft was fired manually via the render webhook script (`test_render_webhook.sh`, org 4358 / deal 3097) and the deal completed. **Applied fix:** the node-12 delay was raised from 1 to **3 minutes** so SyncQ's round-trip has time to land before the gate checks.

**Why it matters:** Mode A is a SyncQ/legacy-parent ticket; Mode B is our own delay-tuning. Some of the 12 alerts are each. Fixing one does not fix the other.

### Why "most deals succeed" fits the timing theory

If the 1-minute delay were universally too short, every deal would fail at node 14 — but most succeed, so SyncQ usually finishes inside the window. Mode B is therefore a **race lost near a threshold**, not a systematic failure: SyncQ's completion time varies (its poll/queue cadence, QBO API latency, load), so the occasional deal whose sync lands just after a cycle blows past the delay and loses. The low failure rate (12 alerts / 45 days, many test/repeat) is the signature of an occasional race loss. The deterministic repeat-failures (zz50 ×4, Cotality ×3, 803) are Mode A, not this race.

### Mechanics confirmed along the way

- **Nesting driver:** SyncQ nests a sub-customer via Pipedrive "Parent Organization" (ORG) → QBO `ParentRef` (mapping **LQB-45440**) — NOT the custom `Parent_Org_ID` field. The blank `Parent_Org_ID` on the legacy parent was a red herring for nesting.
- **Step-8 fix (consistency):** 2B step 8 now sources the child's `Parent_Org_ID` from the parent's intrinsic Organization ID rather than the custom `Parent_Org_ID` field (which is blank on legacy parents).
- **SyncQ ↔ QBO is healthy:** a manual SyncQ push created the sub-customer correctly nested (QBO 5184, "Is a sub-customer" under Images by Lighting) with correct `BillAddr`. The fragile leg is Pipedrive ↔ SyncQ.

> **⚠ Pipedrive UI staleness — verify by refresh/API, not by eye.** Pipedrive's UI can display a stale (blank) custom-field value even after SyncQ's API write has landed; the value only appears after a human save/refresh. "Blank in the UI" ≠ "not written." This misled early diagnosis (we briefly concluded the write-back was broken when it had actually written the ID). Confirm field states by forcing a refresh or reading via the API.

### Recovery status — deal 2893 (Images by Lighting)

- **Manually stamped:** `QuickBooks Id:SyncQ = 5184`, `HID-QBO-Status = QBO-SubCust`. QBO sub-customer 5184 exists and is nested.
- **Still open:** the Quoter draft was not fired (automation exited before step 17). Fire it via the render webhook script (org 4319 / its deal) — NOT a 2B re-run (would duplicate the child org). Confirm SyncQ recognizes the manual link before re-triggering.

### Hardening backlog

- **2B pre-check:** verify the mothership is properly provisioned/linked before creating the child; if not, re-provision or alert — self-healing for legacy parents (Mode A).
- **Backfill legacy motherships:** link each in SyncQ + stamp the expected fields so their future children sync.
- **Child-gate timing (Mode B — fix APPLIED):** node-12 delay raised 1 → 3 minutes. Under observation — track the STALL emails; if any Mode-B races persist, bump further or make node 14 **re-poll** (loop through a short delay and re-check a few times) instead of a single one-shot read. With the delay now 3 min, node 15's "3-min delay" canary text is finally accurate.
- **Visibility (green-success gap):** the not-met branch logs GREEN because its Slack/email actions succeed, so a stalled run looks healthy in Pipedrive's history. To force a red/failed run, add a deliberately-erroring final step on the not-met branch (e.g., a `Send webhook request` to a non-existent path → 404). A plain condition will NOT turn it red — only an erroring action does. Alternatively, stamp a filterable deal field/label (`Provisioning = Stalled`).
- **Canary wording:** the child-gate email boilerplate says "the sub-customer WAS created," which can contradict the diagnostic fields — trust the fields.

### Open threads (as of pause)

1. Watch the STALL emails to confirm the 3-minute delay stops Mode-B races.
2. Wire the red-on-failure step on the canary branch.
3. SyncQ's log review on the Mode A / legacy-parent side — the **803-vs-817 diff** is the key.
