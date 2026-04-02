#!/usr/bin/env python3
"""
Fire Plant Location Maps Generator
Generate interactive HTML maps showing plant locations categorized by fire-related traits
Based on the methodology from historical_species_analysis.py using Leaflet.js
"""

import pandas as pd
import numpy as np
import re
import os
from datetime import datetime

class FirePlantLocationMapper:
    """Generate interactive maps for fire-related plant locations"""
    
    def __init__(self):
        """Initialize the mapper"""
        self.traits_data = None
        self.occurrence_data = None
        self.species_with_fire_traits = None
        self.fire_categories = {}
        
    def load_data(self):
        """Load fire traits and occurrence data"""
        print("📂 Loading fire traits and occurrence data...")
        
        try:
            # Load fire traits data
            traits_file = "../Database/final_Traits_clean_data_with_insert_common_name_local_stauts.csv"
            self.traits_data = pd.read_csv(traits_file)
            print(f"✓ Fire traits loaded: {len(self.traits_data)} species")
            
            # Load occurrence data
            occurrence_file = "../Database/flora_occurrence_data.csv"
            self.occurrence_data = pd.read_csv(occurrence_file)
            print(f"✓ Occurrence data loaded: {len(self.occurrence_data)} records")
            
            # Clean coordinate data
            self.occurrence_data = self.occurrence_data.dropna(subset=['Decimal Latitude', 'Decimal Longitude'])
            print(f"✓ Valid coordinates: {len(self.occurrence_data)} records")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
    
    def identify_fire_related_species(self):
        """Identify species with fire-related traits"""
        print("\n🔍 Identifying species with fire-related traits...")
        
        # Define fire-related traits
        fire_traits = [
            'plant_tolerance_fire',
            'post_fire_recruitment', 
            'post_fire_flowering',
            'resprouting_capacity',
            'resprouting_capacity_non_fire_disturbance',
            'resprouting_capacity_juvenile',
            'resprouting_capacity_proportion_individuals',
            'resprouting_capacity_time_from_germination',
            'fire_time_from_fire_to_fruiting',
            'fire_time_from_fire_to_flowering',
            'fire_time_from_fire_to_flowering_decline',
            'fire_time_from_fire_to_50_percent_flowering',
            'fire_time_from_fire_to_50_percent_fruiting',
            'fire_time_from_fire_to_peak_flowering'
        ]
        
        # Find species with any fire-related trait
        species_with_traits = set()
        for trait in fire_traits:
            if trait in self.traits_data.columns:
                # Get species with non-null values for this trait
                species_with_data = self.traits_data[
                    self.traits_data[trait].notna() & 
                    (self.traits_data[trait] != '') & 
                    (self.traits_data[trait] != 'nan')
                ]['species_name'].tolist()
                species_with_traits.update(species_with_data)
        
        self.species_with_fire_traits = list(species_with_traits)
        print(f"✓ Found {len(self.species_with_fire_traits)} species with fire-related traits")
        
        return self.species_with_fire_traits
    
    def categorize_fire_recovery_time(self, species_name):
        """Categorize species by fire recovery time"""
        has_timing_data = False
        max_time = 0
        
        # Check for fire timing traits
        timing_traits = [
            'fire_time_from_fire_to_fruiting',
            'fire_time_from_fire_to_flowering', 
            'fire_time_from_fire_to_flowering_decline',
            'fire_time_from_fire_to_50_percent_flowering',
            'fire_time_from_fire_to_50_percent_fruiting',
            'fire_time_from_fire_to_peak_flowering'
        ]
        
        for trait in timing_traits:
            if trait in self.traits_data.columns:
                species_data = self.traits_data[self.traits_data['species_name'] == species_name]
                if not species_data.empty:
                    trait_value = species_data[trait].iloc[0]
                    if pd.notna(trait_value) and str(trait_value) != '':
                        has_timing_data = True
                        # Extract numeric values
                        numbers = re.findall(r'(\d+(?:\.\d+)?)', str(trait_value))
                        if numbers:
                            trait_max = max([float(n) for n in numbers])
                            max_time = max(max_time, trait_max)
        
        if has_timing_data:
            if max_time < 12:
                return 'Fast (<12 months)', 'green'
            elif max_time <= 24:
                return 'Medium (12-24 months)', 'orange'
            else:
                return 'Slow (>24 months)', 'red'
        else:
            return 'No Data', 'gray'
    
    def categorize_fire_risk(self, species_name):
        """Categorize species by fire risk level"""
        species_data = self.traits_data[self.traits_data['species_name'] == species_name]
        if species_data.empty:
            return 'No Data', 'gray'
        
        # Check resprouting capacity
        can_resprout = False
        if 'resprouting_capacity' in self.traits_data.columns:
            resprout_value = species_data['resprouting_capacity'].iloc[0]
            if pd.notna(resprout_value) and 'resprouts' in str(resprout_value).lower():
                can_resprout = True
        
        # Check post-fire recruitment
        has_recruitment = False
        if 'post_fire_recruitment' in self.traits_data.columns:
            recruitment_value = species_data['post_fire_recruitment'].iloc[0]
            if pd.notna(recruitment_value) and 'post_fire_recruitment' in str(recruitment_value).lower():
                has_recruitment = True
        
        # Determine risk level
        if can_resprout and has_recruitment:
            return 'Low Risk', 'green'
        elif can_resprout or has_recruitment:
            return 'Medium Risk', 'orange'
        else:
            return 'High Risk', 'red'
    
    def categorize_post_fire_recruitment(self, species_name):
        """Categorize species by post-fire recruitment"""
        species_data = self.traits_data[self.traits_data['species_name'] == species_name]
        if species_data.empty:
            return 'No Data', 'gray'
        
        if 'post_fire_recruitment' in self.traits_data.columns:
            recruitment_value = species_data['post_fire_recruitment'].iloc[0]
            if pd.notna(recruitment_value):
                value_str = str(recruitment_value).lower()
                if 'post_fire_recruitment' in value_str:
                    return 'Has Recruitment', 'blue'
                elif 'absent' in value_str:
                    return 'No Recruitment', 'red'
                else:
                    return 'Mixed Response', 'purple'
        
        return 'No Data', 'gray'
    
    def categorize_resprouting_capacity(self, species_name):
        """Categorize species by resprouting capacity"""
        species_data = self.traits_data[self.traits_data['species_name'] == species_name]
        if species_data.empty:
            return 'No Data', 'gray'
        
        if 'resprouting_capacity' in self.traits_data.columns:
            resprout_value = species_data['resprouting_capacity'].iloc[0]
            if pd.notna(resprout_value):
                value_str = str(resprout_value).lower()
                print(f"DEBUG: {species_name} -> resprout_value: '{resprout_value}' -> value_str: '{value_str}'")
                if 'resprouts' in value_str:
                    return 'Can Resprout', 'green'
                elif 'fire killed' in value_str or 'killed' in value_str:
                    return 'Fire Killed', 'red'
                else:
                    return 'Mixed Response', 'orange'
        
        return 'No Data', 'gray'
    
    def create_fire_recovery_time_map(self):
        """Create map showing fire recovery time distribution"""
        print("\n🗺️ Creating Fire Recovery Time Distribution Map...")
        
        # Filter occurrence data for species with fire traits
        fire_occurrences = self.occurrence_data[
            self.occurrence_data['Scientific Name'].isin(self.species_with_fire_traits)
        ].copy()
        
        # Categorize each occurrence
        fire_occurrences['Recovery_Category'] = fire_occurrences['Scientific Name'].apply(
            lambda x: self.categorize_fire_recovery_time(x)[0]
        )
        fire_occurrences['Color'] = fire_occurrences['Scientific Name'].apply(
            lambda x: self.categorize_fire_recovery_time(x)[1]
        )
        
        # Calculate center point
        center_lat = fire_occurrences['Decimal Latitude'].mean()
        center_lon = fire_occurrences['Decimal Longitude'].mean()
        
        # Create HTML content with Leaflet.js
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Fire Recovery Time Distribution Map</title>
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
            <h1>Fire Recovery Time Distribution Map</h1>
            <p>Interactive map showing plant locations categorized by fire recovery time</p>
        </div>
        
        <div class="map-container">
            <div id="map"></div>
            
            <div class="legend">
                <h3>Fire Recovery Time Categories</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #27ae60;"></div>
                    <span>Fast Recovery (<12 months)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #f39c12;"></div>
                    <span>Medium Recovery (12-24 months)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #e74c3c;"></div>
                    <span>Slow Recovery (>24 months)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #95a5a6;"></div>
                    <span>No Data</span>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences):,}</div>
                    <div>Total Plant Locations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Recovery_Category'] == 'Fast (<12 months)']):,}</div>
                    <div>Fast Recovery</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Recovery_Category'] == 'Medium (12-24 months)']):,}</div>
                    <div>Medium Recovery</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Recovery_Category'] == 'Slow (>24 months)']):,}</div>
                    <div>Slow Recovery</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        var map = L.map('map').setView([{center_lat}, {center_lon}], 10);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        var fastLayer = L.layerGroup();
        var mediumLayer = L.layerGroup();
        var slowLayer = L.layerGroup();
        var noDataLayer = L.layerGroup();
