#!/usr/bin/env python3
"""
Enhanced CSV Analysis Script for Quoter Item Import
"""

import pandas as pd
import os
import re

def analyze_csv():
    """Analyze the CSV file for duplicates and missing data."""
    csv_file = "Cleaned_Goodshuffle_Line_Items - Sheet1.csv"
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return
    try:
        df = pd.read_csv(csv_file)
        print(f"📊 CSV Analysis Results")
        print(f"Total rows: {len(df)}")
        print(f"Total columns: {len(df.columns)}")
        print()
        # Data completeness analysis
        required_fields = ["*Item Name", "*Category", "*USD Price (e.g. 1000.00)"]
        complete_rows = 0
        partial_rows = 0
        empty_rows = 0
        for idx, row in df.iterrows():
            missing_fields = sum(1 for field in required_fields if pd.isna(row[field]) or str(row[field]).strip() == "")
            if missing_fields == 0:
                complete_rows += 1
            elif missing_fields < len(required_fields):
                partial_rows += 1
            else:
                empty_rows += 1
        print(f"✅ Complete rows: {complete_rows}")
        print(f"⚠️  Partial rows: {partial_rows}")
        print(f"❌ Empty rows: {empty_rows}")
        print()
        # Duplicate analysis
        print("🔍 Duplicate Analysis:")
        item_name_counts = df["*Item Name"].value_counts()
        exact_duplicates = item_name_counts[item_name_counts > 1]
        if len(exact_duplicates) > 0:
            print(f"Found {len(exact_duplicates)} exact duplicates:")
            for item_name, count in exact_duplicates.items():
                print(f"  • {item_name} appears {count} times")
        else:
            print("✅ No exact duplicates found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_csv()
