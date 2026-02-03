import sqlite3
import requests
import json
import logging
from bs4 import BeautifulSoup
import time
import urllib3

# Disable warnings for self-signed certs (common in small SMEs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("crawler")

KEYWORDS = [
    "responsabilidad social", " rsc ", " rse ", "sostenibilidad", "solidaridad", 
    "cruz roja", "donación", " ong ", "fundación", "igualdad", "medio ambiente",
    "ods", "agenda 2030", "voluntariado", "sin animo de lucro", "integración"
]

def crawl_company_sites(limit=50):
    conn = sqlite3.connect('data/companies.db')
    cursor = conn.cursor()
    
    # Select companies with Web but NO evidence yet (prioritize unscanned)
    # Also prioritize high potential scores (> 1.5) to not waste time on low-value targets
    query = """
        SELECT c.id, c.name, c.web, s.score_total 
        FROM gva_companies c 
        JOIN company_scores s ON c.id = s.company_id 
        WHERE c.web IS NOT NULL 
          AND c.web != '' 
          AND (s.news_evidence IS NULL OR s.news_evidence = '[]')
          AND s.score_total > 1.5
        ORDER BY s.score_total DESC
        LIMIT ?
    """
    
    rows = cursor.execute(query, (limit,)).fetchall()
    logger.info(f"Iniciando rastreo para {len(rows)} empresas prioritarias...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    updated_count = 0
    
    for row in rows:
        cid, name, url, score = row
        
        # Normalize URL
        if not url.startswith('http'):
            url = 'http://' + url
            
        logger.info(f"Rastreando: {name} ({url}) [Score: {score}]")
        
        matches = []
        try:
            # Timeout short to be fast
            resp = requests.get(url, headers=headers, timeout=10, verify=False)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                text = soup.get_text().lower()
                
                # Check keywords
                found_terms = []
                for kw in KEYWORDS:
                    if kw in text:
                        found_terms.append(kw.strip())
                
                if found_terms:
                    # Create evidence object
                    matches.append({
                        "title": f"Web Corporativa: Detectados términos {', '.join(found_terms)}",
                        "source": url,
                        "verified_at": time.strftime("%Y-%m-%d")
                    })
                    logger.info(f" -> ¡ÉXITO! Encontrado: {found_terms}")
                else:
                    logger.info(" -> Sin términos clave detectados.")
            else:
                logger.warning(f" -> Error HTTP {resp.status_code}")
                
        except Exception as e:
            logger.error(f" -> Error conectando: {str(e)}")
            
        # Update DB regardless (to mark as scanned, currently just updating if found or marking empty list)
        # In a real system we would have a 'last_scanned' column. Here we just update news_evidence.
        
        evidence_json = json.dumps(matches)
        
        # If matches found, we add a bonus!
        bonus_sql = ""
        if matches:
            bonus_sql = ", score_social = score_social + 0.5, score_total = score_total + 0.5"
            
        cursor.execute(f"""
            UPDATE company_scores 
            SET news_evidence = ? {bonus_sql}
            WHERE company_id = ?
        """, (evidence_json, cid))
        
        conn.commit()
        if matches:
            updated_count += 1
            
        # Be nice to servers
        time.sleep(1)

    conn.close()
    logger.info(f"Proceso finalizado. {updated_count} empresas nuevas identificadas como Socialmente Responsables.")

if __name__ == "__main__":
    crawl_company_sites(20) # Default to 20 for this demo run
