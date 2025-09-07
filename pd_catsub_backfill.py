 #!/usr/bin/env python3

"""
Pipedrive Cat:Sub Backfill (Passive)
------------------------------------
Populates a Pipedrive text custom field (e.g., "QBO-Category:Subcategory")
with "Parent:Child" built from:
  - Product Category (enum)  -> parent label
  - Your Subcategory custom field (text) -> child

It skips records where Sync-to-QBO is already "Yes" (if you provide the key+ID),
and it never flips Sync, so it won't wake SyncQ or QBO.

Usage examples:

  python pd_catsub_backfill.py \
    --domain tlciscreative.pipedrive.com \
    --api-token $PIPEDRIVE_API_TOKEN \
    --catsub-key 9c636133839b978b686bbc952fbd5dc41d5cd087 \
    --subcategory-key ae55145d60840de457ff9e785eba68f0b39ab777 \
    --sync-key 98ec4970ff4f9f9cc17926d27675eee823a4eb86 \
    --sync-yes-id 83 \
    --category-field-id 26 \
    --filter-id 1234 \
    --batch-size 50 \
    --dry-run

Requirements:
  pip install requests

Notes:
- If you omit --category-field-id, the script will GET /productFields and auto-detect the
  Category field by key == "category".
- If you omit --filter-id, it will iterate over all products (paged) and filter client-side.
- --dry-run prints what would change but does not write.
"""

import argparse
import os
import sys
import time
from typing import Dict, Any, Optional, List, Tuple

import requests

API_BASE = "https://{domain}/api/v1"

def backoff_sleep(attempt: int):
    # Exponential backoff with jitter
    delay = min(60, (2 ** attempt)) + (0.1 * attempt)
    time.sleep(delay)

def pd_call(domain: str, api_token: str, method: str, path: str,
            params: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
            retries: int = 5) -> Dict[str, Any]:
    url = API_BASE.format(domain=domain) + path
    params = dict(params or {})
    params["api_token"] = api_token
    headers = {"Accept": "application/json"}
    if json is not None:
        headers["Content-Type"] = "application/json"

    for attempt in range(retries + 1):
        resp = requests.request(method, url, params=params, json=json, headers=headers, timeout=30)
        if resp.status_code in (429, 500, 502, 503, 504):
            if attempt < retries:
                backoff_sleep(attempt + 1)
                continue
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            raise
        if resp.ok and (isinstance(data, dict) and data.get("success", True)):
            return data
        # If strict_mode surfaces errors, return them
        if attempt < retries:
            backoff_sleep(attempt + 1)
            continue
        # Final failure
        raise RuntimeError(f"Pipedrive API error {resp.status_code}: {data}")
    raise RuntimeError("Unreachable")

def get_category_mapping(domain: str, token: str, category_field_id: Optional[int]) -> Tuple[int, Dict[str, str]]:
    """Return (field_id, {id_str: label}) for the Product Category enum."""
    if category_field_id is not None:
        data = pd_call(domain, token, "GET", f"/productFields/{category_field_id}")
        fld = data.get("data") or {}
        opts = fld.get("options") or []
        mapping = {str(o["id"]): o.get("label", "") for o in opts if "id" in o}
        return fld.get("id", category_field_id), mapping

    # Auto-detect by key == 'category'
    pf = pd_call(domain, token, "GET", "/productFields")
    for fld in pf.get("data", []):
        if fld.get("key") == "category":
            opts = fld.get("options") or []
            mapping = {str(o["id"]): o.get("label", "") for o in opts if "id" in o}
            return fld.get("id"), mapping
    raise RuntimeError("Could not find Product 'category' field in /productFields. Pass --category-field-id explicitly.")

def clean_piece(s: Any) -> str:
    """Trim and replace ':' with '-' to avoid nested separators."""
    txt = ("" if s is None else str(s)).strip()
    return txt.replace(":", "-")

def build_catsub(cat_id: Any, sub_value: Any, cat_map: Dict[str, str]) -> Optional[str]:
    if cat_id in (None, "", 0, "0"):
        return None
    label = cat_map.get(str(cat_id), "").strip()
    if not label:
        # Unknown category ID; we can still return the id as a string or skip
        label = str(cat_id).strip()
    parent = clean_piece(label)
    child = clean_piece(sub_value)
    if child:
        return f"{parent}:{child}"
    return parent