'''

        # Add markers for each category
        for _, row in fire_occurrences.iterrows():
            species_name = str(row['Scientific Name']).replace("'", "\\'")
            category = row['Recovery_Category']
            
            if category == 'Fast (<12 months)':
                color = '#27ae60'
                layer = 'fastLayer'
            elif category == 'Medium (12-24 months)':
                color = '#f39c12'
                layer = 'mediumLayer'
            elif category == 'Slow (>24 months)':
                color = '#e74c3c'
                layer = 'slowLayer'
            else:
                color = '#95a5a6'
                layer = 'noDataLayer'
            
            html_content += f'''
        L.circleMarker([{row['Decimal Latitude']}, {row['Decimal Longitude']}], {{
            radius: 4, fillColor: '{color}', color: '{color}', weight: 2, opacity: 0.8, fillOpacity: 0.7
        }}).bindPopup('<b>{species_name}</b><br>Recovery Time: {category}').addTo({layer});'''

        html_content += '''
        fastLayer.addTo(map);
        mediumLayer.addTo(map);
        slowLayer.addTo(map);
        noDataLayer.addTo(map);

        var overlayMaps = {
            "Fast Recovery": fastLayer,
            "Medium Recovery": mediumLayer,
            "Slow Recovery": slowLayer,
            "No Data": noDataLayer
        };

        L.control.layers({}, overlayMaps).addTo(map);
        L.control.scale().addTo(map);
    </script>
