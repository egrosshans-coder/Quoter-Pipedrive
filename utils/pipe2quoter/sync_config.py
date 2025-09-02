#!/usr/bin/env python3
"""
Configuration file for Pipedrive to Quoter sync.
"""

# Fields to compare and sync
SYNC_FIELDS = {
    "name": {
        "enabled": True,
        "description": "Product name"
    },
    "code": {
        "enabled": True,
        "description": "Product code/SKU"
    },
    "category": {
        "enabled": True,
        "description": "Product category"
    },
    "description": {
        "enabled": False,  # Disabled for now
        "description": "Product description"
    },
    "price": {
        "enabled": False,  # You mentioned pricing didn't change
        "description": "Product price"
    }
}

# API Configuration
API_CONFIG = {
    "pipedrive": {
        "base_url": "https://api.pipedrive.com/v1",
        "timeout": 10,
        "retry_attempts": 3
    },
    "quoter": {
        "base_url": "https://api.quoter.com/v1",
        "timeout": 10,
        "retry_attempts": 3
    }
}

# Sync Settings
SYNC_SETTINGS = {
    "batch_size": 100,
    "dry_run": True,  # Set to True to see what would be updated without making changes
    "log_level": "INFO"
}

# Field Mappings (Pipedrive -> Quoter)
FIELD_MAPPINGS = {
    "name": "name",
    "code": "code", 
    "category": "category_id",
    "description": "description"
}
