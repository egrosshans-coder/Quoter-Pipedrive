#!/usr/bin/env python3
"""
Daily Bundle Verification Script
Runs bundle verification against Quoter API
"""

import sys
from quoter import get_access_token
from template_mapping_enhanced import verify_bundle_against_quoter

def main():
    print('🔍 DAILY BUNDLE VERIFICATION')
    print('=' * 50)
    
    access_token = get_access_token()
    if access_token:
        # Verify floating-video template
        verification_results = verify_bundle_against_quoter('floating-video', access_token)
        
        print(f'\n📊 VERIFICATION SUMMARY:')
        print(f'   Total items: {verification_results["total_items"]}')
        print(f'   Items verified: {verification_results["items_verified"]}')
        print(f'   Items changed: {len(verification_results["items_changed"])}')
        print(f'   Items not found: {len(verification_results["items_not_found"])}')
        print(f'   Items unchanged: {len(verification_results["items_unchanged"])}')
        
        # Check if there are any changes
        if verification_results['items_changed']:
            print(f'\n⚠️  CHANGES DETECTED:')
            for item in verification_results['items_changed']:
                print(f'   {item["sku"]}: {item["changes"]}')
            
            # Exit with error code to notify of changes
            sys.exit(1)
        else:
            print(f'\n✅ ALL ITEMS VERIFIED - NO CHANGES DETECTED')
            sys.exit(0)
    else:
        print('❌ Failed to get access token')
        sys.exit(1)

if __name__ == '__main__':
    main()
