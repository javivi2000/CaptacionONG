import yaml
from gva_client import GVAClient
from api.models import init_db, GVACompany
from sqlalchemy.orm import sessionmaker
from scoring import calculate_scores
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_gva")

def sync():
    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    db_url = config["database"]["url"]
    engine = init_db(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    client = GVAClient(config["gva_api"]["base_url"])
    
    resources = config["gva_api"]["resources"]
    
    total_found = 0
    for key, resource_id in resources.items():
        logger.info(f"Sincronizando recurso: {key} ({resource_id})")
        
        limit_target = 30000 if key == "viviendas_2025" else 3000
        offset = 0
        batch_size = 100
        resource_count = 0
        
        while resource_count < limit_target:
            result = client.fetch_resource(resource_id, q="ALACANT", limit=batch_size, offset=offset)
            if not result or not result.get("records"):
                break
                
            records = result["records"]
            for rec in records:
                m_rec = {k.lower().replace(".", ""): v for k, v in rec.items()}
                
                # Filtro de Alicante
                prov = str(m_rec.get("provincia") or "").upper()
                muni = str(m_rec.get("municipio") or "").upper()
                if "ALICANTE" not in prov and "ALACANT" not in prov and "ALICANTE" not in muni and "ALACANT" not in muni:
                    continue

                name = m_rec.get("nombre") or m_rec.get("razon_social")
                if not name:
                    sign = m_rec.get("signatura")
                    if sign: name = f"Empresa {sign}"
                    else: continue
                
                municipality = m_rec.get("municipio", "ALICANTE")
                cif = m_rec.get("cif") or m_rec.get("nif") or m_rec.get("signatura")
                
                # Evitar duplicados (Deduplicación rápida en memoria para la tanda actual si es necesario, 
                # pero confiamos en DB index para grandes volúmenes)
                existing = session.query(GVACompany).filter_by(name=name, municipality=municipality).first()
                
                def safe_float(val):
                    if not val or str(val).lower() == 'none' or val == '': return None
                    try: return float(val)
                    except: return None

                data = {
                    "gva_resource_id": resource_id,
                    "cif": cif,
                    "name": name,
                    "address": m_rec.get("direccion") or m_rec.get("domicilio"),
                    "municipality": municipality,
                    "postal_code": m_rec.get("cp") or m_rec.get("codigo_postal") or m_rec.get("cod_postal"),
                    "category": m_rec.get("modalidad") or m_rec.get("tipo") or m_rec.get("categoria"),
                    "modality": m_rec.get("modalidad") or m_rec.get("tipo"),
                    "phone": m_rec.get("telefono"),
                    "email": m_rec.get("email") or m_rec.get("correo_electronico") or m_rec.get("correo"),
                    "web": m_rec.get("web") or m_rec.get("url"),
                    "latitude": safe_float(m_rec.get("latitud")),
                    "longitude": safe_float(m_rec.get("longitud"))
                }
                
                if existing:
                    for k, v in data.items():
                        setattr(existing, k, v)
                else:
                    session.add(GVACompany(**data))
                
                resource_count += 1
                if resource_count % 500 == 0:
                    session.commit()
                    logger.info(f"[{key}] Procesados {resource_count} registros...")
            
            if len(records) < batch_size:
                break
            offset += batch_size
            
        session.commit()
        total_found += resource_count
        logger.info(f"Finalizado recurso {key}. Total registros: {resource_count}")

    logger.info(f"Sincronización global finalizada. Total: {total_found}")

if __name__ == "__main__":
    sync()
