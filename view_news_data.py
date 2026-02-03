import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect('data/companies.db')
    # Verificar columnas
    cols_df = pd.read_sql_query("PRAGMA table_info(company_news)", conn)
    print("Columnas encontradas:", cols_df['name'].tolist())
    
    # Obtener las 5 primeras noticias con el nombre de la empresa
    query = """
    SELECT c.name, n.category, n.cre_category, n.cre_score, n.title, n.date
    FROM company_news n
    JOIN gva_companies c ON n.company_id = c.id
    ORDER BY n.id DESC
    LIMIT 5
    """
    df = pd.read_sql_query(query, conn)
    print("\nRESULTADOS:")
    print(df.to_markdown())
    conn.close()
except Exception as e:
    print(f"Error: {e}")
