#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Experiment 4: Fire Tolerant Plants Analysis
Analyzes fire-related traits in plant species data and creates a comprehensive report.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import re
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Set style for better plots
plt.style.use('default')
sns.set_palette("husl")

def load_data():
    """Load the plant traits data."""
    print("Loading plant traits data...")
    df = pd.read_csv("../Database/final_Traits_clean_data_with_insert_common_name_local_stauts.csv")
    print(f"Data loaded: {df.shape[0]} species, {df.shape[1]} traits")
    return df

def identify_fire_related_traits(df):
    """Identify all fire-related trait columns."""
    print("\nIdentifying fire-related traits...")
    
    # Direct fire-related traits
    fire_traits = [
        'plant_tolerance_fire',
        'post_fire_recruitment', 
        'post_fire_flowering',
        'resprouting_capacity',
        'resprouting_capacity_non_fire_disturbance',
        'resprouting_capacity_juvenile',
        'resprouting_capacity_proportion_individuals',
        'resprouting_capacity_time_from_germination'
    ]
    
    # Fire time-related traits (starting with fire_time_from_fire_to_)
    fire_time_traits = [col for col in df.columns if col.startswith('fire_time_from_fire_to_')]
    
    # Combine all fire-related traits
    all_fire_traits = fire_traits + fire_time_traits
    
    # Filter to only include traits that exist in the dataset
    existing_fire_traits = [trait for trait in all_fire_traits if trait in df.columns]
    
    print(f"Found {len(existing_fire_traits)} fire-related traits:")
    for trait in existing_fire_traits:
        print(f"  - {trait}")
    
    return existing_fire_traits

def analyze_trait_data(df, trait):
    """Analyze data for a specific trait."""
    print(f"\nAnalyzing trait: {trait}")
    
    # Get non-null values
    non_null_data = df[trait].dropna()
    total_species = len(df)
    species_with_data = len(non_null_data)
    
    print(f"  Species with data: {species_with_data}/{total_species} ({species_with_data/total_species*100:.1f}%)")
    
    if species_with_data == 0:
        return {
            'trait': trait,
            'total_species': total_species,
            'species_with_data': 0,
            'coverage_percentage': 0,
            'unique_values': 0,
            'most_common_values': [],
            'v_marked_count': 0,
            'description': get_trait_description(trait)
        }
    
    # Count unique values
    unique_values = non_null_data.nunique()
    
    # Get most common values (including those with (V) markers)
    value_counts = non_null_data.value_counts()
    most_common = value_counts.head(5).to_dict()
    
    # Analyze (V) markers
    v_marked_values = non_null_data[non_null_data.str.contains(r'\(V\)', na=False)]
    v_count = len(v_marked_values)
    
    return {
        'trait': trait,
        'total_species': total_species,
        'species_with_data': species_with_data,
        'coverage_percentage': species_with_data/total_species*100,
        'unique_values': unique_values,
        'most_common_values': most_common,
        'v_marked_count': v_count,
        'description': get_trait_description(trait)
    }

def get_trait_description(trait):
    """Get description for fire-related traits."""
    descriptions = {
        'plant_tolerance_fire': 'Plant tolerance to fire - indicates how well a species can survive fire',
        'post_fire_recruitment': 'Post-fire recruitment - ability to establish new individuals after fire',
        'post_fire_flowering': 'Post-fire flowering - flowering response after fire events',
        'resprouting_capacity': 'Resprouting capacity - ability to regrow from surviving plant parts after fire',
        'resprouting_capacity_non_fire_disturbance': 'Resprouting capacity for non-fire disturbances',
        'resprouting_capacity_juvenile': 'Resprouting capacity of juvenile plants',
        'resprouting_capacity_proportion_individuals': 'Proportion of individuals that can resprout',
        'resprouting_capacity_time_from_germination': 'Time from germination to resprouting capacity',
        'fire_time_from_fire_to_fruiting': 'Time from fire to fruiting - how long after fire before fruiting',
        'fire_time_from_fire_to_flowering': 'Time from fire to flowering - how long after fire before flowering',
        'fire_time_from_fire_to_50_percent_flowering': 'Time from fire to 50% flowering',
        'fire_time_from_fire_to_50_percent_fruiting': 'Time from fire to 50% fruiting',
        'fire_time_from_fire_to_peak_flowering': 'Time from fire to peak flowering',
        'fire_time_from_fire_to_flowering_decline': 'Time from fire to flowering decline'
    }
    
    return descriptions.get(trait, 'Fire-related trait - specific function not defined')

