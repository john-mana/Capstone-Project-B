import pandas as pd
import geopandas as gpd #this handles geometry as it needs to handle polygons
from pathlib import Path

# File paths (change if needed)

BASE_DIR = Path('.') #current folder
SHAPEFILES_DIR = BASE_DIR / 'Shapefiles'

OCCURRENCES_CSV = SHAPEFILES_DIR / 'occurrences.csv' #input file
RESERVE_SHP = SHAPEFILES_DIR / 'Parks Gardens MD_region.shp' #polygon shapefile
PCT_SHP = SHAPEFILES_DIR / '2022 vegetation mapping.shp' #polygon shapefile

# Output directory
OUTPUT_DIR = BASE_DIR / 'Mapping Files'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Output files
RESERVES_IMPORT_CSV = OUTPUT_DIR / 'reserves_import.csv'  # to import
PCTS_IMPORT_CSV = OUTPUT_DIR / 'pcts_import.csv'  # to import
MAPPING_TEMP_CSV = OUTPUT_DIR / 'occurrence_mapping_temp.csv'  # mapping result for each occurrence record
DIAGNOSTICS_CSV = OUTPUT_DIR / 'occurrence_mapping_diagnostics.csv'  # what rows were not mapped

#read three files
def load_inputs():
    occurrences = pd.read_csv(OCCURRENCES_CSV) #need to export the file from db
    reserves_gdf = gpd.read_file(RESERVE_SHP) #shapefile has to be ready
    pct_gdf = gpd.read_file(PCT_SHP) #shapefile has to be ready
    return occurrences, reserves_gdf, pct_gdf

