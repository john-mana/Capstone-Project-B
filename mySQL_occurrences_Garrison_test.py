import pandas as pd
import json
from pathlib import Path

# INITIAL CONFIGURATION

INPUT_PATH = "Garrison-records-2026-04-14.csv"      # need to chage when the source is different
INPUT_TYPE = "csv"                         # "xlsx" or "csv"
SHEET_NAME = ""                       # only used if INPUT_TYPE == "xlsx"
OUTPUT_SQL = "Garrison_import.sql"     # output name

SOURCE_NAME = "ALA"
DATASET_NAME = "Garrison-Records"   # change this for each import file

# HELPERS TO CLEAN UP THE DATASET

def clean(v):
    if pd.isna(v):
        return None
    if isinstance(v, str):
        v = v.strip()
        return v if v != "" else None
    return v


def sql_escape_string(s: str) -> str:
    return s.replace("\\", "\\\\").replace("'", "''")


def sql_literal(v):
    v = clean(v)
    if v is None:
        return "NULL"
    if isinstance(v, pd.Timestamp):
        return f"'{v.strftime('%Y-%m-%d %H:%M:%S')}'"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    return f"'{sql_escape_string(str(v))}'"


def parse_datetime(v):
    v = clean(v)
    if v is None:
        return None
    try:
        dt = pd.to_datetime(v, errors="coerce")
        if pd.isna(dt):
            return None
        return dt
    except Exception:
        return None


def json_sql_literal(v):
    v = clean(v)
    if v is None:
        return "NULL"

    if isinstance(v, str):
        try:
            json.loads(v)
            return f"'{sql_escape_string(v)}'"
        except Exception:
            wrapped = json.dumps({"raw": v}, ensure_ascii=False)
            return f"'{sql_escape_string(wrapped)}'"

    wrapped = json.dumps({"raw": str(v)}, ensure_ascii=False)
    return f"'{sql_escape_string(wrapped)}'"


def find_col(df, candidates):
    cols = {str(c).strip().lower(): str(c).strip() for c in df.columns}
    for c in candidates:
        if c.lower() in cols:
            return cols[c.lower()]
    return None

# DATA LOAD

if INPUT_TYPE.lower() == "xlsx":
    df = pd.read_excel(INPUT_PATH, sheet_name=SHEET_NAME)
elif INPUT_TYPE.lower() == "csv":
    df = pd.read_csv(INPUT_PATH)
else:
    raise ValueError("INPUT_TYPE must be either 'xlsx' or 'csv'")

df.columns = [str(c).strip() for c in df.columns]

# MATCHING THE COLUMNS

col_scientific = find_col(df, ["scientificName", "scientific_name"])
col_vernacular = find_col(df, ["vernacularName", "vernacular_name", "commonName"])

col_lat = find_col(df, ["decimalLatitude", "decimal_latitude"])
col_lon = find_col(df, ["decimalLongitude", "decimal_longitude"])
col_event = find_col(df, ["eventDate", "event_date"])
col_recorded_by = find_col(df, ["recordedBy", "recorded_by"])

col_data_gen = find_col(df, ["dataGeneralizations", "data_generalisations", "data_generalizations"])
col_dynamic = find_col(df, ["dynamicProperties", "dynamic_properties"])

col_kingdom = find_col(df, ["kingdom"])
col_phylum = find_col(df, ["phylum"])
col_class = find_col(df, ["class"])
col_order = find_col(df, ["order"])
col_family = find_col(df, ["family"])
col_genus = find_col(df, ["genus"])
col_epithet = find_col(df, ["specificEpithet", "species_epithet"])

required = {
    "scientific_name": col_scientific,
    "decimal_latitude": col_lat,
    "decimal_longitude": col_lon,
    "event_date": col_event,
}

missing = [k for k, v in required.items() if v is None]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

# BUILD TAXONOMY ROWS

taxonomy_rows = []
taxonomy_seen = set()

for _, row in df.iterrows():
    scientific_name = clean(row[col_scientific])
    if not scientific_name:
        continue

    tax_key = (
        clean(row[col_kingdom]) if col_kingdom else None,
        clean(row[col_phylum]) if col_phylum else None,
        clean(row[col_class]) if col_class else None,
        clean(row[col_order]) if col_order else None,
        clean(row[col_family]) if col_family else None,
        clean(row[col_genus]) if col_genus else None,
        clean(row[col_epithet]) if col_epithet else None,
    )

    if tax_key not in taxonomy_seen:
        taxonomy_seen.add(tax_key)
        taxonomy_rows.append(tax_key)

# BUILD SPECIES ROWS

species_rows = []
species_seen = set()

