# Manual Webhook + Address Test Guide

Use this when you have **new Person, new Org, new Deal** in Pipedrive and want to test the webhook (with address) **without** promoting the deal to quote stage. You hand the payload to the webhook manually, then check handler → Quoter address book → fix errors → then run automation.

---

## What you need from me (checklist)

Before sending the manual POST, collect these from Pipedrive and fill the payload.

### 1. From your new **Person**
- [ ] **Deal contact person name** (e.g. `Jane Test`)
- [ ] **Deal contact person email** (e.g. `jane.test@example.com`)

### 2. From your new **Organization**
- [ ] **Org ID** (e.g. `12345`)
- [ ] **Organization name** (must end with `-DEAL_ID` for deal-ID fallback, e.g. `Test Company-99999`)
- [ ] **HID-QBO-Status** = `289` (or `QBO-SubCust`) so the handler doesn’t ignore the webhook
- [ ] **Organization address (house number)** (e.g. `8070`)
- [ ] **Organization address route** (e.g. `Webb Avenue`)
- [ ] **Organization address apartment/suite no** (optional, e.g. `Suite 100` or leave blank)
- [ ] **Organization city/town/village/locality** (e.g. `Los Angeles`)
- [ ] **Organization address state/county** (e.g. `CA` or `California`)
- [ ] **Organization address postal code** (e.g. `91605`)
- [ ] **Organization address country** (e.g. `United States` or `US`)

### 3. From your new **Deal**
- [ ] **Deal ID** (e.g. `99999` – must match the number at the end of org name if you use `Name-99999`)
- [ ] **Deal title** (e.g. `Test Quote Deal`)
- [ ] **Quote Template** value (e.g. `454` or the enum ID for your template)

### 4. Webhook URL
- [ ] **Local:** `http://localhost:8000/webhook/pipedrive/organization` (or whatever port you use)
- [ ] **Render:** `https://YOUR-SERVICE.onrender.com/webhook/pipedrive/organization`

---

## Payload template (JSON)

Copy this and replace the placeholder values with what you collected. **Important:** Use the **exact** key names below (including the long custom field IDs).

```json
{
  "{{organization.id}}": "YOUR_ORG_ID",
  "{{organization.name}}": "YOUR_ORG_NAME",
  "{{organization.454a3767bce03a880b31d78a38c480d6870e0f1b}}": "289",
  "{{deal.id}}": "YOUR_DEAL_ID",
  "{{deal.title}}": "YOUR_DEAL_TITLE",
  "{{deal.person_name}}": "YOUR_PERSON_NAME",
  "{{person.email}}": "YOUR_PERSON_EMAIL",
  "{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}": "YOUR_TEMPLATE_ENUM",
  "{{organization.address_street_number}}": "YOUR_STREET_NUMBER",
  "{{organization.address_route}}": "YOUR_STREET_NAME",
  "{{organization.address_subpremise}}": "YOUR_SUITE_OR_EMPTY",
  "{{organization.address_locality}}": "YOUR_CITY",
  "{{organization.address_admin_area_level_1}}": "YOUR_STATE",
  "{{organization.address_postal_code}}": "YOUR_ZIP",
  "{{organization.address_country}}": "YOUR_COUNTRY"
}
```

Example with sample data:

```json
{
  "{{organization.id}}": "99123",
  "{{organization.name}}": "Manual Test Org-99999",
  "{{organization.454a3767bce03a880b31d78a38c480d6870e0f1b}}": "289",
  "{{deal.id}}": "99999",
  "{{deal.title}}": "Manual Test Deal",
  "{{deal.person_name}}": "Jane Test",
  "{{person.email}}": "jane.test@example.com",
  "{{deal.42ab0c919271cb24f3587f0b01ea2af166019c8d}}": "454",
  "{{organization.address_street_number}}": "8070",
  "{{organization.address_route}}": "Webb Avenue",
  "{{organization.address_subpremise}}": "",
  "{{organization.address_locality}}": "Los Angeles",
  "{{organization.address_admin_area_level_1}}": "CA",
  "{{organization.address_postal_code}}": "91605",
  "{{organization.address_country}}": "United States"
}
```

