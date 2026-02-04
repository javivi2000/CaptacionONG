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
import argparse

# Configuración de logs unificada a STDOUT para captura web
logging.basicConfig(
    level=logging.INFO, 
    format='%(message)s', # Formato más limpio para la consola web
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger("batch_enrichment")

def get_year_week(date_obj):
    """Devuelve el formato YYYY-WW para la base de datos"""
    return date_obj.strftime("%Y-W%W")

def run_enrichment(limit=20, municipality=None, name=None):
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

    # 2. Parámetros (Interactivo o Argumentos)
    muni_filter = municipality
    name_filter = name
    period_days = 7

    # Si NO vienen por parámetro, NO usamos input() para evitar bloqueos en la web
    if muni_filter is None and name_filter is None:
        logger.info("Iniciando modo automático sin filtros (se procesarán todas las empresas según límite)")
        # Podríamos poner un municipio por defecto si quisiéramos, pero el usuario pide "todas"
    else:
        logger.info(f"Filtros aplicados: Municipio='{muni_filter}', Nombre='{name_filter}'")

    limit_str = "TODAS" if limit == -1 else str(limit)
    logger.info(f"Configuración: Límite={limit_str}, Periodo={period_days} días")

    # 3. Inicializar componentes
    collector = NewsCollector()
    classifier = NewsClassifier()

    # 4. Obtener empresas
    # Usamos outerjoin para incluir empresas que aún no tienen registro en CompanyScore (recién sincronizadas)
    query = session.query(GVACompany).outerjoin(CompanyScore)
    
    if muni_filter:
        query = query.filter(GVACompany.municipality.ilike(f"%{muni_filter}%"))
    
    if name_filter:
        query = query.filter(GVACompany.name.ilike(f"%{name_filter}%"))
    
    # Si hay CompanyScore, ordenamos por él. Si no, las nuevas van al final o según ID.
    from sqlalchemy import desc
    query = query.order_by(desc(CompanyScore.score_total == None), CompanyScore.score_total.desc())
    
    if limit > 0:
        query = query.limit(limit)
    
    top_companies = query.all()
    
    if not top_companies:
        logger.warning(f"No se han encontrado empresas con los filtros aplicados.")
        return

    logger.info(f"Procesando {len(top_companies)} empresas.")

    new_news_count = 0
    total_to_process = len(top_companies)
    
    for index, company in enumerate(top_companies):
        # Emitir progreso para el orquestador
        print(f"[PROGRESS] {index+1}/{total_to_process}")
        sys.stdout.flush()
        
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
    parser = argparse.ArgumentParser(description="Enriquecimiento de Noticias")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--municipality", type=str, default=None)
    parser.add_argument("--name", type=str, default=None)
    
    args = parser.parse_args()
    
    run_enrichment(limit=args.limit, municipality=args.municipality, name=args.name)
