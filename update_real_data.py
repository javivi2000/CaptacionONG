import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("update_real_data")

def update_db_with_real_news():
    conn = sqlite3.connect('data/companies.db')
    cursor = conn.cursor()
    
    # 1. ALICANTE BOAT TOURS / CATAMARAN
    # Buscamos por nombre aproximado
    # Nota: Si no existe exacto, buscaremos 'ALICANTE CATAMARAN' o similar, o usaremos el ID de 'Boat Tours' si lo tenemos identificado.
    # En el paso anterior vimos 'ALICANTE BOAT TOURS' con Score 3.0.
    
    news_boat_tours = [
        {"title": "Colaboración con Fundación ECOMAR para limpieza de océanos", "source": "Alicante Catamaran Web"},
        {"title": "Viajes educativos y concienciación ambiental para niños", "source": "Programa ECOMAR"}
    ]
    
    cursor.execute("""
        UPDATE company_scores 
        SET news_evidence = ? 
        WHERE company_id IN (SELECT id FROM gva_companies WHERE name LIKE '%BOAT TOURS%' OR name LIKE '%CATAMARAN%')
    """, (json.dumps(news_boat_tours),))
    
    # 2. BALEARIA (Si existe en la BBDD)
    news_balearia = [
        {"title": "Fundación Baleària: Proyectos de Cohesión Social y Cultura", "source": "Web Corporativa"},
        {"title": "Programa 'Baleària Solidaria' para igualdad de oportunidades", "source": "Memoria RSC"},
        {"title": "Compromiso EcoBaleària: Emisiones cero para 2050", "source": "Prensa Sectorial"}
    ]
    cursor.execute("""
        UPDATE company_scores 
        SET news_evidence = ?, score_social = score_social + 0.5 
        WHERE company_id IN (SELECT id FROM gva_companies WHERE name LIKE '%BALEARIA%')
    """, (json.dumps(news_balearia),))
    # Note: Added +0.5 score boost for verified Foundation status
    
    
    # 3. GRUPO IDEX (Si existe)
    news_idex = [
        {"title": "Pioneros en 'Responsabilidad Social Inherente' en Alicante", "source": "Alicante Plaza"},
        {"title": "Consultora líder en comunicación social y tercer sector", "source": "Web Corporativa"}
    ]
    cursor.execute("""
        UPDATE company_scores 
        SET news_evidence = ? 
        WHERE company_id IN (SELECT id FROM gva_companies WHERE name LIKE '%IDEX%')
    """, (json.dumps(news_idex),))

    conn.commit()
    
    # Verify updates
    print("--- VERIFICACIÓN DE ACTUALIZACIONES ---")
    rows = cursor.execute("""
        SELECT c.name, s.news_evidence 
        FROM gva_companies c 
        JOIN company_scores s ON c.id=s.company_id 
        WHERE s.news_evidence IS NOT NULL AND s.news_evidence NOT LIKE '%Simulado%'
    """).fetchall()
    
    for r in rows:
        print(f"EMPRESA: {r[0]}")
        evidence = json.loads(r[1])
        for e in evidence:
            print(f" - {e['title']} ({e['source']})")
        print("---")
        
    conn.close()

if __name__ == "__main__":
    update_db_with_real_news()
