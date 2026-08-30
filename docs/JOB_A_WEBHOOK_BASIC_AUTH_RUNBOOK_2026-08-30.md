# Job A — Webhook Basic Auth and `WEBHOOK_SECRET` Rotation

**Date:** 2026-08-30
**Scope:** `webhook_handler.py` `_is_authorized()`, the `Ready-Quoter-Draft Quote Creation-v3` webhook definition, `WEBHOOK_SECRET` in Render and both local `.env` files, and `test_render_webhook.sh`.
**Out of scope:** the payload (Job B), the composition path, `Ready-Quoter-Draft Quote Creation-v2`.
**Governing discipline:** verify, don't assume. Each step below has a stated pass condition. Do not proceed past a gate that has not passed.

---

## 0. What changes and why

`WEBHOOK_SECRET` travels as `?token=` in the URL, so it is in every access log. **[Confirmed, Ch3 §16.5]** Pipedrive's automated webhooks do not support custom headers, so the existing `X-Webhook-Token` path cannot serve this caller. They do support HTTP Basic Auth, which travels in the `Authorization` header. **[Confirmed, Ch3 §16.5]**

The code change alone does not remove the exposure. Historical access logs keep the old secret permanently. **Rotation is the fix; Basic Auth stops it recurring.**

### Deviation from the kickoff brief

The brief's step 4 says "callers before Render, or everything 401s in the gap." That holds for a single-secret design, but it does not remove the gap — it moves it. Set the new password in Pipedrive first and Render still validates the old one; rotate Render first and Pipedrive is still sending the old one. Either way a deal crossing into *Send Quote/Negotiate* during the window gets a 401 and no quote.

**Resolution:** accept two secrets for the duration of the rotation via `WEBHOOK_SECRET_PREV`, then delete it. Order stops mattering and the window closes. This is the only substantive departure from the brief's sequence.

### One webhook definition, both automations

`2B-V3` step 19 and `2C-V1` step 9 both point at `Ready-Quoter-Draft Quote Creation-v3`. **[Confirmed, Ch3 §19.2]** Step 3 below is therefore a single edit.

### Closed, no action needed

`Ready-Quoter-Draft Quote Creation-v2` carries no token and is referenced by four automations, **all four confirmed inactive**. **[Confirmed, Ch3 §19.4]** No 401 risk. §16.5 still lists this as open; §19.4 is later in the same revision and supersedes it.

### Secret stores touched

| Store | Touched |
| :-- | :-- |
| Render dashboard | yes |
| `.env` on Mac Mini | yes |
| `.env` on MacBook Air | yes |
| Pipedrive webhook definition | yes |
| GitHub Actions secrets | **no** — the dropdown sync talks to Quoter and Pipedrive directly, never to this endpoint |

---

## 1. Pre-flight

```
./retrieve.sh
git status
grep -n gunicorn requirements.txt
```

**Pass:** working tree clean or only expected changes, and `gunicorn==23.0.0` present. Three deploys failed on 2026-08-29 because that line was committed away by a stale-file overwrite. Check it every time before a commit on this repo.

Record the **current** `WEBHOOK_SECRET` value somewhere you can paste from. You need it as `WEBHOOK_SECRET_PREV` in step 4.

---

## 2. Step 1 — the code

Replace `_is_authorized()` in `webhook_handler.py`. All three auth methods stay live; the query and header paths are deleted at step 6, not now.

```python
import hmac
import logging
import os

from flask import request

log = logging.getLogger(__name__)


def _is_authorized():
    """Authorize a webhook request.

    Accepts, in order of preference:
      1. HTTP Basic Auth  - the Pipedrive automated-webhook path (§16.5)
      2. X-Webhook-Token  - legacy header, no known caller
      3. ?token=          - legacy query param, puts the secret in access logs

    WEBHOOK_SECRET_PREV is honoured while set, so a rotation has no window
    in which one side has the new value and the other does not. Remove it
    once rotation is complete.
    """
    secrets = [s for s in (os.getenv("WEBHOOK_SECRET"),
                           os.getenv("WEBHOOK_SECRET_PREV")) if s]
    if not secrets:
        log.error("webhook auth: WEBHOOK_SECRET is unset, failing closed")
        return False

    def matches(candidate):
        return any(hmac.compare_digest(candidate, s) for s in secrets)

    auth = request.authorization
    if auth and auth.type == "basic" and auth.password:
        if matches(auth.password):
            log.info("webhook auth: basic (user=%s)", auth.username)
            return True
        log.warning("webhook auth: basic rejected (user=%s)", auth.username)
        return False

    header_token = request.headers.get("X-Webhook-Token")
    if header_token and matches(header_token):
        log.info("webhook auth: header-token")
        return True

    query_token = request.args.get("token")
    if query_token and matches(query_token):
        log.info("webhook auth: query-token")
        return True

    log.warning("webhook auth: rejected")
    return False
```

**Three deliberate choices.**

