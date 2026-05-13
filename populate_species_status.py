"""
Populate native_flag and endangered_status_code columns in the species table.
Uses two source files:
  1. PaulsList-Final.xlsx (V-Status, NSW vul, C'wealth vul columns)
  2. ALA-checklist-2026-05-10.csv (NSW Conservation Status, EPBC Act columns)

How values are decided:
  native_flag:
    'native' or 'Native' from V-Status -> 1
    'exotic' or 'Exotic' from V-Status -> 0
    'Uncertain' or no match -> NULL (left alone)

  endangered_status_code:
    Combined format like 'NSW:E1, Fed:V' from PaulsList
    Falls back to ALA-checklist if PaulsList has no data for that species
    Uses meaning words from PaulsList-Codes Endangered Codes sheet

Input:
  - species_native.csv (exported from species table with species_id, scientific_name)
  - PaulsList-Final.xlsx
  - ALA-checklist-2026-05-10.csv
  - PaulsList-Codes.xlsx (for code meanings)

Output:
  - update_species_status.sql with UPDATE statements
"""

import pandas as pd
import re

SPECIES_CSV = 'species_native.csv'
PAULS_XLSX = 'PaulsList-Final.xlsx'
ALA_CSV = 'ALA-checklist-2026-05-10.csv'
CODES_XLSX = 'PaulsList-Codes.xlsx'
OUTPUT_SQL = 'update_species_status.sql'


def escape_sql_string(value):
    if value is None or pd.isna(value) or str(value).strip() == '':
        return 'NULL'
    text = str(value).strip().replace("'", "''")
    return f"'{text}'"


def normalise_status(v_status):
    """Convert V-Status text to native_flag value (1=native, 0=exotic, None=unknown)."""
    if pd.isna(v_status):
        return None
    text = str(v_status).strip().lower()
    if text == 'native':
        return 1
    if text == 'exotic':
        return 0
    return None  # Uncertain or anything else


def build_code_meanings(codes_xlsx):
    """Read PaulsList-Codes Endangered Codes sheet, build code -> meaning lookup."""
    df = pd.read_excel(codes_xlsx, sheet_name='Endangered Codes')
    meanings = {}
    for _, row in df.iterrows():
        category = row.get('Category')
        value = row.get('Value')
        meaning = row.get('Meaning')
        if pd.isna(value) or pd.isna(meaning):
            continue
        # store by code, prefer the first meaning (NSW codes get priority)
        key = str(value).strip()
        if key not in meanings:
            meanings[key] = str(meaning).strip()
    return meanings


def format_endangered(nsw_code, cw_code, ala_nsw, ala_epbc, code_meanings):
    """
    Build the endangered_status_code string.
    Format: 'NSW:Endangered, Fed:Vulnerable' or similar
    Falls back to ALA-checklist if PaulsList is empty.
    """
    parts = []

    # NSW status (prefer PaulsList, fall back to ALA-checklist)
    nsw_text = None
    if not pd.isna(nsw_code) and str(nsw_code).strip():
        raw = str(nsw_code).strip()
        # use code meaning if known, else raw code
        meaning = code_meanings.get(raw, raw)
        nsw_text = meaning
    elif not pd.isna(ala_nsw) and str(ala_nsw).strip():
        nsw_text = str(ala_nsw).strip()

    # Federal status (prefer PaulsList, fall back to ALA-checklist)
    fed_text = None
    if not pd.isna(cw_code) and str(cw_code).strip():
        raw = str(cw_code).strip()
        meaning = code_meanings.get(raw, raw)
        fed_text = meaning
    elif not pd.isna(ala_epbc) and str(ala_epbc).strip():
        fed_text = str(ala_epbc).strip()

    if nsw_text:
        parts.append(f"NSW:{nsw_text}")
    if fed_text:
        parts.append(f"Fed:{fed_text}")

    if parts:
        return ", ".join(parts)
    return None


