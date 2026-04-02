from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

# ===== 路径统一定义 =====
THIS_FILE = Path(__file__).resolve()
EXP_DIR   = THIS_FILE.parent                         # 本脚本所在目录（Remade experiment/experiment3）
PROJ_ROOT = THIS_FILE.parents[2]                     # 项目根：plantwebsite-main
OUTPUT_DIR = EXP_DIR / "experiment3_outputs"         # 建议的输出目录
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 你项目根目录下的文件都从 PROJ_ROOT 取
TRAITS_CSV = PROJ_ROOT / "Final_Species_Traits.csv"
DATASETS = {
    "ALA_e9":          PROJ_ROOT / "ALA_e9.csv",
    "iNaturalist_e9":  PROJ_ROOT / "iNaturalist_e9.csv",
    "Prototype_e9":    PROJ_ROOT / "Prototype_e9.csv",
}

plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_and_prepare_data():
    print("Loading datasets...")

    # 用绝对路径读取
    traits_df = pd.read_csv(TRAITS_CSV)
    print(f"Loaded {len(traits_df)} species from traits data")

    datasets = {}
    for name, csv_path in DATASETS.items():
        print("Reading ->", csv_path)               # 调试：显示绝对路径
        df = pd.read_csv(csv_path)
        datasets[name] = df
        print(f"Loaded {len(df)} records from {name}")

    return traits_df, datasets

def extract_plant_forms(traits_df):
    """Extract and clean plant growth forms from traits data."""
    print("Extracting plant growth forms...")
    
    # Get unique species and their forms
    species_forms = traits_df[['species_name', 'plant_growth_form']].copy()
    species_forms = species_forms.dropna(subset=['plant_growth_form'])
    
    # Clean and split multiple forms
    forms_data = []
    for _, row in species_forms.iterrows():
        species = row['species_name']
        forms_str = str(row['plant_growth_form']).strip()
        
        if forms_str and forms_str != 'nan':
            # Split by comma and clean each form
            forms = [form.strip() for form in forms_str.split(',')]
            for form in forms:
                if form and form != 'nan':
                    forms_data.append({
                        'species_name': species,
                        'plant_growth_form': form
                    })
    
    forms_df = pd.DataFrame(forms_data)
    print(f"Extracted {len(forms_df)} species-form combinations")
    
    return forms_df

def count_observations_by_species(datasets):
    """Count observations for each species in each dataset."""
    print("Counting observations by species...")
    
    species_counts = {}
    
    for dataset_name, df in datasets.items():
        # Count occurrences by species
        species_count = df['Scientific Name'].value_counts().reset_index()
        species_count.columns = ['species_name', 'observation_count']
        species_count['dataset'] = dataset_name
        species_counts[dataset_name] = species_count
        print(f"{dataset_name}: {len(species_count)} unique species")
    
    return species_counts

def merge_forms_with_observations(forms_df, species_counts):
    """Merge plant forms with observation counts for each dataset."""
    print("Merging forms with observation data...")
    
    merged_data = {}
    
    for dataset_name, counts_df in species_counts.items():
        # Merge forms with counts
        merged = pd.merge(forms_df, counts_df, on='species_name', how='inner')
        
        # For species with multiple forms, keep the one with highest observation count
        merged_sorted = merged.sort_values('observation_count', ascending=False)
        merged_deduped = merged_sorted.drop_duplicates(subset=['species_name'], keep='first')
        
        merged_data[dataset_name] = merged_deduped
        print(f"{dataset_name}: {len(merged_deduped)} species after deduplication")
    
    return merged_data

def analyze_forms_by_dataset(merged_data):
    """Analyze plant form distribution for each dataset."""
    print("Analyzing form distributions...")
    
    analysis_results = {}
    
    for dataset_name, df in merged_data.items():
        # Count species by form
        form_counts = df['plant_growth_form'].value_counts().reset_index()
        form_counts.columns = ['plant_growth_form', 'species_count']
        
        # Calculate total observations by form
        form_obs = df.groupby('plant_growth_form')['observation_count'].sum().reset_index()
        form_obs.columns = ['plant_growth_form', 'total_observations']
        
        # Merge counts and observations
        analysis = pd.merge(form_counts, form_obs, on='plant_growth_form')
        analysis['dataset'] = dataset_name
        analysis = analysis.sort_values('species_count', ascending=False)
        
        analysis_results[dataset_name] = analysis
        print(f"\n{dataset_name} - Top 5 forms by species count:")
        print(analysis.head())
    
    return analysis_results

