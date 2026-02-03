import sqlite3
import pandas as pd

def check():
    conn = sqlite3.connect('data/companies.db')
    cursor = conn.cursor()
    
    # 1. Check count for Turismo Activo resource
    ta_id = "a1802652-f1cb-4a7d-b8ac-5bdc0183a740"
    count = cursor.execute("SELECT count(*) FROM gva_companies WHERE gva_resource_id = ?", (ta_id,)).fetchone()[0]
    print(f"Turismo Activo Count: {count}")
    
    if count > 0:
        # 2. Check content of one record
        row = cursor.execute("SELECT * FROM gva_companies WHERE gva_resource_id = ? LIMIT 1", (ta_id,)).fetchone()
        print(f"Sample Row: {row}")
        
        # 3. Check what modality/category they have
        mod = cursor.execute("SELECT modality, category FROM gva_companies WHERE gva_resource_id = ? LIMIT 1", (ta_id,)).fetchone()
        print(f"Modality/Category: {mod}")

    conn.close()

if __name__ == "__main__":
    check()
