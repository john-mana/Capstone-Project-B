#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import pandas as pd
import numpy as np
import sys
import os

# Add project root directory to Python path
THIS_DIR = Path(__file__).resolve().parent
PROJ_ROOT = THIS_DIR.parents[2]
sys.path.append(str(PROJ_ROOT))

# Import Flask app and database models
import sys
import os
sys.path.append(str(PROJ_ROOT))

# Set environment variables (if needed)
os.environ.setdefault('DATABASE_URL', 'sqlite:///instance/users.db')

from __init__ import app, db
from models import Species, Traits, SpeciesTraitJunction

# ===== Directories =====
OUT_DIR = PROJ_ROOT / "static" / "report" / "experiment5" / "experiment5_outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Load data from database ----------
def load_from_database():
    """Load species-trait data from SQL database"""
    with app.app_context():
        # Query all species-trait association data
        query = db.session.query(
            SpeciesTraitJunction.scientific_name,
            SpeciesTraitJunction.trait_name,
            SpeciesTraitJunction.trait_value,
            Traits.trait_info
        ).join(
            Traits, SpeciesTraitJunction.trait_name == Traits.trait_name
        ).filter(
            SpeciesTraitJunction.trait_value.isnot(None),
            SpeciesTraitJunction.trait_value != '',
            SpeciesTraitJunction.trait_value != 'nan'
        )
        
        # Convert to DataFrame
        data = []
        for row in query.all():
            data.append({
                'scientific_name': row.scientific_name,
                'trait_name': row.trait_name,
                'trait_value': row.trait_value,
                'trait_info': row.trait_info
            })
        
        df = pd.DataFrame(data)
        
        # Infer trait_type based on trait_info (trait category)
        # This needs to be classified based on actual trait_info content
        def get_trait_type(trait_name, trait_info):
            if pd.isna(trait_info):
                return "Uncategorized"
            
            trait_info_lower = str(trait_info).lower()
            trait_name_lower = str(trait_name).lower()
            
            # Infer category based on trait_name and trait_info
            if any(keyword in trait_name_lower for keyword in ['flower', 'bloom', 'blossom']):
                return "Flower"
            elif any(keyword in trait_name_lower for keyword in ['leaf', 'foliage']):
                return "Leaf"
            elif any(keyword in trait_name_lower for keyword in ['seed', 'fruit']):
                return "Seed/Fruit"
            elif any(keyword in trait_name_lower for keyword in ['root', 'stem', 'height']):
                return "Structure"
            elif any(keyword in trait_name_lower for keyword in ['fire', 'tolerance']):
                return "Fire Response"
            elif any(keyword in trait_name_lower for keyword in ['water', 'drought']):
                return "Water Response"
            elif any(keyword in trait_name_lower for keyword in ['soil', 'nutrient']):
                return "Soil Response"
            else:
                return "Other"
        
        df['trait_type'] = df.apply(lambda x: get_trait_type(x['trait_name'], x['trait_info']), axis=1)
        
        return df

# ---------- Statistics ----------
def compute_stats(df: pd.DataFrame):
    """Calculate statistics according to task requirements"""
    with app.app_context():
        # 1. Total species per trait & type
        # How many species per trait
        trait_sp_count = df.groupby("trait_name")["scientific_name"].nunique().sort_values(ascending=False)
        
        # How many species per trait type
        type_sp_count = df.groupby("trait_type")["scientific_name"].nunique().sort_values(ascending=False)
        
        # 2. Total types & traits per species
        # How many trait types per species
        species_type_count = df.groupby("scientific_name")["trait_type"].nunique().sort_values(ascending=False)
        
        # How many traits per species
        species_trait_count = df.groupby("scientific_name")["trait_name"].nunique().sort_values(ascending=False)
        
        # 3. List species with no traits
        # Get all species
        all_species_query = db.session.query(Species.scientific_name).all()
        all_species = set([s.scientific_name for s in all_species_query])
        
        # Species with trait records
        species_with_traits = set(df["scientific_name"].unique())
        
        # Species without traits
        species_no_traits = list(all_species - species_with_traits)
        
        # 4. List traits & trait categories with no species
        # Get all traits
        all_traits_query = db.session.query(Traits.trait_name).all()
        all_traits = set([t.trait_name for t in all_traits_query])
        
        # Traits with species records
        traits_with_species = set(df["trait_name"].unique())
        
        # Traits without species
        traits_no_species = list(all_traits - traits_with_species)
        
        # Trait types without species
        types_with_species = set(df["trait_type"].unique())
        all_types = set(df["trait_type"].unique())  # Simplified handling here, may need to get all possible types from elsewhere
        types_no_species = []  # Simplified handling, as types are inferred
        
        # 5. Detailed trait statistics (trait name + trait value -> species count)
        trait_value_stats = df.groupby(["trait_name", "trait_value"])["scientific_name"].nunique().sort_values(ascending=False)
        
        return {
            "trait_sp_count": trait_sp_count,
            "type_sp_count": type_sp_count,
            "species_trait_count": species_trait_count,
            "species_type_count": species_type_count,
            "species_no_traits": species_no_traits,
            "traits_no_species": traits_no_species,
            "types_no_species": types_no_species,
            "trait_value_stats": trait_value_stats,
            "long": df
        }

