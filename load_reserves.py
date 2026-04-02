import pandas as pd
from __init__ import app
from extensions import db
from models import Reserve

def load_reserves():
    df = pd.read_excel('Parks Gardens MD-580-list.xlsx', sheet_name='Parks Gardens MD', header=0)
    
    # Keep only the columns we need
    df = df[['ASSET_NAME', 'ASSET_TYPE', 'LOCATION']].copy()
    
    # Remove rows where ASSET_NAME is empty
    df = df.dropna(subset=['ASSET_NAME'])
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['ASSET_NAME'])
    
    count_added = 0
    count_skipped = 0
    
    with app.app_context():
        for _, row in df.iterrows():
            existing = db.session.query(Reserve).filter_by(
                reserve_name=str(row['ASSET_NAME'])
            ).one_or_none()
            
            if existing is None:
                reserve = Reserve(
                    reserve_name=str(row['ASSET_NAME']),
                    reserve_type=str(row['ASSET_TYPE']) if pd.notna(row['ASSET_TYPE']) else None,
                    reserve_address=str(row['LOCATION']) if pd.notna(row['LOCATION']) else None
                )
                db.session.add(reserve)
                count_added += 1
            else:
                count_skipped += 1
        
        db.session.commit()
        print(f"Done. Added: {count_added}, Skipped (already exist): {count_skipped}")

if __name__ == '__main__':
    load_reserves()