def create_species_tables(merged_data, pdf):
    """Create detailed tables showing each species with its form and observation counts."""
    print("Creating species tables...")
    
    for dataset_name, df in merged_data.items():
        # Sort by species name for better readability
        df_sorted = df.sort_values('species_name').copy()
        
        # Create table
        fig, ax = plt.subplots(figsize=(16, 12))
        ax.axis('tight')
        ax.axis('off')
        
        # Prepare table data
        table_data = []
        for _, row in df_sorted.iterrows():
            table_data.append([
                row['species_name'],
                row['plant_growth_form'],
                f"{row['observation_count']:,}"
            ])
        
        # Create table
        table = ax.table(cellText=table_data,
                        colLabels=['Species Name', 'Plant Growth Form', 'Observation Count'],
                        cellLoc='left',
                        loc='center',
                        bbox=[0, 0, 1, 1])
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.5)
        
        # Style header
        for i in range(3):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Style data rows
        for i in range(1, len(table_data) + 1):
            for j in range(3):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
                else:
                    table[(i, j)].set_facecolor('white')
        
        # Set title
        ax.set_title(f'{dataset_name} Dataset - Species Forms and Observation Counts\n'
                    f'Total Species: {len(df_sorted)}, Total Observations: {df_sorted["observation_count"].sum():,}',
                    fontsize=14, fontweight='bold', pad=20)
        
        pdf.savefig(fig, bbox_inches='tight', dpi=300)
        plt.close()