</body>
</html>'''

        # Save map
        map_file = "fire_recovery_time_map.html"
        with open(map_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Fire Recovery Time Map saved: {map_file}")
        return map_file
    
    def create_fire_risk_map(self):
        """Create map showing fire risk distribution"""
        print("\n🗺️ Creating Overall Fire Risk Distribution Map...")
        
        # Filter occurrence data for species with fire traits
        fire_occurrences = self.occurrence_data[
            self.occurrence_data['Scientific Name'].isin(self.species_with_fire_traits)
        ].copy()
        
        # Categorize each occurrence
        fire_occurrences['Risk_Category'] = fire_occurrences['Scientific Name'].apply(
            lambda x: self.categorize_fire_risk(x)[0]
        )
        fire_occurrences['Color'] = fire_occurrences['Scientific Name'].apply(
            lambda x: self.categorize_fire_risk(x)[1]
        )
        
        # Calculate center point
        center_lat = fire_occurrences['Decimal Latitude'].mean()
        center_lon = fire_occurrences['Decimal Longitude'].mean()
        
        # Create HTML content with Leaflet.js
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Fire Risk Distribution Map</title>
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
            <h1>Fire Risk Distribution Map</h1>
            <p>Interactive map showing plant locations categorized by fire risk level</p>
        </div>
        
        <div class="map-container">
            <div id="map"></div>
            
            <div class="legend">
                <h3>Fire Risk Categories</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #27ae60;"></div>
                    <span>Low Risk (Can resprout + has recruitment)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #f39c12;"></div>
                    <span>Medium Risk (Either resprout OR recruitment)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #e74c3c;"></div>
                    <span>High Risk (No resprout + no recruitment)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #95a5a6;"></div>
                    <span>No Data</span>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences):,}</div>
                    <div>Total Plant Locations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Risk_Category'] == 'Low Risk']):,}</div>
                    <div>Low Risk</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Risk_Category'] == 'Medium Risk']):,}</div>
                    <div>Medium Risk</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Risk_Category'] == 'High Risk']):,}</div>
                    <div>High Risk</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        var map = L.map('map').setView([{center_lat}, {center_lon}], 10);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        var lowRiskLayer = L.layerGroup();
        var mediumRiskLayer = L.layerGroup();
        var highRiskLayer = L.layerGroup();
        var noDataLayer = L.layerGroup();
'''

        # Add markers for each category
        for _, row in fire_occurrences.iterrows():
            species_name = str(row['Scientific Name']).replace("'", "\\'")
            category = row['Risk_Category']
            
            if category == 'Low Risk':
                color = '#27ae60'
                layer = 'lowRiskLayer'
            elif category == 'Medium Risk':
                color = '#f39c12'
                layer = 'mediumRiskLayer'
            elif category == 'High Risk':
                color = '#e74c3c'
                layer = 'highRiskLayer'
            else:
                color = '#95a5a6'
                layer = 'noDataLayer'
            
            html_content += f'''
        L.circleMarker([{row['Decimal Latitude']}, {row['Decimal Longitude']}], {{
            radius: 4, fillColor: '{color}', color: '{color}', weight: 2, opacity: 0.8, fillOpacity: 0.7
        }}).bindPopup('<b>{species_name}</b><br>Risk Level: {category}').addTo({layer});'''

        html_content += '''
        lowRiskLayer.addTo(map);
        mediumRiskLayer.addTo(map);
        highRiskLayer.addTo(map);
        noDataLayer.addTo(map);

        var overlayMaps = {
            "Low Risk": lowRiskLayer,
            "Medium Risk": mediumRiskLayer,
            "High Risk": highRiskLayer,
            "No Data": noDataLayer
        };

        L.control.layers({}, overlayMaps).addTo(map);
        L.control.scale().addTo(map);
    </script>
</body>
</html>'''

        # Save map
        map_file = "fire_risk_distribution_map.html"
        with open(map_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Fire Risk Distribution Map saved: {map_file}")
        return map_file
    
    def create_post_fire_recruitment_map(self):
        """Create map showing post-fire recruitment distribution"""
        print("\n🗺️ Creating Post-Fire Recruitment Distribution Map...")
        
        # Filter occurrence data for species with fire traits
        fire_occurrences = self.occurrence_data[
            self.occurrence_data['Scientific Name'].isin(self.species_with_fire_traits)
        ].copy()
        
        # Categorize each occurrence
        fire_occurrences['Recruitment_Category'] = fire_occurrences['Scientific Name'].apply(
            lambda x: self.categorize_post_fire_recruitment(x)[0]
        )
        fire_occurrences['Color'] = fire_occurrences['Scientific Name'].apply(
            lambda x: self.categorize_post_fire_recruitment(x)[1]
        )
        
        # Calculate center point
        center_lat = fire_occurrences['Decimal Latitude'].mean()
        center_lon = fire_occurrences['Decimal Longitude'].mean()
        
        # Create HTML content with Leaflet.js
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Post-Fire Recruitment Distribution Map</title>
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
            <h1>Post-Fire Recruitment Distribution Map</h1>
            <p>Interactive map showing plant locations categorized by post-fire recruitment ability</p>
        </div>
        
        <div class="map-container">
            <div id="map"></div>
            
            <div class="legend">
                <h3>Post-Fire Recruitment Categories</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #3498db;"></div>
                    <span>Has Recruitment (Can establish new individuals)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #e74c3c;"></div>
                    <span>No Recruitment (Cannot establish new individuals)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #9b59b6;"></div>
                    <span>Mixed Response (Variable recruitment)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #95a5a6;"></div>
                    <span>No Data</span>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences):,}</div>
                    <div>Total Plant Locations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Recruitment_Category'] == 'Has Recruitment']):,}</div>
                    <div>Has Recruitment</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Recruitment_Category'] == 'No Recruitment']):,}</div>
                    <div>No Recruitment</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Recruitment_Category'] == 'Mixed Response']):,}</div>
                    <div>Mixed Response</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        var map = L.map('map').setView([{center_lat}, {center_lon}], 10);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        var hasRecruitmentLayer = L.layerGroup();
        var noRecruitmentLayer = L.layerGroup();
        var mixedResponseLayer = L.layerGroup();
        var noDataLayer = L.layerGroup();
