#!/bin/bash
# sync-gdrive-quoter_sync.sh — push quoter_sync to Google Drive with rclone.
#
# WHY THIS EXISTS AS A SCRIPT
# ---------------------------
# This started as an alias in ~/.zshrc on the Mac Mini. That works, but an
# alias lives on one machine and nowhere else -- it is not version-controlled,
# it does not travel with the repo, and nothing reveals it except reading
# ~/.zshrc. The Air never had it.
#
# As a script it is committed, shared by ./sync.sh and ./retrieve.sh, and can
# do more than run one command: check its prerequisites, and report what moved.
#
# WHAT IT IS FOR
# --------------
# Git moves code between the Mini and the Air. rclone pushes quoter_sync to
# Drive, which is how the work is readable outside the repo. Different jobs,
# neither replaces the other:
#
#     git      Mini <-> Air
#     rclone   either machine -> Drive
#
# So a file committed but not rclone`d is invisible in Drive, and a file
# rclone`d but not committed exists on one machine only.
#
# Usage:
#     ./sync-gdrive-quoter_sync.sh
#     ./sync-gdrive-quoter_sync.sh --dry-run    show what would change, move nothing

set -uo pipefail

# SCOPED TO quoter_sync DELIBERATELY.
#
# This used to sync all of ~/projects. That was unsafe once two machines were
# involved: `rclone sync` MIRRORS, so running it from the machine with fewer
# files DELETES the rest from Drive. Git keeps the Mini and the Air identical
# inside quoter_sync, but says nothing about pipedrive-scripts, speaking_robot
# or anything else alongside it -- so a mirror from the wrong machine could
# remove work that exists in only one place.
#
# Narrowing to quoter_sync makes mirroring safe, because Git guarantees both
# machines match here. It also leaves the rest of gdrive:projects alone, so
# files that live only in Drive are no longer at risk from a sync.
#
# Other projects, if they ever need Drive backup, get their own command run
# deliberately from whichever machine holds the current state.
SRC="${GDRIVE_SYNC_SRC:-$HOME/projects/quoter_sync}"
DEST="${GDRIVE_SYNC_DEST:-gdrive:projects/quoter_sync}"
EXCLUDE="${GDRIVE_SYNC_EXCLUDE:-$HOME/.rclone-exclude}"

DRY=""
if [ "${1:-}" = "--dry-run" ]; then
    DRY="--dry-run"
fi

echo "☁️  SYNC quoter_sync TO GOOGLE DRIVE"
echo "=================================================="
echo "   source : $SRC"
echo "   dest   : $DEST"
[ -n "$DRY" ] && echo "   mode   : DRY RUN — nothing will be moved"
echo

# --- prerequisites ---------------------------------------------------------
if ! command -v rclone >/dev/null 2>&1; then
    echo "❌ rclone is not installed."
    echo "   brew install rclone"
    exit 1
fi

if [ ! -d "$SRC" ]; then
    echo "❌ $SRC does not exist."
    exit 1
fi

# Refuse to run against a directory that is not the repo. A wrong SRC with a
# mirroring sync is how you delete the Drive copy.
if [ ! -d "$SRC/.git" ]; then
    echo "❌ $SRC is not a git repository."
    echo "   This script mirrors, so it only runs against the repo."
    exit 1
fi

if ! rclone listremotes 2>/dev/null | grep -q "^gdrive:"; then
    echo "❌ No 'gdrive:' remote configured for this machine."
    echo "   rclone config"
    echo "   Each machine needs its own OAuth client — the Mini uses one"
    echo "   created in the GCP project 'rclone-drive-sync'."
    exit 1
fi

# The exclude file is what keeps venv/ out of Drive. Without it rclone copies
# tens of MB of installed packages on every run. Missing it is not fatal, but
# it is worth saying out loud rather than silently syncing everything.
if [ ! -f "$EXCLUDE" ]; then
    echo "⚠️  $EXCLUDE not found — syncing WITHOUT exclusions."
    echo "   That means venv/, myenv/ and anything else large go to Drive."
    echo "   Create it with at least:"
    echo "       venv/**"
    echo "       myenv/**"
    echo "       .venv/**"
    echo
    EXCLUDE_ARG=""
else
    EXCLUDE_ARG="--exclude-from $EXCLUDE"
    echo "   excludes: $(grep -cv '^[[:space:]]*$' "$EXCLUDE") pattern(s)"
    echo
fi

# --- sync ------------------------------------------------------------------
# `sync` mirrors: files deleted locally are deleted in Drive. That is the
# intent -- Drive should reflect the working tree -- but it is not `copy`, so
# a local deletion is not recoverable from Drive afterwards.
echo "🔄 Syncing..."
# shellcheck disable=SC2086
rclone sync "$SRC" "$DEST" $EXCLUDE_ARG $DRY --progress
STATUS=$?

echo
if [ $STATUS -eq 0 ]; then
    if [ -n "$DRY" ]; then
        echo "✅ Dry run complete — nothing was moved."
    else
        echo "✅ gdrive:projects/quoter_sync now mirrors $SRC"
        echo "   Nothing else under gdrive:projects was touched."
        echo "   Symlink warnings are normal: rclone will not follow venv/bin"
        echo "   symlinks without --copy-links, and should not."
    fi
else
    echo "❌ rclone exited $STATUS"
    echo "   If it is an auth error, re-run: rclone config reconnect gdrive:"
fi
exit $STATUS
