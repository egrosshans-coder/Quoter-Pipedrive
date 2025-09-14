# Cover Letter Procedure and Links

## Overview
This document outlines the complete cover letter system for the Quoter Sync project, including procedures, deployment options, and useful links.

## System Components

### 1. Cover Letter Editor (`cover_letter_editor.py`)
**Purpose**: Web-based interface for sales reps to modify cover letters
**Features**:
- Select from 11 different templates
- Live preview with sample data
- Field code help sidebar
- Save changes instantly
- Reset to original content

**Field Codes Available**:
- `{{person.first_name}}` - Contact's first name
- `{{deal.title}}` - Deal title from Pipedrive
- `{{deal.id}}` - Deal ID from Pipedrive
- `{{deal.owner_name}}` - Deal owner's name
- `{{quote.owner.name}}` - Quote owner's name
- `{{quote.owner.email}}` - Quote owner's email

**Dynamic Role Logic**:
- Maurice Capillaire → Sales and Logistics
- Jeff Ward → Sales and Logistics
- Eric Grosshans → Technical Director
- Others → Sales Team

### 2. Template Mapping System (`template_mapping_enhanced.py`)
**Purpose**: Contains all 11 templates with cover letter and appended content
**Templates**:
1. floating-video
2. balloons
3. co2-foggers
4. confetti-streamers
5. fireworks-pyro
6. led-lanyards
7. led-wristbands
8. basic
9. low-level-fog
10. robotics
11. tank-delivery

### 3. Bundle Verification System (`verify_bundles.py`)
**Purpose**: Automated verification of template bundles against Quoter API
**Schedule**: Runs twice daily via GitHub Actions
**Function**: Checks for changes in item names, SKUs, prices, and types

## Deployment Options

### Option 1: Render.com (Recommended)
**File**: `render_cover_letter_editor.yaml`
**Benefits**:
- Free tier available
- Automatic deployments from GitHub
- 24/7 uptime
- Custom domain support

**Setup Steps**:
1. Connect GitHub repository to Render
2. Use `render_cover_letter_editor.yaml` configuration
3. Set environment variables
4. Deploy automatically

### Option 2: GitHub Pages
**File**: `docs/DEPLOY_TO_GITHUB_PAGES.md`
**Benefits**:
- Free hosting
- Easy setup
- Automatic updates

**Limitations**:
- Static hosting only
- No server-side processing
- Requires build process

### Option 3: Local Development
**Files**: 
- `test_files/start_cover_letter_editor.sh`
- `test_files/start_with_ngrok.sh`

**Usage**:
- For testing and development
- ngrok provides temporary public access
- Port 5001 (to avoid conflicts)

## File Organization

### Production Files
- `cover_letter_editor.py` - Main application
- `render_cover_letter_editor.yaml` - Render deployment config
- `verify_bundles.py` - Bundle verification script

### Documentation Files
- `docs/COVER_LETTER_EDITOR_README.md` - Editor documentation
- `docs/COVER_LETTER_PROCEDURE_AND_LINKS.md` - This file

### Test/Development Files
- `test_files/deploy_to_github_pages.md` - GitHub Pages guide
- `test_files/start_cover_letter_editor.sh` - Local startup script
- `test_files/start_with_ngrok.sh` - ngrok startup script

## Workflow Integration

### Cover Letter Creation Process
1. **Webhook Trigger**: Pipedrive webhook triggers quote creation
2. **Template Selection**: System selects appropriate template
3. **Field Replacement**: Dynamic fields are replaced with real data
4. **Quote Creation**: Quote is created with cover letter and appended content
5. **Sales Rep Access**: Sales reps can modify via web interface

### Bundle Verification Process
1. **Daily Check**: GitHub Actions runs twice daily
2. **API Comparison**: Compares stored bundles with Quoter API
3. **Change Detection**: Identifies any changes in items
4. **Issue Creation**: Creates GitHub issues for review
5. **Manual Update**: Sales team reviews and updates bundles

## Useful Links

### GitHub Repository
- **Main Repository**: `https://github.com/egrosshans-coder/Quoter-Pipedrive.git`
- **Cover Letter Editor**: Available in root directory
- **Documentation**: All docs in `docs/` folder

### Deployment Links
- **Render.com**: `https://render.com` (recommended hosting)
- **GitHub Pages**: `https://pages.github.com` (alternative hosting)
- **ngrok**: `https://ngrok.com` (temporary public access)

### API Documentation
- **Quoter API**: For quote creation and item management
- **Pipedrive API**: For deal and contact data
- **Field Codes**: Available in cover letter editor sidebar

## Maintenance

### Regular Tasks
- **Bundle Verification**: Automated daily checks
- **Template Updates**: Manual updates via web interface
- **Deployment Updates**: Automatic via GitHub integration

### Troubleshooting
- **Port Conflicts**: Use port 5001 instead of 5000
- **Environment Variables**: Ensure all required variables are set
- **API Limits**: Monitor Quoter and Pipedrive API usage

## Support

### Documentation
- All procedures documented in `docs/` folder
- README files for each component
- Step-by-step deployment guides

### Contact
- **Technical Issues**: Check GitHub issues
- **Deployment Help**: Refer to deployment guides
- **Feature Requests**: Create GitHub issues

---

**Last Updated**: September 14, 2025
**Version**: 1.0
**Status**: Production Ready
