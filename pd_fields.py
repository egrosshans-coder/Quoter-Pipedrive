"""
pd_fields.py — Pipedrive v1 dealFields resource wrapper.

ADDITIVE MODULE. Transport + resource wrappers only, no business logic, per
DECISIONS D-003/D-004. Does not import or modify pipedrive.py, so it cannot
affect the running sync.

Pipedrive v1 (base https://api.pipedrive.com/v1), auth: api_token query param.
  GET  /dealFields              list all fields
  GET  /dealFields/{id}         one field, including its options
  PUT  /dealFields/{id}         replace the options array
  POST /dealFields              create a field
  DELETE /dealFields/{id}       delete a field

WHY OPTION WRITES GO THROUGH PUT
--------------------------------
There is no POST /dealFields/{id}/options route. Confirmed live 2026-08-23:

    404 "Route POST:/v1/dealFields/90/options not found"

(sync_templates_to_pipedrive.py, Jan 2026, is built on that route and has
therefore never worked.)

The supported path is PUT /dealFields/{id} with the COMPLETE options array.
This carries a real hazard: a deal stores the option's numeric ID, not its
label. Omit an existing option's id from the array and Pipedrive may reassign
it — silently repointing every deal that referenced it.

So `set_options` REQUIRES that every pre-existing option be passed with its
id, and verifies afterwards that no id changed meaning. Verified safe on a
scratch field 2026-08-23: ids 499/500 kept their labels, 501 was added.

The client is imported lazily so tests can inject a fake with no token.
"""

import os

BASE_URL_V1 = "https://api.pipedrive.com/v1"


class PipedriveV1Client:
    """Transport only. api_token goes in the query string, as pipedrive.py does."""

    def __init__(self, api_token=None, base_url=BASE_URL_V1):
        import requests
        self.api_token = api_token or os.getenv("PIPEDRIVE_API_TOKEN")
        if not self.api_token:
            raise ValueError("Missing PIPEDRIVE_API_TOKEN")
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def _request(self, method, path, params=None, data=None):
        p = dict(params or {})
        p["api_token"] = self.api_token
        r = self.session.request(method, f"{self.base_url}/{path.lstrip('/')}",
                                 params=p, json=data, timeout=30)
        r.raise_for_status()
        return r.json() if r.text else None

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, data=None):
        return self._request("POST", path, data=data)

    def put(self, path, data=None):
        return self._request("PUT", path, data=data)

    def delete(self, path):
        return self._request("DELETE", path)


class OptionIdDrift(Exception):
    """Raised when a write would change what an existing option id means."""


class PipedriveFields:
    def __init__(self, client=None):
        if client is None:
            client = PipedriveV1Client()
        self.client = client

    # ---- reads -----------------------------------------------------------

    def list_deal_fields(self):
        return (self.client.get("/dealFields") or {}).get("data") or []

    def get_deal_field(self, field_id):
        return (self.client.get(f"/dealFields/{field_id}") or {}).get("data")

    def get_options(self, field_id):
        """[{id, label}, ...] for an enum/set field."""
        return (self.get_deal_field(field_id) or {}).get("options") or []

    def option_map(self, field_id):
        """{option_id(str): label}. This is what a consumer needs at runtime:
        a webhook carries the option id, never the label."""
        return {str(o["id"]): o.get("label") for o in self.get_options(field_id)}

    def find_field_by_key(self, key):
        return next((f for f in self.list_deal_fields()
                     if f.get("key") == key), None)

    # ---- writes ----------------------------------------------------------

    def set_options(self, field_id, options, verify=True):
        """PUT the full options array.

        `options` must be the COMPLETE desired list. Pre-existing entries must
        carry their `id`; new entries carry only `label`.

        Verifies afterwards that every id present before the call still maps to
        the same label, and raises OptionIdDrift if not — the failure mode that
        would corrupt historical deals.
        """
        before = {str(o["id"]): o.get("label") for o in self.get_options(field_id)}

        sent_ids = {str(o["id"]) for o in options if o.get("id") is not None}
        dropped = set(before) - sent_ids
        if dropped:
            raise ValueError(
                f"refusing: options {sorted(dropped)} exist on field {field_id} "
                f"but were not included. Omitting an existing option removes it, "
                f"orphaning any deal that stores its id. Pass every existing "
                f"option with its id, or remove it deliberately in the UI."
            )

        self.client.put(f"/dealFields/{field_id}", data={"options": options})

        if not verify:
            return self.get_options(field_id)

        after = {str(o["id"]): o.get("label") for o in self.get_options(field_id)}
        drift = {i: (before[i], after.get(i)) for i in before
                 if after.get(i) != before[i]}
        if drift:
            raise OptionIdDrift(
                f"field {field_id}: option ids changed meaning: {drift}. "
                f"Deals referencing these ids now resolve to different values."
            )
        return [{"id": k, "label": v} for k, v in after.items()]

    def add_option(self, field_id, label):
        """Append one label, preserving every existing option id."""
        current = self.get_options(field_id)
        if any((o.get("label") or "").strip().lower() == label.strip().lower()
               for o in current):
            return None                      # already present; nothing to do
        payload = [{"id": o["id"], "label": o["label"]} for o in current]
        payload.append({"label": label})
        after = self.set_options(field_id, payload)
        known = {str(o["id"]) for o in current}
        return next((o for o in after if str(o["id"]) not in known), None)

    def rename_option(self, field_id, option_id, new_label):
        """Change a label while keeping its id — so deals keep resolving."""
        current = self.get_options(field_id)
        if not any(str(o["id"]) == str(option_id) for o in current):
            raise ValueError(f"option {option_id} not on field {field_id}")
        payload = [{"id": o["id"],
                    "label": new_label if str(o["id"]) == str(option_id)
                    else o["label"]}
                   for o in current]
        # A rename is an intentional change of meaning, so id-drift
        # verification is skipped for this one call.
        return self.set_options(field_id, payload, verify=False)

    # ---- field lifecycle (used for scratch fields in testing) ------------

    def create_enum_field(self, name, labels):
        body = {"name": name, "field_type": "enum",
                "options": [{"label": l} for l in labels]}
        return (self.client.post("/dealFields", data=body) or {}).get("data")

    def delete_field(self, field_id):
        return self.client.delete(f"/dealFields/{field_id}")
