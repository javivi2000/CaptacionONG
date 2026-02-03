import requests
from bs4 import BeautifulSoup
import logging
from sqlalchemy.orm import sessionmaker
from api.models import init_db, GVACompany, ScrapedCompany
import yaml
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EconomistaScraper:
    def __init__(self):
        self.base_url = "https://ranking-empresas.eleconomista.es/ranking_provincias.php?id_provincia=3"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def scrape_top_ranking(self, limit=100):
        """Scrapea el ranking de empresas de Alicante para obtener ingresos."""
        companies = []
        # El Economista pagina de 50 en 50
        for page in range(0, limit, 50):
            url = f"{self.base_url}&posicion={page}"
            logger.info(f"Scrapeando página: {url}")
            
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                table = soup.find('table', {'id': 'tablaRanking'})
                if not table:
                    logger.warning("No se encontró la tabla de ranking.")
                    break
                    
                rows = table.find_all('tr')[1:] # Saltar cabecera
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        name = cols[1].text.strip()
                        revenue_str = cols[4].text.strip().replace('.', '').replace(',', '.')
                        try:
                            revenue = float(revenue_str)
                        except:
                            revenue = 0.0
                            
                        companies.append({
                            "name": name,
                            "ranking": int(cols[0].text.strip().replace('.', '')),
                            "revenue": revenue,
                            "url": cols[1].find('a')['href'] if cols[1].find('a') else None
                        })
                
                time.sleep(1) # Respeto al servidor
            except Exception as e:
                logger.error(f"Error en scrapeo: {e}")
                break
                
        return companies

def run_cruce():
    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    engine = init_db(config["database"]["url"])
    Session = sessionmaker(bind=engine)
    session = Session()
    
    scraper = EconomistaScraper()
    logger.info("Iniciando captura de datos financieros (El Economista)...")
    scraped_data = scraper.scrape_top_ranking(limit=200)
    
    count = 0
    for item in scraped_data:
        # Intento de cruce por nombre (Búsqueda aproximada)
        name_clean = item["name"].upper()
        # Buscamos en gva_companies
        gva_comp = session.query(GVACompany).filter(GVACompany.name.contains(name_clean)).first()
        
        if gva_comp:
            # Si ya tiene financieros, los actualizamos
            financial = session.query(ScrapedCompany).filter_by(gva_company_id=gva_comp.id).first()
            if not financial:
                financial = ScrapedCompany(gva_company_id=gva_comp.id)
                session.add(financial)
            
            financial.revenue = item["revenue"]
            financial.ranking_position = item["ranking"]
            financial.url_source = item["url"]
            count += 1
            
    session.commit()
    logger.info(f"Cruce finalizado. {count} empresas enriquecidas con datos financieros.")

if __name__ == "__main__":
    run_cruce()
