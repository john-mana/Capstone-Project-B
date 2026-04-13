import pandas as pd

df = pd.read_excel('TraitsDescriptions-71-in-use.xlsx')

rows = []
for _, row in df.iterrows():
    def clean(val):
        if pd.isna(val):
            return 'NULL'
        return "'" + str(val).replace("'", "''") + "'"
    
    r = f"({clean(row['Trait Type Name'])}, {clean(row['trait'])}, {clean(row['description'])}, {clean(row['units'])}, {clean(row['trait_type'])}, {clean(row['label'])}, {clean(row['Column'])})"
    rows.append(r)

sql = 'INSERT INTO traits (trait_type_name, trait_name, trait_info, trait_unit, trait_type, trait_label, column_number) VALUES\n' + ',\n'.join(rows) + ';'

with open('insert_traits.sql', 'w', encoding='utf-8') as f:
    f.write(sql)

print('done', len(rows), 'rows')