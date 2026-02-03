import yaml
from sqlalchemy.orm import sessionmaker
from api.models import init_db, CompanyNews, ImpactWeekly, CompanyScore

def clear_evidence_data():
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
        print("Borrando evidencias de noticias (CompanyNews)...")
        num_news = session.query(CompanyNews).delete()
        
        print("Borrando agregados semanales (ImpactWeekly)...")
        num_impact = session.query(ImpactWeekly).delete()

        print("Limpiando campo de evidencias antiguas en CompanyScore...")
        # Ponemos a None o string vacío el campo news_evidence de todas las puntuaciones
        session.query(CompanyScore).update({CompanyScore.news_evidence: None})
        
        session.commit()
        print(f"\nÉXITO: Se han borrado {num_news} noticias y {num_impact} registros de impacto.")
        print("El sistema está listo para una nueva carga limpia.")
    except Exception as e:
        session.rollback()
        print(f"Error durante la limpieza: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    confirm = input("¿Estás seguro de que quieres borrar TODAS las noticias y evidencias? (s/n): ").strip().lower()
    if confirm == 's':
        clear_evidence_data()
    else:
        print("Operación cancelada.")
