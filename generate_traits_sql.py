"""
Generate SQL INSERT statements for the traits table.
Loads ALL 522 traits from APD_traits-New-FullList.xlsx (not just 70).
The 70 "in use" traits get of_interest = TRUE, others get FALSE.

1. Reads APD_traits-New-FullList.xlsx for all 522 traits
2. Reads TraitsDescriptions-71-in-use.xlsx for the 70 "in use" traits
   (gets trait_type_name, column_number, of_interest flag from here)
3. For traits in both files, uses TraitsDescriptions data + sets of_interest=TRUE
4. For traits only in APD, uses APD data + sets of_interest=FALSE
5. Maps trait_type from APD long names to short codes (cat./num/date)
6. Writes INSERT statements to insert_traits.sql
"""

import pandas as pd

# file names
APD_XLSX = 'APD_traits-New-FullList.xlsx'
IN_USE_XLSX = 'TraitsDescriptions-71-in-use.xlsx'
OUTPUT_SQL = 'insert_traits.sql'


def escape_sql_string(value):
    """Make a value safe for SQL. Handles quotes and None."""
    if value is None or pd.isna(value):
        return 'NULL'
    text = str(value).replace("'", "''")
    return f"'{text}'"


def map_trait_type(apd_type, in_use_type=None):
    """Map trait_type to short code: cat. / num / date"""
    # if in_use file has it, prefer that (because it has 'date' which APD doesn't)
    if in_use_type and not pd.isna(in_use_type):
        return in_use_type
    # otherwise map from APD long name
    if pd.isna(apd_type):
        return None
    apd_str = str(apd_type).lower()
    if 'continuous' in apd_str:
        return 'num'
    if 'categorical' in apd_str:
        return 'cat.'
    return None


def main():
    # step 1: load APD full list (522 traits)
    print(f"Loading {APD_XLSX}...")
    apd_df = pd.read_excel(APD_XLSX, sheet_name='APD_traits-New-All')
    print(f"  Loaded {len(apd_df)} traits from APD")

    # step 2: load in-use list (70 traits)
    print(f"Loading {IN_USE_XLSX}...")
    in_use_df = pd.read_excel(IN_USE_XLSX, sheet_name='AllOurTraits')
    print(f"  Loaded {len(in_use_df)} 'in use' traits")

    # build a lookup from in_use file by trait name
    in_use_lookup = {}
    for _, row in in_use_df.iterrows():
        trait_name = row['trait']
        in_use_lookup[trait_name] = {
            'trait_type_name': row.get('Trait Type Name'),
            'column_number': row.get('Column'),
            'trait_type': row.get('trait_type'),
        }

    # step 3: build INSERT rows
    print("\nBuilding INSERT rows...")
    insert_rows = []
    of_interest_count = 0

    for _, row in apd_df.iterrows():
        trait_name = row['trait']

        # check if this trait is in the 70-in-use list
        in_use_data = in_use_lookup.get(trait_name)
        is_of_interest = in_use_data is not None
        if is_of_interest:
            of_interest_count += 1

        # gather field values
        if in_use_data:
            trait_type_name = in_use_data['trait_type_name']
            column_number = in_use_data['column_number']
            trait_type = map_trait_type(row.get('trait_type'), in_use_data['trait_type'])
        else:
            trait_type_name = None
            column_number = None
            trait_type = map_trait_type(row.get('trait_type'))

        # other fields from APD
        trait_label = row.get('label')
        trait_info = row.get('description')
        trait_unit = row.get('units')
        allowed_min = row.get('allowed_values_min')
        allowed_max = row.get('allowed_values_max')

        # build SQL value tuple
        values = (
            escape_sql_string(trait_type_name),
            escape_sql_string(trait_name),
            escape_sql_string(trait_info),
            escape_sql_string(trait_unit),
            escape_sql_string(trait_type),
            escape_sql_string(trait_label),
            escape_sql_string(column_number) if not pd.isna(column_number) else 'NULL',
            escape_sql_string(allowed_min) if not pd.isna(allowed_min) else 'NULL',
            escape_sql_string(allowed_max) if not pd.isna(allowed_max) else 'NULL',
            'TRUE' if is_of_interest else 'FALSE',
        )
        insert_rows.append(f"({', '.join(values)})")

    print(f"  Total rows: {len(insert_rows)}")
    print(f"  Of interest (in 70 in-use): {of_interest_count}")
    print(f"  Not of interest: {len(insert_rows) - of_interest_count}")

    # step 4: write SQL file
    print(f"\nWriting {OUTPUT_SQL}...")
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write("-- Auto generated INSERT statements for traits table\n")
        f.write(f"-- Total rows: {len(insert_rows)}\n")
        f.write(f"-- Of interest (in 70 in-use list): {of_interest_count}\n\n")

        # batch into 200 rows per INSERT to avoid huge statements
        batch_size = 200
        for i in range(0, len(insert_rows), batch_size):
            batch = insert_rows[i:i + batch_size]
            f.write(
                "INSERT INTO traits "
                "(trait_type_name, trait_name, trait_info, trait_unit, trait_type, "
                "trait_label, column_number, allowed_values_min, allowed_values_max, of_interest) "
                "VALUES\n"
            )
            f.write(",\n".join(batch))
            f.write(";\n\n")

    print(f"Done. File saved: {OUTPUT_SQL}")


if __name__ == '__main__':
    main()