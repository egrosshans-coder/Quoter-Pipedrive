# Job A — `_is_authorized()` patch

Replaces the block in `webhook_handler.py` that currently reads:

```python
# Shared-secret gate for inbound webhooks and debug endpoints.
# ...
# Behavior: fail-OPEN when WEBHOOK_SECRET is unset (so existing deployments keep
# working until the secret is configured on both senders), fail-CLOSED once it is set.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    logger.warning("⚠️ WEBHOOK_SECRET not set - inbound webhook/debug-endpoint auth is DISABLED (fail-open). Set WEBHOOK_SECRET to enable.")

def _is_authorized(req):
    """True if the request carries the shared secret, or if no secret is configured (fail-open)."""
    if not WEBHOOK_SECRET:
        return True
    provided = req.headers.get("X-Webhook-Token") or req.args.get("token")
    return provided == WEBHOOK_SECRET
```

---

## The replacement

Add `import hmac` to the imports at the top of the file. Everything else below is
self-contained.

```python
# Shared-secret gate for inbound webhooks and debug endpoints.
#
# Three accepted methods, in order of preference:
#   1. HTTP Basic Auth  - Pipedrive's automated webhooks support username and
#                         password fields on the webhook definition but do NOT
#                         support custom headers. The credential travels in the
#                         Authorization header and never reaches an access log.
#   2. X-Webhook-Token  - legacy header. Retained until step 6 of the migration.
#   3. ?token=          - legacy query param. Puts the secret in EVERY access
#                         log. Retained until step 6, then removed.
#
# WEBHOOK_SECRET_PREV is honoured while it is set, so a rotation has no window in
# which one side holds the new value and the other still holds the old one.
# Unset it once rotation is complete.
#
# Behavior: fail-OPEN when no secret is configured, fail-CLOSED once one is.
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_SECRET_PREV = os.getenv("WEBHOOK_SECRET_PREV")

_WEBHOOK_SECRETS = [s for s in (WEBHOOK_SECRET, WEBHOOK_SECRET_PREV) if s]

if not _WEBHOOK_SECRETS:
    logger.warning("⚠️ WEBHOOK_SECRET not set - inbound webhook/debug-endpoint auth is DISABLED (fail-open). Set WEBHOOK_SECRET to enable.")
if WEBHOOK_SECRET_PREV:
    logger.warning("⚠️ WEBHOOK_SECRET_PREV is set - rotation in progress, the previous secret is still accepted. Unset it when rotation is complete.")


def _secret_matches(candidate):
    """Constant-time comparison against every currently-accepted secret."""
    if not candidate:
        return False
    return any(hmac.compare_digest(candidate, s) for s in _WEBHOOK_SECRETS)


def _is_authorized(req):
    """True if the request carries an accepted secret, or if none is configured (fail-open).

    Logs which method succeeded, so the legacy paths can be removed on evidence
    rather than on the assumption that nothing uses them.
    """
    if not _WEBHOOK_SECRETS:
        return True

    auth = req.authorization
    if auth and auth.type == "basic":
        if _secret_matches(auth.password):
            logger.info(f"🔑 webhook auth: basic (user={auth.username})")
            return True
        logger.warning(f"🚫 webhook auth: basic rejected (user={auth.username})")
        return False

    if _secret_matches(req.headers.get("X-Webhook-Token")):
        logger.info("🔑 webhook auth: header-token")
        return True

    if _secret_matches(req.args.get("token")):
        logger.info("🔑 webhook auth: query-token")
        return True

    logger.warning("🚫 webhook auth: rejected")
    return False
```

No call sites change. `_is_authorized(request)` keeps its signature.

---

## What changed, and why each one

**Basic Auth added.** The point of the job. `req.authorization` is Flask's parsed
`Authorization` header; `auth.type` is lowercase `"basic"`. If the header is
absent or malformed, `req.authorization` is `None` and the function falls through
to the legacy paths.

**Basic Auth returns early on failure.** If a caller presents Basic credentials
and they are wrong, that is a rejection, not an invitation to try the query
string. This keeps the failure legible in the logs.

**The password is checked, the username is not.** Both travel in the same header,
so validating the username adds no security and adds a second value to keep
synchronised across Pipedrive and Render. It is logged so you can tell callers
apart.

**`hmac.compare_digest` replaces `==`.** Constant-time. The existing `==` leaks
timing information. Cheap to fix while the function is open.

**Dual-secret support via `WEBHOOK_SECRET_PREV`.** This is the deviation from the
kickoff brief's step 4, and the reason for it is in the runbook: "callers before
Render" does not close the 401 window, it only moves it. With both secrets
accepted, the order of the rotation stops mattering.

**Auth method logged at INFO.** Step 6 removes the query-token path. `_is_authorized()`
gates the debug endpoints as well as the webhook, and the original comment names
"Pipedrive + Quoter (and any debug caller)" as senders — so Pipedrive is not
necessarily the only user of the query token. This log line is what turns step 6
from an assumption into a measurement.

**Startup warning when `WEBHOOK_SECRET_PREV` is set.** A half-finished rotation is
easy to forget. This makes it visible in the deploy log every restart.

---

## One decision left to you: fail-open

The current function returns `True` when no secret is configured. The comment
explains why — "so existing deployments keep working until the secret is
configured on both senders." That transition finished some time ago;
`WEBHOOK_SECRET` is set in Render.

**The patch above preserves fail-open** rather than quietly changing it. The
argument for switching to fail-closed:

- The stated reason for fail-open has expired.
- It gates debug endpoints, not just the webhook.
- The failure mode is silent. A typo'd env var name in Render does not break
  anything visibly; it opens the endpoint.

The argument against: local runs without a `.env` entry currently work, and would
start returning 401.

If you want fail-closed, change two lines:

```python
if not _WEBHOOK_SECRETS:
    logger.error("❌ WEBHOOK_SECRET not set - refusing all inbound webhook and debug requests.")

def _is_authorized(req):
    if not _WEBHOOK_SECRETS:
        return False
    ...
```

This is a separate change from Job A. Doing it in the same commit means a 401
during testing has two possible causes instead of one. Recommend deciding now
and doing it as its own commit either before or after.