#read shapefile (Created csv form to import it to reserves table)
def build_reserves_import(reserves_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Build the reserves lookup table import file based on the agreed DB structure.
    reserve_id is created from row order because the target table uses an internal PK.
    """
    reserves_df = reserves_gdf.copy() #not to damage the original dataset

    #look up location, if none, suburb, else, NULL
    location_series = None
    if 'LOCATION' in reserves_df.columns:
        location_series = reserves_df['LOCATION']
    elif 'SUBURB' in reserves_df.columns:
        location_series = reserves_df['SUBURB']
    else:
        location_series = pd.Series([None] * len(reserves_df))

    if 'SUBURB' in reserves_df.columns:
        location_series = location_series.fillna(reserves_df['SUBURB'])

    #final reserves outcome to import
    out = pd.DataFrame({
        'reserve_id': range(1, len(reserves_df) + 1),
        'asset_name': reserves_df['ASSET_NAME'] if 'ASSET_NAME' in reserves_df.columns else None,
        'location': location_series,
        'asset_type': reserves_df['ASSET_TYPE'] if 'ASSET_TYPE' in reserves_df.columns else None,
        'asset_class': reserves_df['ASSET_CLAS'] if 'ASSET_CLAS' in reserves_df.columns else None,
        'shape_file_name': RESERVE_SHP.name,
        'shape_file_path': str(RESERVE_SHP)
    })
    return out


def build_pcts_import(pct_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Build the PCT lookup table import file.
    The shapefile contains many polygons per PCT, so we deduplicate by pct_code.
    pct_id is created from row order because the target table uses an internal PK.
    """
    pct_df = pct_gdf.copy()

    #extract necessary columns only
    cols = ['PCTID', 'PCTName', 'vegForm']
    available = [c for c in cols if c in pct_df.columns]
    lookup = pct_df[available].copy()

    rename_map = {
        'PCTID': 'pct_code',
        'PCTName': 'pct_name',
        'vegForm': 'vegetation_form'
    }
    lookup = lookup.rename(columns=rename_map)

    #convert all into String format to prevent type mismatch 
    if 'pct_code' in lookup.columns:
        lookup['pct_code'] = lookup['pct_code'].astype(str)

    #no duplicated pct_code in db
    lookup = lookup.drop_duplicates(subset=['pct_code']).reset_index(drop=True)
    lookup.insert(0, 'pct_id', range(1, len(lookup) + 1))
    lookup['form_pct'] = None
    #final outcome columns
    return lookup[['pct_id', 'pct_code', 'pct_name', 'vegetation_form', 'form_pct']]


#convert long/latitude into pinpoint on the map
def build_occurrence_points(occurrences: pd.DataFrame) -> gpd.GeoDataFrame:

    #make sure that there are critical columns, if not, stop
    needed = ['occurrence_id', 'decimal_latitude', 'decimal_longitude']
    missing = [c for c in needed if c not in occurrences.columns]
    if missing:
        raise ValueError(f'Missing required occurrence columns: {missing}')

    #remove rows do not contain coordinates
    occ = occurrences.copy()
    occ = occ.dropna(subset=['decimal_latitude', 'decimal_longitude']).copy()

    # Drop existing mapping columns to avoid merge name conflicts
    for col in ['reserve_id', 'pct_id']:
        if col in occ.columns:
            occ = occ.drop(columns=col)

    #create point geometry  &&&&&&&must be in order - longitude first &&&&&&&
    occ_gdf = gpd.GeoDataFrame(
        occ,
        geometry=gpd.points_from_xy(occ['decimal_longitude'], occ['decimal_latitude']),
        crs='EPSG:4326'
    )
    return occ_gdf


#map the points to reserve polygon -> output reserve_id***
def map_to_reserves(occ_gdf: gpd.GeoDataFrame, reserves_gdf: gpd.GeoDataFrame, reserves_lookup: pd.DataFrame) -> pd.DataFrame:
    # Match points to reserve polygons.

    #crs conversion -> both need to be using the same crs. Converting occurrence points to reserve shapefile's crs
    occ_proj = occ_gdf.to_crs(reserves_gdf.crs)

    reserve_join_cols = [c for c in ['ASSET_NAME', 'LOCATION', 'SUBURB', 'ASSET_TYPE', 'ASSET_CLAS', 'geometry'] if c in reserves_gdf.columns]
    reserve_polygons = reserves_gdf[reserve_join_cols].copy()
    reserve_polygons['reserve_row_id'] = range(1, len(reserve_polygons) + 1)

    # within = point must be inside polygon.
    joined = gpd.sjoin(occ_proj, reserve_polygons, how='left', predicate='within')

    # Use row order mapping because reserves_import was created in the same polygon order.
    row_to_reserve_id = pd.DataFrame({
        'reserve_row_id': range(1, len(reserves_lookup) + 1),
        'reserve_id': reserves_lookup['reserve_id']
    })

    joined = joined.merge(row_to_reserve_id, on='reserve_row_id', how='left')
    return joined[['occurrence_id', 'reserve_id']].drop_duplicates(subset=['occurrence_id'])


def map_to_pcts(occ_gdf: gpd.GeoDataFrame, pct_gdf: gpd.GeoDataFrame, pcts_lookup: pd.DataFrame) -> pd.DataFrame:
    occ_proj = occ_gdf.to_crs(pct_gdf.crs)

    pct_polygons = pct_gdf[['PCTID', 'geometry']].copy()
    pct_polygons['PCTID'] = pct_polygons['PCTID'].astype(str)

    joined = gpd.sjoin(occ_proj, pct_polygons, how='left', predicate='within')

    lookup = pcts_lookup[['pct_id', 'pct_code']].copy()
    lookup['pct_code'] = lookup['pct_code'].astype(str)

    joined = joined.merge(lookup, left_on='PCTID', right_on='pct_code', how='left')
    return joined[['occurrence_id', 'pct_id']].drop_duplicates(subset=['occurrence_id'])


def build_diagnostics(occurrences: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    base = occurrences[['occurrence_id', 'scientific_name', 'decimal_latitude', 'decimal_longitude']].copy()
    diag = base.merge(mapping, on='occurrence_id', how='left')
    diag['missing_reserve'] = diag['reserve_id'].isna() # look up rows without reserve/pct mappings
    diag['missing_pct'] = diag['pct_id'].isna() # look up rows without reserve/pct mappings
    return diag

def write_mapping_temp_csv(mapping: pd.DataFrame, output_path: Path) -> None:
    """
    Write mapping CSV in a DB-friendly format:
    - occurrence_id as integer
    - reserve_id / pct_id as integer when present
    - NULL text when missing
    """
    clean = mapping.copy()

    # Force numeric conversion first
    clean['occurrence_id'] = pd.to_numeric(clean['occurrence_id'], errors='raise').astype('Int64')
    clean['reserve_id'] = pd.to_numeric(clean['reserve_id'], errors='coerce').astype('Int64')
    clean['pct_id'] = pd.to_numeric(clean['pct_id'], errors='coerce').astype('Int64')

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.write('occurrence_id,reserve_id,pct_id\n')
        for _, row in clean.iterrows():
            occ = 'NULL' if pd.isna(row['occurrence_id']) else str(int(row['occurrence_id']))
            reserve = 'NULL' if pd.isna(row['reserve_id']) else str(int(row['reserve_id']))
            pct = 'NULL' if pd.isna(row['pct_id']) else str(int(row['pct_id']))
            f.write(f'{occ},{reserve},{pct}\n')

#***CP to keep the order***
def main():
    occurrences, reserves_gdf, pct_gdf = load_inputs()

    reserves_import = build_reserves_import(reserves_gdf)
    pcts_import = build_pcts_import(pct_gdf)
    occ_gdf = build_occurrence_points(occurrences)

    reserve_map = map_to_reserves(occ_gdf, reserves_gdf, reserves_import)
    pct_map = map_to_pcts(occ_gdf, pct_gdf, pcts_import)

    mapping = occurrences[['occurrence_id']].copy().merge(reserve_map, on='occurrence_id', how='left')
    mapping = mapping.merge(pct_map, on='occurrence_id', how='left')

    diagnostics = build_diagnostics(occurrences, mapping)

    reserves_import.to_csv(RESERVES_IMPORT_CSV, index=False)
    pcts_import.to_csv(PCTS_IMPORT_CSV, index=False)
    write_mapping_temp_csv(mapping, MAPPING_TEMP_CSV)
    diagnostics.to_csv(DIAGNOSTICS_CSV, index=False)

    print('Done.')
    print(f'Reserves rows: {len(reserves_import)}')
    print(f'PCT rows: {len(pcts_import)}')
    print(f'Occurrence mapping rows: {len(mapping)}')
    print(f'Reserve matched: {mapping["reserve_id"].notna().sum()} / {len(mapping)}')
    print(f'PCT matched: {mapping["pct_id"].notna().sum()} / {len(mapping)}')
    print(f'Wrote: {RESERVES_IMPORT_CSV}')
    print(f'Wrote: {PCTS_IMPORT_CSV}')
    print(f'Wrote: {MAPPING_TEMP_CSV}')
    print(f'Wrote: {DIAGNOSTICS_CSV}')


if __name__ == '__main__':
    main()