def create_trait_summary_table(analysis_results):
    """Create a summary table of all fire-related traits."""
    print("\nCreating trait summary table...")
    
    summary_data = []
    for result in analysis_results:
        summary_data.append({
            'Trait Name': result['trait'],
            'Description': result['description'],
            'Species with Data': f"{result['species_with_data']}/{result['total_species']}",
            'Coverage %': f"{result['coverage_percentage']:.1f}%",
            'Unique Values': result['unique_values'],
            'V-Marked Count': result['v_marked_count'],
            'Most Common Values': str(list(result['most_common_values'].keys())[:3]) if result['most_common_values'] else 'None'
        })
    
    summary_df = pd.DataFrame(summary_data)
    return summary_df

def create_species_fire_traits_table(df, fire_traits):
    """Create a table showing specific species with their fire traits."""
    print("\nCreating species fire traits table...")
    
    # Filter species that have at least one fire-related trait
    species_with_fire_data = []
    
    for idx, row in df.iterrows():
        species_name = row['species_name']
        fire_traits_data = {}
        
        for trait in fire_traits:
            if trait in df.columns and pd.notna(row[trait]) and str(row[trait]).strip() != '':
                fire_traits_data[trait] = str(row[trait])
        
        if fire_traits_data:  # Only include species with fire trait data
            species_with_fire_data.append({
                'Species Name': species_name,
                'Family': row.get('family', ''),
                'Genus': row.get('genus', ''),
                'Local Status': row.get('Local Status', ''),
                'Fire Traits': fire_traits_data
            })
    
    return species_with_fire_data

def create_visualizations(df, fire_traits, species_data):
    """Create visualizations showing fire trait patterns."""
    print("\nCreating visualizations...")
    
    # Set up the plotting
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Fire-Related Plant Species Analysis', fontsize=16, fontweight='bold')
    
    # 1. Fire recovery time distribution
    ax1 = axes[0, 0]
    recovery_times = {'Fast (<12 months)': 0, 'Medium (12-24 months)': 0, 'Slow (>24 months)': 0, 'No Data': 0}
    
    for species in species_data:
        has_timing_data = False
        max_time = 0
        
        for trait_name, trait_value in species['Fire Traits'].items():
            if 'fire_time_from_fire_to' in trait_name:
                has_timing_data = True
                # Extract numeric values
                numbers = re.findall(r'(\d+(?:\.\d+)?)', str(trait_value))
                if numbers:
                    trait_max = max([float(n) for n in numbers])
                    max_time = max(max_time, trait_max)
        
        if has_timing_data:
            if max_time < 12:
                recovery_times['Fast (<12 months)'] += 1
            elif max_time <= 24:
                recovery_times['Medium (12-24 months)'] += 1
            else:
                recovery_times['Slow (>24 months)'] += 1
        else:
            recovery_times['No Data'] += 1
    
    categories = list(recovery_times.keys())
    counts = list(recovery_times.values())
    colors = ['green', 'orange', 'red', 'gray']
    
    bars = ax1.bar(categories, counts, color=colors, alpha=0.7)
    ax1.set_xlabel('Recovery Time Category')
    ax1.set_ylabel('Number of Species')
    ax1.set_title('Fire Recovery Time Distribution')
    ax1.tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    # 2. Fire risk distribution
    ax2 = axes[0, 1]
    family_risk = {}
    for species in species_data:
        family = species['Family']
        if not family:
            continue
            
        if family not in family_risk:
            family_risk[family] = {'Low Risk': 0, 'Medium Risk': 0, 'High Risk': 0}
        
        # Calculate risk based on resprouting and recruitment
        can_resprout = False
        has_recruitment = False
        
        if 'resprouting_capacity' in species['Fire Traits']:
            trait_value = str(species['Fire Traits']['resprouting_capacity']).lower()
            if 'resprouts' in trait_value:
                can_resprout = True
        
        if 'post_fire_recruitment' in species['Fire Traits']:
            trait_value = str(species['Fire Traits']['post_fire_recruitment']).lower()
            if 'post_fire_recruitment' in trait_value and 'absent' not in trait_value:
                has_recruitment = True
        
        # Determine risk level
        if can_resprout and has_recruitment:
            family_risk[family]['Low Risk'] += 1
        elif can_resprout or has_recruitment:
            family_risk[family]['Medium Risk'] += 1
        else:
            family_risk[family]['High Risk'] += 1
    
    # Show risk distribution
    total_low = sum(data['Low Risk'] for data in family_risk.values())
    total_medium = sum(data['Medium Risk'] for data in family_risk.values())
    total_high = sum(data['High Risk'] for data in family_risk.values())
    
    risk_labels = ['Low Risk', 'Medium Risk', 'High Risk']
    risk_counts = [total_low, total_medium, total_high]
    risk_colors = ['green', 'orange', 'red']
    
    bars = ax2.bar(risk_labels, risk_counts, color=risk_colors, alpha=0.7)
    ax2.set_xlabel('Fire Risk Level')
    ax2.set_ylabel('Number of Species')
    ax2.set_title('Overall Fire Risk Distribution')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    # 3. Resprouting capacity distribution
    ax3 = axes[1, 0]
    resprout_categories = {'Can Resprout': 0, 'Fire Killed': 0, 'Mixed Response': 0, 'No Data': 0}
    
    for species in species_data:
        if 'resprouting_capacity' in species['Fire Traits']:
            trait_value = str(species['Fire Traits']['resprouting_capacity']).lower()
            if 'resprouts' in trait_value and 'fire_killed' not in trait_value:
                resprout_categories['Can Resprout'] += 1
            elif 'fire_killed' in trait_value and 'resprouts' not in trait_value:
                resprout_categories['Fire Killed'] += 1
            elif 'resprouts' in trait_value and 'fire_killed' in trait_value:
                resprout_categories['Mixed Response'] += 1
        else:
            resprout_categories['No Data'] += 1
    
    categories = list(resprout_categories.keys())
    counts = list(resprout_categories.values())
    colors = ['green', 'red', 'orange', 'gray']
    
    bars = ax3.bar(categories, counts, color=colors, alpha=0.7)
    ax3.set_xlabel('Resprouting Response')
    ax3.set_ylabel('Number of Species')
    ax3.set_title('Species Resprouting Capacity Distribution')
    ax3.tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    # 4. Post-fire recruitment distribution
    ax4 = axes[1, 1]
    recruitment_categories = {'Has Recruitment': 0, 'No Recruitment': 0, 'Mixed Response': 0, 'No Data': 0}
    
    for species in species_data:
        if 'post_fire_recruitment' in species['Fire Traits']:
            trait_value = str(species['Fire Traits']['post_fire_recruitment']).lower()
            if 'post_fire_recruitment' in trait_value and 'absent' not in trait_value:
                recruitment_categories['Has Recruitment'] += 1
            elif 'absent' in trait_value:
                recruitment_categories['No Recruitment'] += 1
            else:
                recruitment_categories['Mixed Response'] += 1
        else:
            recruitment_categories['No Data'] += 1
    
    categories = list(recruitment_categories.keys())
    counts = list(recruitment_categories.values())
    colors = ['blue', 'red', 'purple', 'gray']
    
    bars = ax4.bar(categories, counts, color=colors, alpha=0.7)
    ax4.set_xlabel('Recruitment Response')
    ax4.set_ylabel('Number of Species')
    ax4.set_title('Post-Fire Recruitment Distribution')
    ax4.tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    return fig

