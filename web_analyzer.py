import sqlite3
import requests
import json
import logging
from bs4 import BeautifulSoup
import time
import urllib3
import yaml

# Disable warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import argparse
import sys

# Configuración de logs unificada a STDOUT para captura web
logging.basicConfig(
    level=logging.INFO, 
    format='%(message)s', 
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger("web_analyzer")

# Grupos de Keywords definidos en el plan
KEYWORD_GROUPS = {
    "RSE": ["responsabilidad social", "rsc", "rse", "impacto social", "ética empresarial", "inclusión", "diversidad", "igualdad", "transparencia"],
    "Salud": ["prevención", "promoción salud", "hábitos saludables", "donación sangre", "bienestar laboral"],
    "Inclusión": ["colectivos vulnerables", "pobreza", "exclusión", "personas mayores", "soledad", "discapacidad"],
    "Empleo": ["inserción laboral", "formación", "empleabilidad", "talento diverso", "becas"],
    "Medio Ambiente": ["sostenibilidad", "huella carbono", "reciclaje", "eficiencia energética", "ecología"],
    "Juventud": ["apoyo escolar", "éxito escolar", "ocio saludable", "infancia"]
}

def analyze_all_webs(limit=50, municipality=None, name=None):
    # Load config for DB path
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    db_path = config["database"]["url"].replace("sqlite:///", "")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Construir consulta dinámica
    query = """
        SELECT c.id, c.name, c.web, s.score_total 
        FROM gva_companies c 
        JOIN company_scores s ON c.id = s.company_id 
        WHERE c.web IS NOT NULL AND c.web != ''
    """
    params = []
    
    if municipality:
        query += " AND c.municipality LIKE ?"
        params.append(f"%{municipality}%")
        
    if name:
        query += " AND c.name LIKE ?"
        params.append(f"%{name}%")
        
    query += " ORDER BY s.score_total DESC LIMIT ?"
    params.append(limit)
    
    rows = cursor.execute(query, tuple(params)).fetchall()
    logger.info(f"Filtros: Municipio={municipality}, Empresa={name}")
    logger.info(f"Iniciando análisis de {len(rows)} sitios web corporativos...")
    
    total_to_process = len(rows)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    analyzed_count = 0
    matches_count = 0
    
    for index, row in enumerate(rows):
        cid, name, url, score = row
        
        # Emitir progreso para el orquestador
        print(f"[PROGRESS] {index+1}/{total_to_process}")
        sys.stdout.flush()
        
        if not url.startswith('http'):
            url = 'https://' + url # Preferimos HTTPS
            
        logger.info(f"Analizando: {name} ({url})")
        
        found_keywords = {}
        try:
            # Intentar conexión
            resp = requests.get(url, headers=headers, timeout=12, verify=False)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Eliminar scripts y estilos para limpiar texto
                for script in soup(["script", "style"]):
                    script.extract()
                    
                text = soup.get_text().lower()
                
                # Buscar en cada grupo
                for group, keywords in KEYWORD_GROUPS.items():
                    for kw in keywords:
                        if kw in text:
                            if group not in found_keywords:
                                found_keywords[group] = []
                            found_keywords[group].append(kw)
                
                if found_keywords:
                    logger.info(f" -> Términos detectados: {list(found_keywords.keys())}")
                    matches_count += 1
                else:
                    logger.info(" -> No se detectaron términos específicos de RSE.")
            else:
                logger.warning(f" -> Error HTTP {resp.status_code}")
                
        except Exception as e:
            logger.error(f" -> Error analizando {url}: {str(e)}")
            
        # Guardar en base de datos (incluso si está vacío para evitar re-análisis constante)
        kw_json = json.dumps(found_keywords)
        
        # Opcional: Dar un pequeño bonus si se detectan muchos términos
        bonus = 0.0
        if found_keywords:
            # Bonus de 0.2 si hay términos, hasta un máximo si hay muchos grupos
            bonus = min(0.1 * len(found_keywords), 0.5)
            
        cursor.execute("""
            UPDATE company_scores 
            SET web_keywords = ?, 
                score_total = score_total + ?,
                updated_at = datetime('now')
            WHERE company_id = ?
        """, (kw_json, bonus, cid))
        
        conn.commit()
        analyzed_count += 1
        time.sleep(1) # Be nice
        
    conn.close()
    logger.info(f"Análisis finalizado. {analyzed_count} webs procesadas, {matches_count} con hallazgos.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Análisis de Webs RSE")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--municipality", type=str, default=None)
    parser.add_argument("--name", type=str, default=None)
    
    args = parser.parse_args()
    analyze_all_webs(limit=args.limit, municipality=args.municipality, name=args.name)
