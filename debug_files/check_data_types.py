#!/usr/bin/env python3
"""
Check Data Types
Examine the exact data types that Quoter is sending for pricing fields.
"""

import json
from quoter import get_quoter_products

def check_data_types():
    """
    Check the data types of pricing fields from Quoter.
    """
    print("🔍 CHECKING QUOTER DATA TYPES")
    print("=" * 50)
    
    # Get a few products from Quoter
    products = get_quoter_products()
    
    if not products:
        print("❌ No products found")
        return
    
    for i, product in enumerate(products, 1):
        print(f"\n📦 PRODUCT {i}: {product.get('name', 'Unknown')}")
        print("-" * 40)
        
        # Check price_decimal
        price_decimal = product.get('price_decimal')
        if price_decimal is not None:
            print(f"   price_decimal: {price_decimal}")
            print(f"   Type: {type(price_decimal).__name__}")
            print(f"   Repr: {repr(price_decimal)}")
            
            # Test conversions
            try:
                as_int = int(price_decimal)
                print(f"   As int: {as_int} (type: {type(as_int).__name__})")
            except:
                print(f"   ❌ Cannot convert to int")
                
            try:
                as_float = float(price_decimal)
                print(f"   As float: {as_float} (type: {type(as_float).__name__})")
            except:
                print(f"   ❌ Cannot convert to float")
        else:
            print(f"   price_decimal: None")
        
        # Check cost_decimal
        cost_decimal = product.get('cost_decimal')
        if cost_decimal is not None:
            print(f"   cost_decimal: {cost_decimal}")
            print(f"   Type: {type(cost_decimal).__name__}")
            print(f"   Repr: {repr(cost_decimal)}")
            
            # Test conversions
            try:
                as_int = int(cost_decimal)
                print(f"   As int: {as_int} (type: {type(as_int).__name__})")
            except:
                print(f"   ❌ Cannot convert to float")
                
            try:
                as_float = float(cost_decimal)
                print(f"   As float: {as_float} (type: {type(as_float).__name__})")
            except:
                print(f"   ❌ Cannot convert to float")
        else:
            print(f"   cost_decimal: None")
        
        # Check if there are other price-related fields
        price_fields = {k: v for k, v in product.items() if 'price' in k.lower()}
        if price_fields:
            print(f"   Other price fields: {price_fields}")

if __name__ == "__main__":
    check_data_types()
