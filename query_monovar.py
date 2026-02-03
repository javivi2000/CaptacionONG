import sqlite3
import json

def show_monovar_top():
    db_path = 'data/companies.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Debug: Check municipality names first
    print("Buscando municipios similares a 'MON'...")
    munis = cursor.execute("SELECT DISTINCT municipality, count(*) FROM gva_companies WHERE municipality LIKE '%MON%' GROUP BY municipality").fetchall()
    for m in munis:
        print(f" - {m[0]} ({m[1]} empresas)")

    query = """
    SELECT c.name, s.score_total, s.tags_explainer 
    FROM gva_companies c 
    JOIN company_scores s ON c.id = s.company_id 
    WHERE c.municipality LIKE '%MONòVER%' 
       OR c.municipality LIKE '%MONÓVAR%'
       OR c.municipality LIKE '%MONOVER%'
    ORDER BY s.score_total DESC 
    LIMIT 20
    """
    
    results = cursor.execute(query).fetchall()
    
    print(f"--- TOP EMPRESAS EN MONÓVAR ({len(results)} encontradas) ---\n")
    
    for row in results:
        name = row[0]
        score = row[1]
        tags = row[2]
        print(f"Empresa: {name}")
        print(f"Puntuación: {score}")
        print(f"Argumento: {tags}")
        print("-" * 40)

    conn.close()

if __name__ == "__main__":
    show_monovar_top()
