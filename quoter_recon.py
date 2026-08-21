#!/usr/bin/env python3
"""
quoter_recon.py — READ-ONLY reconnaissance against the ScalePad/Quoter v1 API.

Purpose: gather the facts needed to decide the Item Group naming/matching
convention (Kickoff Brief step 2) WITHOUT guessing at endpoint shapes.

This script issues GET requests only. It never POSTs, PATCHes, or DELETEs.
It cannot modify production data.

CREDENTIAL SCOPE — read this before setting anything:
    TLC runs TWO separate APIs concurrently (Chapter 3 section 2). They use
    different credentials and are NOT interchangeable:

      legacy   api.quoter.com          OAuth: client_id (cid_...) + secret
                                       -> Authorization: Bearer <token>
      v2       api.scalepad.com        single opaque key
                                       -> x-api-key: <key>

    This script targets api.scalepad.com ONLY, so it needs the ScalePad key
    and nothing else. Neither the legacy client_id nor the legacy client
    secret will authenticate here, under any header.

    Caution on Render's env var names: Render's QUOTER_API_KEY holds a legacy
    client_id (cid_...), despite the name. The ScalePad key lives in Render's
    SCALEPAD_API_KEY. Names in that dashboard do not describe contents.

Governing discipline: verify, don't assume. Where the API shape is unknown
(item list endpoint, pagination style), this script PROBES and REPORTS rather
than assuming. Unknowns are printed as unknowns.

Usage:
    export SCALEPAD_API_KEY='...'
    python3 quoter_recon.py

Requires Python 3.8+. Standard library only — no pip install needed.

Outputs:
    ./quoter_recon/*.json   raw responses, for follow-up work
    ./quoter_recon/REPORT.txt  compact summary — paste this back
"""

import http.client
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

BASE = "https://api.scalepad.com/quoter/v1"
OUTDIR = Path("./quoter_recon")
CSV_PATH = "export_items_20260724b.csv"   # optional; skipped if absent

API_KEY = os.environ.get("SCALEPAD_API_KEY", "").strip()
if not API_KEY:
    sys.exit("ERROR: set SCALEPAD_API_KEY in your environment first.\n"
             "  read -rs SCALEPAD_API_KEY && export SCALEPAD_API_KEY\n"
             "(Passing it as argv would leak it into shell history.)\n"
             "This must be the ScalePad v2 key, NOT a legacy Quoter\n"
             "client_id or client secret. See CREDENTIAL SCOPE above.")

# Guard: catch the legacy client_id being passed by mistake, before burning
# a round of 401s working out why. Prefix check only -- the value is never
# printed, logged, or written to any output file.
if API_KEY.startswith("cid_"):
    sys.exit("ERROR: that is a legacy Quoter OAuth client_id (cid_ prefix),\n"
             "not a ScalePad v2 API key. It cannot authenticate against\n"
             f"{BASE} under any header. Use Render's SCALEPAD_API_KEY value.")

# Known IDs from the kickoff brief (test/sandbox — safe to read)
KNOWN = {
    "balloons_template": "tmpl_32CqUL7Iloih2Xgx68JvjptGYXy",
    "test_item_group":   "igrp_3Fgct9Xz5Uwu03SUmOoNP6RmZ9o",
    "drop_category":     "cat_30LNfgV7gCwhQydirKD1KhNrS00",
    "test_quote":        "quot_3I9UCyBcqZJ39soTFYS5SodFzlW",
}

REPORT = []


def log(line=""):
    print(line)
    REPORT.append(line)


def get(path, params=None, timeout=30):
    """GET a path. Returns (status, parsed_or_text, error_str).

    Uses http.client rather than urllib because urllib normalizes header
    names via .capitalize(), sending 'X-api-key'. ScalePad's gateway matches
    case-sensitively and rejects that with 401. Confirmed live Aug 19 2026:
    curl with lowercase 'x-api-key' -> 200, urllib -> 401, same key/URL.
    """
    url = BASE + path
    if params:
        # filter[x] brackets must stay literal, matching filter[field]=eq:val
        url += "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote,
                                            safe="[]:")
    parts = urllib.parse.urlsplit(url)
    target = parts.path + (("?" + parts.query) if parts.query else "")
    conn = None
    try:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(parts.netloc, timeout=timeout,
                                           context=ctx)
        # Header name written exactly as-is -- no capitalization.
        conn.putrequest("GET", target, skip_accept_encoding=True)
        conn.putheader("x-api-key", API_KEY)
        conn.putheader("Accept", "application/json")
        conn.endheaders()
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", "replace")
        try:
            return resp.status, json.loads(body), None
        except json.JSONDecodeError:
            return resp.status, body[:2000], "non-JSON response"
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def save(name, obj):
    OUTDIR.mkdir(exist_ok=True)
    (OUTDIR / f"{name}.json").write_text(json.dumps(obj, indent=2))


