#!/usr/bin/env python3
"""
Daily Bundle Update Script
Automatically updates bundle data from Quoter API to keep pricing and categories current
"""

import sys
from quoter import get_access_token
from template_mapping_enhanced import verify_bundle_against_quoter, update_bundle_from_quoter

def main():
    print('🔄 DAILY BUNDLE UPDATE')
    print('=' * 50)
    
    # All 11 templates to verify
    templates_to_verify = [
        'floating-video',
        'led-wristbands', 
        'balloons',
        'co2-smoke-foggers',
        'confetti-streamers',
        'fireworks-pyro-fire',
        'basic',
        'low-level-fog',
        'robotics',
        'tank-delivery',
        'led-lanyards'
    ]
    
    access_token = get_access_token()
    if access_token:
        total_changes = 0
        all_changes = []
        
        for template_name in templates_to_verify:
            print(f'\n🔄 Updating {template_name} template...')
            
            # First verify to see what needs updating
            verification_results = verify_bundle_against_quoter(template_name, access_token)
            
            print(f'📊 {template_name.upper()} STATUS:')
            print(f'   Total items: {verification_results["total_items"]}')
            print(f'   Items to update: {len(verification_results["items_changed"])}')
            print(f'   Items not found: {len(verification_results["items_not_found"])}')
            print(f'   Items unchanged: {len(verification_results["items_unchanged"])}')
            
            if verification_results['items_changed']:
                total_changes += len(verification_results['items_changed'])
                print(f'🔄 UPDATING {template_name.upper()}:')
                for item in verification_results['items_changed']:
                    print(f'   {item["sku"]}: {", ".join(item["changes"])}')
                
                # Apply the updates automatically (now with proper parent/child category handling)
                update_results = update_bundle_from_quoter(template_name, access_token, dry_run=False, verification_results=verification_results)
                if update_results.get('success'):
                    print(f'✅ {template_name.upper()} - BUNDLE UPDATED SUCCESSFULLY')
                else:
                    print(f'❌ {template_name.upper()} - UPDATE FAILED')
            else:
                print(f'✅ {template_name.upper()} - NO UPDATES NEEDED')
        
        # Final summary
        print(f'\n📊 OVERALL UPDATE SUMMARY:')
        print(f'   Templates processed: {len(templates_to_verify)}')
        print(f'   Total changes applied: {total_changes}')
        
        # Report results
        if total_changes > 0:
            print(f'\n✅ BUNDLE UPDATE COMPLETED: {total_changes} changes applied')
            print(f'📝 Bundle data synchronized with current Quoter pricing and categories')
            sys.exit(0)  # Success - changes were applied
        else:
            print(f'\n✅ ALL BUNDLES UP TO DATE - NO UPDATES NEEDED')
            sys.exit(0)
    else:
        print('❌ Failed to get access token')
        sys.exit(1)

if __name__ == '__main__':
    main()
