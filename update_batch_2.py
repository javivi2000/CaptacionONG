import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)

def update_batch_2():
    conn = sqlite3.connect('data/companies.db')
    cursor = conn.cursor()
    
    # 1. TUK TOUR ALICANTE
    news_tuk = [
        {"title": "Vehículos 100% Eléctricos: Turismo Cero Emisiones", "source": "Web Corporativa"},
        {"title": "Turismo Accesible: Adaptado a zonas peatonales", "source": "WalkTuk Info"}
    ]
    cursor.execute("""
        UPDATE company_scores 
        SET news_evidence = ? 
        WHERE company_id IN (SELECT id FROM gva_companies WHERE name LIKE '%TUK TOUR%')
    """, (json.dumps(news_tuk),))

    # 2. SEGWAY ALICANTE
    news_segway = [
        {"title": "Movilidad Sostenible y Ecológica (Cero Emisiones)", "source": "Portal Turismo"}
    ]
    cursor.execute("""
        UPDATE company_scores 
        SET news_evidence = ? 
        WHERE company_id IN (SELECT id FROM gva_companies WHERE name LIKE '%SEGWAY%')
    """, (json.dumps(news_segway),))
    
    # 3. MEGAZONA / PAINTBALL INDOOR
    news_mega = [
        {"title": "Eventos para Colegios y Asociaciones Juveniles", "source": "Web Oficial"},
        {"title": "Ocio Inclusivo: Laser Tag apto para todos", "source": "Web Oficial"}
    ]
    cursor.execute("""
        UPDATE company_scores 
        SET news_evidence = ? 
        WHERE company_id IN (SELECT id FROM gva_companies WHERE name LIKE '%PAINTBALL INDOOR%' OR name LIKE '%MEGAZONA%')
    """, (json.dumps(news_mega),))

    # 4. PALASIET / LA MAR DE AIGUA (Sin evidencia, marcamos null para que el usuario sepa que se buscó)
    cursor.execute("""
        UPDATE company_scores 
        SET news_evidence = '[]', breakdown_sector = breakdown_sector || ' (Sin hallazgos web recientes)'
        WHERE company_id IN (SELECT id FROM gva_companies WHERE name LIKE '%PALASIET%' OR name LIKE '%LA MAR DE AIGUA%')
    """)

    conn.commit()
    conn.close()
    print("Batch 2 Actualizado.")

if __name__ == "__main__":
    update_batch_2()
