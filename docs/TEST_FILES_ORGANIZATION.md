# Test Files Organization

**Last Updated:** September 7, 2025  
**Version:** 1.0

## Overview

Test files have been organized into a dedicated `test_files/` directory to maintain a clean main project structure for Render deployment while preserving valuable testing utilities for local development.

## Directory Structure

```
quoter_sync/
├── test_files/                    # Test utilities directory
│   ├── test_slack_notification.py
│   ├── test_email_notification.py
│   └── [other test files]
├── notification.py                # Main notification system
├── webhook_handler.py            # Production webhook handler
└── [other production files]
```

## Test Files

### **Slack Notification Test**
- **File:** `test_files/test_slack_notification.py`
- **Purpose:** Test Slack webhook connectivity and message delivery
- **Usage:** `python test_files/test_slack_notification.py`
- **Features:**
  - Environment variable validation
  - Webhook URL testing
  - Message formatting verification
  - Error handling validation

### **Email Notification Test**
- **File:** `test_files/test_email_notification.py`
- **Purpose:** Test Gmail SMTP integration and email delivery
- **Usage:** `python test_files/test_email_notification.py`
- **Features:**
  - SMTP authentication testing
  - HTML email formatting validation
  - Recipient list verification
  - Gmail app password validation

## Benefits of Organization

### **Clean Production Directory**
- Main directory contains only production-ready files
- Render deployment focuses on essential files
- Reduced deployment complexity
- Clear separation of concerns

### **Preserved Testing Capabilities**
- Test files remain accessible for local development
- Easy to run individual channel tests
- Comprehensive validation tools available
- Debugging and troubleshooting support

### **Development Workflow**
- Test locally before deploying
- Validate configuration changes
- Debug notification issues
- Verify environment setup

## Usage Guidelines

### **Local Development**
```bash
# Test individual notification channels
python test_files/test_slack_notification.py
python test_files/test_email_notification.py

# Test from main directory
python test_files/test_slack_notification.py
```

### **Production Deployment**
- Test files are excluded from Render deployment
- Only production files are deployed
- Environment variables configured in Render dashboard
- No test dependencies in production

## File Dependencies

### **Test File Requirements**
- Must be run from main project directory
- Import from parent directory modules
- Use project's virtual environment
- Access to `.env` file for configuration

### **Import Structure**
```python
# Test files import from parent directory
from notification import send_slack_notification
from notification import send_email_notification
```

## Maintenance

### **Adding New Tests**
- Place new test files in `test_files/` directory
- Follow existing naming convention: `test_[feature].py`
- Import from parent directory modules
- Document test purpose and usage

### **Updating Tests**
- Keep tests synchronized with production code
- Update when notification system changes
- Maintain environment variable validation
- Test all notification channels regularly

---

**Status:** ✅ **ORGANIZED AND DOCUMENTED**  
**Last Updated:** September 7, 2025  
**Purpose:** Clean production deployment with preserved testing capabilities
