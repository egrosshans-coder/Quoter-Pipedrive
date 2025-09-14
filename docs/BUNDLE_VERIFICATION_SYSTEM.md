# Bundle Verification System

## Overview
The Bundle Verification System automatically monitors template bundles against the Quoter API to detect changes in item names, SKUs, prices, and types. This ensures data consistency and alerts the team when manual updates are needed.

## System Components

### 1. Verification Script (`verify_bundles.py`)
**Purpose**: Clean Python script for GitHub Actions workflow
**Function**: Calls verification functions from template mapping system
**Usage**: Executed by GitHub Actions twice daily

### 2. Template Mapping Functions (`template_mapping_enhanced.py`)
**Functions**:
- `verify_bundle_against_quoter()` - Main verification logic
- `update_bundle_from_quoter()` - Update bundles with live data
- `get_template_bundle()` - Retrieve template bundle data

### 3. GitHub Actions Workflow (`.github/workflows/daily-bundle-verification.yml`)
**Schedule**: 
- 2 AM PT (10 AM UTC) - Daily morning check
- 2 PM PT (10 PM UTC) - Daily afternoon check
**Triggers**: Automatic schedule + manual trigger
**Environment**: Ubuntu latest with Python 3.9

## Verification Process

### What Gets Verified
1. **Item Names**: Compare stored names with Quoter API
2. **SKUs/Item Codes**: Verify unique identifiers
3. **Prices**: Check `price_decimal` values
4. **Types**: Validate item categories
5. **Availability**: Confirm items still exist in Quoter

### Verification Results
- **Items Verified**: Successfully checked against API
- **Items Changed**: Differences detected
- **Items Not Found**: Items missing from Quoter
- **Items Unchanged**: No differences found

### Change Detection
The system identifies:
- **Name Changes**: Item names updated in Quoter
- **Price Changes**: Price modifications
- **Type Changes**: Category updates
- **SKU Changes**: Item code modifications
- **Missing Items**: Items removed from Quoter

## GitHub Actions Integration

### Workflow Steps
1. **Checkout Code**: Get latest repository code
2. **Setup Python**: Install Python 3.9 environment
3. **Install Dependencies**: Install required packages
4. **Run Verification**: Execute bundle verification
5. **Create Issues**: Generate GitHub issues for changes

### Environment Variables
- `QUOTER_CLIENT_ID`: Quoter API client ID
- `QUOTER_CLIENT_SECRET`: Quoter API client secret
- `QUOTER_REDIRECT_URI`: OAuth redirect URI
- `QUOTER_REFRESH_TOKEN`: API refresh token

### Issue Creation
When changes are detected:
- **Title**: "Bundle Verification Alert - Changes Detected"
- **Labels**: `automation`, `bundle-verification`
- **Body**: Detailed change information and next steps

## Manual Verification

### Running Locally
```bash
# Activate virtual environment
source venv/bin/activate

# Run verification script
python3 verify_bundles.py
```

### Verification Modes
1. **Verify Mode**: Check for changes only
2. **Dry Run Mode**: Show changes without updating
3. **Live Update Mode**: Update bundles with live data

### Template Selection
Currently verifies:
- **floating-video** template (primary focus)
- Can be extended to all 11 templates

## Maintenance

### Regular Tasks
- **Monitor Issues**: Check GitHub issues for verification alerts
- **Review Changes**: Assess if changes require bundle updates
- **Update Bundles**: Modify template mapping when needed
- **Test Changes**: Verify updates work correctly

### Troubleshooting
- **API Errors**: Check Quoter API credentials
- **Missing Items**: Verify items still exist in Quoter
- **Price Discrepancies**: Confirm pricing changes are intentional
- **Workflow Failures**: Check GitHub Actions logs

## Benefits

### Automation
- **Daily Monitoring**: Automatic twice-daily checks
- **Change Detection**: Immediate alerts for modifications
- **Issue Tracking**: GitHub issues for change management
- **Consistency**: Ensures data accuracy across systems

### Quality Assurance
- **Data Integrity**: Maintains bundle accuracy
- **Price Validation**: Confirms correct pricing
- **Item Verification**: Ensures items exist in Quoter
- **Change Tracking**: Documents all modifications

## Future Enhancements

### Planned Features
- **Multi-Template Verification**: Extend to all 11 templates
- **Automated Updates**: Auto-update bundles for minor changes
- **Email Notifications**: Send alerts to team members
- **Change History**: Track all verification results over time

### Integration Opportunities
- **Slack Notifications**: Send alerts to team channels
- **Dashboard**: Web interface for verification status
- **Reporting**: Weekly/monthly verification reports
- **API Endpoints**: REST API for verification status

---

**Last Updated**: September 14, 2025
**Version**: 1.0
**Status**: Production Ready
