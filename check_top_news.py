from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.models import CompanyNews, GVACompany

db_url = "sqlite:///./data/companies.db"
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

news = session.query(CompanyNews, GVACompany).join(GVACompany).order_by(CompanyNews.created_at.desc()).limit(5).all()

print("| Empresa | Categoría | Vínculo CRE | Nota CRE | Título |")
print("| :--- | :--- | :--- | :--- | :--- |")
for n, c in news:
    print(f"| {c.name[:20]} | {n.category} | {n.cre_category} | {n.cre_score}/10 | {n.title[:50]}... |")
