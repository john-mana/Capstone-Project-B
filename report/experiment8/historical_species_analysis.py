#!/usr/bin/env python3
"""
Historical Species Analysis for ALA Data - Simplified Version
Generates PDF with charts only and interactive HTML map
"""
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import pandas as pd
import numpy as np
from datetime import datetime
import os
import warnings
from matplotlib.backends.backend_pdf import PdfPages

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

class HistoricalSpeciesAnalyzer:
    """Simplified analyzer for historical species recording patterns"""
    
    def __init__(self, data_path):
        """Initialize the analyzer"""
        self.data_path = data_path
        self.data = None
        self.species_timeline = None
        self.missing_species = None
        self.survey_coverage = None
        
        # Analysis parameters
        self.cutoff_year = 2000
        self.recent_years = 5
        
        print("Historical Species Analyzer initialized")
    
    def load_data(self):
        """Load and preprocess the ALA data"""
        print(f"Loading data from {self.data_path}...")
        
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        self.data = pd.read_csv(self.data_path, low_memory=False)
        print(f"Data loaded: {len(self.data):,} records")
        
        # Preprocess dates
        self.preprocess_dates()
        
        print(f"Date range: {self.data['Year'].min()} - {self.data['Year'].max()}")
        print(f"Unique species: {self.data['Scientific Name'].nunique():,}")
        print(f"Records with GPS: {self.data[['Decimal Latitude', 'Decimal Longitude']].dropna().shape[0]:,}")
    
    def preprocess_dates(self):
        """Preprocess and clean date information"""
        if 'Event Date' in self.data.columns:
            self.data['Event Date'] = pd.to_datetime(self.data['Event Date'], errors='coerce')
            
            if 'Year' not in self.data.columns:
                self.data['Year'] = self.data['Event Date'].dt.year
            else:
                missing_years = self.data['Year'].isna()
                if missing_years.any():
                    self.data.loc[missing_years, 'Year'] = self.data.loc[missing_years, 'Event Date'].dt.year
        
        self.data['Year'] = pd.to_numeric(self.data['Year'], errors='coerce')
        self.data = self.data.dropna(subset=['Year'])
    
    def analyze_species_timeline(self):
        """Analyze species recording timeline"""
        print("Analyzing species timeline...")
        
        species_years = self.data.groupby('Scientific Name')['Year'].agg(['min', 'max', 'count']).reset_index()
        species_years.columns = ['Scientific Name', 'First_Record', 'Last_Record', 'Total_Records']
        species_years['Time_Span'] = species_years['Last_Record'] - species_years['First_Record']
        
        current_year = datetime.now().year
        recent_threshold = current_year - self.recent_years
        species_years['Recent_Records'] = species_years['Last_Record'] >= recent_threshold
        species_years['Missing_Years'] = current_year - species_years['Last_Record']
        
        self.species_timeline = species_years
        
        total_species = len(species_years)
        recent_species = species_years['Recent_Records'].sum()
        print(f"Total species analyzed: {total_species:,}")
        print(f"Species with recent records: {recent_species:,}")
        
        return species_years
    
    def identify_missing_species(self):
        """Identify species that appear to be missing"""
        print(f"Identifying species only recorded before {self.cutoff_year}...")
        
        old_only = self.species_timeline[self.species_timeline['Last_Record'] < self.cutoff_year].copy()
        old_only = old_only.sort_values('Last_Record')
        self.missing_species = old_only
        
        print(f"Species only recorded before {self.cutoff_year}: {len(old_only):,}")
        
        if len(old_only) > 0:
            print("Top 5 longest missing species:")
            for idx, row in old_only.head(5).iterrows():
                years_missing = datetime.now().year - row['Last_Record']
                print(f"   {row['Scientific Name']}: last seen {int(row['Last_Record'])}, missing {years_missing} years")
        
        return old_only
    
    def analyze_survey_coverage(self):
        """Analyze survey coverage over time and space"""
        print("Analyzing survey coverage...")
        
        yearly_records = self.data.groupby('Year').agg({
            'Scientific Name': ['count', 'nunique'],
            'Decimal Latitude': 'count',
            'Decimal Longitude': 'count'
        }).reset_index()
        
        yearly_records.columns = ['Year', 'Total_Records', 'Unique_Species', 'GPS_Records_Lat', 'GPS_Records_Lon']
        
        gps_data = self.data[['Decimal Latitude', 'Decimal Longitude', 'Year', 'Scientific Name']].dropna()
        
        # Use 2000 as cutoff for historical vs recent
        historical_cutoff = 2000
        recent_gps = gps_data[gps_data['Year'] >= historical_cutoff]
        historical_gps = gps_data[gps_data['Year'] < historical_cutoff]
        
        self.survey_coverage = {
            'yearly_records': yearly_records,
            'gps_data': gps_data,
            'recent_gps': recent_gps,
            'historical_gps': historical_gps,
        }
        
        print(f"Total GPS records: {len(gps_data):,}")
        print(f"Recent GPS records: {len(recent_gps):,}")
        print(f"Historical GPS records: {len(historical_gps):,}")
        
        return self.survey_coverage
      
    def create_timeline_analysis_page(self, pdf_pages):
        """Create timeline analysis page - Charts only"""
        print("Creating timeline analysis page...")
        
        yearly_data = self.survey_coverage['yearly_records']
        years = yearly_data['Year'].astype(int)

        # Calculate cumulative species
        years_sorted = sorted(years)
        cumulative_species, seen = [], set()
        for y in years_sorted:
            sp = set(self.data[self.data['Year'] == y]['Scientific Name'].dropna())
            seen.update(sp)
            cumulative_species.append(len(seen))

        fig = plt.figure(figsize=(8.5, 11), constrained_layout=True)
        gs = GridSpec(nrows=3, ncols=1, height_ratios=[1, 1, 1], figure=fig)
        
        # Chart 1: Annual Survey Records
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(years, yearly_data['Total_Records'], marker='o', linewidth=2.5, markersize=4, color='#3498db')
        ax1.fill_between(years, yearly_data['Total_Records'], alpha=0.3, color='#3498db')
        ax1.set_title('Annual Survey Records', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Records')
        ax1.grid(True, alpha=0.3)

        # Chart 2: Annual Species Diversity
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.plot(years, yearly_data['Unique_Species'], marker='s', linewidth=2.5, markersize=4, color='#e74c3c')
        ax2.fill_between(years, yearly_data['Unique_Species'], alpha=0.3, color='#e74c3c')
        ax2.set_title('Annual Species Diversity', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Unique Species')
        ax2.grid(True, alpha=0.3)

        # Chart 3: Cumulative Species Discovery
        ax3 = fig.add_subplot(gs[2, 0])
        ax3.plot(years_sorted, cumulative_species, marker='d', linewidth=2.5, markersize=4, color='#f39c12')
        ax3.fill_between(years_sorted, cumulative_species, alpha=0.3, color='#f39c12')
        ax3.set_title('Cumulative Species Discovery', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Year')
        ax3.set_ylabel('Total Species Found')
        ax3.grid(True, alpha=0.3)

        pdf_pages.savefig(fig, dpi=300)
        plt.close(fig)
        
    def create_missing_species_page(self, pdf_pages):
        """Create missing species analysis page - Charts only"""
        print("Creating missing species analysis page...")
        
        if len(self.missing_species) > 0:
            fig = plt.figure(figsize=(8.5, 11), constrained_layout=True)
            gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[1, 1])
            
            # Chart 1: Distribution of Last Record Years
            ax1 = fig.add_subplot(gs[0, 0])
            ax1.hist(self.missing_species['Last_Record'], bins=15, alpha=0.7, color='#E63946', edgecolor='black')
            ax1.set_title('Distribution of Last Record Years (Missing Species)', fontsize=12, fontweight='bold')
            ax1.set_xlabel('Year of Last Record')
            ax1.set_ylabel('Number of Species')
            ax1.axvline(x=self.cutoff_year, color='black', linestyle='--', linewidth=2, label=f'Cutoff Year ({self.cutoff_year})')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Chart 2: Years Since Last Record
            ax2 = fig.add_subplot(gs[1, 0])
            missing_years = (datetime.now().year - self.missing_species['Last_Record'])
            ax2.hist(missing_years, bins=15, alpha=0.7, color='#F77F00', edgecolor='black')
            ax2.set_title('Years Since Last Record (Missing Species)', fontsize=12, fontweight='bold')
            ax2.set_xlabel('Years Since Last Record')
            ax2.set_ylabel('Number of Species')
            ax2.grid(True, alpha=0.3)

            pdf_pages.savefig(fig, dpi=300)
            plt.close(fig)
        else:
            fig = plt.figure(figsize=(8.5, 11), constrained_layout=True)
            ax = fig.add_subplot(1, 1, 1)
            ax.axis('off')
            ax.text(0.5, 0.5, 'No Missing Species Found', transform=ax.transAxes, 
                    fontsize=24, ha='center', va='center', fontweight='bold', color='#2c3e50')
            pdf_pages.savefig(fig, dpi=300)
            plt.close(fig)
    
    def create_spatial_coverage_page(self, pdf_pages):
        """Create spatial coverage analysis page - Charts only"""
        print("Creating spatial coverage analysis page...")
        
        fig = plt.figure(figsize=(8.5, 11), constrained_layout=True)
        gs = fig.add_gridspec(nrows=3, ncols=1, height_ratios=[1, 1, 1])
        
        gps_data = self.survey_coverage['gps_data']
        recent_gps = self.survey_coverage['recent_gps']
        historical_gps = self.survey_coverage['historical_gps']
        
        # Chart 1: All GPS records
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.scatter(gps_data['Decimal Longitude'], gps_data['Decimal Latitude'], alpha=0.6, s=0.5, c='#457B9D')
        ax1.set_title('All Survey Locations (GPS Records)', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Longitude')
        ax1.set_ylabel('Latitude')
        ax1.grid(True, alpha=0.3)
        
        # Chart 2: Recent vs Historical comparison
        ax2 = fig.add_subplot(gs[1, 0])
        if len(historical_gps) > 0:
            ax2.scatter(historical_gps['Decimal Longitude'], historical_gps['Decimal Latitude'], 
                       alpha=0.7, s=1, c='#E63946', label='Historical (pre-2000)')
        if len(recent_gps) > 0:
            ax2.scatter(recent_gps['Decimal Longitude'], recent_gps['Decimal Latitude'], 
                       alpha=0.7, s=1, c='#2A9D8F', label='Recent (2000+)')
        ax2.set_title('Survey Location Comparison: Historical vs Recent', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Longitude')
        ax2.set_ylabel('Latitude')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Chart 3: Survey intensity heatmap
        ax3 = fig.add_subplot(gs[2, 0])
        lat_bins = np.linspace(gps_data['Decimal Latitude'].min(), gps_data['Decimal Latitude'].max(), 15)
        lon_bins = np.linspace(gps_data['Decimal Longitude'].min(), gps_data['Decimal Longitude'].max(), 15)
        
        H, xedges, yedges = np.histogram2d(gps_data['Decimal Longitude'], gps_data['Decimal Latitude'], 
                                          bins=[lon_bins, lat_bins])
        
        im = ax3.imshow(H.T, origin='lower', aspect='auto', cmap='YlOrRd',
                        extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
        ax3.set_title('Survey Intensity Heatmap', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Longitude')
        ax3.set_ylabel('Latitude')
        plt.colorbar(im, ax=ax3, label='Records per Grid Cell')
        
        pdf_pages.savefig(fig, dpi=300)
        plt.close()
        
    def generate_interactive_map(self, output_file="species_survey_map.html"):
        """Generate an interactive HTML map showing survey locations"""
        print(f"Generating interactive map: {output_file}...")
        
        gps_data = self.survey_coverage['gps_data']
        historical_cutoff = 2000
        recent_gps = gps_data[gps_data['Year'] >= historical_cutoff]
        historical_gps = gps_data[gps_data['Year'] < historical_cutoff]
        
        center_lat = gps_data['Decimal Latitude'].mean()
        center_lon = gps_data['Decimal Longitude'].mean()
        
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Species Survey Locations</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .map-container {{ padding: 20px; }}
        #map {{ height: 600px; width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
        .legend {{ background: white; padding: 15px; margin-top: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .legend-item {{ display: flex; align-items: center; margin: 8px 0; }}
        .legend-color {{ width: 20px; height: 20px; border-radius: 50%; margin-right: 10px; border: 2px solid #333; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-number {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Species Survey Locations</h1>
            <p>Interactive map showing historical and recent species survey locations</p>
        </div>
        
        <div class="map-container">
            <div id="map"></div>
            
            <div class="legend">
                <h3>Map Legend</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #e74c3c;"></div>
                    <span>Historical Survey Locations (before 2000)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #27ae60;"></div>
                    <span>Recent Survey Locations (2000+)</span>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(gps_data):,}</div>
                    <div>Total Survey Points</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(historical_gps):,}</div>
                    <div>Historical Points</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(recent_gps):,}</div>
                    <div>Recent Points</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{gps_data['Scientific Name'].nunique():,}</div>
                    <div>Unique Species</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        var map = L.map('map').setView([{center_lat}, {center_lon}], 8);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        var historicalLayer = L.layerGroup();
        var recentLayer = L.layerGroup();
'''

        # Add all points (no sampling limit)
        if len(historical_gps) > 0:
            for _, row in historical_gps.iterrows():
                species_name = str(row['Scientific Name']).replace("'", "\\'")
                year = int(row['Year'])
                html_content += f'''
        L.circleMarker([{row['Decimal Latitude']}, {row['Decimal Longitude']}], {{
            radius: 3, fillColor: '#e74c3c', color: '#c0392b', weight: 1, opacity: 0.8, fillOpacity: 0.6
        }}).bindPopup('<b>{species_name}</b><br>Year: {year}<br>Type: Historical').addTo(historicalLayer);'''

        if len(recent_gps) > 0:
            for _, row in recent_gps.iterrows():
                species_name = str(row['Scientific Name']).replace("'", "\\'")
                year = int(row['Year'])
                html_content += f'''
        L.circleMarker([{row['Decimal Latitude']}, {row['Decimal Longitude']}], {{
            radius: 3, fillColor: '#27ae60', color: '#229954', weight: 1, opacity: 0.8, fillOpacity: 0.6
        }}).bindPopup('<b>{species_name}</b><br>Year: {year}<br>Type: Recent').addTo(recentLayer);'''

        html_content += '''
        historicalLayer.addTo(map);
        recentLayer.addTo(map);

        var overlayMaps = {
            "Historical Surveys": historicalLayer,
            "Recent Surveys": recentLayer
        };

        L.control.layers({}, overlayMaps).addTo(map);
        L.control.scale().addTo(map);
    </script>
</body>
</html>'''

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Interactive map saved as: {os.path.abspath(output_file)}")
        return output_file
    
    def generate_missing_species_csv(self, output_file="missing_species_by_years.csv"):
        """Generate detailed CSV file with missing species sorted by years missing"""
        print(f"Generating missing species CSV: {output_file}...")
        
        if len(self.missing_species) == 0:
            print("No missing species found - skipping CSV generation")
            return None
        
        # Create detailed missing species report
        current_year = datetime.now().year
        missing_report = []
        
        for _, species in self.missing_species.iterrows():
            species_name = species['Scientific Name']
            last_year = int(species['Last_Record'])
            first_year = int(species['First_Record'])
            total_records = int(species['Total_Records'])
            years_missing = current_year - last_year
            record_span = last_year - first_year
            
            # Get all records for this species
            species_data = self.data[self.data['Scientific Name'] == species_name]
            
            # GPS location information
            gps_records = species_data.dropna(subset=['Decimal Latitude', 'Decimal Longitude'])
            gps_count = len(gps_records)
            
            # Get last known location details
            last_location_data = species_data[species_data['Year'] == last_year]
            last_lat = last_lon = last_reserve = last_date = None
            
            if len(last_location_data) > 0:
                # Get the first record from the last year (in case multiple records)
                last_record = last_location_data.iloc[0]
                
                # Extract location data
                if not pd.isna(last_record.get('Decimal Latitude')):
                    last_lat = round(float(last_record['Decimal Latitude']), 6)
                if not pd.isna(last_record.get('Decimal Longitude')):
                    last_lon = round(float(last_record['Decimal Longitude']), 6)
                if 'Reserve Name' in last_record and not pd.isna(last_record.get('Reserve Name')):
                    last_reserve = last_record['Reserve Name']
                if 'Event Date' in last_record and not pd.isna(last_record.get('Event Date')):
                    last_date = str(last_record['Event Date'])[:10]  # YYYY-MM-DD format
            
            # Get first known location details
            first_location_data = species_data[species_data['Year'] == first_year]
            first_lat = first_lon = first_reserve = first_date = None
            
            if len(first_location_data) > 0:
                first_record = first_location_data.iloc[0]
                if not pd.isna(first_record.get('Decimal Latitude')):
                    first_lat = round(float(first_record['Decimal Latitude']), 6)
                if not pd.isna(first_record.get('Decimal Longitude')):
                    first_lon = round(float(first_record['Decimal Longitude']), 6)
                if 'Reserve Name' in first_record and not pd.isna(first_record.get('Reserve Name')):
                    first_reserve = first_record['Reserve Name']
                if 'Event Date' in first_record and not pd.isna(first_record.get('Event Date')):
                    first_date = str(first_record['Event Date'])[:10]
            
            # Calculate geographic range if we have multiple GPS points
            min_lat = max_lat = min_lon = max_lon = lat_range = lon_range = None
            if len(gps_records) > 1:
                min_lat = round(gps_records['Decimal Latitude'].min(), 6)
                max_lat = round(gps_records['Decimal Latitude'].max(), 6)
                min_lon = round(gps_records['Decimal Longitude'].min(), 6)
                max_lon = round(gps_records['Decimal Longitude'].max(), 6)
                lat_range = round(max_lat - min_lat, 6)
                lon_range = round(max_lon - min_lon, 6)
            
            # Get all unique reserves where this species was found
            unique_reserves = species_data['Reserve Name'].dropna().unique() if 'Reserve Name' in species_data.columns else []
            reserves_list = '; '.join(unique_reserves) if len(unique_reserves) > 0 else None
            
            # Create comprehensive record
            missing_report.append({
                'Scientific_Name': species_name,
                'Years_Missing': years_missing,
                'Last_Record_Year': last_year,
                'Last_Record_Date': last_date,
                'Last_Known_Latitude': last_lat,
                'Last_Known_Longitude': last_lon,
                'Last_Known_Reserve': last_reserve,
                'First_Record_Year': first_year,
                'First_Record_Date': first_date,
                'First_Known_Latitude': first_lat,
                'First_Known_Longitude': first_lon,
                'First_Known_Reserve': first_reserve,
                'Record_Span_Years': record_span,
                'Total_Records': total_records,
                'GPS_Locations': gps_count,
                'All_Reserves_Found': reserves_list,
                'Geographic_Range_Lat': lat_range,
                'Geographic_Range_Lon': lon_range,
                'Min_Latitude': min_lat,
                'Max_Latitude': max_lat,
                'Min_Longitude': min_lon,
                'Max_Longitude': max_lon
            })
        
        # Convert to DataFrame and sort by years missing (descending)
        df = pd.DataFrame(missing_report)
        df = df.sort_values('Years_Missing', ascending=False)
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        
        # Print summary statistics
        print(f"Missing species CSV saved as: {os.path.abspath(output_file)}")
        print(f"Total missing species: {len(df)}")
        print(f"Species with GPS data: {len(df[df['GPS_Locations'] > 0])}")
        
        return output_file
    
    def generate_all_species_csv(self, output_file="all_species_complete_data.csv"):
        """Generate comprehensive CSV file with ALL species data"""
        print(f"Generating complete species CSV: {output_file}...")
        
        if len(self.species_timeline) == 0:
            print("No species timeline data found - skipping CSV generation")
            return None
        
        # Create comprehensive report for ALL species
        current_year = datetime.now().year
        all_species_report = []
        
        for _, species in self.species_timeline.iterrows():
            species_name = species['Scientific Name']
            last_year = int(species['Last_Record'])
            first_year = int(species['First_Record'])
            total_records = int(species['Total_Records'])
            years_missing = current_year - last_year
            record_span = last_year - first_year
            
            # Get all records for this species
            species_data = self.data[self.data['Scientific Name'] == species_name]
            
            # GPS location information
            gps_records = species_data.dropna(subset=['Decimal Latitude', 'Decimal Longitude'])
            gps_count = len(gps_records)
            
            # Get last known location details
            last_location_data = species_data[species_data['Year'] == last_year]
            last_lat = last_lon = last_reserve = last_date = None
            
            if len(last_location_data) > 0:
                last_record = last_location_data.iloc[0]
                if not pd.isna(last_record.get('Decimal Latitude')):
                    last_lat = round(float(last_record['Decimal Latitude']), 6)
                if not pd.isna(last_record.get('Decimal Longitude')):
                    last_lon = round(float(last_record['Decimal Longitude']), 6)
                if 'Reserve Name' in last_record and not pd.isna(last_record.get('Reserve Name')):
                    last_reserve = last_record['Reserve Name']
                if 'Event Date' in last_record and not pd.isna(last_record.get('Event Date')):
                    last_date = str(last_record['Event Date'])[:10]
            
            # Get first known location details
            first_location_data = species_data[species_data['Year'] == first_year]
            first_lat = first_lon = first_reserve = first_date = None
            
            if len(first_location_data) > 0:
                first_record = first_location_data.iloc[0]
                if not pd.isna(first_record.get('Decimal Latitude')):
                    first_lat = round(float(first_record['Decimal Latitude']), 6)
                if not pd.isna(first_record.get('Decimal Longitude')):
                    first_lon = round(float(first_record['Decimal Longitude']), 6)
                if 'Reserve Name' in first_record and not pd.isna(first_record.get('Reserve Name')):
                    first_reserve = first_record['Reserve Name']
                if 'Event Date' in first_record and not pd.isna(first_record.get('Event Date')):
                    first_date = str(first_record['Event Date'])[:10]
            
            # Calculate geographic range if we have multiple GPS points
            min_lat = max_lat = min_lon = max_lon = lat_range = lon_range = None
            if len(gps_records) > 1:
                min_lat = round(gps_records['Decimal Latitude'].min(), 6)
                max_lat = round(gps_records['Decimal Latitude'].max(), 6)
                min_lon = round(gps_records['Decimal Longitude'].min(), 6)
                max_lon = round(gps_records['Decimal Longitude'].max(), 6)
                lat_range = round(max_lat - min_lat, 6)
                lon_range = round(max_lon - min_lon, 6)
            
            # Get all unique reserves where this species was found
            unique_reserves = species_data['Reserve Name'].dropna().unique() if 'Reserve Name' in species_data.columns else []
            reserves_list = '; '.join(unique_reserves) if len(unique_reserves) > 0 else None
            
            # Determine if species is missing (before 2000)
            is_missing = last_year < self.cutoff_year
            missing_status = "Missing" if is_missing else "Recent"
            
            # Create comprehensive record for ALL species
            all_species_report.append({
                'Scientific_Name': species_name,
                'Missing_Status': missing_status,
                'Years_Missing': years_missing,
                'Last_Record_Year': last_year,
                'Last_Record_Date': last_date,
                'Last_Known_Latitude': last_lat,
                'Last_Known_Longitude': last_lon,
                'Last_Known_Reserve': last_reserve,
                'First_Record_Year': first_year,
                'First_Record_Date': first_date,
                'First_Known_Latitude': first_lat,
                'First_Known_Longitude': first_lon,
                'First_Known_Reserve': first_reserve,
                'Record_Span_Years': record_span,
                'Total_Records': total_records,
                'GPS_Locations': gps_count,
                'All_Reserves_Found': reserves_list,
                'Geographic_Range_Lat': lat_range,
                'Geographic_Range_Lon': lon_range,
                'Min_Latitude': min_lat,
                'Max_Latitude': max_lat,
                'Min_Longitude': min_lon,
                'Max_Longitude': max_lon
            })
        
        # Convert to DataFrame and sort by years missing (descending)
        df = pd.DataFrame(all_species_report)
        df = df.sort_values('Years_Missing', ascending=False)
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        
        # Print summary statistics
        total_species = len(df)
        missing_species = len(df[df['Missing_Status'] == 'Missing'])
        recent_species = len(df[df['Missing_Status'] == 'Recent'])
        
        print(f"Complete species CSV saved as: {os.path.abspath(output_file)}")
        print(f"Total species: {total_species}")
        print(f"Missing species (before 2000): {missing_species}")
        print(f"Recent species (2000+): {recent_species}")
        print(f"Species with GPS data: {len(df[df['GPS_Locations'] > 0])}")
        
        return output_file
    
    def generate_pdf_report(self, output_file):
        """Generate PDF report with charts only"""
        print(f"Generating PDF report: {output_file}...")
        
        with PdfPages(output_file) as pdf:
            try:
                self.create_timeline_analysis_page(pdf)
                print("Timeline analysis page")
            except Exception as e:
                print(f"Skipped timeline page: {e}")
            
            try:
                self.create_missing_species_page(pdf)
                print("Missing species page")
            except Exception as e:
                print(f"Skipped missing species page: {e}")
            
            try:
                self.create_spatial_coverage_page(pdf)
                print("Spatial coverage page")
            except Exception as e:
                print(f"Skipped spatial coverage page: {e}")
        
        print("PDF report generated successfully!")
    
    def run_analysis(self):
        """Run the complete historical species analysis"""
        print("Starting Historical Species Analysis...")
        print("="*50)
        
        try:
            # Load and analyze data
            self.load_data()
            self.analyze_species_timeline()
            self.identify_missing_species()
            self.analyze_survey_coverage()
            
            # Generate reports
            pdf_file = "Historical_Species_Analysis_Report.pdf"
            self.generate_pdf_report(pdf_file)
            
            map_file = self.generate_interactive_map()
            
            csv_file = self.generate_missing_species_csv()
            all_species_csv = self.generate_all_species_csv()
            
            print(f"\nAnalysis complete!")
            print(f"PDF Report saved as: {pdf_file}")
            print(f"Interactive map saved as: {map_file}")
            if csv_file:
                print(f"Missing species CSV saved as: {csv_file}")
            if all_species_csv:
                print(f"All species CSV saved as: {all_species_csv}")
            
            return True
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function to run the historical species analysis"""
    print("Historical Species Analysis - Simplified Version")
    print("="*50)
    
    data_path = "../Database/ALA.csv"
    
    try:
        analyzer = HistoricalSpeciesAnalyzer(data_path)
        success = analyzer.run_analysis()
        
        if success:
            print("\nHistorical Species Analysis completed successfully!")
        else:
            print("\nAnalysis failed - check error messages above")
            
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
