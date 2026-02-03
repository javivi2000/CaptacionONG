import yaml
from sqlalchemy.orm import sessionmaker
from api.models import init_db, GVACompany, CompanyScore, CompanyNews, ImpactWeekly

def remove_cruz_roja():
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        db_url = config["database"]["url"]
    except Exception as e:
        print(f"Error cargando config.yaml: {e}")
        return

    engine = init_db(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        test_name = "Cruz Roja Española"
        print(f"Buscando '{test_name}'...")
        company = session.query(GVACompany).filter(GVACompany.name.ilike(f"%{test_name}%")).first()
        
        if company:
            print(f"Eliminando registros asociados a ID {company.id} ({company.name})...")
            
            # Borrar dependencias manualmente por si acaso el Cascade no está configurado en todos los entornos
            session.query(CompanyNews).filter_by(company_id=company.id).delete()
            session.query(ImpactWeekly).filter_by(company_id=company.id).delete()
            session.query(CompanyScore).filter_by(company_id=company.id).delete()
            
            session.delete(company)
            session.commit()
            print(f"ÉXITO: '{test_name}' ha sido eliminada por completo.")
        else:
            print(f"No se ha encontrado ninguna empresa con el nombre '{test_name}'.")
            
    except Exception as e:
        session.rollback()
        print(f"Error durante la eliminación: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    remove_cruz_roja()
