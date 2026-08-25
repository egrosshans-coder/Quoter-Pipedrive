#!/bin/bash
# sync_dropdowns.sh — cron entry point for the Quoter -> Pipedrive dropdown sync.
#
# Keeps two Pipedrive dropdowns in step with Quoter:
#   field  90  Quote Template  <- Quoter quote templates (presentation)
#   field 102  Quote Effects   <- Quoter Item Groups     (content)
#
# For each:
#   created  -> option added
#   renamed  -> option relabelled, id preserved (deals keep resolving)
#   deleted  -> option relabelled XX-RET-<name>, id preserved
#
# NOTHING IS EVER DELETED. A deal stores the option's numeric id, so removing
# an option orphans that deal's stored value. Removal stays a human decision.
#
# Install (runs 06:00 daily):
#   chmod +x sync_dropdowns.sh
#   crontab -e
#   0 6 * * * /Users/pro/projects/quoter_sync/sync_dropdowns.sh
#
# Logs to logs/sync_dropdowns.log, pruned to the last 2000 lines.

set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

LOG_DIR="$PROJECT_DIR/logs"
LOG="$LOG_DIR/sync_dropdowns.log"
mkdir -p "$LOG_DIR"

# cron gets a minimal PATH and no shell profile, so the venv is explicit.
if [ -x "$PROJECT_DIR/venv/bin/python3" ]; then
    PY="$PROJECT_DIR/venv/bin/python3"
else
    PY="$(command -v python3)"
fi

# Credentials come from .env. The Python side calls load_dotenv(), but the
# vars are exported here too so the sync works the same way by hand.
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$PROJECT_DIR/.env"
    set +a
fi

{
    echo "=================================================================="
    echo "sync_dropdowns  $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "=================================================================="

    if [ -z "${SCALEPAD_API_KEY:-}" ] || [ -z "${PIPEDRIVE_API_TOKEN:-}" ]; then
        echo "ABORT: SCALEPAD_API_KEY or PIPEDRIVE_API_TOKEN missing from .env"
        exit 1
    fi

    # Field 90 -- Quote Template. Presentation templates: which layout,
    # cover page and branding a quote uses. Source of truth is Quoter's
    # template list.
    "$PY" sync_quoter_to_pipedrive.py \
        --source templates \
        --field 90 \
        --retire-orphans \
        --apply
    S1=$?
    echo "field 90 (Quote Template) exit status: $S1"

    echo
    # Field 102 -- Quote Effects. Item Groups: which effects a quote is
    # composed from. Multi-select, so a deal can carry several. Added
    # 2026-08-24 when the 20 SFX-/SVC-/STE- groups were built.
    "$PY" sync_quoter_to_pipedrive.py \
        --source item-groups \
        --field 102 \
        --retire-orphans \
        --apply
    S2=$?
    echo "field 102 (Quote Effects) exit status: $S2"

    STATUS=$(( S1 > S2 ? S1 : S2 ))
    echo "overall exit status: $STATUS"

    # The state file records quoter_id -> option_id and is what makes a rename
    # distinguishable from a delete-plus-create. It must persist. If this is a
    # git checkout, commit it -- otherwise a fresh clone loses the pairings and
    # every rename looks like a new option plus an orphan.
    # The state files map quoter_id -> pipedrive_option_id and are what make a
    # rename distinguishable from a delete-plus-create. Without them a rename
    # becomes a new option plus an orphan, and every deal still points at the
    # old id. They must be committed.
    if [ -d "$PROJECT_DIR/.git" ]; then
        for f in pd_option_map_templates.json pd_option_map_item_groups.json; do
            if ! git -C "$PROJECT_DIR" diff --quiet -- "$f" 2>/dev/null; then
                echo "NOTE: $f changed and is uncommitted."
                echo "      Commit it, or the mapping is lost on a fresh clone."
            fi
        done
    fi
} >> "$LOG" 2>&1

# keep the log from growing without bound
if [ -f "$LOG" ]; then
    tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
