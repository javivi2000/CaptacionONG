from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from api.models import init_db, GVACompany, CompanyScore, CompanyNews
import yaml
import json

app = FastAPI(title="Captación Alicante API")

# Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
db_url = config["database"]["url"]
engine = init_db(db_url)

def get_db():
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir frontend estático
import os
os.makedirs("static", exist_ok=True)
from fastapi.responses import RedirectResponse

@app.get("/")
def root_redirect():
    return RedirectResponse(url="/dashboard/")

app.mount("/dashboard", StaticFiles(directory="static", html=True), name="static")

@app.get("/companies/search")
def search_companies(
    municipality: Optional[str] = None, 
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    query = db.query(GVACompany, CompanyScore).join(CompanyScore)
    
    if municipality:
        query = query.filter(GVACompany.municipality.ilike(f"%{municipality}%"))
    
    results = query.order_by(CompanyScore.score_total.desc()).limit(limit).all()
    
    output = []
    for comp, score in results:
        # Obtener noticias de la nueva tabla
        real_news = db.query(CompanyNews).filter_by(company_id=comp.id).order_by(CompanyNews.date.desc()).limit(5).all()
        news_list = []
        for n in real_news:
            news_list.append({
                "title": n.title,
                "source": n.source,
                "url": n.url,
                "category": n.category,         # Categoría general (Sostenibilidad, etc)
                "impact_score": n.impact_score, # Importancia 1-5
                "cre_category": n.cre_category, # Categoría del vínculo CRE
                "cre_score": n.cre_score        # Nota 0-10 de la noticia CRE
            })
            
        # Intentar obtener el desglose numérico estructurado
        try:
            full_breakdown = json.loads(score.news_evidence)
            # Verificar que sea nuestro nuevo formato de desglose y no el fallback de noticias legacy
            if not isinstance(full_breakdown, dict) or "sector" not in full_breakdown:
                full_breakdown = None
        except:
            full_breakdown = None

        output.append({
            "id": comp.id,
            "name": comp.name,
            "municipality": comp.municipality,
            "category": comp.category or comp.modality or "General",
            "contact": {
                "email": comp.email,
                "phone": comp.phone,
                "web": comp.web
            },
            "score_total": round(score.score_total, 2),
            "score_cre": round(score.score_cre_link or 0.0, 2),
            "breakdown": {
                "sector": score.breakdown_sector,
                "territory": score.breakdown_territory,
                "financial": score.breakdown_financial,
                "news": full_breakdown["news"] if full_breakdown else 0.0,
                "cre_bonus": full_breakdown["cre_bonus"] if full_breakdown else 0.0,
                # Enviamos también los valores numéricos para facilitar el renderizado
                "num_sector": full_breakdown["sector"] if full_breakdown else 0.0,
                "num_territory": full_breakdown["territory"] if full_breakdown else 0.0,
                "num_financial": full_breakdown["financial"] if full_breakdown else 0.0
            },
            "evidence": {
                "news": news_list
            },
            "analysis_summary": json.loads(score.tags_explainer or "[]")
        })
    return output

@app.get("/companies/ranking")
def get_ranking(limit: int = 100, db: Session = Depends(get_db)):
    # Usar el mismo buscador para coherencia
    return search_companies(None, limit, db)

@app.get("/health")
def health():
    return {"status": "online", "source": "GVA Open Data", "region": "Alicante"}

@app.get("/companies/{company_id}/pitch")
def generate_pitch(company_id: int, db: Session = Depends(get_db)):
    from googlesearch import search
    import requests
    from bs4 import BeautifulSoup
    
    score_entry = db.query(CompanyScore).filter_by(company_id=company_id).first()
    if not score_entry:
        return {"error": "Company not found"}
        
    comp = score_entry.company
    
    # 1. Real-time Web Search (Mock-safe or Real)
    # Buscamos 3 resultados frescos
    search_query = f"{comp.name} responsabilidad social alicante"
    results = []
    try:
        # Limitamos a 3 para velocidad
        for url in search(search_query, num_results=3, lang="es"):
            results.append(url)
    except Exception as e:
        results = ["Error buscando en Google: " + str(e)]

    # 2. Análisis Web Directo (si tiene web)
    web_keywords = []
    if comp.web:
        try:
            target_url = comp.web if comp.web.startswith("http") else "http://" + comp.web
            resp = requests.get(target_url, timeout=5, verify=False)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                text = soup.get_text().lower()
                for kw in ["sostenibilidad", "igualdad", "fundación", "donación", "medio ambiente", "cruz roja", "solidaridad"]:
                    if kw in text:
                        web_keywords.append(kw)
        except:
            pass # Fail silently for speed

    # 3. Construcción del Generador de Argumentario
    
    # Saludo y Contexto
    pitch = f"Hola, buenos días. Soy voluntario de Cruz Roja en {comp.municipality or 'Alicante'}. "
    pitch += f"Os contactamos porque hemos visto que sois un referente en el sector de {comp.category or comp.modality or 'vuestra actividad'}."
    
    # Argumento "Gancho" (Tier Social)
    if score_entry.score_total >= 3.0:
        pitch += " Llevamos un tiempo siguiendo vuestra trayectoria y vemos que compartimos valores muy fuertes. "
    elif score_entry.score_total >= 2.0:
        pitch += " Estamos buscando aliados estratégicos en la zona y vuestro perfil encaja perfectamente. "
    
    # Argumento Específico (Evidence)
    pitch += "\n\n**Argumento Personalizado:**\n"
    if web_keywords:
        pitch += f"- HE VISTO EN VUESTRA WEB menciones a: {', '.join(web_keywords).upper()}. En Cruz Roja tenemos proyectos justo en esas áreas.\n"
    
    # Argumento Search (Real-time)
    if len(results) > 0 and "Error" not in results[0]:
         pitch += f"- HE LEÍDO NOTICIAS sobre vosotros, por ejemplo en: {results[0]}. Nos encantaría colaborar en iniciativas así.\n"
    elif score_entry.news_evidence and len(score_entry.news_evidence) > 5:
        # Fallback to stored evidence
        evidence = json.loads(score_entry.news_evidence)
        if evidence:
             pitch += f"- HE LEÍDO SOBRE: {evidence[0]['title']}.\n"

    # Cierre de Venta
    pitch += "\n\n**Cierre:**\n"
    pitch += "¿Os interesaría tomar un café de 10 minutos para explicaros cómo vuestra RSC puede tener impacto directo aquí en Alicante?"

    return {
        "company_name": comp.name,
        "pitch": pitch,
        "real_time_results": results,
        "web_detected_keywords": web_keywords
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
