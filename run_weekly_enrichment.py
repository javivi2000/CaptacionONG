import yaml
import logging
import json
from sqlalchemy.orm import sessionmaker
from api.models import init_db, GVACompany, CompanyScore, CompanyNews, ImpactWeekly
from news_collector import NewsCollector
from news_classifier import NewsClassifier
from datetime import datetime
from scoring import calculate_scores
import sys

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("batch_enrichment")

def get_year_week(date_obj):
    """Devuelve el formato YYYY-WW para la base de datos"""
    return date_obj.strftime("%Y-W%W")

def run_enrichment(limit=20):
    # 1. Cargar configuración y conectar a BBDD
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        db_url = config["database"]["url"]
    except Exception as e:
        logger.error(f"Error cargando config.yaml: {e}")
        return

    engine = init_db(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 2. Solicitar parámetros al usuario (interactivo)
    print("\n--- Sistema de Enriquecimiento de Noticias (Cruz Roja) ---")
    
    muni_filter = input("Municipio para buscar (EJ: Monovar, Alicante, Elche...): ").strip()
    if not muni_filter:
        print("[AVISO] No has introducido municipio. Se usará 'Alicante' por defecto.")
        muni_filter = "Alicante"

    try:
        limit_input = input(f"¿Cuántas empresas del Top de '{muni_filter}' procesar? (Defecto {limit}): ").strip()
        if limit_input:
            limit = int(limit_input)
    except:
        pass

    print("\nSeleccione el periodo de búsqueda histórica:")
    print("1. Semanal (7 días)")
    print("2. Mensual (30 días)")
    print("3. Semestral (180 días) - Recomendado para carga inicial")
    
    choice = input("Opción (1/2/3): ").strip()
    
    period_days = 7
    if choice == '2':
        period_days = 30
    elif choice == '3':
        period_days = 180
    
    logger.info(f"Configuración: Localidad='{muni_filter}', Top={limit}, Periodo={period_days} días")

    # 3. Inicializar componentes
    collector = NewsCollector()
    classifier = NewsClassifier()

    # 4. Obtener empresas
    # Filtramos estrictamente por el municipio introducido
    query = session.query(GVACompany).join(CompanyScore).filter(GVACompany.municipality.ilike(f"%{muni_filter}%"))
    
    top_companies = query.order_by(CompanyScore.score_total.desc()).limit(limit).all()
    
    if not top_companies:
        logger.warning(f"No se han encontrado empresas en '{muni_filter}'. ¿Está bien escrito?")
        return

    logger.info(f"Procesando {len(top_companies)} empresas en {muni_filter}.")

    new_news_count = 0
    for company in top_companies:
        logger.info(f">>> Analizando: {company.name} ({company.municipality})")
        
        # Buscar noticias
        found_news = collector.search_company_news(company.name, company.municipality or "Alicante", period_days=period_days)
        
        if not found_news:
            logger.info(f"    No se han encontrado noticias recientes.")
            continue

        for n in found_news:
            # Comprobar si ya existe la noticia para esta empresa (por URL)
            exists = session.query(CompanyNews).filter_by(company_id=company.id, url=n['link']).first()
            if exists:
                continue

            # Clasificar impacto
            # Para velocidad, usamos el título primero. Opcionalmente newspaper3k para el texto completo.
            categories, impact_conf = classifier.classify(n['title'])
            
            # Análisis de impacto y vínculo CRE
            cre_cat, cre_note = classifier.calculate_cre_score(n['title'], n.get('summary', ''))

            # Guardar noticia
            new_entry = CompanyNews(
                company_id=company.id,
                date=n['published'],
                title=n['title'],
                url=n['link'],
                source=n['source'],
                category=categories[0],
                cre_category=cre_cat,  # Categoría del vínculo
                cre_score=cre_note,    # Nota del vínculo (0-10)
                impact_score=impact_conf,
                summary=f"Detectado automáticamente: {', '.join(categories)}"
            )
            session.add(new_entry)
            
            # Actualizar o Crear Impacto Semanal
            yw = get_year_week(n['published'])
            impact_record = session.query(ImpactWeekly).filter_by(company_id=company.id, year_week=yw).first()
            
            if not impact_record:
                impact_record = ImpactWeekly(
                    company_id=company.id,
                    year_week=yw,
                    top_category=categories[0],
                    score_total=0.0,
                    news_count=0
                )
                session.add(impact_record)
            
            impact_record.news_count += 1
            impact_record.score_total += impact_conf
            # Actualizamos categoría predominante si hay muchos
            if impact_record.news_count > 1:
                # Lógica simple: la última encontrada manda o la más frecuente. 
                # Aquí simplemente tomamos la de la noticia actual por ahora.
                impact_record.top_category = categories[0]

            new_news_count += 1
            logger.info(f"    [NUEVA] {n['title'][:50]}... -> {categories[0]}")

        # Guardar progresos por empresa
        session.commit()

    logger.info(f"PROCESO FINALIZADO. Se han insertado {new_news_count} nuevas evidencias de noticias.")
    
    print("\n[INFO] Actualizando Ranking General de empresas...")
    calculate_scores()
    print("[ÉXITO] Ranking actualizado con el nuevo impacto de noticias.")

if __name__ == "__main__":
    # Podemos pasar el límite por argumento o usar 20 por defecto
    limit = 20
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    
    run_enrichment(limit)
