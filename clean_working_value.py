"""
  1. Multi-value cleanup: rows with ; , or ( get cleaned to single value
  2. Date conversion: date-type rows in old Y/n format get converted
     to month letters (e.g. "nnnnnnyyynnn" -> "nnnnnnJASnn")

  - Always pick the 1st value when there are multiple
  - Strip the trailing vote marker like (1) or (V)
  - For date types, convert Y to month letter at that position
  - For comma-only AI cases (no votes), set source_code = 'a'
"""

import pandas as pd
import re
import os

BAD_ROWS_CSV = 'bad_rows.csv'
FIX_DATES_CSV = 'fix_dates.csv'
OUTPUT_SQL = 'update_working_value.sql'


def escape_sql_string(value):
    """Make a value safe for SQL."""
    if value is None or pd.isna(value):
        return 'NULL'
    text = str(value).replace("'", "''")
    return f"'{text}'"


def convert_date_string(s):
    """
    Convert 12-char Y/n string to month letters.
    Position 1=J(an), 2=F(eb), 3=M(ar), 4=A(pr), 5=M(ay), 6=J(un),
             7=J(ul), 8=A(ug), 9=S(ep), 10=O(ct), 11=N(ov), 12=D(ec).
    """
    if s is None or pd.isna(s):
        return s
    s = str(s).strip()
    if len(s) != 12:
        return s

    months = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
    result = []
    for i, ch in enumerate(s):
        if ch.lower() == 'y':
            result.append(months[i])
        else:
            result.append('n')
    return ''.join(result)


def clean_working_value(value, trait_type=None):
    """
    Take the first value from a multi-value string.
    Returns tuple: (new_value, is_ai_case)
    is_ai_case is True when value is comma-separated with no votes
    (these are AI results from semester 1 and need source_code = 'a').
    """
    if value is None or pd.isna(value):
        return None, False

    text = str(value).strip()

    # detect AI case: has comma, but no ; and no (
    is_ai_case = (',' in text) and (';' not in text) and ('(' not in text)

    # split on ; first (most common separator)
    if ';' in text:
        first = text.split(';')[0]
    elif ',' in text:
        first = text.split(',')[0]
    else:
        first = text

    # strip trailing vote marker like (1), (2), (V), (v), etc.
    cleaned = re.sub(r'\s*\([^)]*\)\s*$', '', first).strip()

    # for date types, convert Y to month letter
    if trait_type == 'date':
        cleaned = convert_date_string(cleaned)

    return cleaned, is_ai_case


def process_bad_rows():
    """Process the multi-value rows from bad_rows.csv"""
    if not os.path.exists(BAD_ROWS_CSV):
        print(f"Skipping bad rows: {BAD_ROWS_CSV} not found")
        return [], 0

    print(f"\n--- Processing {BAD_ROWS_CSV} (multi-value cleanup) ---")
    df = pd.read_csv(BAD_ROWS_CSV)
    print(f"Loaded {len(df)} rows")

    update_rows = []
    no_change_count = 0
    ai_count = 0
    examples = []

    for _, row in df.iterrows():
        junction_id = row['species_trait_junction_id']
        trait_type = row['trait_type']
        old_value = row['working_value']
        new_value, is_ai_case = clean_working_value(old_value, trait_type)

        if new_value == old_value and not is_ai_case:
            no_change_count += 1
            continue

        new_value_sql = escape_sql_string(new_value)

        if is_ai_case:
            ai_count += 1
            update_rows.append(
                f"UPDATE species_traits_junction "
                f"SET working_value = {new_value_sql}, source_code = 'a' "
                f"WHERE species_trait_junction_id = {junction_id};"
            )
        else:
            update_rows.append(
                f"UPDATE species_traits_junction SET working_value = {new_value_sql} "
                f"WHERE species_trait_junction_id = {junction_id};"
            )

        if len(examples) < 5:
            examples.append((trait_type, old_value, new_value, is_ai_case))

    print(f"  Updates: {len(update_rows)}")
    print(f"  Unchanged: {no_change_count}")
    print(f"  AI cases (source_code = 'a'): {ai_count}")
    print("  Sample conversions:")
    for ttype, old, new, ai in examples:
        old_short = (old[:50] + '...') if len(str(old)) > 53 else old
        marker = ' [AI]' if ai else ''
        print(f"    {ttype:<5} {old_short:<55} -> {new}{marker}")

    return update_rows, ai_count


def process_date_conversion():
    """Process date rows from fix_dates.csv that need Y to month letter conversion"""
    if not os.path.exists(FIX_DATES_CSV):
        print(f"\nSkipping date conversion: {FIX_DATES_CSV} not found")
        return []

    print(f"\n--- Processing {FIX_DATES_CSV} (date conversion) ---")
    df = pd.read_csv(FIX_DATES_CSV)
    print(f"Loaded {len(df)} rows")

    update_rows = []
    skipped = 0
    examples = []

    for _, row in df.iterrows():
        junction_id = row['species_trait_junction_id']
        old_value = row['working_value']
        new_value = convert_date_string(old_value)

        if new_value == old_value:
            skipped += 1
            continue

        new_value_sql = escape_sql_string(new_value)
        update_rows.append(
            f"UPDATE species_traits_junction SET working_value = {new_value_sql} "
            f"WHERE species_trait_junction_id = {junction_id};"
        )

        if len(examples) < 5:
            examples.append((old_value, new_value))

    print(f"  Updates: {len(update_rows)}")
    print(f"  Skipped: {skipped}")
    print("  Sample conversions:")
    for old, new in examples:
        print(f"    {old} -> {new}")

    return update_rows


def main():
    bad_updates, ai_count = process_bad_rows()
    date_updates = process_date_conversion()

    all_updates = bad_updates + date_updates

    print(f"\n--- Summary ---")
    print(f"  Multi-value cleanup updates: {len(bad_updates)}")
    print(f"  Date conversion updates: {len(date_updates)}")
    print(f"  Total updates: {len(all_updates)}")

    print(f"\nWriting {OUTPUT_SQL}...")
    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write("-- Auto generated UPDATE statements for working_value cleanup\n")
        f.write(f"-- Total updates: {len(all_updates)}\n")
        f.write(f"-- Multi-value cleanup: {len(bad_updates)}\n")
        f.write(f"-- Date conversion: {len(date_updates)}\n\n")

        if bad_updates:
            f.write("-- === Multi-value cleanup ===\n")
            for stmt in bad_updates:
                f.write(stmt + "\n")
            f.write("\n")

        if date_updates:
            f.write("-- === Date conversion (Y/n -> month letters) ===\n")
            for stmt in date_updates:
                f.write(stmt + "\n")

    print(f"Done. File saved: {OUTPUT_SQL}")


if __name__ == '__main__':
    main()