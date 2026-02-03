import sqlite3

try:
    conn = sqlite3.connect('data/companies.db')
    cursor = conn.cursor()
    query = """
    SELECT c.name, n.cre_category, n.cre_score, n.title, n.source
    FROM company_news n
    JOIN gva_companies c ON n.company_id = c.id
    WHERE n.cre_score > 0
    ORDER BY n.cre_score DESC, n.id DESC
    LIMIT 5
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print("\nVALORES DE EVIDENCIAS EN BBDD (TOP VÍNCULO CRE):")
    print("-" * 100)
    print(f"{'EMPRESA':<20} | {'CATEGORÍA CRE':<20} | {'NOTA':<6} | {'TÍTULO'}")
    print("-" * 100)
    for r in rows:
        entidad = r[0][:20]
        cat = r[1] or "General"
        nota = f"{r[2]}/10"
        titulo = r[3][:45] + "..."
        print(f"{entidad:<20} | {cat:<20} | {nota:<6} | {titulo}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