'''

        # Add markers for each category
        for _, row in fire_occurrences.iterrows():
            species_name = str(row['Scientific Name']).replace("'", "\\'")
            category = row['Recruitment_Category']
            
            if category == 'Has Recruitment':
                color = '#3498db'
                layer = 'hasRecruitmentLayer'
            elif category == 'No Recruitment':
                color = '#e74c3c'
                layer = 'noRecruitmentLayer'
            elif category == 'Mixed Response':
                color = '#9b59b6'
                layer = 'mixedResponseLayer'
            else:
                color = '#95a5a6'
                layer = 'noDataLayer'
            
            html_content += f'''
        L.circleMarker([{row['Decimal Latitude']}, {row['Decimal Longitude']}], {{
            radius: 4, fillColor: '{color}', color: '{color}', weight: 2, opacity: 0.8, fillOpacity: 0.7
        }}).bindPopup('<b>{species_name}</b><br>Recruitment: {category}').addTo({layer});'''

        html_content += '''
        hasRecruitmentLayer.addTo(map);
        noRecruitmentLayer.addTo(map);
        mixedResponseLayer.addTo(map);
        noDataLayer.addTo(map);

        var overlayMaps = {
            "Has Recruitment": hasRecruitmentLayer,
            "No Recruitment": noRecruitmentLayer,
            "Mixed Response": mixedResponseLayer,
            "No Data": noDataLayer
        };

        L.control.layers({}, overlayMaps).addTo(map);
        L.control.scale().addTo(map);
    </script>