def determine_item_types(product_code: Any, service_id: int, noninventory_id: int, 
                        service_ps_id: int, noninventory_ps_id: int) -> tuple[int, int]:
    """Determine both QBO item type and Product/Service type based on product code"""
    if not product_code:
        return noninventory_id, noninventory_ps_id  # Default to NonInventory if no code
    
    code = str(product_code).strip().upper()
    if code.startswith("SVC"):
        return service_id, service_ps_id
    else:
        return noninventory_id, noninventory_ps_id

def should_skip(product: Dict[str, Any],
                catsub_key: str,
                desired_value: str,
                sync_key: Optional[str],
                sync_yes_id: Optional[int]) -> bool:
    # Skip if already equal
    current = product.get(catsub_key)
    if isinstance(current, str) and current.strip() == desired_value:
        return True
    # Skip if Sync == Yes (avoid waking SyncQ logic downstream)
    if sync_key and (str(product.get(sync_key, "")).strip() == str(sync_yes_id)):
        return True
    return False

def iter_products(domain: str, token: str, filter_id: Optional[int], batch_size: int):
    start = 0
    while True:
        params = {"limit": batch_size, "start": start}
        if filter_id is not None:
            params["filter_id"] = filter_id
        data = pd_call(domain, token, "GET", "/products", params=params)
        items = data.get("data") or []
        if not items:
            break
        for it in items:
            yield it
        # Paging
        addl = data.get("additional_data", {})
        more = addl.get("pagination", {}).get("more_items_in_collection", False)
        if not more:
            break
        start = addl.get("pagination", {}).get("next_start", start + batch_size)

