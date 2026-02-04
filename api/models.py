from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime

Base = declarative_base()

class GVACompany(Base):
    """Empresas obtenidas directamente de la API de la GVA"""
    __tablename__ = 'gva_companies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    gva_resource_id = Column(String, index=True)
    cif = Column(String, index=True)
    name = Column(String, nullable=False, index=True)
    address = Column(String)
    municipality = Column(String, index=True)
    postal_code = Column(String)
    category = Column(String)
    modality = Column(String)
    phone = Column(String)
    email = Column(String)
    web = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    scores = relationship("CompanyScore", back_populates="company", cascade="all, delete-orphan")
    financials = relationship("ScrapedCompany", back_populates="gva_company", uselist=False)

class ScrapedCompany(Base):
    """Datos financieros y de ranking (ej. El Economista)"""
    __tablename__ = 'scraped_companies'
    
    scraped_id = Column(Integer, primary_key=True)
    gva_company_id = Column(Integer, ForeignKey('gva_companies.id'))
    
    revenue = Column(Float) # Ingresos anuales
    ranking_position = Column(Integer)
    cnae = Column(String)
    sector_text = Column(Text)
    url_source = Column(String)
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    gva_company = relationship("GVACompany", back_populates="financials")

class CompanyScore(Base):
    """Puntuaciones y análisis social/territorial"""
    __tablename__ = 'company_scores'
    
    score_id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('gva_companies.id'))
    
    score_social = Column(Float, default=0.0)
    score_territorial = Column(Float, default=0.0)
    score_total = Column(Float, default=0.0)
    
    # Campos de Evidencia Cualitativa
    tags_explainer = Column(Text) # JSON general (Legacy/Resumen)
    breakdown_sector = Column(Text) # Justificación del Sector
    breakdown_territory = Column(Text) # Justificación Territorial
    breakdown_financial = Column(Text) # Justificación Económica
    news_evidence = Column(Text) # JSON con titulares de noticias/RSC
    web_keywords = Column(Text)  # Nuevo: JSON con términos de RSE detectados en su web
    
    # Nuevo: Vínculo Social CRE
    score_cre_link = Column(Float, default=0.0) # Nota promedio 0-10
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    company = relationship("GVACompany", back_populates="scores")
    
class CompanyNews(Base):
    """Evidencias de noticias encontradas para una empresa"""
    __tablename__ = 'company_news'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('gva_companies.id'))
    
    date = Column(DateTime, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source = Column(String)
    category = Column(String) # Empleo, Inclusión, Medioambiente, etc.
    cre_category = Column(String) # Alianza Humanitaria, Salud, etc.
    cre_score = Column(Float, default=0.0) # Nota 0-10 específica CRE
    impact_score = Column(Float, default=1.0)
    summary = Column(Text)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    company = relationship("GVACompany")

class ImpactWeekly(Base):
    """Agregados semanales de impacto por empresa"""
    __tablename__ = 'impact_weekly'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey('gva_companies.id'))
    
    year_week = Column(String, index=True) # Formato YYYY-WW
    top_category = Column(String)
    score_total = Column(Float, default=0.0)
    news_count = Column(Integer, default=0)
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    company = relationship("GVACompany")

def init_db(db_url="sqlite:///./data/companies.db"):
    import os
    os.makedirs(os.path.dirname(db_url.replace("sqlite:///", "")), exist_ok=True)
    
    engine = create_engine(db_url)
    
    # Enable WAL mode for SQLite
    if "sqlite" in db_url:
        from sqlalchemy import event
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
            
    Base.metadata.create_all(engine)
    return engine
