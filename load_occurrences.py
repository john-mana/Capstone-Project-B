import pandas as pd
from __init__ import app
from extensions import db
from models import Occurrence, Species

def load_occurrences():
    df = pd.read_excel('ALA-LansdowneSouth.xlsx', sheet_name='records-2026-03-03', header=0)
    
    print(f"Total records in file: {len(df)}")
    
    count_added = 0
    count_skipped = 0
    count_no_species = 0
    
    with app.app_context():
        for _, row in df.iterrows():
            scientific_name = row.get('scientificName')
            
            # Skip if no scientific name
            if pd.isna(scientific_name):
                count_skipped += 1
                continue
            
            # Check if species exists in species table
            existing_species = db.session.query(Species).filter_by(
                scientific_name=str(scientific_name)
            ).one_or_none()
            
            if existing_species is None:
                count_no_species += 1
                continue
            
            # Parse event date
            event_date = None
            if pd.notna(row.get('eventDate')):
                try:
                    event_date = pd.to_datetime(row['eventDate'])
                except:
                    event_date = None
            
            occurrence = Occurrence(
                scientific_name=str(scientific_name),
                event_date=event_date,
                dataset_name=str(row['datasetName']) if pd.notna(row.get('datasetName')) else None,
                decimal_latitude=float(row['decimalLatitude']) if pd.notna(row.get('decimalLatitude')) else None,
                decimal_longitude=float(row['decimalLongitude']) if pd.notna(row.get('decimalLongitude')) else None,
                individual_count=int(row['individualCount']) if pd.notna(row.get('individualCount')) else None,
                reproductive_condition=str(row['reproductiveCondition']) if pd.notna(row.get('reproductiveCondition')) else None,
                establishment_means=str(row['establishmentMeans']) if pd.notna(row.get('establishmentMeans')) else None,
                occurrence_remarks=str(row['occurrenceRemarks']) if pd.notna(row.get('occurrenceRemarks')) else None,
                year=int(row['year']) if pd.notna(row.get('year')) else None,
                month=str(row['month']) if pd.notna(row.get('month')) else None,
                day=int(row['day']) if pd.notna(row.get('day')) else None,
                habitat=str(row['habitat']) if pd.notna(row.get('habitat')) else None,
                sampling_protocol=str(row['samplingProtocol']) if pd.notna(row.get('samplingProtocol')) else None,
                locality=str(row['locality']) if pd.notna(row.get('locality')) else None,
                location_remarks=str(row['locationRemarks']) if pd.notna(row.get('locationRemarks')) else None,
                identified_by=str(row['identifiedBy']) if pd.notna(row.get('identifiedBy')) else None,
                date_identified=str(row['dateIdentified']) if pd.notna(row.get('dateIdentified')) else None,
                owner_institution_code=str(row['ownerInstitutionCode']) if pd.notna(row.get('ownerInstitutionCode')) else None,
                basis_of_record=str(row['basisOfRecord']) if pd.notna(row.get('basisOfRecord')) else None,
                data_generalizations=str(row['dataGeneralizations']) if pd.notna(row.get('dataGeneralizations')) else None,
                recorded_by=str(row['recordedBy']) if pd.notna(row.get('recordedBy')) else None,
            )
            
            db.session.add(occurrence)
            count_added += 1
            
            # Commit in batches of 100
            if count_added % 100 == 0:
                db.session.commit()
                print(f"Progress: {count_added} added so far...")
        
        db.session.commit()
        print(f"Done. Added: {count_added}, No species match: {count_no_species}, Skipped: {count_skipped}")

if __name__ == '__main__':
    load_occurrences()


# test