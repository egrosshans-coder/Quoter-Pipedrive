#!/bin/bash
# test_render_webhook.sh — fire the deployed webhook and watch what happens.
#
# WHAT THIS TESTS THAT A LOCAL RUN CANNOT
# ---------------------------------------
# `python3 quote_composer.py --deal 3101 --write` proves the COMPOSER works.
# It proves nothing about production, because it runs on your machine with
# your .env and calls create_quote_v2() directly.
#
# This exercises the four things only Render can exercise:
#
#   1. USE_V2_COMPOSITION being read from Render's environment
#   2. the branch in webhook_handler.py actually being taken
#   3. the deal RE-FETCH -- the webhook payload carries only the Quote
#      Template enum, never field 102, so the v2 branch calls
#      get_deal_by_id() to get Quote Effects. That logic has never run.
#   4. SCALEPAD_API_KEY resolving inside Render
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
#                         for testing. The file lives on Render's disk; clear
#                         the line via the Shell tab, or use a different deal.
#
# Both return 200 with a "reason", so read the response rather than assuming
# success from the status code.
#
# Usage:
#   ./test_render_webhook.sh
#   WEBHOOK_SECRET=xxx ./test_render_webhook.sh     # if the secret is set
#   ORG_ID=4351 DEAL_ID=3101 ./test_render_webhook.sh

set -uo pipefail

BASE="${RENDER_URL:-https://quoter-webhook-server.onrender.com}"
ORG_ID="${ORG_ID:-4351}"
ORG_NAME="${ORG_NAME:-zz53-org-3101}"
DEAL_ID="${DEAL_ID:-3101}"

echo "=================================================================="
echo "RENDER WEBHOOK TEST"
echo "=================================================================="
echo "  service : $BASE"
echo "  org     : $ORG_NAME (id $ORG_ID)"
echo "  deal    : $DEAL_ID"
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

# --- 2. fire the webhook ---------------------------------------------------
# Query token if a secret is configured; the handler also accepts an
# X-Webhook-Token header. It fails OPEN when WEBHOOK_SECRET is unset.
URL="$BASE/webhook/pipedrive/organization"
if [ -n "${WEBHOOK_SECRET:-}" ]; then
    URL="$URL?token=$WEBHOOK_SECRET"
    echo "2. Posting webhook (with token)"
else
    echo "2. Posting webhook (no token — handler fails open when"
    echo "   WEBHOOK_SECRET is unset; expect 401 if it IS set)"
fi

# HID-QBO-Status 289 = QBO-SubCust, the readiness gate.
# Field 102 is deliberately absent: the v2 branch must re-fetch to find it.
read -r -d '' PAYLOAD <<EOF
{
  "{{organization.id}}": "$ORG_ID",
  "{{organization.name}}": "$ORG_NAME",
  "{{deal.id}}": "$DEAL_ID",
  "{{deal.title}}": "zz53-deal",
  "454a3767bce03a880b31d78a38c480d6870e0f1b": "289"
}
EOF

echo "   payload:"
echo "$PAYLOAD" | sed 's/^/     /'
echo

RESP=$(curl -sS -m 120 -w "\n---HTTP %{http_code}---" \
    -X POST "$URL" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" 2>&1)

echo "   response:"
echo "$RESP" | sed 's/^/     /'
echo

# --- 3. read the outcome ---------------------------------------------------
echo "=================================================================="
case "$RESP" in
  *'"status": "success"'*|*'"status":"success"'*)
      echo "SUCCESS — a quote was created. Check Render Logs for"
      echo "  'USE_V2_COMPOSITION=true' to confirm the v2 branch was taken."
      echo "  If that line is absent, the flag is not set and this quote came"
      echo "  from the LEGACY path — which would also report success."
      ;;
  *already_processed*)
      echo "BLOCKED: already_processed."
      echo "  processed_organizations.txt on Render contains $ORG_ID:$DEAL_ID."
      echo "  The composer never ran. Clear that line via Render's Shell tab,"
      echo "  or rerun with a different deal:"
      echo "    ORG_ID=... DEAL_ID=... ./test_render_webhook.sh"
      ;;
  *not_ready_for_quotes*)
      echo "BLOCKED: not_ready_for_quotes."
      echo "  The handler did not see HID-QBO-Status = 289. Unexpected here,"
      echo "  since the payload sets it — worth checking the field key."
      ;;
  *unauthorized*)
      echo "BLOCKED: unauthorized. WEBHOOK_SECRET is set in Render."
      echo "  Rerun as: WEBHOOK_SECRET=xxx ./test_render_webhook.sh"
      ;;
  *"Deal not found for v2"*)
      echo "The v2 branch WAS taken, and the deal re-fetch failed."
      echo "  Good news: the flag is on and the branch works. Check the"
      echo "  PIPEDRIVE_API_TOKEN in Render."
      ;;
  *)
      echo "Unclear — read the response above and Render's Logs."
      ;;
esac
echo "=================================================================="
echo
echo "Logs: $BASE  ->  Render dashboard  ->  Logs"
echo "Look for these, in order:"
echo "    USE_V2_COMPOSITION=true - composing via Item Groups"
echo "    Effects: SFX-Balloons, ..."
echo "    Auto-appended: SCO-ScopeOfWork"
echo "    Created draft quot_..."
