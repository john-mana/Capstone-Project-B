"""
Read SpeciesTraitsWorkingValues-Lovable.xlsx and generate an SQL INSERT file
for the species_traits_junction table.

1. Reads species.csv to build a lookup: scientific_name to species_id
2. Reads traits.csv to build a lookup: trait_name to trait_id
3. Reads the Lovable xlsx (working_value and source_code)
4. Reads the AusTraits xlsx (original_value)
5. For each species and each trait, creates one junction row
6. Skips empty cells and the 2 non-trait columns (Local Status, planted_native)
7. Writes all INSERT statements to insert_junction.sql
"""

import pandas as pd

# file names, change if needed
SPECIES_CSV = 'species.csv'
TRAITS_CSV = 'traits.csv'
SOURCE_XLSX = 'SpeciesTraitsWorkingValues-Lovable.xlsx'
AUSTRAITS_XLSX = 'Traits summary-from-AusTraits.xlsx'
OUTPUT_SQL = 'insert_junction.sql'


def escape_sql_string(value):
    """Make a value safe for SQL. Handles quotes and None."""
    if value is None or pd.isna(value):
        return 'NULL'
    # convert to string and escape single quotes by doubling them
    text = str(value).replace("'", "''")
    return f"'{text}'"


def main():
    # step 1: load species lookup (scientific_name to species_id)
    print(f"Loading {SPECIES_CSV}...")
    species_df = pd.read_csv(SPECIES_CSV)
    species_lookup = dict(zip(species_df['scientific_name'], species_df['species_id']))
    print(f"  Loaded {len(species_lookup)} species")

    # step 2: load trait lookup (trait_name to trait_id)
    print(f"Loading {TRAITS_CSV}...")
    traits_df = pd.read_csv(TRAITS_CSV)
    trait_lookup = dict(zip(traits_df['trait_name'], traits_df['trait_id']))
    print(f"  Loaded {len(trait_lookup)} traits")

    # step 3: load the source xlsx (Lovable file has working_value and source_code)
    print(f"Loading {SOURCE_XLSX}...")
    source_df = pd.read_excel(SOURCE_XLSX, sheet_name='Species_Traits_Sorted')
    print(f"  Loaded {len(source_df)} species rows")

    # step 3b: load the AusTraits file for original_value
    print(f"Loading {AUSTRAITS_XLSX}...")
    austraits_df = pd.read_excel(AUSTRAITS_XLSX, sheet_name='final Traits summary')
    # build a lookup: (species_name, trait_name) to original_value
    austraits_lookup = {}
    for _, row in austraits_df.iterrows():
        sp_name = row['species_name']
        for col in austraits_df.columns:
            if col == 'species_name':
                continue
            val = row[col]
            if pd.notna(val):
                austraits_lookup[(sp_name, col)] = val
    print(f"  Loaded {len(austraits_lookup)} original values")

    # step 4: figure out trait columns
    # columns look like "3-flower_colour" and "3-code"
    # we want pairs: value column and its matching code column
    # skip columns with numbers 71 and 72 (not real traits)
    trait_columns = []
    for col in source_df.columns:
        if col == 'species_name':
            continue
        # parse the number prefix
        parts = col.split('-', 1)
        if not parts[0].isdigit():
            continue
        trait_num = int(parts[0])
        # skip 71 (Local Status) and 72 (planted_native)
        if trait_num >= 71:
            continue
        # skip code columns
        if 'code' in col.lower():
            continue
        # this is a value column
        # find its matching code column
        code_col = f"{trait_num}-code"
        code_col_alt = f"{trait_num}-Code"  # 7-Code uses capital C
        if code_col in source_df.columns:
            match_code = code_col
        elif code_col_alt in source_df.columns:
            match_code = code_col_alt
        else:
            match_code = None
        # trait name is the part after the number
        trait_name = parts[1]
        trait_columns.append((col, match_code, trait_name))

    print(f"  Found {len(trait_columns)} trait columns to process")

    # step 5: loop through data and build INSERT rows
    insert_rows = []
    missing_species = set()
    missing_traits = set()
    skipped_empty = 0
    original_filled = 0
    original_missing = 0

    for _, row in source_df.iterrows():
        species_name = row['species_name']
        # lookup species_id
        if species_name not in species_lookup:
            missing_species.add(species_name)
            continue
        species_id = species_lookup[species_name]

        for value_col, code_col, trait_name in trait_columns:
            # lookup trait_id
            if trait_name not in trait_lookup:
                missing_traits.add(trait_name)
                continue
            trait_id = trait_lookup[trait_name]

            # get the value
            value = row[value_col]
            if pd.isna(value):
                skipped_empty += 1
                continue

            # get the source code
            code = row[code_col] if code_col else None

            # get the original_value from AusTraits lookup
            original = austraits_lookup.get((species_name, trait_name))
            if original is not None:
                original_filled += 1
            else:
                original_missing += 1

            # build INSERT values
            original_value_sql = escape_sql_string(original)
            working_value_sql = escape_sql_string(value)
            source_code_sql = escape_sql_string(code)

            insert_rows.append(
                f"({species_id}, {trait_id}, {original_value_sql}, {working_value_sql}, {source_code_sql})"
            )

    print(f"\nResults:")
    print(f"  INSERT rows to generate: {len(insert_rows)}")
    print(f"  Empty cells skipped: {skipped_empty}")
    print(f"  Original values filled: {original_filled}")
    print(f"  Original values missing (will be NULL): {original_missing}")
    print(f"  Missing species (not in species table): {len(missing_species)}")
    print(f"  Missing traits (not in traits table): {len(missing_traits)}")

    if missing_species:
        print(f"\n  First 10 missing species:")
        for name in list(missing_species)[:10]:
            print(f"    - {name}")

    if missing_traits:
        print(f"\n  Missing trait names:")
        for name in missing_traits:
            print(f"    - {name}")

    # step 6: write SQL file
    print(f"\nWriting {OUTPUT_SQL}...")
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write("-- Auto generated INSERT statements for species_traits_junction\n")
        f.write(f"-- Total rows: {len(insert_rows)}\n\n")

        # write in batches of 500 to avoid huge single statements
        batch_size = 500
        for i in range(0, len(insert_rows), batch_size):
            batch = insert_rows[i:i + batch_size]
            f.write(
                "INSERT INTO species_traits_junction "
                "(species_id, trait_id, original_value, working_value, source_code) VALUES\n"
            )
            f.write(",\n".join(batch))
            f.write(";\n\n")

    print(f"Done. File saved: {OUTPUT_SQL}")


if __name__ == '__main__':
    main()