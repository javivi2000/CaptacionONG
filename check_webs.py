import sqlite3

def check_webs():
    conn = sqlite3.connect('data/companies.db')
    cursor = conn.cursor()
    
    count = cursor.execute("SELECT count(*) FROM gva_companies WHERE web IS NOT NULL AND web != ''").fetchone()[0]
    print(f"Total Empresas con Web: {count}")
    
    rows = cursor.execute("SELECT name, web FROM gva_companies WHERE web IS NOT NULL AND web != '' LIMIT 5").fetchall()
    print("Ejemplos:")
    for r in rows:
        print(f" - {r[0]}: {r[1]}")
        
    conn.close()

if __name__ == "__main__":
    check_webs()
