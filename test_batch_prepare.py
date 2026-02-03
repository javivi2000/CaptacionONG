import yaml
from sqlalchemy.orm import sessionmaker
from api.models import init_db, GVACompany, CompanyScore
from run_weekly_enrichment import run_enrichment
import os

def prepare_test_company():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    engine = init_db(config["database"]["url"])
    Session = sessionmaker(bind=engine)
    session = Session()

    # Añadir empresa de prueba que garantice noticias
    test_name = "Cruz Roja Española"
    exists = session.query(GVACompany).filter_by(name=test_name).first()
    if not exists:
        c = GVACompany(name=test_name, municipality="Alicante")
        session.add(c)
        session.commit()
        session.add(CompanyScore(company_id=c.id, score_total=10.0))
        session.commit()
        print(f"Empresa de prueba '{test_name}' añadida.")
    else:
        print(f"La empresa '{test_name}' ya existe en la BBDD.")

if __name__ == "__main__":
    prepare_test_company()
    print("\nLanzando proceso de enriquecimiento (Simulando opción 3 - 180 días)...")
    # Nota: El script original es interactivo. Para la prueba, simplemente llamamos a la lógica.
    # Pero como queremos probar run_weekly_enrichment.py tal cual, 
    # usaremos el pipe en el siguiente paso de la consola.