def shape(obj):
    """Describe a response's top-level shape without assuming a schema."""
    if not isinstance(obj, dict):
        return f"(non-dict: {type(obj).__name__})"
    bits = []
    for k, v in obj.items():
        if isinstance(v, list):
            bits.append(f"{k}[{len(v)}]")
        elif isinstance(v, dict):
            bits.append(f"{k}{{{','.join(list(v.keys())[:4])}}}")
        else:
            bits.append(f"{k}={v!r}"[:60])
    return ", ".join(bits)


# ---------------------------------------------------------------------------
# 1. Endpoint discovery — which item-listing path actually exists?
# ---------------------------------------------------------------------------
def probe_endpoints():
    log("=" * 72)
    log("1. ENDPOINT PROBE  (unconfirmed paths — reporting what actually exists)")
    log("=" * 72)
    # Ch3 confirms /item-group-item-assignments carries item_id, but never
    # confirms how to LIST items. These are the plausible candidates.
    candidates = [
        "/items",
        "/catalog-items",
        "/products",
        "/line-items",
        "/item-groups",
        "/item-group-item-assignments",
        "/quote-templates",
        "/categories",
    ]
    found = {}
    for path in candidates:
        status, body, err = get(path, {"page[size]": 1})
        if err:
            log(f"  {path:34} ERROR  {err}")
            continue
        marker = "OK " if status == 200 else "   "
        detail = shape(body) if status == 200 else str(body)[:110]
        log(f"  {marker}{path:32} {status}  {detail}")
        if status == 200:
            found[path] = body
        time.sleep(0.2)
    save("00_endpoint_probe", {k: v for k, v in found.items()})
    log()
    return found


# ---------------------------------------------------------------------------
# 2. Pagination discovery — probe styles, do not assume
# ---------------------------------------------------------------------------
def probe_pagination(path):
    log("=" * 72)
    log(f"2. PAGINATION PROBE on {path}")
    log("=" * 72)
    styles = [
        ("page[size]/page[number]", {"page[size]": 2, "page[number]": 1},
                                    {"page[size]": 2, "page[number]": 2}),
        ("limit/offset",            {"limit": 2, "offset": 0},
                                    {"limit": 2, "offset": 2}),
        ("per_page/page",           {"per_page": 2, "page": 1},
                                    {"per_page": 2, "page": 2}),
    ]
    working = None
    for name, p1, p2 in styles:
        s1, b1, e1 = get(path, p1)
        s2, b2, e2 = get(path, p2)
        if e1 or e2 or s1 != 200 or s2 != 200:
            log(f"  {name:26} rejected ({s1}/{s2})")
            continue
        d1 = b1.get("data", []) if isinstance(b1, dict) else []
        d2 = b2.get("data", []) if isinstance(b2, dict) else []
        ids1 = [x.get("id") for x in d1 if isinstance(x, dict)]
        ids2 = [x.get("id") for x in d2 if isinstance(x, dict)]
        honored = len(d1) <= 2
        advanced = bool(ids1) and bool(ids2) and ids1 != ids2
        log(f"  {name:26} 200  page1={len(d1)} page2={len(d2)}  "
            f"size_honored={honored} advanced={advanced}")
        if honored and advanced and working is None:
            working = (name, p1)
        time.sleep(0.2)
    if working:
        log(f"  --> USING: {working[0]}")
    else:
        log("  --> No pagination style confirmed. Will fetch unpaged and")
        log("      compare returned count against total_count to detect a cap.")
    log()
    return working


def fetch_all(path, page_style, hard_cap=5000):
    """Page through a collection using the confirmed style; else single GET."""
    rows, meta = [], {}
    if page_style is None:
        status, body, err = get(path)
        if status == 200 and isinstance(body, dict):
            rows = body.get("data", [])
            meta = {k: v for k, v in body.items() if k != "data"}
        return rows, meta, ("unpaged" if status == 200 else f"failed:{status}")

    name, _ = page_style
    n = 1
    while len(rows) < hard_cap:
        if name.startswith("page["):
            params = {"page[size]": 100, "page[number]": n}
        elif name.startswith("limit"):
            params = {"limit": 100, "offset": (n - 1) * 100}
        else:
            params = {"per_page": 100, "page": n}
        status, body, err = get(path, params)
        if status != 200 or not isinstance(body, dict):
            break
        batch = body.get("data", [])
        meta = {k: v for k, v in body.items() if k != "data"}
        rows.extend(batch)
        if len(batch) < 100:
            break
        n += 1
        time.sleep(0.15)
    return rows, meta, name


# ---------------------------------------------------------------------------
# 3-5. Collections
# ---------------------------------------------------------------------------
def pull_collection(label, path, page_style, filename):
    log("=" * 72)
    log(f"{label}  ({path})")
    log("=" * 72)
    rows, meta, how = fetch_all(path, page_style)
    save(filename, {"meta": meta, "data": rows})
    log(f"  fetched {len(rows)} records via {how}")
    if meta:
        log(f"  response meta: {meta}")
    tc = meta.get("total_count")
    if isinstance(tc, int) and tc != len(rows):
        log(f"  !! MISMATCH: total_count={tc} but fetched {len(rows)} "
            f"— pagination incomplete, do not treat as full catalog")
    if rows:
        log(f"  first record keys: {sorted(rows[0].keys())}")
        log(f"  sample: {json.dumps(rows[0])[:400]}")
    log()
    return rows, meta


