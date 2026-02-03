import sqlite3
import pandas as pd
import os

def export_to_csv():
    db_path = 'data/companies.db'
    output_path = 'directorio_alicante_completo.csv'
    
    if not os.path.exists(db_path):
        print("Base de datos no encontrada.")
        return
        
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT 
        c.name as Nombre,
        c.municipality as Municipio,
        c.category as Categoria,
        c.modality as Modalidad,
        c.email as Email,
        c.phone as Telefono,
        c.web as Web,
        s.score_total as Score_Responsabilidad,
        s.breakdown_sector as Motivo_Sector,
        s.breakdown_territory as Motivo_Arraigo,
        s.breakdown_financial as Motivo_Capacidad,
        s.news_evidence as Evidencia_Noticias,
        s.tags_explainer as Analisis_Raw
    FROM gva_companies c
    JOIN company_scores s ON c.id = s.company_id
    ORDER BY s.score_total DESC
    """
    
    print("Exportando 31.479 registros a CSV...")
    df = pd.read_sql_query(query, conn)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    conn.close()
    print(f"¡Éxito! Archivo guardado como: {output_path}")

if __name__ == "__main__":
    export_to_csv()