for _, row in df.iterrows():
    scientific_name = clean(row[col_scientific])
    if not scientific_name:
        continue

    vernacular_name = clean(row[col_vernacular]) if col_vernacular else None
    tax_key = (
        clean(row[col_kingdom]) if col_kingdom else None,
        clean(row[col_phylum]) if col_phylum else None,
        clean(row[col_class]) if col_class else None,
        clean(row[col_order]) if col_order else None,
        clean(row[col_family]) if col_family else None,
        clean(row[col_genus]) if col_genus else None,
        clean(row[col_epithet]) if col_epithet else None,
    )

    sp_key = (scientific_name,)
    if sp_key not in species_seen:
        species_seen.add(sp_key)
        species_rows.append((scientific_name, vernacular_name, tax_key))

# GENERATE SQL

lines = []
lines.append("/* ALA import SQL generated automatically */")
lines.append("-- Generated from source file using Python")
lines.append("")

# dataset
lines.append(
    f"INSERT INTO datasets (source_name, dataset_name, most_recent_download_date) "
    f"VALUES ({sql_literal(SOURCE_NAME)}, {sql_literal(DATASET_NAME)}, NOW());"
)
lines.append("")

# taxonomy
for tax in taxonomy_rows:
    kingdom, phylum, class_name, order_name, family, genus, epithet = tax
    lines.append(
        "INSERT INTO taxonomy "
        "(kingdom, phylum, class_name, order_name, family, genus, species_epithet) "
        f"VALUES ({sql_literal(kingdom)}, {sql_literal(phylum)}, {sql_literal(class_name)}, "
        f"{sql_literal(order_name)}, {sql_literal(family)}, {sql_literal(genus)}, {sql_literal(epithet)});"
    )
lines.append("")

# species
for scientific_name, vernacular_name, tax in species_rows:
    kingdom, phylum, class_name, order_name, family, genus, epithet = tax
    lines.append(
        "INSERT IGNORE INTO species "
        "(taxonomy_id, scientific_name, vernacular_name, native_flag, endangered_status_code) "
        "VALUES ("
        " (SELECT taxonomy_id FROM taxonomy "
        f"   WHERE COALESCE(kingdom,'') = COALESCE({sql_literal(kingdom)}, '')"
        f"     AND COALESCE(phylum,'') = COALESCE({sql_literal(phylum)}, '')"
        f"     AND COALESCE(class_name,'') = COALESCE({sql_literal(class_name)}, '')"
        f"     AND COALESCE(order_name,'') = COALESCE({sql_literal(order_name)}, '')"
        f"     AND COALESCE(family,'') = COALESCE({sql_literal(family)}, '')"
        f"     AND COALESCE(genus,'') = COALESCE({sql_literal(genus)}, '')"
        f"     AND COALESCE(species_epithet,'') = COALESCE({sql_literal(epithet)}, '')"
        "   LIMIT 1), "
        f"{sql_literal(scientific_name)}, {sql_literal(vernacular_name)}, NULL, NULL"
        ");"
    )
lines.append("")

# occurrences
for _, row in df.iterrows():
    scientific_name = clean(row[col_scientific])
    if not scientific_name:
        continue

    lat = clean(row[col_lat])
    lon = clean(row[col_lon])
    event_date = parse_datetime(row[col_event])
    recorded_by = clean(row[col_recorded_by]) if col_recorded_by else None
    data_generalisations = clean(row[col_data_gen]) if col_data_gen else None
    dynamic_properties = row[col_dynamic] if col_dynamic else None

    lines.append(
        "INSERT INTO occurrences "
        "("
        "dataset_id, species_id, reserve_id, pct_id, scientific_name, "
        "decimal_latitude, decimal_longitude, event_date, recorded_by, "
        "most_recent_flag, data_generalisations, dynamic_properties"
        ") VALUES ("
        f"(SELECT dataset_id FROM datasets WHERE source_name = {sql_literal(SOURCE_NAME)} "
        f" AND dataset_name = {sql_literal(DATASET_NAME)} ORDER BY dataset_id DESC LIMIT 1), "
        f"(SELECT species_id FROM species WHERE scientific_name = {sql_literal(scientific_name)} LIMIT 1), "
        "NULL, NULL, "
        f"{sql_literal(scientific_name)}, "
        f"{sql_literal(lat)}, "
        f"{sql_literal(lon)}, "
        f"{sql_literal(event_date)}, "
        f"{sql_literal(recorded_by)}, "
        "0, "
        f"{sql_literal(data_generalisations)}, "
        f"{json_sql_literal(dynamic_properties)}"
        ");"
    )

Path(OUTPUT_SQL).write_text("\n".join(lines), encoding="utf-8")

print(f"Done. SQL file generated: {OUTPUT_SQL}")
print(f"Rows in source file: {len(df)}")
print(f"Unique taxonomy rows: {len(taxonomy_rows)}")
print(f"Unique species rows: {len(species_rows)}")