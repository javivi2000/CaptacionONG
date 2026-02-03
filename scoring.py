import yaml
from api.models import init_db, GVACompany, CompanyScore, ImpactWeekly, CompanyNews
from sqlalchemy.orm import sessionmaker
import logging
import json
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scoring")

def calculate_scores():
    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    db_url = config["database"]["url"]
    cnae_weights = config["scoring"]["cnae_weights"]
    priority_munis = config["scoring"]["priority_municipalities"]
    gva_mapping = config["scoring"]["gva_sector_mapping"]
    
    engine = init_db(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    companies = session.query(GVACompany).all()
    logger.info(f"Analizando {len(companies)} empresas...")
    
    for comp in companies:
        score_social = 0.0
        score_territorial = 0.0
        tags = []
        
        # Evidencias Textuales
        d_sector = None
        d_territory = None
        d_financial = None
        
        # --- 1. Vertical/Sector (Tier 1) ---
        cnae_prefix = None
        if comp.financials and comp.financials.cnae:
            cnae_str = str(comp.financials.cnae).strip()
            if len(cnae_str) >= 2:
                cnae_prefix = cnae_str[:2]
        
        sector_found = False
        if cnae_prefix and cnae_prefix in cnae_weights:
            points = cnae_weights[cnae_prefix]
            score_social += points
            d_sector = f"Sector CNAE {cnae_prefix} (+{points}): Prioridad Alta para Cruz Roja."
            tags.append(d_sector)
            sector_found = True
        
        if not sector_found:
            mod = (comp.modality or comp.category or "").upper()
            # Patch inferred from ID
            if not mod:
                for key, rid in config["gva_api"]["resources"].items():
                    if comp.gva_resource_id == rid:
                        mod = key.replace("_", " ").upper()
                        break
            
            added = 0
            for key, val in gva_mapping.items():
                if key in mod:
                    added = val
                    break
            if added > 0:
                score_social += added
                d_sector = f"Sector GVA '{mod}' (+{added}): Actividad relevante."
                tags.append(d_sector)
            else:
                score_social += 0.5
                d_sector = "Sector General (+0.5): Sin prioridad específica."
                tags.append("Sector General (+0.5)")

        # --- 2. Arraigo Territorial (Tier 2) ---
        muni_upper = comp.municipality.upper() if comp.municipality else ""
        if any(m in muni_upper for m in priority_munis):
            score_territorial += 1.0
            d_territory = f"Municipio Prioritario '{muni_upper}' (+1.0): Sede en zona clave."
            tags.append(d_territory)
        else:
            d_territory = "Municipio Estándar (+0.0)"
        
        # --- BONUS: Capacidad Financiera ---
        if comp.financials and comp.financials.revenue:
            if comp.financials.revenue > 1000000:
                score_social += 1.0
                d_financial = f"Facturación >1M€ (+1.0): Alta capacidad de colaboración."
                tags.append(d_financial)

        # --- 3. Pilar de Actualidad (Tier 3) ---
        # Consultamos el impacto acumulado en las últimas semanas
        news_impact = session.query(ImpactWeekly).filter_by(company_id=comp.id).all()
        if news_impact:
            total_news_points = sum(n.score_total for n in news_impact)
            # Capamos el impacto de noticias a un máximo de 2 puntos (10-20% del total)
            actualidad_points = min(total_news_points * 0.1, 2.0)
            if actualidad_points > 0:
                score_social += actualidad_points
                tags.append(f"Actualidad Social (+{round(actualidad_points, 2)}): Basado en evidencias de prensa.")

        # --- 4. Cálculo de Vínculo CRE (0-10) ---
        cre_news = session.query(CompanyNews).filter_by(company_id=comp.id).all()
        avg_cre_link = 0.0
        if cre_news:
            avg_cre_link = sum(n.cre_score for n in cre_news) / len(cre_news)
            # Bonus adicional al score total si tiene buen vínculo (>5)
            if avg_cre_link > 5:
                score_social += 1.0
                tags.append(f"Vínculo CRE Notable (+1.0): Nota media {round(avg_cre_link, 1)}/10.")

        # Cálculo Final
        final_score = score_social + score_territorial
        
        # Guardar/Actualizar score
        score_entry = session.query(CompanyScore).filter_by(company_id=comp.id).first()
        if not score_entry:
            score_entry = CompanyScore(company_id=comp.id)
            session.add(score_entry)
        
        score_entry.score_cre_link = round(avg_cre_link, 2)
        score_entry.score_social = score_social
        score_entry.score_territorial = score_territorial
        score_entry.score_total = round(final_score, 2)
        score_entry.tags_explainer = json.dumps(tags)
        
        # Guardar Desgloses
        score_entry.breakdown_sector = d_sector
        score_entry.breakdown_territory = d_territory
        score_entry.breakdown_financial = d_financial
        
        score_entry.updated_at = datetime.datetime.now(datetime.timezone.utc)
        
    session.commit()
    logger.info("Scoring completado.")

if __name__ == "__main__":
    calculate_scores()
