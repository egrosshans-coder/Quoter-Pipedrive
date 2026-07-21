# Template Synchronization Strategy

**Version:** 1.0  
**Status:** Active Investigation  
**Last Updated:** 2026-06-30

---

# Purpose

The original Quoter-Pipedrive integration maintained template definitions in Python (`template_mapping_enhanced.py`) because neither the Legacy Quoter API nor the ScalePad API exposed the contents of Quoter quote templates.

Recent investigation has revealed a new architectural approach that eliminates the need to maintain template definitions manually.

The long-term objective is to synchronize Quoter Templates into ScalePad Item Groups on a scheduled basis, allowing Quoter to remain the authoritative source while ScalePad maintains an operational mirror used during quote creation.

---

# Background

## Legacy Quoter API

Responsibilities:

- Create Draft Quotes
- Legacy quote operations not yet available through the ScalePad API

Current limitation:

- Does not expose template line items.

---

## ScalePad API

Responsibilities:

- Quote Templates
- Items
- Item Groups
- Item Group Assignments
- Quotes
- Other documented resources

Current limitation:

- Does not expose template line items.

---

# Discovery

Investigation of the Quoter web application revealed that requesting:

```
https://tlciscreative.quoter.com/admin/quotes/create/<template-slug>
```

does not simply return HTML for rendering.

Instead, the browser receives a serialized template model containing the information required to build the quote editor.

Examples of discovered fields include:

- line_items
- part_number
- item_id
- supplier_sku
- description
- category_id
- pricing_category_id
- quantity
- taxable
- discountable
- section_id

Example:

```
part_number = BAL-FIL-001
```

This serialized payload becomes the candidate source of truth for synchronizing ScalePad Item Groups.

---

# Architectural Evolution

## Original Architecture

```
Pipedrive
      │
      ▼
template_mapping_enhanced.py
      │
      ▼
Legacy Quoter API
      │
      ▼
Draft Quote
```

Python contained the template definitions.

---

## New Architecture

```
Quoter Template
        │
        ▼
Serialized Template Payload
        │
        ▼
Nightly Synchronization
        │
        ▼
ScalePad Item Group
        │
        ▼
Draft Quote Creation
```

Quoter becomes the authoritative source.

ScalePad Item Groups become a synchronized operational mirror.

Python no longer maintains template definitions.

---

# Synchronization Workflow

## Step 1 – Authenticate

Authenticate to the Quoter web application.

Objective:

Establish a browser-equivalent authenticated session capable of requesting:

```
/admin/quotes/create/<template-slug>
```

This authentication is completely independent of both the Legacy Quoter API and the ScalePad API.

---

## Step 2 – Retrieve Template Payload

Request:

```
GET /admin/quotes/create/<template-slug>
```

Example:

```
/admin/quotes/create/balloons
```

Retrieve the server response.

The response contains the serialized template payload used by the browser.

---

## Step 3 – Sweep Template Payload

Extract every template line item.

Examples:

```
BAL-FIL-001
BAL-DRP-001
BAL-MOON-001
...
```

Primary synchronization key:

```
part_number
```

Additional metadata may include:

- Description
- Quantity
- Category
- Section
- Pricing
- Tax flags
- Additional template attributes

---

## Step 4 – Synchronize ScalePad Item Group

Using the ScalePad API:

- Create Item Group if missing.
- Update existing Item Group.
- Compare assignments.
- Add missing items.
- Remove obsolete items.

The Item Group becomes a synchronized mirror of the Quoter template.

---

## Step 5 – Nightly Synchronization

Repeat for every template.

```
Retrieve Template List
        │
        ▼
For Each Template
        │
        ▼
Authenticate
        │
        ▼
Retrieve Template Payload
        │
        ▼
Sweep Template Payload
        │
        ▼
Update Item Group
```

---

# Draft Quote Workflow

Quote creation continues to use the Legacy Quoter API.

```
Pipedrive
      │
Determine Template
      │
      ▼
Legacy Quoter API
Create Draft Quote
      │
      ▼
Lookup Matching Item Group
      │
      ▼
Retrieve Assigned Items
      │
      ▼
Populate Draft Quote
      │
      ▼
Sales Review
      │
      ▼
Publish
```

No template-specific Python mapping file is required.

---

# Benefits

Compared to `template_mapping_enhanced.py`:

- Quoter remains the source of truth.
- Python no longer stores template definitions.
- ScalePad Item Groups remain synchronized automatically.
- New template items require no code changes.
- Nightly synchronization keeps templates current.
- Cleaner architecture.
- Reduced long-term maintenance.
- Easier migration away from hard-coded template definitions.

---

# Remaining Investigation

The following items remain under investigation:

1. Browser authentication mechanism.
2. Exact format of the serialized template payload.
3. Reliable payload extraction.
4. Parser implementation.
5. Synchronization error handling.
6. Change detection strategy.
7. Automated nightly execution.

---

# Long-Term Vision

```
Authenticate
      │
      ▼
Retrieve Template Payload
      │
      ▼
Sweep Template Payload
      │
      ▼
Synchronize Item Group
      │
      ▼
Create Draft Quote
      │
      ▼
Populate Quote from Item Group
      │
      ▼
Publish Quote
```

This architecture removes the need to manually maintain template definitions in Python while continuing to leverage the Legacy Quoter API for draft quote creation until equivalent ScalePad functionality becomes available.

---

# Authentication Strategy (Investigation)

## Objective

The nightly synchronization process requires access to the Quoter web application.

Unlike the Legacy Quoter API and the ScalePad API, template retrieval occurs through the authenticated Quoter web interface.

Target URL:

```
https://tlciscreative.quoter.com/admin/quotes/create/<template-slug>
```

Example:

```
https://tlciscreative.quoter.com/admin/quotes/create/balloons
```

The objective is to retrieve the same serialized template payload received by the browser during manual quote creation.

---

# Three Independent Authentication Systems

## Legacy Quoter API

```
api.quoter.com
```

Authentication:

- OAuth
- API credentials

Purpose:

- Create draft quotes
- Legacy API operations

---

## ScalePad API

```
api.scalepad.com
```

Authentication:

- x-api-key

Purpose:

- Templates
- Items
- Item Groups
- Assignments
- Quotes

---

## Quoter Web Application

```
https://tlciscreative.quoter.com
```

Authentication:

- Browser session (under investigation)

Purpose:

- Quote editor
- Template editor
- Manual quote creation
- Template serialization

---

# Investigation Plan

The initial objective is **not** to automate login.

The objective is to understand how an authenticated browser communicates with the Quoter web application.

## Step 1

Open an authenticated browser session.

Navigate to:

```
/admin/quotes/create/<template-slug>
```

---

## Step 2

Open Chrome Developer Tools.

Use the Network tab.

Reload the page.

---

## Step 3

Inspect the initial request.

Record:

- Request URL
- Response status
- Request headers
- Response headers
- Cookies
- Redirects

---

## Step 4

Determine how the template payload is delivered.

Possible mechanisms include:

- Server-rendered HTML
- Embedded JavaScript
- Embedded JSON
- XML
- XHR
- Fetch

No assumptions should be made until confirmed.

---

## Step 5

Design an authentication strategy.

Only after understanding the browser session will a Python implementation be considered.

Potential approaches include:

- Reusing authenticated session cookies
- Programmatic login
- Session persistence
- Browser-equivalent authentication

The preferred solution will be the simplest approach that reliably reproduces the authenticated browser request.

---

# Current Assumptions

Current working assumptions include:

- Every template has a unique slug.
- The browser payload contains all information necessary to reconstruct the template.
- `part_number` is the preferred synchronization key.
- Quoter Templates remain the authoritative source.
- ScalePad Item Groups become TLC's synchronized operational mirror.
- Draft quote creation continues to use the Legacy Quoter API until ScalePad reaches feature parity.

These assumptions will be updated as additional investigation confirms or disproves them.

---

# Guiding Principle

The Quoter web application should be treated as the authoritative source for template composition.

The objective is **not** generic web scraping.

The objective is to reproduce the authenticated requests made by the Quoter web application in order to retrieve the template payload used by the browser and synchronize that information into ScalePad Item Groups.

---

# Discovery History

## 2026-06-30

Major discoveries:

- Public APIs do not expose template line items.
- `/admin/quotes/create/<template-slug>` is the primary investigation target.
- The browser receives a serialized template payload during page generation.
- ScalePad Item Groups can replace hard-coded Python template definitions.
- Browser authentication is the remaining major unknown before implementation.
- The project architecture has shifted from static template mappings to dynamic nightly synchronization.