- **The password is validated, the username is not.** Both travel in the same header, so validating the username buys no security and adds a value to keep in sync across two systems. It is logged so you can see which caller arrived.
- **`hmac.compare_digest` rather than `==`.** Constant-time comparison. Cheap.
- **The auth method is logged at INFO.** Step 6 deletes the query-token path. That deletion should rest on a log search proving nothing used it, not on an assumption. This is the line that makes step 6 measurable.

**If the current signature takes an argument** (`_is_authorized(request)`), keep it and drop the `from flask import request` import. **If there is no module logger,** substitute whatever `webhook_handler.py` already uses.

**Pass:** `python -c "import webhook_handler"` succeeds locally.

---

## 3. Step 2 — deploy

```
git add -A
git status
git commit -m "webhook: accept HTTP Basic Auth, support dual secret during rotation"
git push
```

Watch the Render deploy. **The start command that runs is in Render → Settings, not `render.yaml`** — that file is inert. **[Confirmed, Ch3 §16.4]**

**Pass:** service starts, gunicorn reports two workers, and the old path still authorizes:

```
PAYLOAD_FILE=test_payload.json ./test_render_webhook.sh query-token
```

Expect a non-401 response. A `200` carrying `not_ready_for_quotes` or `already_processed` is a pass — **a 200 does not mean a quote was created** **[Confirmed, Ch3 §15.4]**, and for an auth test that is exactly what you want.

**Rollback:** revert the commit and push. Nothing outside the repo has changed yet.

---

## 4. Step 3 — Pipedrive webhook definition

Edit `Ready-Quoter-Draft Quote Creation-v3`:

- **Username:** `pipedrive` (any value; it is logged, not validated)
- **Password:** the **current** `WEBHOOK_SECRET`, unrotated
- **URL:** strip `?token=...`, leaving the bare endpoint

Using the current secret here is deliberate. Basic Auth starts working immediately, and rotation becomes a separate, independently verifiable step.

**Pass:** fire the webhook through Pipedrive itself and read the Render log for `webhook auth: basic`. Toggle `Run 2C Manual SubCust Repair` (field 100) to **Yes** on a `zz-` test org — that triggers `2C-V1`, which fires the webhook at step 9. **[Confirmed, Ch3 §19.1]** Pick an org already in `processed_organizations.txt` so the handler stops at `already_processed` and no quote is created.

Note that `2C-V1` also writes QBO ids back to the deal and resets its own trigger field. Use a test org, not a live one.

**Rollback:** re-add `?token=<current secret>` to the URL and clear the Basic Auth fields. The code still accepts the query path.

---

## 5. Step 4 — rotate

Generate the new value. No trailing `#` comments on shell lines — this zsh parses them as arguments.

```
openssl rand -hex 32
```

Then, in this order:

1. **Render → Environment:** set `WEBHOOK_SECRET_PREV` to the **old** value and `WEBHOOK_SECRET` to the **new** value. Save. The service restarts.
2. Confirm the service is back up.
3. **Pipedrive:** change the webhook password to the **new** value.
4. **`.env` on the Mac Mini and the MacBook Air:** set the new value. These are three separate stores that do not see each other.

**Pass:** with both secrets live, a Basic Auth request using either the old or the new password is accepted. Verify with step 5.

**Rollback:** because both secrets are accepted, there is nothing to roll back mid-rotation. Fix whichever side is wrong and continue.

---

## 6. Step 5 — test

```
PAYLOAD_FILE=test_payload.json ./test_render_webhook.sh all
```

| Case | Expected |
| :-- | :-- |
| Basic Auth, new secret | not 401 |
| Basic Auth, old secret | not 401, while `WEBHOOK_SECRET_PREV` is set |
| Basic Auth, wrong password | **401** |
| No credentials at all | **401** |
| Query token, new secret | not 401, until step 6 |

The 401 cases matter as much as the 200s. An endpoint that accepts everything passes the happy-path test too.

---

## 7. Step 6 — cleanup

Do this only after the Render logs show `webhook auth: basic` for real traffic and **no** `webhook auth: query-token` or `header-token` entries over a period long enough to cover every automation that fires this endpoint.

1. Delete the `X-Webhook-Token` and `?token=` branches from `_is_authorized()`.
2. Remove `WEBHOOK_SECRET_PREV` from Render and from both `.env` files.
3. Deploy.
4. Re-run `./test_render_webhook.sh all`. The query-token case should now be **401**.

`test_render_webhook.sh` also carried stale advice to check the logs for `USE_V2_COMPOSITION=true`, a flag that no longer exists. **[Confirmed, Ch3 §18.2]** The replacement script drops it.

---

## 8. Not done here

- **Job B — payload slimming.** Blocked on `_contact_from_webhook()` reading the re-fetched deal rather than the payload. **[Confirmed, Ch3 §19.3]**
- Deleting `Ready-Quoter-Draft Quote Creation-v2`. Optional, no risk either way. **[Confirmed, Ch3 §19.4]**
