import pandas as pd

df = pd.read_excel('APD_traits-New-FullList.xlsx', sheet_name='CategoryValuesFull')

rows = []
for _, row in df.iterrows():
    def clean(val):
        if pd.isna(val):
            return 'NULL'
        return "'" + str(val).replace("'", "''") + "'"
    
    trait_name = str(row['trait']).strip()
    category_value = clean(row['allowed_values_levels'])
    category_description = clean(row['categorical_trait_description'])
    
    r = f"((SELECT trait_id FROM traits WHERE trait_name = '{trait_name}'), {category_value}, {category_description})"
    rows.append(r)

sql = 'INSERT INTO trait_categories (trait_id, category_value, category_description) VALUES\n' + ',\n'.join(rows) + ';'

with open('insert_categories.sql', 'w', encoding='utf-8') as f:
    f.write(sql)

print('done', len(rows), 'rows')