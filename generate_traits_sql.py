import pandas as pd

# Read data
df_traits = pd.read_excel('TraitsDescriptions-71-in-use.xlsx')
df_full = pd.read_excel('APD_traits-New-FullList.xlsx', sheet_name='APD_traits-New-All')

our_traits = set(df_traits['trait'].dropna().str.strip())

# Generate INSERT for traits
rows = []
for _, row in df_traits.iterrows():
    def clean(val):
        if pd.isna(val):
            return 'NULL'
        return "'" + str(val).replace("'", "''") + "'"
    
    # get min/max from full list
    full_row = df_full[df_full['trait'] == row['trait']]
    min_val = clean(full_row['allowed_values_min'].values[0]) if len(full_row) > 0 else 'NULL'
    max_val = clean(full_row['allowed_values_max'].values[0]) if len(full_row) > 0 else 'NULL'
    
    r = f"({clean(row['Trait Type Name'])}, {clean(row['trait'])}, {clean(row['description'])}, {clean(row['units'])}, {clean(row['trait_type'])}, {clean(row['label'])}, {clean(row['Column'])}, {min_val}, {max_val})"
    rows.append(r)

sql = 'INSERT INTO traits (trait_type_name, trait_name, trait_info, trait_unit, trait_type, trait_label, column_number, allowed_values_min, allowed_values_max) VALUES\n' + ',\n'.join(rows) + ';'

with open('insert_traits.sql', 'w', encoding='utf-8') as f:
    f.write(sql)

print('done', len(rows), 'rows')