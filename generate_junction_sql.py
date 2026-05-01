"""
Generate INSERT SQL for species_traits_junction table from AusTraits source data.
Uses shared logic from trait_rules.py to derive clean working_value and source_code
from the AusTraits original_value.

This is for ADDING NEW DATA. To fix existing data in the DB, use
rebuild_from_original.py instead.

1. Reads species.csv to build a lookup: scientific_name to species_id
2. Reads traits.csv to build a lookup: trait_name to trait_id
3. Reads AusTraits xlsx (Traits_summary-from-AusTraits.xlsx) for original_value
4. Also reads Lovable xlsx for the trait column ordering and trait names
5. For each species and trait combo with original_value:
   - Derive working_value and source_code using trait_rules.derive_from_original
6. Skip empty cells and non-trait columns (Local Status, planted_native, family)
7. Write INSERT statements to insert_junction.sql
"""

import pandas as pd
from trait_rules import derive_from_original

SPECIES_CSV = 'species.csv'
TRAITS_CSV = 'traits.csv'
SOURCE_XLSX = 'SpeciesTraitsWorkingValues-Lovable.xlsx'
AUSTRAITS_XLSX = 'Traits_summary-from-AusTraits.xlsx'
OUTPUT_SQL = 'insert_junction.sql'


def escape_sql_string(value):
    if value is None or pd.isna(value):
        return 'NULL'
    text = str(value).replace("'", "''")
    return f"'{text}'"


def main():
    # step 1: load species lookup
    print(f"Loading {SPECIES_CSV}...")
    species_df = pd.read_csv(SPECIES_CSV)
    species_lookup = dict(zip(species_df['scientific_name'], species_df['species_id']))
    print(f"  Loaded {len(species_lookup)} species")

    # step 2: load trait lookup AND trait type lookup
    print(f"Loading {TRAITS_CSV}...")
    traits_df = pd.read_csv(TRAITS_CSV)
    trait_id_lookup = dict(zip(traits_df['trait_name'], traits_df['trait_id']))
    trait_type_lookup = dict(zip(traits_df['trait_name'], traits_df['trait_type']))
    print(f"  Loaded {len(trait_id_lookup)} traits")

    # step 3: load Lovable xlsx (used to know which traits to process)
    print(f"Loading {SOURCE_XLSX}...")
    source_df = pd.read_excel(SOURCE_XLSX, sheet_name='Species_Traits_Sorted')
    print(f"  Loaded {len(source_df)} species rows")

    # find trait columns (numbered prefix like "3-flower_colour")
    trait_columns = []
    for col in source_df.columns:
        if col == 'species_name':
            continue
        parts = col.split('-', 1)
        if not parts[0].isdigit():
            continue
        trait_num = int(parts[0])
        if trait_num >= 71:
            continue
        if 'code' in col.lower():
            continue
        trait_name = parts[1]
        trait_columns.append(trait_name)
    print(f"  Found {len(trait_columns)} trait columns")

    # step 4: load AusTraits original values
    print(f"Loading {AUSTRAITS_XLSX}...")
    austraits_df = pd.read_excel(AUSTRAITS_XLSX, sheet_name='final Traits summary')
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

    # step 5: build INSERT rows
    print("\nBuilding INSERT rows...")
    insert_rows = []
    missing_species = set()
    missing_traits = set()
    no_original = 0

    for _, row in source_df.iterrows():
        species_name = row['species_name']
        if species_name not in species_lookup:
            missing_species.add(species_name)
            continue
        species_id = species_lookup[species_name]

        for trait_name in trait_columns:
            if trait_name not in trait_id_lookup:
                missing_traits.add(trait_name)
                continue
            trait_id = trait_id_lookup[trait_name]
            trait_type = trait_type_lookup.get(trait_name)

            original = austraits_lookup.get((species_name, trait_name))

            if original is None or pd.isna(original):
                no_original += 1
                continue

            working_value, source_code = derive_from_original(original, trait_type)

            if working_value is None:
                continue

            insert_rows.append(
                f"({species_id}, {trait_id}, "
                f"{escape_sql_string(original)}, "
                f"{escape_sql_string(working_value)}, "
                f"{escape_sql_string(source_code)})"
            )

    print(f"\nResults:")
    print(f"  INSERT rows: {len(insert_rows)}")
    print(f"  Skipped (no original_value in AusTraits): {no_original}")
    print(f"  Missing species: {len(missing_species)}")
    print(f"  Missing traits: {len(missing_traits)}")

    if missing_traits:
        print(f"  Trait names missing from traits table:")
        for name in missing_traits:
            print(f"    - {name}")

    # step 6: write SQL
    print(f"\nWriting {OUTPUT_SQL}...")
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write("-- Auto generated INSERT statements for species_traits_junction\n")
        f.write(f"-- Total rows: {len(insert_rows)}\n")
        f.write("-- working_value and source_code derived from AusTraits original_value\n\n")

        batch_size = 500
        for i in range(0, len(insert_rows), batch_size):
            batch = insert_rows[i:i + batch_size]
            f.write(
                "INSERT INTO species_traits_junction "
                "(species_id, trait_id, original_value, working_value, source_code) "
                "VALUES\n"
            )
            f.write(",\n".join(batch))
            f.write(";\n\n")

    print(f"Done. File saved: {OUTPUT_SQL}")


if __name__ == '__main__':
    main()