# ARCHITECTURAL DECISIONS

**Version:** 1.0  
**Last Updated:** 2026-06-30

---

# Purpose

This document records the major architectural decisions made during the Quoter-Pipedrive project.

Unlike status documents, architectural decisions are intended to remain stable over time.

Each decision records an engineering principle that guides future development.

---

# D-001 — Maintain the Legacy Quoter API

**Decision**

Continue using `quoter.py` until the ScalePad API reaches functional parity.

**Reason**

Draft Quote creation and other legacy capabilities are not yet available through the ScalePad API.

---

# D-002 — Adopt a Dual-Client Architecture

**Decision**

Maintain two independent API clients.

```
quoter.py
```

and

```
scalepad_v2.py
```

**Reason**

Both APIs currently provide unique functionality.

Neither API completely replaces the other.

---

# D-003 — Separate Transport from Business Logic

**Decision**

`scalepad_v2.py` contains only:

- Authentication
- HTTP transport
- Resource wrapper methods

Business logic belongs in higher-level service modules.

**Reason**

Separating responsibilities improves maintainability and simplifies future migration.

---

# D-004 — ScalePad SDK Evolution

**Decision**

`scalepad_v2.py` will evolve into TLC's internal ScalePad SDK.

Responsibilities include:

- Generic HTTP methods
- Resource wrappers
- Common request handling

Business workflows remain outside the SDK.

**Reason**

The SDK becomes the reusable foundation for all future ScalePad development.

---

# D-005 — Incremental Migration

**Decision**

Migration from the Legacy Quoter API occurs incrementally.

Legacy functionality will only be removed after equivalent ScalePad functionality has been verified.

**Reason**

Production stability has priority over migration speed.

---

# D-006 — Investigation Before Implementation

**Decision**

Endpoints are investigated and verified before wrapper methods are written.

**Reason**

Avoids unnecessary implementation and ensures wrappers are based upon verified behavior.

---

# D-007 — Documentation Before Implementation

**Decision**

Major architectural discoveries should be documented before implementation whenever practical.

**Reason**

Project knowledge should be preserved independently of conversation history.

Documentation captures the reasoning behind implementation decisions.

---

# D-008 — Browser Investigation as an Engineering Tool

**Decision**

Chrome Developer Tools is the preferred method for understanding undocumented Quoter behavior.

Primary investigation areas include:

- Network traffic
- XHR / Fetch requests
- Embedded payloads
- HTML
- JavaScript

**Reason**

Browser behavior represents the authoritative implementation when public APIs do not expose required functionality.

---

# D-009 — Quoter is the Source of Truth for Templates

**Decision**

Quote templates will not be maintained manually in Python.

Quoter Templates become the authoritative source.

ScalePad Item Groups become the synchronized operational mirror.

**Reason**

This eliminates hard-coded template definitions while allowing automatic synchronization of template changes.

---

# D-010 — Investigation-First Development

**Decision**

Project development follows the sequence:

```
Investigate
        │
        ▼
Understand
        │
        ▼
Design
        │
        ▼
Document
        │
        ▼
Implement
        │
        ▼
Test
        │
        ▼
Commit
```

**Reason**

Architectural understanding should always precede implementation.

This reduces rework and preserves engineering knowledge.

---

# Decision Lifecycle

Architectural decisions remain in this document permanently.

If a decision changes, it should not be deleted.

Instead:

- Record a new decision.
- Reference the superseded decision.
- Explain why the architecture evolved.

This preserves the historical reasoning behind the project.