def create_visualizations(analysis_results, merged_data, pdf):
    """Create comprehensive visualizations comparing datasets."""
    print("Creating visualizations...")
    
    # 1. Species count by form - Bar chart comparison
    plt.figure(figsize=(15, 10))
    
    # Prepare data for comparison
    all_forms = set()
    for analysis in analysis_results.values():
        all_forms.update(analysis['plant_growth_form'].tolist())
    
    all_forms = sorted(list(all_forms))
    
    # Create subplot for each dataset
    fig, axes = plt.subplots(2, 2, figsize=(20, 15))
    axes = axes.flatten()
    
    for i, (dataset_name, analysis) in enumerate(analysis_results.items()):
        if i < 3:  # Only plot first 3 datasets
            ax = axes[i]
            
            # Create a complete dataframe with all forms
            complete_data = pd.DataFrame({'plant_growth_form': all_forms})
            complete_data = complete_data.merge(analysis, on='plant_growth_form', how='left')
            complete_data['species_count'] = complete_data['species_count'].fillna(0)
            
            # Plot
            bars = ax.bar(range(len(complete_data)), complete_data['species_count'], 
                         color=plt.cm.Set3(i/3))
            ax.set_title(f'{dataset_name} - Species Count by Plant Form', fontsize=14, fontweight='bold')
            ax.set_xlabel('Plant Growth Form', fontsize=12)
            ax.set_ylabel('Number of Species', fontsize=12)
            ax.set_xticks(range(len(complete_data)))
            ax.set_xticklabels(complete_data['plant_growth_form'], rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    # Remove empty subplot
    axes[3].remove()
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight', dpi=300)
    plt.close()
    
    # 2. Observation count by form - Bar chart comparison
    plt.figure(figsize=(15, 10))
    
    fig, axes = plt.subplots(2, 2, figsize=(20, 15))
    axes = axes.flatten()
    
    for i, (dataset_name, analysis) in enumerate(analysis_results.items()):
        if i < 3:
            ax = axes[i]
            
            # Create complete dataframe
            complete_data = pd.DataFrame({'plant_growth_form': all_forms})
            complete_data = complete_data.merge(analysis, on='plant_growth_form', how='left')
            complete_data['total_observations'] = complete_data['total_observations'].fillna(0)
            
            # Plot
            bars = ax.bar(range(len(complete_data)), complete_data['total_observations'], 
                         color=plt.cm.Set2(i/3))
            ax.set_title(f'{dataset_name} - Total Observations by Plant Form', fontsize=14, fontweight='bold')
            ax.set_xlabel('Plant Growth Form', fontsize=12)
            ax.set_ylabel('Total Observations', fontsize=12)
            ax.set_xticks(range(len(complete_data)))
            ax.set_xticklabels(complete_data['plant_growth_form'], rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                           f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    axes[3].remove()
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight', dpi=300)
    plt.close()
    
    # 3. Combined comparison - Side by side
    plt.figure(figsize=(20, 12))
    
    # Prepare data for side-by-side comparison
    comparison_data = []
    for dataset_name, analysis in analysis_results.items():
        for _, row in analysis.iterrows():
            comparison_data.append({
                'dataset': dataset_name,
                'plant_growth_form': row['plant_growth_form'],
                'species_count': row['species_count'],
                'total_observations': row['total_observations']
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # Species count comparison
    pivot_species = comparison_df.pivot(index='plant_growth_form', columns='dataset', values='species_count').fillna(0)
    pivot_species.plot(kind='bar', ax=ax1, width=0.8)
    ax1.set_title('Species Count Comparison Across Datasets', fontsize=16, fontweight='bold')
    ax1.set_xlabel('Plant Growth Form', fontsize=14)
    ax1.set_ylabel('Number of Species', fontsize=14)
    ax1.legend(title='Dataset', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.tick_params(axis='x', rotation=45)
    
    # Observation count comparison
    pivot_obs = comparison_df.pivot(index='plant_growth_form', columns='dataset', values='total_observations').fillna(0)
    pivot_obs.plot(kind='bar', ax=ax2, width=0.8)
    ax2.set_title('Total Observations Comparison Across Datasets', fontsize=16, fontweight='bold')
    ax2.set_xlabel('Plant Growth Form', fontsize=14)
    ax2.set_ylabel('Total Observations', fontsize=14)
    ax2.legend(title='Dataset', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight', dpi=300)
    plt.close()
    
    print("Visualizations created successfully")

def generate_summary_statistics(analysis_results, merged_data):
    """Generate summary statistics for the analysis."""
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    for dataset_name, analysis in analysis_results.items():
        species_total = len(merged_data.get(dataset_name, []))
        observation_sum = analysis['total_observations'].sum()

        print(f"\n{dataset_name} Dataset:")
        print(f"  Total unique species: {species_total}")
        print(f"  Total unique forms: {len(analysis)}")
        print(f"  Total observations: {observation_sum:,}")
        if species_total:
            print(f"  Average observations per species: {observation_sum / species_total:.1f}")
        else:
            print("  Average observations per species: N/A (no species found)")
        
        print(f"\n  Top 5 forms by species count:")
        for _, row in analysis.head().iterrows():
            print(f"    {row['plant_growth_form']}: {row['species_count']} species, {row['total_observations']:,} observations")
    
    # Cross-dataset comparison
    print(f"\nCross-Dataset Analysis:")
    all_species = set()
    for df in merged_data.values():
        all_species.update(df['species_name'].tolist())
    
    print(f"  Total unique species across all datasets: {len(all_species)}")
    
    # Find common species
    merged_keys = list(merged_data.keys())
    if merged_keys:
        common_species = set(merged_data[merged_keys[0]]['species_name'].tolist())
        for key in merged_keys[1:]:
            common_species &= set(merged_data[key]['species_name'].tolist())
        print(f"  Species present in all datasets: {len(common_species)}")
    else:
        print("  Species present in all datasets: 0 (no merged datasets available)")

def main():
    """Main function to run the complete analysis."""
    print("Starting Species Form Analysis for Survey Quality Verification")
    print("="*70)
    
    try:
        # Load and prepare data
        traits_df, datasets = load_and_prepare_data()
        
        # Extract plant forms
        forms_df = extract_plant_forms(traits_df)
        
        # Count observations
        species_counts = count_observations_by_species(datasets)
        
        # Merge data
        merged_data = merge_forms_with_observations(forms_df, species_counts)
        
        # Analyze forms
        analysis_results = analyze_forms_by_dataset(merged_data)
        
        # Create visualizations and tables
        with PdfPages('species_form_analysis_report.pdf') as pdf:
            create_visualizations(analysis_results, merged_data, pdf)
            create_species_tables(merged_data, pdf)
        
        # Generate summary
        generate_summary_statistics(analysis_results, merged_data)
        
        print("\n" + "="*70)
        print("Analysis completed successfully!")
        print("Results saved to 'species_form_analysis_report.pdf'")
        print("="*70)
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()