def main():
    ap = argparse.ArgumentParser(description="Backfill Pipedrive Cat:Sub custom field from Category enum + Subcategory text.")
    ap.add_argument("--domain", required=True, help="Company domain, e.g. tlciscreative.pipedrive.com")
    ap.add_argument("--api-token", default=os.getenv("PIPEDRIVE_API_TOKEN"), required=False, help="Pipedrive API token")
    ap.add_argument("--catsub-key", required=True, help="Custom field key for QBO-Category:Subcategory (text)")
    ap.add_argument("--subcategory-key", required=True, help="Custom field key for your Subcategory (text)")
    ap.add_argument("--sync-key", required=True, help="Custom field key for Sync to QuickBooks (enum) - now required to set Sync field")
    ap.add_argument("--sync-yes-id", type=int, required=True, help="Option ID that represents 'Yes' for the Sync field - now required to set Sync field")
    ap.add_argument("--qbo-itemtype-key", required=True, help="Custom field key for QuickBooks Item Type (enum)")
    ap.add_argument("--service-id", type=int, required=True, help="Option ID for 'Service' in QuickBooks Item Type field")
    ap.add_argument("--noninventory-id", type=int, required=True, help="Option ID for 'NonInventory' in QuickBooks Item Type field")
    ap.add_argument("--product-service-key", required=True, help="Custom field key for Product/Service (enum)")
    ap.add_argument("--service-ps-id", type=int, required=True, help="Option ID for 'Service' in Product/Service field")
    ap.add_argument("--noninventory-ps-id", type=int, required=True, help="Option ID for 'Non-inventory' in Product/Service field")
    ap.add_argument("--category-field-id", type=int, help="Product field id for Category enum (optional; will auto-detect if omitted)")
    ap.add_argument("--filter-id", type=int, help="Pipedrive product filter_id to limit scope (recommended)")
    ap.add_argument("--product-ids", help="Comma-separated list of specific product IDs to update")
    ap.add_argument("--product-names", help="Comma-separated list of specific product names to update")
    ap.add_argument("--batch-size", type=int, default=50, help="Page size for listing products (default 50)")
    ap.add_argument("--max", type=int, default=0, help="Max products to process (0 = no limit)")
    ap.add_argument("--require-subcategory", action="store_true", help="Skip if Subcategory value is empty")
    ap.add_argument("--dry-run", action="store_true", help="Compute and print changes but do not write")
    args = ap.parse_args()

    if not args.api_token:
        print("Missing --api-token or PIPEDRIVE_API_TOKEN env var", file=sys.stderr)
        sys.exit(2)

    # Fetch Category mapping
    cat_field_id, cat_map = get_category_mapping(args.domain, args.api_token, args.category_field_id)
    if not cat_map:
        print(f"[WARN] Category field {cat_field_id} has no options; will fall back to raw IDs", file=sys.stderr)

    processed = 0
    updated = 0
    skipped_equal = 0
    skipped_sync_yes = 0
    skipped_missing_sub = 0
    errors = 0

    # Parse specific product filters
    target_ids = set()
    target_names = set()
    if args.product_ids:
        target_ids = set(int(x.strip()) for x in args.product_ids.split(',') if x.strip())
    if args.product_names:
        target_names = set(x.strip() for x in args.product_names.split(',') if x.strip())
    
    for prod in iter_products(args.domain, args.api_token, args.filter_id, args.batch_size):
        pid = prod.get("id")
        product_name = prod.get("name", "")
        
        # Skip if we have specific filters and this product doesn't match
        if target_ids and pid not in target_ids:
            continue
        if target_names and product_name not in target_names:
            continue
            
        cat_id = prod.get("category")
        sub_val = prod.get(args.subcategory_key)
        product_code = prod.get("code")  # Get the product code for item type determination
        
        if args.require_subcategory and not (isinstance(sub_val, str) and sub_val.strip()):
            skipped_missing_sub += 1
            continue

        catsub = build_catsub(cat_id, sub_val, cat_map)
        if not catsub:
            # No category; nothing to do
            continue
        
        # Determine both QBO item type and Product/Service type based on product code
        qbo_item_type_id, ps_item_type_id = determine_item_types(
            product_code, args.service_id, args.noninventory_id, 
            args.service_ps_id, args.noninventory_ps_id
        )
        # Always process - we want to set all fields regardless of current values

        processed += 1
        qbo_type_name = "Service" if qbo_item_type_id == args.service_id else "NonInventory"
        ps_type_name = "Service" if ps_item_type_id == args.service_ps_id else "Non-inventory"
        print(f"[{processed}] Product {pid}: {prod.get('name','(no name)')} -> {catsub} (QBO: {qbo_type_name}, PS: {ps_type_name})")
        
        if args.dry_run:
            print(f"DRY RUN - Would update with body:")
            print(f"  {args.catsub_key}: {catsub}")
            print(f"  {args.qbo_itemtype_key}: {qbo_item_type_id}")
            print(f"  {args.product_service_key}: {ps_item_type_id}")
            print(f"  {args.sync_key}: {args.sync_yes_id}")
            continue

        try:
            # Set CatSub field, QBO Item Type, Product/Service, and Sync field (LAST) in one update
            body = {
                args.catsub_key: catsub,
                args.qbo_itemtype_key: qbo_item_type_id,  # Set QBO Item Type based on product code
                args.product_service_key: ps_item_type_id,  # Set Product/Service based on product code
                args.sync_key: args.sync_yes_id  # Set Sync to QuickBooks to "Yes" (83) - LAST!
            }
            response = pd_call(args.domain, args.api_token, "PUT", f"/products/{pid}",
                        params={"strict_mode": 1, "return_item": 1}, json=body)
            updated += 1
        except Exception as e:
            errors += 1
            print(f"[ERROR] Failed to update product {pid}: {e}", file=sys.stderr)

        if args.max and updated >= args.max:
            break

    print("\n=== Summary ===")
    print(f"Processed:         {processed}")
    print(f"Updated:           {updated}")
    print(f"Skipped equal:     {skipped_equal}")
    if args.sync_key and args.sync_yes_id is not None:
        print(f"Skipped Sync=Yes:  {skipped_sync_yes}")
    if args.require_subcategory:
        print(f"Skipped no sub:    {skipped_missing_sub}")
    print(f"Errors:            {errors}")

if __name__ == "__main__":
    main()
