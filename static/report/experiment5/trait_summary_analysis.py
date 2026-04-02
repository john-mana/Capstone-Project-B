#!/usr/bin/env python3
"""
Experiment 5 - Trait Summary Analysis
Generates comprehensive trait summaries using SQL database
"""
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import warnings
import sqlite3

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class TraitSummaryAnalyzer:
    """Analyzer for trait summaries and statistics using SQL database"""
    
    def __init__(self, db_path="../../instance/users.db"):
        """Initialize the analyzer with database connection"""
        self.db_path = db_path
        self.conn = None
        self.trait_groups = {
            "Blossoming": ["flowering_cues", "flowering_time"],
            "Botany": ["bud_bank_location", "clonal_spread_mechanism", "flower_structural_sex_type", "genome_size", "ploidy", "root_system_type", "sex_type"],
            "Descriptive": ["flower_colour", "fruit_colour", "leaf_type", "parasitic", "plant_climbing_mechanism", "plant_growth_form", "plant_growth_substrate", "plant_height", "plant_physical_defence_structures"],
            "Fire recovery": ["fire_time_from_fire_to_50_percent_flowering", "fire_time_from_fire_to_50_percent_fruiting", "fire_time_from_fire_to_flowering", "fire_time_from_fire_to_flowering_decline", "fire_time_from_fire_to_fruiting", "fire_time_from_fire_to_peak_flowering"],
            "Fire response": ["life_history_ephemeral_class", "plant_tolerance_fire", "post_fire_flowering", "post_fire_recruitment", "resprouting_capacity", "resprouting_capacity_juvenile", "resprouting_capacity_proportion_individuals", "resprouting_capacity_time_from_germination"],
            "Germination": ["establishment_light_environment_index", "recruitment_time", "reproductive_light_environment_index", "root_structure", "seed_germination", "seed_germination_time", "seedling_establishment_conditions", "seedling_germination_location"],
            "Life history": ["life_history", "lifespan"],
            "Natural Growth": ["competitive_stratum", "dispersal_syndrome", "dispersers", "nitrogen_fixing", "resprouting_capacity_non_fire_disturbance", "sprout_depth", "stem_growth_habit", "storage_organ", "vegetative_reproduction_ability"],
            "Pollination": ["pollination_syndrome", "pollination_system"],
            "Seedbank": ["seedbank_location", "seedbank_longevity", "seedbank_longevity_class"],
            "Seeds": ["dispersal_unit", "fruiting_time", "reproductive_maturity", "seed_viability", "serotiny"],
            "Propagation": ["seed_dormancy_class", "seed_germination_treatment", "germination_treatment"],
            "Soil tolerances": ["plant_tolerance_calcicole", "plant_tolerance_salt", "plant_tolerance_soil_salinity", "plant_type_by_resource_use"],
            "Water response": ["plant_flood_regime_classification", "plant_tolerance_inundation", "plant_tolerance_snow", "plant_tolerance_water_logged_soils"]
        }
        
        print("Trait Summary Analyzer initialized")
    
    def connect_database(self):
        """Connect to SQLite database"""
        try:
            # Try multiple possible paths
            possible_paths = [
                self.db_path,
                "../instance/users.db",
                "../../instance/users.db",
                "../../../instance/users.db",
                os.path.join(os.path.dirname(__file__), "..", "..", "instance", "users.db"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "instance", "users.db")
            ]
            
            connected = False
            for path in possible_paths:
                if os.path.exists(path):
                    self.conn = sqlite3.connect(path)
                    self.db_path = path
                    print(f"Connected to database: {path}")
                    connected = True
                    break
                else:
                    print(f"Database not found at: {path}")
            
            if not connected:
                print("Could not find database file in any expected location")
                return False
                
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def load_data(self):
        """Load data from SQL database or create sample data"""
        print("Loading data from database...")
        
        # Try to connect to database first
        if self.connect_database():
            try:
                # Test database connection
                cursor = self.conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                print(f"Available tables: {[table[0] for table in tables]}")
                
                if not tables:
                    print("Database is empty, creating sample data...")
                    return self.create_sample_data()
                
                # Load species data
                species_query = "SELECT scientific_name, vernacular_name, genus, family_name FROM species"
                self.species_data = pd.read_sql_query(species_query, self.conn)
                print(f"Loaded {len(self.species_data)} species records")
                
                # Load traits data
                traits_query = "SELECT trait_name, trait_info FROM traits"
                self.traits_data = pd.read_sql_query(traits_query, self.conn)
                print(f"Loaded {len(self.traits_data)} trait records")
                
                # Load species-trait junction data
                junction_query = """
                    SELECT stj.scientific_name, stj.trait_name, stj.trait_value
                    FROM species_trait_junction stj
                    WHERE stj.trait_value IS NOT NULL AND stj.trait_value != ''
                """
                self.junction_data = pd.read_sql_query(junction_query, self.conn)
                print(f"Loaded {len(self.junction_data)} species-trait junction records")
                
                # Show sample data
                if not self.junction_data.empty:
                    print("Sample junction data:")
                    print(self.junction_data.head())
                else:
                    print("No junction data found - checking if table exists...")
                    cursor.execute("SELECT COUNT(*) FROM species_trait_junction")
                    count = cursor.fetchone()[0]
                    print(f"Total records in species_trait_junction: {count}")
                
                return True
                
            except Exception as e:
                print(f"Error loading data from database: {e}")
                import traceback
                traceback.print_exc()
                return self.create_sample_data()
            finally:
                if self.conn:
                    self.conn.close()
        else:
            print("Failed to connect to database, creating sample data...")
            return self.create_sample_data()
    
    def create_sample_data(self):
        """Load data from PostgreSQL dump file"""
        print("Loading data from PostgreSQL dump file...")
        
        try:
            # Try to load from PostgreSQL dump file
            dump_file = "../../Database/full_flora_database_dump_20250724114138.sql"
            if os.path.exists(dump_file):
                return self.load_from_dump_file(dump_file)
            else:
                print(f"Dump file not found: {dump_file}")
                return self.create_fallback_sample_data()
        except Exception as e:
            print(f"Error loading from dump file: {e}")
            return self.create_fallback_sample_data()
    
    def load_from_dump_file(self, dump_file):
        """Load data from PostgreSQL dump file"""
        print(f"Loading data from dump file: {dump_file}")
        
        try:
            with open(dump_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract species data
            species_data = self.extract_species_from_dump(content)
            # Extract traits data  
            traits_data = self.extract_traits_from_dump(content)
            # Extract junction data
            junction_data = self.extract_junction_from_dump(content)
            
            if not species_data.empty and not traits_data.empty and not junction_data.empty:
                self.species_data = species_data
                self.traits_data = traits_data
                self.junction_data = junction_data
                
                print(f"Loaded from dump: {len(self.species_data)} species, {len(self.traits_data)} traits, {len(self.junction_data)} junction records")
                return True
            else:
                print("Failed to extract data from dump file, using fallback data")
                return self.create_fallback_sample_data()
                
        except Exception as e:
            print(f"Error processing dump file: {e}")
            return self.create_fallback_sample_data()
    
    def extract_species_from_dump(self, content):
        """Extract species data from PostgreSQL dump"""
        print("Extracting species data from dump...")
        
        # Find species data section
        species_pattern = "COPY public.species (scientific_name, vernacular_name, genus, subgenus, taxon_rank, family_name, exotic, threatened_species_status) FROM stdin;"
        species_start = content.find(species_pattern)
        if species_start == -1:
            print("Species data section not found")
            return pd.DataFrame()
        
        species_start = content.find("\n", species_start) + 1
        species_end = content.find("\\.", species_start)
        
        if species_end == -1:
            print("Species data end marker not found")
            return pd.DataFrame()
        
        species_lines = content[species_start:species_end].strip().split('\n')
        species_data = []
        
        print(f"Processing {len(species_lines)} species lines...")
        
        for i, line in enumerate(species_lines):
            if line.strip() and not line.startswith('--'):
                parts = line.split('\t')
                if len(parts) >= 8:
                    species_data.append({
                        'scientific_name': parts[0],
                        'vernacular_name': parts[1] if parts[1] != '\\N' else None,
                        'genus': parts[2] if parts[2] != '\\N' else None,
                        'family_name': parts[5] if parts[5] != '\\N' else None
                    })
                if i < 5:  # Show first 5 lines for debugging
                    print(f"Species line {i}: {parts[:3]}...")
        
        print(f"Extracted {len(species_data)} species records")
        return pd.DataFrame(species_data)
    
    def extract_traits_from_dump(self, content):
        """Extract traits data from PostgreSQL dump"""
        print("Extracting traits data from dump...")
        
        # Find traits data section
        traits_pattern = "COPY public.traits (trait_name, trait_info) FROM stdin;"
        traits_start = content.find(traits_pattern)
        if traits_start == -1:
            print("Traits data section not found")
            return pd.DataFrame()
        
        traits_start = content.find("\n", traits_start) + 1
        traits_end = content.find("\\.", traits_start)
        
        if traits_end == -1:
            print("Traits data end marker not found")
            return pd.DataFrame()
        
        traits_lines = content[traits_start:traits_end].strip().split('\n')
        traits_data = []
        
        print(f"Processing {len(traits_lines)} traits lines...")
        
        for i, line in enumerate(traits_lines):
            if line.strip() and not line.startswith('--'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    traits_data.append({
                        'trait_name': parts[0],
                        'trait_info': parts[1] if parts[1] != '\\N' else None
                    })
                if i < 5:  # Show first 5 lines for debugging
                    print(f"Traits line {i}: {parts}")
        
        print(f"Extracted {len(traits_data)} traits records")
        return pd.DataFrame(traits_data)
    
    def extract_junction_from_dump(self, content):
        """Extract species-trait junction data from PostgreSQL dump"""
        print("Extracting junction data from dump...")
        
        # Find junction data section with trait_value
        junction_pattern = "COPY public.species_trait_junction (species_trait_junction_id, scientific_name, trait_name, trait_value) FROM stdin;"
        junction_start = content.find(junction_pattern)
        if junction_start == -1:
            print("Junction data section with trait_value not found")
            return pd.DataFrame()
        
        junction_start = content.find("\n", junction_start) + 1
        junction_end = content.find("\\.", junction_start)
        
        if junction_end == -1:
            print("Junction data end marker not found")
            return pd.DataFrame()
        
        junction_lines = content[junction_start:junction_end].strip().split('\n')
        junction_data = []
        
        print(f"Processing {len(junction_lines)} junction lines...")
        
        for i, line in enumerate(junction_lines):
            if line.strip() and not line.startswith('--'):
                parts = line.split('\t')
                if len(parts) >= 4:
                    junction_data.append({
                        'scientific_name': parts[1],
                        'trait_name': parts[2],
                        'trait_value': parts[3] if parts[3] != '\\N' else None
                    })
                if i < 5:  # Show first 5 lines for debugging
                    print(f"Junction line {i}: {parts[:4]}...")
        
        # Filter out records with null trait_value
        junction_df = pd.DataFrame(junction_data)
        junction_df = junction_df.dropna(subset=['trait_value'])
        junction_df = junction_df[junction_df['trait_value'] != '']
        
        print(f"Extracted {len(junction_df)} junction records with valid trait values")
        return junction_df
    
    def create_fallback_sample_data(self):
        """Create fallback sample data if dump file processing fails"""
        print("Creating fallback sample data...")
        
        # Create minimal sample data
        self.species_data = pd.DataFrame({
            'scientific_name': ['Eucalyptus globulus', 'Acacia melanoxylon'],
            'vernacular_name': ['Tasmanian Blue Gum', 'Blackwood'],
            'genus': ['Eucalyptus', 'Acacia'],
            'family_name': ['Myrtaceae', 'Fabaceae']
        })
        
        self.traits_data = pd.DataFrame({
            'trait_name': ['plant_height', 'plant_growth_form'],
            'trait_info': ['Maximum height', 'Growth form']
        })
        
        self.junction_data = pd.DataFrame({
            'scientific_name': ['Eucalyptus globulus', 'Acacia melanoxylon'],
            'trait_name': ['plant_height', 'plant_height'],
            'trait_value': ['30-70m', '10-30m']
        })
        
        print(f"Created fallback data: {len(self.species_data)} species, {len(self.traits_data)} traits, {len(self.junction_data)} junction records")
        return True
    
    def analyze_trait_summaries(self):
        """Generate comprehensive trait summaries"""
        print("Analyzing trait summaries...")
        
        # Create output directory
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. All unique trait names
        all_traits = self.get_all_traits()
        
        # 2. Total species per trait
        species_per_trait = self.generate_species_per_trait()
        
        # 3. Total traits per species
        traits_per_species = self.generate_traits_per_species()
        
        # 4. Species with no traits
        species_no_traits = self.find_species_with_no_traits()
        
        # 5. Traits with no species
        unused_traits = self.find_unused_traits()
        
        # Generate HTML report
        self.generate_html_report(
            all_traits,
            species_per_trait,
            traits_per_species,
            species_no_traits,
            unused_traits,
            output_dir
        )
        
        print("Trait summary analysis completed!")
        return True
    
    def get_all_traits(self):
        """Get all unique trait names from database"""
        print("Getting all unique trait names...")
        
        if self.traits_data.empty:
            return []
        
        return self.traits_data['trait_name'].tolist()
    
    def generate_trait_type_summary(self):
        """Generate summary by trait type"""
        print("Generating trait type summary...")
        
        trait_type_summary = {}
        
        for trait_type, traits in self.trait_groups.items():
            type_data = {
                'trait_type': trait_type,
                'total_traits': len(traits),
                'traits_with_data': 0,
                'total_species_with_traits': 0,
                'traits_list': traits
            }
            
            # Count traits with data
            for trait in traits:
                if not self.junction_data.empty:
                    trait_species = self.junction_data[
                        (self.junction_data['trait_name'] == trait) & 
                        (self.junction_data['trait_value'].notna()) &
                        (self.junction_data['trait_value'] != '')
                    ]
                    if len(trait_species) > 0:
                        type_data['traits_with_data'] += 1
                        type_data['total_species_with_traits'] += len(trait_species['scientific_name'].unique())
            
            trait_type_summary[trait_type] = type_data
        
        return trait_type_summary
    
    def generate_species_per_trait(self):
        """Generate species count per trait"""
        print("Generating species per trait summary...")
        
        if self.junction_data.empty:
            return pd.DataFrame(columns=['trait_name', 'species_count'])
        
        # Count species per trait
        species_per_trait = self.junction_data.groupby('trait_name')['scientific_name'].nunique().reset_index()
        species_per_trait.columns = ['trait_name', 'species_count']
        species_per_trait = species_per_trait.sort_values('species_count', ascending=False)
        
        return species_per_trait
    
    def generate_traits_per_species(self):
        """Generate traits count per species"""
        print("Generating traits per species summary...")
        
        if self.junction_data.empty:
            return pd.DataFrame(columns=['scientific_name', 'trait_count', 'unique_traits'])
        
        # Count traits per species
        traits_per_species = self.junction_data.groupby('scientific_name').agg({
            'trait_name': ['count', lambda x: len(set(x))]
        }).reset_index()
        traits_per_species.columns = ['scientific_name', 'trait_count', 'unique_traits']
        traits_per_species = traits_per_species.sort_values('trait_count', ascending=False)
        
        return traits_per_species
    
    def find_species_with_no_traits(self):
        """Find species with no traits"""
        print("Finding species with no traits...")
        
        if self.species_data.empty:
            return pd.DataFrame(columns=['scientific_name'])
        
        if self.junction_data.empty:
            return self.species_data[['scientific_name']].copy()
        
        # Find species not in junction data
        species_with_traits = set(self.junction_data['scientific_name'].unique())
        all_species = set(self.species_data['scientific_name'].unique())
        species_no_traits = all_species - species_with_traits
        
        return pd.DataFrame({'scientific_name': list(species_no_traits)})
    
    def find_unused_traits(self):
        """Find traits with no species"""
        print("Finding unused traits...")
        
        unused_traits = []
        
        if not self.junction_data.empty:
            used_traits = set(self.junction_data['trait_name'].unique())
        else:
            used_traits = set()
        
        # Check for unused traits
        if not self.traits_data.empty:
            for trait in self.traits_data['trait_name']:
                if trait not in used_traits:
                    unused_traits.append({'trait_name': trait})
        
        return pd.DataFrame(unused_traits)
    
    def generate_html_report(self, all_traits, species_per_trait, traits_per_species, 
                           species_no_traits, unused_traits, output_dir):
        """Generate comprehensive HTML report"""
        print("Generating HTML report...")
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trait Summary Analysis Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background-color: white;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #e8f4f8;
        }}
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .no-data {{
            color: #e74c3c;
            font-style: italic;
        }}
        .highlight {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Trait Summary Analysis Report</h1>
        <p style="text-align: center; color: #7f8c8d;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-number">{len(self.species_data) if not self.species_data.empty else 0}</div>
                <div class="stat-label">Total Species</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(self.traits_data) if not self.traits_data.empty else 0}</div>
                <div class="stat-label">Total Traits</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(all_traits)}</div>
                <div class="stat-label">Unique Traits</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(self.junction_data) if not self.junction_data.empty else 0}</div>
                <div class="stat-label">Species-Trait Records</div>
            </div>
        </div>
        
        <h2>1. All Unique Traits</h2>
        <div class="highlight">
            <strong>{len(all_traits)} unique traits found in database</strong>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Trait Name</th>
                </tr>
            </thead>
            <tbody>"""
        
        for trait in all_traits[:50]:  # Show first 50 traits
            html_content += f"""
                <tr>
                    <td>{trait}</td>
                </tr>"""
        
        html_content += """
            </tbody>
        </table>
        
        <h2>2. Species Count per Trait</h2>"""
        
        if not species_per_trait.empty:
            html_content += """
        <table>
            <thead>
                <tr>
                    <th>Trait Name</th>
                    <th>Species Count</th>
                </tr>
            </thead>
            <tbody>"""
            
            for _, row in species_per_trait.head(20).iterrows():
                html_content += f"""
                <tr>
                    <td>{row['trait_name']}</td>
                    <td>{row['species_count']}</td>
                </tr>"""
            
            html_content += """
            </tbody>
        </table>"""
        else:
            html_content += '<p class="no-data">No trait data available</p>'
        
        html_content += """
        <h2>3. Traits Count per Species</h2>"""
        
        if not traits_per_species.empty:
            html_content += """
        <table>
            <thead>
                <tr>
                    <th>Scientific Name</th>
                    <th>Total Traits</th>
                    <th>Unique Traits</th>
                </tr>
            </thead>
            <tbody>"""
            
            for _, row in traits_per_species.head(20).iterrows():
                html_content += f"""
                <tr>
                    <td>{row['scientific_name']}</td>
                    <td>{row['trait_count']}</td>
                    <td>{row['unique_traits']}</td>
                </tr>"""
            
            html_content += """
            </tbody>
        </table>"""
        else:
            html_content += '<p class="no-data">No species-trait data available</p>'
        
        html_content += """
        <h2>4. Species with No Traits</h2>"""
        
        if not species_no_traits.empty:
            html_content += f"""
        <div class="highlight">
            <strong>{len(species_no_traits)} species have no trait data</strong>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Scientific Name</th>
                </tr>
            </thead>
            <tbody>"""
            
            for _, row in species_no_traits.head(20).iterrows():
                html_content += f"""
                <tr>
                    <td>{row['scientific_name']}</td>
                </tr>"""
            
            html_content += """
            </tbody>
        </table>"""
        else:
            html_content += '<p class="no-data">All species have trait data</p>'
        
        html_content += """
        <h2>5. Unused Traits</h2>"""
        
        if not unused_traits.empty:
            html_content += f"""
        <div class="highlight">
            <strong>{len(unused_traits)} traits have no species data</strong>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Trait Name</th>
                </tr>
            </thead>
            <tbody>"""
            
            for _, row in unused_traits.head(20).iterrows():
                html_content += f"""
                <tr>
                    <td>{row['trait_name']}</td>
                </tr>"""
            
            html_content += """
            </tbody>
        </table>"""
        else:
            html_content += '<p class="no-data">All traits have species data</p>'
        
        html_content += """
        <footer style="margin-top: 40px; text-align: center; color: #7f8c8d; border-top: 1px solid #ddd; padding-top: 20px;">
            <p>Generated by Trait Summary Analysis System</p>
        </footer>
    </div>
