# Patch — exclude `YY-` archived templates from the Pipedrive sync

**File:** `sync_quoter_to_pipedrive.py`
**Date:** 2026-08-29
**Purpose:** let a Quoter template be kept but hidden, so the ten item-named templates can be archived rather than deleted without appearing in Pipedrive field 90.

---

## Why

Deleting the ten item-named templates is irreversible and Quoter has no archive. They hold ~202 curated line items encoding a human judgement about what each kind of job needs — judgements never transferred into `item_group_defs.json`, which derives membership from code prefixes instead (Chapter 3 §8.2.1).

ScalePad describes the template-line-item gap as intended (§6.2.1) but describes the related catalog-reference limitation as one that *"will likely be updated at some point"* (§7.12.0). The probability is not the deciding factor. The **cost asymmetry** is: keeping them costs a few lines of code, deleting them costs days of reconstruction if the capability ever lands.

Renaming alone does not work — `build_plan()` treats a renamed template as a label change on the same option id, so `YY-Balloons` would still sit in the dropdown. Deleting the option alone does not work either, because this branch re-adds it on the next run:

```python
if oid not in by_id:
    to_add.append(rec)          # mapped option deleted in Pipedrive
```

So the template must be excluded at **fetch** time. This mirrors the exclusion that already exists for auto-appended item groups.

---

## The change

### 1. Module level, beside `RETIRE_PREFIX`

```python
# Prefix marking a Quoter record that is KEPT but should not be offered in
# Pipedrive. Distinct from RETIRE_PREFIX, which marks a Pipedrive OPTION whose
# Quoter record is gone. Two different systems, two different meanings:
#
#   XX-RET-  Pipedrive option label  - retired, id kept so old deals resolve
#   YY-      Quoter template title   - archived, hidden from this sync
#   zz-/ZZZ- Quoter items and quotes - test artifact, safe to delete
#
# Archived templates stay fully usable for manual quote building in the Quoter
# UI. They are hidden only from the dropdown that drives automated composition.
ARCHIVE_PREFIX = "YY-"


def is_archived(label):
    return (label or "").upper().startswith(ARCHIVE_PREFIX)
```

### 2. In `fetch_quoter()`, immediately after the existing auto-append filter

```python
    # Archived records: kept in Quoter, deliberately not offered in Pipedrive.
    # See ARCHIVE_PREFIX. Reversing this is a rename in Quoter -- the record
    # reappears in the dropdown on the next run.
    if not INCLUDE_ARCHIVED:
        archived = [r for r in records if is_archived(r["label"])]
        if archived:
            records = [r for r in records if not is_archived(r["label"])]
            print(f"  excluded {len(archived)} archived record(s) "
                  f"({ARCHIVE_PREFIX}): "
                  f"{', '.join(sorted(r['label'] for r in archived))}")
    return records
```

### 3. Argparse flag, and the module global it sets

```python
ap.add_argument("--include-archived", action="store_true",
                help=f"include records whose name starts with {ARCHIVE_PREFIX!r}. "
                     "Diagnostic only -- the scheduled run must NOT pass this, "
                     "or archived templates reappear in the dropdown.")
```

and in `main()`, before `fetch_quoter()` is called:

```python
    global INCLUDE_ARCHIVED
    INCLUDE_ARCHIVED = a.include_archived
```

with `INCLUDE_ARCHIVED = False` declared at module level next to `ARCHIVE_PREFIX`.

*(A global is the smallest change that fits the current shape of the file. If you would rather not add one, thread it as a parameter through `fetch_quoter(path, label_key, include_archived=False)` — one extra argument at the single call site.)*

### 4. Docstring

Add under `DELETION IS DELIBERATELY NOT AUTOMATED`:

```
ARCHIVED RECORDS
----------------
A Quoter template titled YY-<name> is excluded from the dropdown but kept in
Quoter. This exists because Quoter has no archive and deletion is permanent,
while the ScalePad API may one day expose template line items -- at which point
the ten item-named templates become useful again. Renaming alone is not enough:
build_plan() treats a rename as a label change on the same option id, so the
option would remain selectable. The exclusion has to happen at fetch time.

To un-archive: drop the YY- prefix in Quoter. The next run re-adds the option.
```

---

## Rollout order — this matters

**1. Apply the patch and deploy first.** If the templates are renamed before the filter exists, the next sync relabels the ten options to `YY-Balloons` and they stay selectable.

**2. Rename the ten in Quoter** to `YY-Balloons`, `YY-Robotics`, and so on. Numeric ids are in `CHAPTER_4_QUOTE_PRESENTATION_20260829.md` §2.1.

**3. Dry-run the sync.** `--source templates --field 90`, no `--apply`. Expect: `quoter: 2 record(s)` (Basic and Standard), the exclusion line naming ten archived records, and **ten orphans** — options whose template the sync can no longer see.

**4. Let it apply with `--retire-orphans`.** The ten options become `XX-RET-Balloons` etc., ids preserved. Note the label is `XX-RET-Balloons`, not `XX-RET-YY-Balloons` — the sync never renamed the option, because it stopped seeing the template first.

**5. Delete those ten options in Pipedrive.** This is the step that satisfies "the user must not be able to choose them." Retired options remain visible at the bottom of the picker; only deletion removes them. The filter is what stops them being recreated.

Composition is unaffected throughout — `quote_composer.py` falls back to `DEFAULT_TEMPLATE_ID` (Standard) with a warning when a deal's stored option resolves to no template.

---

## Reversing it

Drop the `YY-` prefix in Quoter. The next run re-adds each option and records a fresh pairing in `pd_option_map_templates.json`.

The new option ids will **not** match the deleted ones. That is acceptable — by then nothing references the old ids for selection purposes, and the 82 historical deals were always going to lose their label at step 5 regardless.

**If you would rather keep the old ids reusable**, stop at step 4 and leave the options retired instead of deleting them. `to_unretire` reuses the same id automatically when the record returns. The trade-off is exactly the one you rejected: retired options stay visible in the dropdown.

---

## Testing before it touches field 90

The sync is dry-run by default, so step 3 is already safe. For a stronger check, run it against the scratch field from Chapter 3 §11.3 rather than 90 — though note that field was listed for deletion in §18's cleanup, so confirm it still exists:

```
python3 sync_quoter_to_pipedrive.py --source templates --field 101
```

Verify: two live records, ten excluded, ten orphans reported, and `DRY RUN — nothing written.`