def pull_assignments(groups, page_style):
    log("=" * 72)
    log("6. ITEM GROUP ASSIGNMENTS  (per group)")
    log("=" * 72)
    out = {}
    for g in groups:
        gid = g.get("id")
        if not gid:
            continue
        rows, meta, _ = fetch_all(
            f"/item-group-item-assignments?filter[item_group_id]=eq:{gid}",
            page_style)
        out[gid] = rows
        log(f"  {g.get('name','(unnamed)')[:44]:46} {gid}  members={len(rows)}")
        time.sleep(0.15)
    save("06_assignments", out)
    log()
    return out


# ---------------------------------------------------------------------------
# 7. The actual decision: do template titles line up with catalog categories?
# ---------------------------------------------------------------------------
def compare_templates_to_categories(templates, items):
    log("=" * 72)
    log("7. CONVENTION CHECK — template titles vs. item categories")
    log("=" * 72)

    csv_cats = Counter()
    if Path(CSV_PATH).exists():
        import csv as _csv
        with open(CSV_PATH, newline="", encoding="utf-8") as fh:
            for r in _csv.DictReader(fh):
                c = (r.get("*Category") or "").strip()
                if c:
                    csv_cats[c] += 1
        log(f"  CSV catalog: {sum(csv_cats.values())} items in "
            f"{len(csv_cats)} categories")
    else:
        log(f"  (CSV {CSV_PATH} not found next to script — skipping CSV compare)")

    api_cats = Counter()
    for it in items:
        cat = it.get("category")
        nm = cat.get("name") if isinstance(cat, dict) else cat
        if nm:
            api_cats[str(nm)] += 1
    if api_cats:
        log(f"  API catalog: {sum(api_cats.values())} items in "
            f"{len(api_cats)} categories")

    titles = [t.get("title", "") for t in templates]
    log(f"\n  {len(titles)} templates found:")
    for t in sorted(titles):
        log(f"    - {t}")

    ref = api_cats or csv_cats
    if ref and titles:
        low = {c.lower(): c for c in ref}
        exact, partial, orphan = [], [], []
        for t in titles:
            tl = t.strip().lower()
            if tl in low:
                exact.append((t, low[tl], ref[low[tl]]))
            else:
                hits = [c for cl, c in low.items() if cl in tl or tl in cl]
                (partial if hits else orphan).append((t, hits))
        log(f"\n  exact title==category : {len(exact)}")
        for t, c, n in exact:
            log(f"      {t:38} -> {c} ({n} items)")
        log(f"  partial/substring     : {len(partial)}")
        for t, h in partial:
            log(f"      {t:38} -> {h}")
        log(f"  no category match     : {len(orphan)}")
        for t, _ in orphan:
            log(f"      {t}")
        log()
        log("  READ THIS: high exact-match count means category-based Item Group")
        log("  population is viable NOW and the template-read blocker is mostly")
        log("  bypassed. High orphan count means templates cut across categories")
        log("  and we genuinely need Jon's answer before automating.")
    log()


def main():
    OUTDIR.mkdir(exist_ok=True)
    log(f"ScalePad/Quoter recon — READ ONLY — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"base: {BASE}")
    log()

    found = probe_endpoints()

    items_path = None
    for cand in ("/items", "/catalog-items", "/products", "/line-items"):
        if cand in found:
            items_path = cand
            break

    page_style = probe_pagination(items_path or "/item-groups")

    items = []
    if items_path:
        items, _ = pull_collection("3. ITEMS", items_path, page_style, "03_items")
    else:
        log("=" * 72)
        log("3. ITEMS — NO WORKING ITEM-LIST ENDPOINT FOUND")
        log("=" * 72)
        log("  None of /items, /catalog-items, /products, /line-items returned 200.")
        log("  Assignments need item_id, so this is a hard blocker for the build.")
        log("  Paste the section-1 probe output back and we'll work from the")
        log("  actual status codes rather than guessing further.")
        log()

    groups, _ = pull_collection("4. ITEM GROUPS", "/item-groups",
                                page_style, "04_item_groups")
    templates, _ = pull_collection("5. QUOTE TEMPLATES", "/quote-templates",
                                   page_style, "05_templates")

    if groups:
        pull_assignments(groups, page_style)

    compare_templates_to_categories(templates, items)

    log("=" * 72)
    log("DONE — raw JSON in ./quoter_recon/, summary in ./quoter_recon/REPORT.txt")
    log("=" * 72)
    (OUTDIR / "REPORT.txt").write_text("\n".join(REPORT))


if __name__ == "__main__":
    main()
