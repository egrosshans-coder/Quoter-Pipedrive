from scalepad_v2 import ScalePadV2Client
import json
c = ScalePadV2Client()
email = "zz50@gmail.com"
token = "3Eh296BLe8eTLzrUYuEISqP1Fxw"   # from /admin/clients/dashboard/<token>
path = f"/quoter/v1/contacts?filter[billing_email]=eq:{email}&filter[client.id]=eq:{token}"
print("GET", path)
try:
    r = c.get(path)
    rows = r.get("data", [])
    print(f"rows={len(rows)}")
    for x in rows:
        print("  id:", x.get("id"), " client:", x.get("client"))
    if rows: print(json.dumps(rows[0], indent=2)[:1200])
except Exception as e:
    print("✗", str(e)[:300])
