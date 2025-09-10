#!/usr/bin/env python3
"""
Check HID-QBO-Status for all ZZ deal organizations
"""

import os
from dotenv import load_dotenv
from pipedrive import get_deal_by_id, get_organization_by_id
from utils.logger import logger

load_dotenv()

def check_zz_organizations_status():
    """Check HID-QBO-Status for all ZZ deal organizations"""
    
    deals_to_check = ['2499', '2510', '2512', '2513', '2514', '2515', '2516', '2517', '2519']
    
    logger.info("🔍 Checking HID-QBO-Status for all ZZ deal organizations...")
    logger.info("=" * 80)
    logger.info(f"{'Deal ID':<8} | {'Deal Title':<15} | {'Org Name':<20} | {'Org ID':<6} | {'HID-QBO-Status':<15}")
    logger.info("-" * 80)
    
    for deal_id in deals_to_check:
        try:
            deal = get_deal_by_id(deal_id)
            if deal and 'ZZ' in deal.get('title', ''):
                org_id = deal.get('org_id', {}).get('value')
                org_name = deal.get('org_name', '')
                deal_title = deal.get('title', '')
                
                # Get organization details to check HID-QBO-Status
                hid_status = 'Unknown'
                if org_id:
                    try:
                        org = get_organization_by_id(org_id)
                        if org:
                            # HID-QBO-Status field key
                            hid_field = '454a3767bce03a880b31d78a38c480d6870e0f1b'
                            hid_status = org.get(hid_field, 'Not Set')
                            if hid_status == 'None' or hid_status is None:
                                hid_status = 'Not Set'
                            elif hid_status == 289:
                                hid_status = 'QBO-SubCust (289)'
                            elif hid_status == '289':
                                hid_status = 'QBO-SubCust (289)'
                            elif hid_status == 'QBO-SubCust':
                                hid_status = 'QBO-SubCust (289)'
                    except Exception as e:
                        hid_status = f'Error: {str(e)[:20]}'
                
                logger.info(f"{deal_id:<8} | {deal_title:<15} | {org_name:<20} | {org_id:<6} | {hid_status:<15}")
            else:
                logger.info(f"{deal_id:<8} | Not Found        | {'':<20} | {'':<6} | {'':<15}")
                
        except Exception as e:
            logger.error(f"{deal_id:<8} | Error: {str(e)[:50]}")
    
    logger.info("=" * 80)

if __name__ == "__main__":
    check_zz_organizations_status()