---

## Send the request (curl)

**Local (from your machine):**
```bash
curl -X POST http://localhost:8000/webhook/pipedrive/organization \
  -H "Content-Type: application/json" \
  -d @payload.json
```

Or paste JSON inline:
```bash
curl -X POST http://localhost:8000/webhook/pipedrive/organization \
  -H "Content-Type: application/json" \
  -d '{"{{organization.id}}":"99123","{{organization.name}}":"Manual Test Org-99999", ...}'
```

**Render:** Replace the URL with your Render webhook URL and use the same `-H` and `-d` (or `-d @payload.json`).

Save your payload to a file (e.g. `payload.json`) and run:
```bash
curl -X POST https://YOUR-SERVICE.onrender.com/webhook/pipedrive/organization \
  -H "Content-Type: application/json" \
  -d @payload.json
```

---

## Step 1: Check the webhook (sweep – did we grab data or error?)

1. **HTTP response**
   - `200` + body like `{"status":"success","quote_id":"...","organization_id":"...","deal_id":"..."}` → handler ran and created a quote.
   - `200` + `{"status":"ignored","reason":"..."}` → handler ran but skipped (e.g. not_ready_for_quotes, already_processed).
   - `400` / `404` / `500` → error; check response body and logs.

2. **Logs (local or Render)**
   - Look for: “Received JSON webhook”, “DEBUG: organization_data”, “Person name from webhook”, “Minimal contact created”, “Successfully created quote”.
   - Look for errors: “No organization ID”, “No deal ID”, “Failed to create contact”, “Quote creation failed”.
   - Confirm address is present: logs should show address being built (e.g. flat_address, flat_city, etc.) and passed into contact creation.

3. **If there are errors**
   - Fix payload (missing keys, wrong custom field IDs, org name not `Name-DealID`).
   - Fix code if handler or quoter is wrong (then re-run the same curl).

---

## Step 2: Check Quoter address book

1. In Quoter, open **Address book** (or Contacts).
2. Find the contact you created (e.g. **Jane Test**, org **Manual Test Org-99999**).
3. Open the contact and verify:
   - **Billing address:** street line 1 (and 2 if you sent subpremise), city, state, zip, country match what you sent.
   - **Shipping address:** same if you’re mirroring (current behavior).
4. If anything is wrong (missing, wrong field, wrong format), note it and fix in code or payload, then re-run Step 1 and check again.

---

## Step 3: If all OK – clean up and run automation

1. **Delete the test contact** in Quoter (so the real automation doesn’t think it’s a duplicate or leave test data).
2. **Optional:** Remove the test org:deal from `processed_organizations.txt` (in the project root where the webhook runs) so the same org/deal can be processed again by the real automation if you want:
   - Line to remove looks like: `99123:99999` (or whatever org_id:deal_id you used).
3. **Run the automation:** In Pipedrive, promote the deal to the quote stage so the real webhook fires and the full flow runs.

---

## Notes

- **processed_organizations.txt:** The first time you send a given `organization_id:deal_id`, the handler will add it to this file. For a second manual test with the **same** org/deal IDs, either remove that line or use different IDs.
- **HID-QBO-Status:** Must be `289` or `QBO-SubCust` or the handler returns `200` with `reason: not_ready_for_quotes`.
- **Org name and deal ID:** If you don’t send `{{deal.id}}`, the handler derives deal ID from the org name (e.g. `Manual Test Org-99999` → `99999`). So org name should end with `-DEAL_ID`.
- **Country:** Quoter often expects a country code (e.g. `US`). If you send `United States` and Quoter rejects or normalizes it, switch to `US` in the payload.
