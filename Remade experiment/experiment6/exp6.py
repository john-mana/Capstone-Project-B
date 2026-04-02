import os
from pathlib import Path

import pandas as pd

try:
    import psycopg2
except Exception as e:
    raise ImportError(
        "psycopg2 is not installed or could not be imported; install it with:\n"
        "    python -m pip install psycopg2-binary\n"
        f"Original import error: {e}"
    )


def _db_config():
    """Collect database connection details from environment variables."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    return {
        "host": os.getenv("PGHOST", os.getenv("POSTGRES_HOST", "db")),
        "database": os.getenv("PGDATABASE", os.getenv("POSTGRES_DB", "plants_db")),
        "user": os.getenv("PGUSER", os.getenv("POSTGRES_USER", "postgres")),
        "password": os.getenv("PGPASSWORD", os.getenv("POSTGRES_PASSWORD", "")),
        "port": int(os.getenv("PGPORT", os.getenv("POSTGRES_PORT", "5432"))),
    }


def _resolve_output_dir() -> Path:
    """Resolve the experiment 6 output directory."""
    raw = os.getenv("E6_OUTPUT_DIR")
    path = Path(raw) if raw else Path.cwd() / "experiment6_outputs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _map_value(val):
    if pd.isnull(val) or str(val).strip() == "":
        return ""
    if str(val).strip().upper() == "I":
        return "I"
    return "Y"


def _is_native(exotic_value) -> bool:
    if pd.isnull(exotic_value):
        return False
    if isinstance(exotic_value, bool):
        return not exotic_value
    val = str(exotic_value).strip().lower()
    return val in {"f", "false", "0", "n", "no"}


def main() -> Path:
    output_dir = _resolve_output_dir()
    db_config = _db_config()

    if isinstance(db_config, str):
        conn = psycopg2.connect(db_config)
    else:
        conn = psycopg2.connect(**db_config)

    try:
        traits_df = pd.read_sql("SELECT * FROM traits", conn)
        species_df = pd.read_sql("SELECT * FROM species", conn)
        stj_df = pd.read_sql("SELECT * FROM species_trait_junction", conn)
    finally:
        conn.close()

    exotic_counts = species_df["exotic"].fillna("<NULL>").value_counts()
    print("Exotic flag distribution:", exotic_counts.to_dict())

    native_mask = species_df["exotic"].apply(_is_native)
    native_species = species_df.loc[native_mask, "scientific_name"].dropna().unique()
    print(f"Number of native species: {len(native_species)}")

    stj_df = stj_df[stj_df["scientific_name"].isin(native_species)]
    print(f"Number of species-trait rows after filtering: {len(stj_df)}")

    if stj_df.empty:
        print("No species trait data matched the native species filter.")

    stj_df = stj_df.merge(traits_df, on="trait_name", how="left")
    stj_df["YI"] = stj_df["trait_value"].apply(_map_value)

    pivot_df = stj_df.pivot_table(
        index="scientific_name",
        columns="trait_name",
        values="YI",
        aggfunc=lambda x: "I" if "I" in set(x) else ("Y" if "Y" in set(x) else ""),
        fill_value="",
    )

    traits_indexed = traits_df.set_index("trait_name")
    available = [c for c in pivot_df.columns if c in traits_indexed.index]
    if available:
        trait_order = traits_indexed.loc[available, "trait_info"].sort_values()
        pivot_df = pivot_df[trait_order.index]
    else:
        print("No trait columns available after pivot.")

    print(f"Pivot table shape: {pivot_df.shape}")

    pivot_path = output_dir / "experiment6_native_species_traits_YI.xlsx"
    pivot_df.to_excel(pivot_path)
    print(f"Excel file created successfully: {pivot_path}")

    return pivot_path


if __name__ == "__main__":
    main()
