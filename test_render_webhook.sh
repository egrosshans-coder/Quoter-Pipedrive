#!/bin/bash
# test_render_webhook.sh — fire the deployed webhook and watch what happens.
#
# WHAT THIS TESTS THAT A LOCAL RUN CANNOT
# --------------------------------------
# `python3 quote_composer.py --deal 3101 --write` proves the COMPOSER works.
# It proves nothing about production, because it runs on your machine with
# your .env and calls create_quote_v2() directly.
#
# This exercises the three things only Render can exercise:
#
#   1. authentication as the deployed service actually evaluates it
#   2. the deal RE-FETCH -- the webhook payload never carries field 102, so the
#      composer calls get_deal_by_id() to get Quote Effects
#   3. SCALEPAD_API_KEY resolving inside Render
#
# THE PAYLOAD
# -----------
# Mimics what the Pipedrive automation sends: mustache-style keys, the
# organization id, and HID-QBO-Status = 289 (QBO-SubCust) to satisfy the
# readiness gate. Deliberately does NOT include field 102 -- the point is to
# confirm the re-fetch supplies it.
#
# TWO GATES MAY STOP IT BEFORE THE COMPOSER RUNS, both in the handler's own
# logic and unchanged by this work:
#
#   not_ready_for_quotes  HID-QBO-Status is not 289 / QBO-SubCust
#   already_processed     processed_organizations.txt on Render already has
#                         "4351:3101". LIKELY, since this deal has been used
#                         for testing. The file lives on Render's disk and does
#                         NOT survive a deploy; clear the line via the Shell
#                         tab, or use a different deal.
#
# Both return 200 with a "reason", so read the response rather than assuming
# success from the status code.
#
# AUTH MODES
# ----------
# The handler accepts HTTP Basic Auth (the Pipedrive path), an X-Webhook-Token
# header, and a ?token= query param. The last two are removed at step 6 of the
# Basic Auth migration.
#
# Usage:
#   ./test_render_webhook.sh                     fire once using Basic Auth
#   ./test_render_webhook.sh basic               same, explicit
#   ./test_render_webhook.sh query               fire using ?token=
#   ./test_render_webhook.sh header              fire using X-Webhook-Token
#   ./test_render_webhook.sh authcheck           status-only matrix, no outcome
#                                                interpretation -- use this for
#                                                steps 2, 5 and 7 of the runbook
#
#   WEBHOOK_SECRET=xxx ./test_render_webhook.sh
#   ORG_ID=4351 DEAL_ID=3101 ./test_render_webhook.sh
#   WEBHOOK_SECRET_PREV=old ./test_render_webhook.sh authcheck
#
# Note on authcheck: it asserts 401 vs not-401 and nothing more. A 200 carrying
# not_ready_for_quotes or already_processed is a PASS -- it proves the request
# got past _is_authorized() and stopped at a later gate, which is exactly what
# an auth test wants and leaves no quote behind.

set -uo pipefail

BASE="${RENDER_URL:-https://quoter-webhook-server.onrender.com}"
ORG_ID="${ORG_ID:-4351}"
ORG_NAME="${ORG_NAME:-zz53-org-3101}"
DEAL_ID="${DEAL_ID:-3101}"
BASIC_USER="${WEBHOOK_BASIC_USER:-pipedrive}"
MODE="${1:-basic}"

URL="$BASE/webhook/pipedrive/organization"

# HID-QBO-Status 289 = QBO-SubCust, the readiness gate.
# Field 102 is deliberately absent: the composer must re-fetch to find it.
read -r -d '' PAYLOAD <<EOF
{
  "{{organization.id}}": "$ORG_ID",
  "{{organization.name}}": "$ORG_NAME",
  "{{deal.id}}": "$DEAL_ID",
  "{{deal.title}}": "zz53-deal",
  "454a3767bce03a880b31d78a38c480d6870e0f1b": "289"
}
EOF

echo "=================================================================="
echo "RENDER WEBHOOK TEST"
echo "=================================================================="
echo "  service : $BASE"
echo "  org     : $ORG_NAME (id $ORG_ID)"
echo "  deal    : $DEAL_ID"
echo "  mode    : $MODE"
echo

# --- 1. is the service up? -------------------------------------------------
echo "1. Health check"
HEALTH=$(curl -sS -m 30 "$BASE/health" 2>&1)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   up"
else
    echo "   NOT healthy — stopping here."
    echo "   $HEALTH"
    exit 1
fi
echo

