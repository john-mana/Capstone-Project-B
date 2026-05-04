"""
Rebuild working_value and source_code from original_value for existing rows
in species_traits_junction. Uses shared logic from trait_rules.py.

This is for FIXING data already in the database. To ADD new data from AusTraits,
use generate_junction_sql.py instead.

1. Export current junction data: junction.csv
2. Run this script: python rebuild_from_original.py
3. Import generated SQL in phpMyAdmin

  - Skip rows where original_value is NULL (cannot derive without source)
  - Skip rows where source_code is g/f/m/a (these are derived, leave alone)
  - For others: regenerate working_value AND source_code from original_value

Input:
  - junction.csv: full export from species_traits_junction joined with traits

Output:
  - rebuild_from_original.sql: UPDATE statements
"""

import pandas as pd
from trait_rules import derive_from_original, PROTECTED_SOURCES

INPUT_CSV = 'junction.csv'
OUTPUT_SQL = 'rebuild_from_original.sql'


def escape_sql_string(value):
    if value is None or pd.isna(value):
        return 'NULL'
    text = str(value).replace("'", "''")
    return f"'{text}'"


def main():
    print(f"Loading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV)
    print(f"  Loaded {len(df)} rows")

    update_rows = []
    skipped_null = 0
    skipped_protected = 0
    skipped_no_change = 0
    examples = []

    for _, row in df.iterrows():
        junction_id = row['species_trait_junction_id']
        trait_type = row['trait_type']
        original = row['original_value']
        old_working = row['working_value']
        old_source = row['source_code']

        if pd.isna(original):
            skipped_null += 1
            continue

        if not pd.isna(old_source) and str(old_source).strip() in PROTECTED_SOURCES:
            skipped_protected += 1
            continue

        new_working, new_source = derive_from_original(original, trait_type)

        if new_working is None:
            skipped_no_change += 1
            continue

        old_w_str = '' if pd.isna(old_working) else str(old_working).strip()
        old_s_str = '' if pd.isna(old_source) else str(old_source).strip()
        new_w_str = '' if new_working is None else str(new_working).strip()
        new_s_str = '' if new_source is None else str(new_source).strip()

        if old_w_str == new_w_str and old_s_str == new_s_str:
            skipped_no_change += 1
            continue

        update_rows.append(
            f"UPDATE species_traits_junction "
            f"SET working_value = {escape_sql_string(new_working)}, "
            f"source_code = {escape_sql_string(new_source)} "
            f"WHERE species_trait_junction_id = {junction_id};"
        )

        if len(examples) < 10:
            examples.append((trait_type, original, old_working, new_working, old_source, new_source))

    print(f"\nResults:")
    print(f"  Updates: {len(update_rows)}")
    print(f"  Skipped (NULL original): {skipped_null}")
    print(f"  Skipped (protected source): {skipped_protected}")
    print(f"  Skipped (no change needed): {skipped_no_change}")

    print("\nFirst 10 changes:")
    for ttype, orig, old_w, new_w, old_s, new_s in examples:
        orig_short = (str(orig)[:55] + '...') if len(str(orig)) > 58 else str(orig)
        print(f"  type:{ttype:5} orig: {orig_short}")
        print(f"    OLD: {str(old_w):30} src:{str(old_s)}")
        print(f"    NEW: {str(new_w):30} src:{str(new_s)}")

    print(f"\nWriting {OUTPUT_SQL}...")
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write("-- Auto generated UPDATE statements\n")
        f.write(f"-- Total updates: {len(update_rows)}\n\n")
        for stmt in update_rows:
            f.write(stmt + "\n")

    print(f"Done. File saved: {OUTPUT_SQL}")


if __name__ == '__main__':
    main()