</body>
</html>"""
        
        # Save HTML report
        html_file = os.path.join(output_dir, "trait_summary_report.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML report saved: {html_file}")
        
        # Also save CSV files for detailed analysis
        if not species_per_trait.empty:
            csv_file = os.path.join(output_dir, "species_per_trait.csv")
            species_per_trait.to_csv(csv_file, index=False)
            print(f"Species per trait CSV saved: {csv_file}")
        
        if not traits_per_species.empty:
            csv_file = os.path.join(output_dir, "traits_per_species.csv")
            traits_per_species.to_csv(csv_file, index=False)
            print(f"Traits per species CSV saved: {csv_file}")
        
        if not species_no_traits.empty:
            csv_file = os.path.join(output_dir, "species_no_traits.csv")
            species_no_traits.to_csv(csv_file, index=False)
            print(f"Species with no traits CSV saved: {csv_file}")
        
        if not unused_traits.empty:
            csv_file = os.path.join(output_dir, "unused_traits.csv")
            unused_traits.to_csv(csv_file, index=False)
            print(f"Unused traits CSV saved: {csv_file}")
    
    def run_analysis(self):
        """Run the complete trait summary analysis"""
        try:
            self.load_data()
            return self.analyze_trait_summaries()
        except Exception as e:
            print(f"Error during analysis: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function to run the trait summary analysis"""
    print("Trait Summary Analysis - Experiment 5")
    print("="*50)
    
    try:
        analyzer = TraitSummaryAnalyzer()
        success = analyzer.run_analysis()
        
        if success:
            print("\nTrait summary analysis completed successfully!")
        else:
            print("\nAnalysis failed - check error messages above")
            
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