# --- authcheck: status-only matrix -----------------------------------------
if [ "$MODE" = "authcheck" ]; then
    PASSES=0
    FAILURES=0

    probe() {
        LABEL="$1"
        EXPECT="$2"
        shift 2
        CODE=$(curl -sS -m 120 -o /dev/null -w "%{http_code}" \
            -X POST "$@" \
            -H "Content-Type: application/json" \
            -d "$PAYLOAD" 2>/dev/null)

        if [ "$EXPECT" = "401" ]; then
            if [ "$CODE" = "401" ]; then VERDICT="PASS"; else VERDICT="FAIL"; fi
        else
            if [ "$CODE" = "401" ]; then VERDICT="FAIL"; else VERDICT="PASS"; fi
        fi

        if [ "$VERDICT" = "PASS" ]; then
            PASSES=$((PASSES + 1))
        else
            FAILURES=$((FAILURES + 1))
        fi
        printf "   %-13s expect %-8s got %-5s %s\n" "$LABEL" "$EXPECT" "$CODE" "$VERDICT"
    }

    echo "2. Auth matrix"
    if [ -z "${WEBHOOK_SECRET:-}" ]; then
        echo "   WEBHOOK_SECRET is not set locally — cannot run the matrix."
        echo "   Rerun as: WEBHOOK_SECRET=xxx ./test_render_webhook.sh authcheck"
        exit 2
    fi

    probe "basic"        not-401 "$URL" -u "$BASIC_USER:$WEBHOOK_SECRET"
    if [ -n "${WEBHOOK_SECRET_PREV:-}" ]; then
        probe "basic-prev"   not-401 "$URL" -u "$BASIC_USER:$WEBHOOK_SECRET_PREV"
    else
        echo "   basic-prev    skipped, WEBHOOK_SECRET_PREV not set"
    fi
    probe "basic-bad"    401     "$URL" -u "$BASIC_USER:definitely-not-the-secret"
    probe "no-creds"     401     "$URL"
    probe "query-token"  not-401 "$URL?token=$WEBHOOK_SECRET"
    probe "header-token" not-401 "$URL" -H "X-Webhook-Token: $WEBHOOK_SECRET"

    echo
    echo "=================================================================="
    echo "$PASSES passed, $FAILURES failed"
    echo
    echo "After step 6 removes the legacy paths, query-token and header-token"
    echo "should both return 401. Flip their expectations then."
    echo
    echo "Render Logs will show which method each request used:"
    echo "    webhook auth: basic (user=...)"
    echo "    webhook auth: header-token"
    echo "    webhook auth: query-token"
    echo "=================================================================="
    if [ "$FAILURES" -gt 0 ]; then exit 1; fi
    exit 0
fi

# --- 2. fire the webhook ---------------------------------------------------
if [ -z "${WEBHOOK_SECRET:-}" ]; then
    echo "2. Posting webhook (no credentials — the handler fails OPEN when"
    echo "   WEBHOOK_SECRET is unset on the SERVER; expect 401 if it IS set)"
    set -- "$URL"
else
    case "$MODE" in
      basic)
          echo "2. Posting webhook (HTTP Basic Auth, user=$BASIC_USER)"
          set -- "$URL" -u "$BASIC_USER:$WEBHOOK_SECRET"
          ;;
      query)
          echo "2. Posting webhook (?token= — legacy, removed at step 6)"
          set -- "$URL?token=$WEBHOOK_SECRET"
          ;;
      header)
          echo "2. Posting webhook (X-Webhook-Token — legacy, removed at step 6)"
          set -- "$URL" -H "X-Webhook-Token: $WEBHOOK_SECRET"
          ;;
      *)
          echo "unknown mode: $MODE"
          echo "expected one of: basic query header authcheck"
          exit 2
          ;;
    esac
fi

echo "   payload:"
echo "$PAYLOAD" | sed 's/^/     /'
echo

RESP=$(curl -sS -m 120 -w "\n---HTTP %{http_code}---" \
    -X POST "$@" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" 2>&1)

echo "   response:"
echo "$RESP" | sed 's/^/     /'
echo

# --- 3. read the outcome ---------------------------------------------------
echo "=================================================================="
case "$RESP" in
  *'"status": "success"'*|*'"status":"success"'*)
      echo "SUCCESS — a quote was created."
      echo "  There is one composition path and no flag, so this came through"
      echo "  the Item Group composer. Check Render Logs for the section and"
      echo "  line-item counts."
      ;;
  *already_processed*)
      echo "BLOCKED: already_processed."
      echo "  processed_organizations.txt on Render contains $ORG_ID:$DEAL_ID."
      echo "  The composer never ran. For an AUTH test this is a PASS — the"
      echo "  request got past _is_authorized(). Clear the line via Render's"
      echo "  Shell tab, or rerun with a different deal:"
      echo "    ORG_ID=... DEAL_ID=... ./test_render_webhook.sh"
      ;;
  *not_ready_for_quotes*)
      echo "BLOCKED: not_ready_for_quotes."
      echo "  The handler did not see HID-QBO-Status = 289. Unexpected here,"
      echo "  since the payload sets it — worth checking the field key."
      echo "  For an AUTH test this is still a PASS."
      ;;
  *"---HTTP 401---"*|*unauthorized*)
      echo "BLOCKED: 401 unauthorized."
      case "$MODE" in
        basic)
            echo "  Basic Auth was rejected. Either WEBHOOK_SECRET here does not"
            echo "  match Render's, or the deploy adding Basic Auth has not"
            echo "  landed yet. Render Logs will show 'webhook auth: basic"
            echo "  rejected' if the code is deployed and the password is wrong,"
            echo "  and nothing at all if it is not deployed."
            ;;
        query|header)
            echo "  Expected if step 6 has already removed the legacy paths."
            echo "  Otherwise check WEBHOOK_SECRET against Render."
            ;;
        *)
            echo "  Rerun as: WEBHOOK_SECRET=xxx ./test_render_webhook.sh"
            ;;
      esac
      ;;
  *"---HTTP 404---"*)
      echo "404 — wrong route. This script posts to"
      echo "  /webhook/pipedrive/organization. Confirm that against the"
      echo "  @app.route decorators in webhook_handler.py."
      ;;
  *"Deal not found"*)
      echo "The composer ran and the deal re-fetch failed."
      echo "  Check PIPEDRIVE_API_TOKEN in Render."
      ;;
  *)
      echo "Unclear — read the response above and Render's Logs."
      ;;
esac
echo "=================================================================="
echo
echo "Logs: $BASE  ->  Render dashboard  ->  Logs"
echo "Look for these, in order:"
echo "    webhook auth: basic (user=...)"
echo "    Effects: SFX-Balloons, ..."
echo "    Auto-appended: SCO-ScopeOfWork"
echo "    Created draft quot_..."
