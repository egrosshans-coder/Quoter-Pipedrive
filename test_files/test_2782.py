from scalepad_v2 import ScalePadV2Client
import json
c = ScalePadV2Client()
# 'contains' may surface ambiguous matches that eq: suppressed
for p in ["/quoter/v1/contacts?filter[billing_email]=cont:2782@gmail.com",
          "/quoter/v1/contacts?filter[billing_email]=cont:2782",
          "/quoter/v1/contacts?filter[billing_organization]=cont:zz34"]:
    print("="*60); print("GET", p)
    try:
        r = c.get(p)
        rows = r.get("data", [])
        print(f"  rows={len(rows)} total={r.get('total_count')}")
        for x in rows[:10]:
            print(f"    email={x.get('billing_email')!r} org={x.get('billing_organization')!r} "
                  f"client={x.get('client')} id={x.get('id')}")
    except Exception as e:
        print("  ✗", str(e)[:150])