# ---------- Data processing functions ----------

# ---------- Main process ----------
def main():
    print(f"[INFO] Loading data from database...")
    df = load_from_database()
    print(f"[INFO] Loaded {len(df)} trait records for {df['scientific_name'].nunique()} species")
    stats = compute_stats(df)

    # Generate HTML report (contains all statistical information)

    # Generate HTML report
    # Prepare data tables
    trait_sp_table = stats["trait_sp_count"].to_frame("Species Count").reset_index()
    type_sp_table = stats["type_sp_count"].to_frame("Species Count").reset_index()
    species_trait_table = stats["species_trait_count"].to_frame("Trait Count").reset_index()
    species_type_table = stats["species_type_count"].to_frame("Type Count").reset_index()
    
    # Detailed trait value statistics
    trait_value_table = stats["trait_value_stats"].to_frame("Species Count").reset_index()
    
    def create_table_html(df, title, col_name):
        if df.empty:
            return f"<h3>{title}</h3><p>No data available</p>"
        
        html = f"<h3>{title}</h3><table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += f"<tr><th>{df.columns[0]}</th><th>{col_name}</th></tr>"
        for _, row in df.iterrows():
            html += f"<tr><td>{row.iloc[0]}</td><td>{row.iloc[1]}</td></tr>"
        html += "</table>"
        return html
    
    def create_detailed_table_html(df, title):
        if df.empty:
            return f"<h3>{title}</h3><p>No data available</p>"
        
        html = f"<h3>{title}</h3><table border='1' style='border-collapse: collapse; width: 100%;'>"
        html += f"<tr><th>Trait Name</th><th>Trait Value</th><th>Species Count</th></tr>"
        for _, row in df.iterrows():
            html += f"<tr><td>{row.iloc[0]}</td><td>{row.iloc[1]}</td><td>{row.iloc[2]}</td></tr>"
        html += "</table>"
        return html
    
    # 1. Total species per trait & type
    trait_sp_html = create_table_html(trait_sp_table, "1. Total Species per Trait", "Species Count")
    type_sp_html = create_table_html(type_sp_table, "1. Total Species per Trait Type", "Species Count")
    
    # 2. Total types & traits per species - Save as CSV files
    species_trait_table.to_csv(OUT_DIR / "total_traits_per_species.csv", index=False)
    species_type_table.to_csv(OUT_DIR / "total_trait_types_per_species.csv", index=False)
    
    # 3. Detailed trait value statistics - Save as CSV file
    trait_value_table.to_csv(OUT_DIR / "detailed_trait_value_statistics.csv", index=False)
    
    # 4. Species with no traits
    no_traits_list = stats['species_no_traits']  # Show all species
    no_traits_html = f"<h3>4. Species with No Traits (Count: {len(stats['species_no_traits'])})</h3>"
    if no_traits_list:
        no_traits_html += "<ul>"
        for species in no_traits_list:
            no_traits_html += f"<li>{species}</li>"
        no_traits_html += "</ul>"
    else:
        no_traits_html += "<p>All species have trait records</p>"
    
    # 5. Traits with no species
    no_species_traits_list = stats['traits_no_species'][:50]  # Show only first 50
    no_species_traits_html = f"<h3>5. Traits with No Species (Count: {len(stats['traits_no_species'])})</h3>"
    if no_species_traits_list:
        no_species_traits_html += "<ul>"
        for trait in no_species_traits_list:
            no_species_traits_html += f"<li>{trait}</li>"
        no_species_traits_html += "</ul>"
        if len(stats['traits_no_species']) > 50:
            no_species_traits_html += f"<p>... and {len(stats['traits_no_species']) - 50} more traits</p>"
    else:
        no_species_traits_html += "<p>All traits have species records</p>"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Experiment 5 - Environmental Impact Study Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; }}
            h3 {{ color: #7f8c8d; }}
            .section {{ margin: 30px 0; }}
            table {{ margin: 10px 0; }}
            th, td {{ padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            ul {{ max-height: 300px; overflow-y: auto; }}
        </style>
    </head>
    <body>
        <h1>Experiment 5 - Environmental Impact Study Report</h1>
        <h2>Trait Summaries with Traits Grouped by Trait Type</h2>
        
        <div class="section">
            {trait_sp_html}
        </div>
        
        <div class="section">
            {type_sp_html}
        </div>
        
        <div class="section">
            {no_traits_html}
        </div>
        
        <div class="section">
            {no_species_traits_html}
        </div>
    </body>
    </html>
    """
    
    with open(OUT_DIR / "trait_summary_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[OK] HTML report saved to: {OUT_DIR / 'trait_summary_report.html'}")
    print(f"[OK] CSV files saved:")
    print(f"  - total_traits_per_species.csv")
    print(f"  - total_trait_types_per_species.csv") 
    print(f"  - detailed_trait_value_statistics.csv")

if __name__ == "__main__":
    main()