</body>
</html>'''

        # Save map
        map_file = "post_fire_recruitment_map.html"
        with open(map_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Post-Fire Recruitment Map saved: {map_file}")
        return map_file
    
    def create_resprouting_capacity_map(self):
        """Create map showing resprouting capacity distribution"""
        print("\n🗺️ Creating Species Resprouting Capacity Distribution Map...")
        
        # Filter occurrence data for species with fire traits
        fire_occurrences = self.occurrence_data[
            self.occurrence_data['Scientific Name'].isin(self.species_with_fire_traits)
        ].copy()
        
        # Categorize each occurrence
        fire_occurrences['Resprouting_Category'] = fire_occurrences['Scientific Name'].apply(
            lambda x: self.categorize_resprouting_capacity(x)[0]
        )
        fire_occurrences['Color'] = fire_occurrences['Scientific Name'].apply(
            lambda x: self.categorize_resprouting_capacity(x)[1]
        )
        
        # Calculate center point
        center_lat = fire_occurrences['Decimal Latitude'].mean()
        center_lon = fire_occurrences['Decimal Longitude'].mean()
        
        # Create HTML content with Leaflet.js
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Species Resprouting Capacity Distribution Map</title>
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
            <h1>Species Resprouting Capacity Distribution Map</h1>
            <p>Interactive map showing plant locations categorized by resprouting capacity</p>
        </div>
        
        <div class="map-container">
            <div id="map"></div>
            
            <div class="legend">
                <h3>Resprouting Capacity Categories</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #27ae60;"></div>
                    <span>Can Resprout (Regrows from surviving parts)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #e74c3c;"></div>
                    <span>Fire Killed (Killed by fire)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #f39c12;"></div>
                    <span>Mixed Response (Variable resprouting)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #95a5a6;"></div>
                    <span>No Data</span>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences):,}</div>
                    <div>Total Plant Locations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Resprouting_Category'] == 'Can Resprout']):,}</div>
                    <div>Can Resprout</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Resprouting_Category'] == 'Fire Killed']):,}</div>
                    <div>Fire Killed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(fire_occurrences[fire_occurrences['Resprouting_Category'] == 'Mixed Response']):,}</div>
                    <div>Mixed Response</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        var map = L.map('map').setView([{center_lat}, {center_lon}], 10);

        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);

        var canResproutLayer = L.layerGroup();
        var fireKilledLayer = L.layerGroup();
        var mixedResponseLayer = L.layerGroup();
        var noDataLayer = L.layerGroup();
'''

        # Add markers for each category
        for _, row in fire_occurrences.iterrows():
            species_name = str(row['Scientific Name']).replace("'", "\\'")
            category = row['Resprouting_Category']
            
            if category == 'Can Resprout':
                color = '#27ae60'
                layer = 'canResproutLayer'
            elif category == 'Fire Killed':
                color = '#e74c3c'
                layer = 'fireKilledLayer'
            elif category == 'Mixed Response':
                color = '#f39c12'
                layer = 'mixedResponseLayer'
            else:
                color = '#95a5a6'
                layer = 'noDataLayer'
            
            html_content += f'''
        L.circleMarker([{row['Decimal Latitude']}, {row['Decimal Longitude']}], {{
            radius: 4, fillColor: '{color}', color: '{color}', weight: 2, opacity: 0.8, fillOpacity: 0.7
        }}).bindPopup('<b>{species_name}</b><br>Resprouting: {category}').addTo({layer});'''

        html_content += '''
        canResproutLayer.addTo(map);
        fireKilledLayer.addTo(map);
        mixedResponseLayer.addTo(map);
        noDataLayer.addTo(map);

        var overlayMaps = {
            "Can Resprout": canResproutLayer,
            "Fire Killed": fireKilledLayer,
            "Mixed Response": mixedResponseLayer,
            "No Data": noDataLayer
        };

        L.control.layers({}, overlayMaps).addTo(map);
        L.control.scale().addTo(map);
    </script>
</body>
</html>'''

        # Save map
        map_file = "resprouting_capacity_map.html"
        with open(map_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Resprouting Capacity Map saved: {map_file}")
        return map_file
    
    def generate_all_maps(self):
        """Generate all four fire-related maps"""
        print("🚀 Starting Fire Plant Location Maps Generation...")
        print("=" * 60)
        
        # Load data
        if not self.load_data():
            return False
        
        # Identify fire-related species
        self.identify_fire_related_species()
        
        # Generate only Resprouting Capacity Map for debugging
        maps_created = []
        
        # 4. Resprouting Capacity Map (DEBUG ONLY)
        map4 = self.create_resprouting_capacity_map()
        if map4:
            maps_created.append(map4)
        
        print("\n" + "=" * 60)
        print("🎉 Fire Plant Location Maps Generation Complete!")
        print(f"📊 Generated {len(maps_created)} interactive maps:")
        
        for i, map_file in enumerate(maps_created, 1):
            print(f"   {i}. {map_file}")
        
        print("\n📋 Map Categories:")
        print("   • Species Resprouting Capacity Distribution (DEBUG)")
        
        print("\n🌐 To view maps:")
        print("   1. Open any .html file in your web browser")
        print("   2. Use zoom and pan to explore plant locations")
        print("   3. Click markers to see species details")
        
        return maps_created


def main():
    """Main function to generate fire plant location maps"""
    mapper = FirePlantLocationMapper()
    
    # Generate all maps
    maps = mapper.generate_all_maps()
    
    if maps:
        print("\n✅ All fire plant location maps generated successfully!")
        return True
    else:
        print("\n❌ Map generation failed!")
        return False


if __name__ == "__main__":
    main()