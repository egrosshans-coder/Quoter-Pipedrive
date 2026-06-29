# SCALEPAD_MIGRATION_STATUS

## Purpose
Engineering reference for the ScalePad migration.

## Architecture
- quoter.py = Legacy Quoter API (quote creation remains here).
- scalepad_v2.py = Generic ScalePad HTTP client.
- Dual-client architecture is intentional.

## Principles
- Documentation first.
- Incremental migration.
- Separate transport from business logic.
- Preserve production stability.

## Verified
- Python 3.14.6
- OpenSSL 3.6.2
- GET /quoter/v1/quote-templates
- GET /quoter/v1/quotes

## Documented Endpoints
Quoter: quotes, quote-templates, items, categories, line-items, item-group-item-assignments
Core: service/clients, service/contracts, contacts/{id}
Lifecycle Manager: contracts

## Known Limitations
- Quote creation remains on legacy API.
- Content Blocks not found in public API.

## Next Steps
Continue endpoint inventory and wrapper implementation.
