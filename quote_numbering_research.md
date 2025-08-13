# Quote Numbering Research for Quoter API

## Current Implementation
The current `create_draft_quote` function only sets basic fields:
- `title`
- `status` (draft)
- `pipedrive_deal_id`
- `organization_name`

## Research Questions
1. **Can we set a custom quote number during creation?**
2. **What fields are available in the Quoter API for quotes?**
3. **Can we modify a quote after creation to set the number?**
4. **Is there a way to use Pipedrive deal ID as the quote number?**

## Potential Solutions

### Option 1: Custom Quote Number During Creation
Check if Quoter API supports:
```json
{
  "title": "Quote Title",
  "status": "draft",
  "quote_number": "PD-2096",  // Custom number using deal ID
  "pipedrive_deal_id": "2096",
  "organization_name": "Org Name"
}
```

### Option 2: Modify Quote After Creation
1. Create quote with basic data
2. Immediately update it with custom quote number
3. Use PATCH endpoint to modify quote fields

### Option 3: Use Deal ID as Quote Number
- Format: "PD-{deal_id}" (e.g., "PD-2096")
- This would create a clear link between Pipedrive and Quoter
- Easy to track and reference

## Next Steps
1. Test if `quote_number` field is supported in quote creation
2. Check if quotes can be modified after creation
3. Implement custom numbering system if supported
4. Fall back to basic creation if not supported

## Benefits of Custom Numbering
- **Clear tracking**: PD-2096 immediately shows it's from Pipedrive deal 2096
- **Professional appearance**: Better than auto-generated numbers
- **Easy reference**: Sales team can quickly identify quote source
- **Audit trail**: Clear connection between systems
