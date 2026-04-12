import pandas as pd
import pymysql
import re

# Database connection
DB_HOST = "vps.biogeoda.au"
DB_NAME = "flora-admin_Project.ID.10"
DB_USER = "flora-admin_flora-admin"
DB_PASS = "BOT_mortimer7indiana"

def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        charset='utf8mb4'
    )


def load_traits():
    print("Reading TraitsDescriptions-71-in-use.xlsx...")
    df = pd.read_excel("TraitsDescriptions-71-in-use.xlsx")
 
    conn = get_connection()
    cursor = conn.cursor()
 
    inserted = 0
    for _, row in df.iterrows():
        trait_name = str(row['trait']).strip() if pd.notna(row['trait']) else None
        if not trait_name:
            continue
 
        trait_type_name = str(row['Trait Type Name']).strip() if pd.notna(row['Trait Type Name']) else None
        column_number = int(row['Column']) if pd.notna(row['Column']) else None
        label = str(row['label']).strip() if pd.notna(row['label']) else None
        description = str(row['description']).strip() if pd.notna(row['description']) else None
        trait_type = str(row['trait_type']).strip() if pd.notna(row['trait_type']) else None
        units = str(row['units']).strip() if pd.notna(row['units']) else None
 
        cursor.execute("""
            INSERT INTO traits 
            (trait_type_name, trait_name, trait_info, trait_unit, trait_type, trait_label, column_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (trait_type_name, trait_name, description, units, trait_type, label, column_number))
        inserted += 1
 
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Loaded {inserted} traits")
 
def load_trait_categories():
    print("Reading CategoryValuesFull...")
    df = pd.read_excel("APD_traits-New-FullList.xlsx", sheet_name="CategoryValuesFull")
 
    conn = get_connection()
    cursor = conn.cursor()
 
    inserted = 0
    skipped = 0
    for _, row in df.iterrows():
        trait_name = str(row['trait']).strip() if pd.notna(row['trait']) else None
        category_value = str(row['allowed_values_levels']).strip() if pd.notna(row['allowed_values_levels']) else None
        category_description = str(row['categorical_trait_description']).strip() if pd.notna(row['categorical_trait_description']) else None
 
        if not trait_name or not category_value:
            continue
 
        # get trait_id
        cursor.execute("SELECT trait_id FROM traits WHERE trait_name = %s", (trait_name,))
        result = cursor.fetchone()
        if not result:
            skipped += 1
            continue
 
        trait_id = result[0]
        cursor.execute("""
            INSERT INTO trait_categories (trait_id, category_value, category_description)
            VALUES (%s, %s, %s)
        """, (trait_id, category_value, category_description))
        inserted += 1
 
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Loaded {inserted} trait categories, skipped {skipped}")
 
if __name__ == "__main__":
    print("=== Loading traits data ===")
    load_traits()
    load_trait_categories()
    print("=== Done! ===")