def create_additional_visualizations(species_data):
    """Create additional meaningful visualizations."""
    print("\nCreating additional visualizations...")
    
    # Create multiple figures for different analyses
    figures = []
    
    # Skip all additional visualizations - only keep main Fire-Related Plant Species Analysis
    # No additional figures to add
    
    return figures

def create_detailed_analysis_table(df, fire_traits):
    """Create detailed analysis table for each fire trait."""
    print("\nCreating detailed analysis...")
    
    detailed_results = []
    
    for trait in fire_traits:
        if trait in df.columns:
            trait_data = df[trait].dropna()
            
            if len(trait_data) > 0:
                # Get all unique values and their counts
                value_counts = trait_data.value_counts()
                
                # Analyze V-marked values
                v_marked = trait_data[trait_data.str.contains(r'\(V\)', na=False)]
                
                for value, count in value_counts.head(10).items():  # Top 10 most common
                    is_v_marked = '(V)' in str(value)
                    detailed_results.append({
                        'Trait': trait,
                        'Value': value,
                        'Count': count,
                        'Is V-Marked': is_v_marked,
                        'Percentage': (count / len(trait_data)) * 100
                    })
    
    return pd.DataFrame(detailed_results)

def generate_pdf_report(species_data, detailed_df, fig, analysis_results):
    """Generate comprehensive PDF report."""
    print("\nGenerating PDF report...")
    
    with PdfPages('fire_traits_analysis_report.pdf') as pdf:
        # Title page
        fig_title, ax_title = plt.subplots(figsize=(8.5, 11))
        ax_title.axis('off')
        ax_title.text(0.5, 0.7, 'Experiment 4: Fire Tolerant Plants Analysis', 
                     ha='center', va='center', fontsize=20, fontweight='bold')
        ax_title.text(0.5, 0.6, 'Fire-Related Plant Traits Analysis', 
                     ha='center', va='center', fontsize=14)
        ax_title.text(0.5, 0.4, f'Total Species with Fire Traits: {len(species_data)}', 
                     ha='center', va='center', fontsize=12)
        ax_title.text(0.5, 0.3, f'Fire-Related Traits Analyzed: {len(analysis_results)}', 
                     ha='center', va='center', fontsize=12)
        ax_title.text(0.5, 0.1, 'Generated by Fire Traits Analysis Script', 
                     ha='center', va='center', fontsize=10, style='italic')
        pdf.savefig(fig_title, bbox_inches='tight')
        plt.close(fig_title)
        
        # Fire Risk Assessment Methodology page (Page 2)
        fig_methodology, ax_methodology = plt.subplots(figsize=(11, 8.5))
        ax_methodology.axis('off')
        
        methodology_text = """
FIRE RISK ASSESSMENT METHODOLOGY

Risk Assessment Criteria:
The fire risk assessment is based on two key fire survival traits:

1. RESPROUTING CAPACITY
   - Ability to regrow from surviving plant parts after fire
   - Indicates rapid post-fire recovery potential
   - Species with 'resprouts' in resprouting_capacity trait

2. POST-FIRE RECRUITMENT
   - Ability to establish new individuals after fire events
   - Indicates long-term population recovery potential
   - Species with 'post_fire_recruitment' (not 'absent') in post_fire_recruitment trait

RISK LEVEL DETERMINATION:

LOW RISK (Green):
- Condition: Can BOTH resprout AND has post-fire recruitment
- Interpretation: Best fire survival strategy with dual protection
- Management: Can withstand frequent burning, suitable for hazard reduction burns

MEDIUM RISK (Orange):
- Condition: Can EITHER resprout OR has post-fire recruitment (only one trait)
- Interpretation: Partial fire survival strategy with limited protection
- Management: Moderate fire tolerance, requires careful burn planning

HIGH RISK (Red):
- Condition: Cannot resprout AND has no post-fire recruitment
- Interpretation: Poor fire survival strategy with minimal protection
- Management: High fire sensitivity, needs protection from frequent burning

APPLICATION FOR HAZARD REDUCTION BURNING:
- Low Risk species/families: Suitable for frequent burning
- Medium Risk species/families: Moderate burning frequency
- High Risk species/families: Minimal burning, focus on protection
        """
        
        ax_methodology.text(0.05, 0.95, methodology_text, transform=ax_methodology.transAxes, 
                           fontsize=10, verticalalignment='top', fontfamily='monospace',
                           bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
        
        ax_methodology.set_title('Fire Risk Assessment Methodology', fontsize=16, fontweight='bold', pad=20)
        pdf.savefig(fig_methodology, bbox_inches='tight')
        plt.close(fig_methodology)
        
        # Main visualizations page (Page 3)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print("PDF report generated: fire_traits_analysis_report.pdf")

def main():
    """Main function to run the fire traits analysis."""
    print("=" * 60)
    print("EXPERIMENT 4: FIRE TOLERANT PLANTS ANALYSIS")
    print("=" * 60)
    
    # Load data
    df = load_data()
    
    # Identify fire-related traits
    fire_traits = identify_fire_related_traits(df)
    
    if not fire_traits:
        print("No fire-related traits found in the dataset!")
        return
    
    # Analyze each fire trait
    print(f"\nAnalyzing {len(fire_traits)} fire-related traits...")
    analysis_results = []
    
    for trait in fire_traits:
        result = analyze_trait_data(df, trait)
        analysis_results.append(result)
    
    # Create species fire traits table
    species_data = create_species_fire_traits_table(df, fire_traits)
    print(f"\nFound {len(species_data)} species with fire-related traits")
    
    # Create visualizations showing specific species
    fig = create_visualizations(df, fire_traits, species_data)
    
    # Create detailed analysis
    detailed_df = create_detailed_analysis_table(df, fire_traits)
    
    # Generate PDF report
    generate_pdf_report(species_data, detailed_df, fig, analysis_results)
    
    # Save species data to CSV
    if species_data:
        species_df = pd.DataFrame(species_data)
        species_df.to_csv('fire_species_with_traits.csv', index=False)
        print(f"\nSpecies data saved to: fire_species_with_traits.csv")
    
    # Save detailed analysis to CSV
    if not detailed_df.empty:
        detailed_df.to_csv('fire_traits_detailed_analysis.csv', index=False)
        print(f"Detailed analysis saved to: fire_traits_detailed_analysis.csv")
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)
    print("Files generated:")
    print("- fire_traits_analysis_report.pdf")
    print("- fire_traits_summary.csv") 
    print("- fire_traits_detailed_analysis.csv")

if __name__ == "__main__":
    main()