def main():
    # step 1: load DB species names
    print(f"Loading {SPECIES_CSV}...")
    db_species = pd.read_csv(SPECIES_CSV)
    print(f"  Loaded {len(db_species)} species from DB")

    # step 2: build code meanings lookup
    print(f"Loading {CODES_XLSX}...")
    code_meanings = build_code_meanings(CODES_XLSX)
    print(f"  Loaded {len(code_meanings)} code meanings")

    # step 3: load Paul's list (main source)
    print(f"Loading {PAULS_XLSX}...")
    pauls = pd.read_excel(PAULS_XLSX, sheet_name='PaulsList-final')
    print(f"  Loaded {len(pauls)} rows from Paul's List")
    # build lookup by scientific name
    pauls_lookup = {}
    for _, row in pauls.iterrows():
        name = row.get('ALA scientific name')
        if pd.isna(name):
            continue
        pauls_lookup[str(name).strip()] = {
            'v_status': row.get('V-Status'),
            'nsw_vul': row.get('NSW vul'),
            'cw_vul': row.get("C'wealth vul"),
        }

    # step 4: load ALA checklist (fallback for endangered)
    print(f"Loading {ALA_CSV}...")
    ala = pd.read_csv(ALA_CSV, low_memory=False)
    print(f"  Loaded {len(ala)} rows from ALA checklist")
    ala_lookup = {}
    for _, row in ala.iterrows():
        name = row.get('Species Name')
        if pd.isna(name):
            continue
        ala_lookup[str(name).strip()] = {
            'nsw_status': row.get('New South Wales : Conservation Status'),
            'epbc_status': row.get('EPBC Act Threatened Species'),
        }

    # step 5: build UPDATE statements
    print("\nMatching species and building updates...")
    updates = []
    stats = {
        'native': 0,
        'exotic': 0,
        'no_native_flag': 0,
        'endangered_set': 0,
        'no_endangered': 0,
        'not_in_any_source': 0,
    }

    for _, row in db_species.iterrows():
        species_id = row['species_id']
        sci_name = str(row['scientific_name']).strip() if not pd.isna(row['scientific_name']) else ''

        if not sci_name:
            continue

        # look up in Paul's list
        pauls_row = pauls_lookup.get(sci_name)
        # look up in ALA checklist
        ala_row = ala_lookup.get(sci_name)

        if pauls_row is None and ala_row is None:
            stats['not_in_any_source'] += 1
            continue

        # determine native_flag from Paul's
        native_flag = None
        if pauls_row:
            native_flag = normalise_status(pauls_row['v_status'])

        # determine endangered_status from both sources
        nsw_code = pauls_row['nsw_vul'] if pauls_row else None
        cw_code = pauls_row['cw_vul'] if pauls_row else None
        ala_nsw = ala_row['nsw_status'] if ala_row else None
        ala_epbc = ala_row['epbc_status'] if ala_row else None

        endangered_status = format_endangered(
            nsw_code, cw_code, ala_nsw, ala_epbc, code_meanings
        )

        # if nothing to update, skip
        if native_flag is None and endangered_status is None:
            continue

        # build SQL
        set_parts = []
        if native_flag is not None:
            set_parts.append(f"native_flag = {native_flag}")
            if native_flag == 1:
                stats['native'] += 1
            else:
                stats['exotic'] += 1
        else:
            stats['no_native_flag'] += 1

        if endangered_status:
            set_parts.append(f"endangered_status_code = {escape_sql_string(endangered_status)}")
            stats['endangered_set'] += 1
        else:
            stats['no_endangered'] += 1

        if set_parts:
            updates.append(
                f"UPDATE species SET {', '.join(set_parts)} WHERE species_id = {species_id};"
            )

    print(f"\nStats:")
    print(f"  Updates: {len(updates)}")
    print(f"  Set as native: {stats['native']}")
    print(f"  Set as exotic: {stats['exotic']}")
    print(f"  Endangered status set: {stats['endangered_set']}")
    print(f"  Species not found in any source: {stats['not_in_any_source']}")

    # write SQL
    print(f"\nWriting {OUTPUT_SQL}...")
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write("-- Auto generated UPDATE statements\n")
        f.write(f"-- Total updates: {len(updates)}\n")
        f.write("-- native_flag: 1 = native, 0 = exotic, NULL = unknown\n")
        f.write("-- endangered_status_code: format 'NSW:status, Fed:status'\n\n")
        for stmt in updates:
            f.write(stmt + "\n")

    print(f"Done. File saved: {OUTPUT_SQL}")


if __name__ == '__main__':
    main()