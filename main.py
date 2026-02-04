from fastapi import FastAPI, Depends
from typing import Optional
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

from api.manager import runner

@app.post("/api/admin/run/{task}")
async def run_task(task: str, municipality: Optional[str] = None, name: Optional[str] = None):
    script_map = {
        "sync": "sync_gva.py",
        "enrich": "run_weekly_enrichment.py",
        "export": "export.py",
        "analyze_webs": "web_analyzer.py"
    }
    
    if task not in script_map:
        return {"error": "Tarea no reconocida"}
    
    args = []
    if municipality:
        args.extend(["--municipality", municipality])
    if name:
        args.extend(["--name", name])
        
    success, message = runner.run_script(task, script_map[task], args=args)
    return {"success": success, "message": message}

@app.get("/api/admin/status/{task}")
async def get_task_status(task: str):
    return runner.get_status(task)

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
    name: Optional[str] = None,
    only_evidence: bool = False,
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    query = db.query(GVACompany, CompanyScore).join(CompanyScore)
    
    if municipality:
        query = query.filter(GVACompany.municipality.ilike(f"%{municipality}%"))
    
    if name:
        query = query.filter(GVACompany.name.ilike(f"%{name}%"))
    
    if only_evidence:
        # Filtrar solo empresas que tengan noticias en la tabla CompanyNews
        from sqlalchemy import exists
        query = query.filter(exists().where(CompanyNews.company_id == GVACompany.id))
    
    query = query.order_by(CompanyScore.score_total.desc())
    
    if limit > 0:
        query = query.limit(limit)
    
    results = query.all()
    
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
                "date": n.date.strftime("%Y-%m-%d") if n.date else None,
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
            "web_keywords": json.loads(score.web_keywords or "{}"),
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
    try:
        from googlesearch import search
        import requests
        from bs4 import BeautifulSoup
        
        score_entry = db.query(CompanyScore).filter_by(company_id=company_id).first()
        if not score_entry:
            return {"error": "Company not found"}
            
        comp = score_entry.company
        
        # 1. Real-time Web Search
        search_query = f"{comp.name} responsabilidad social alicante"
        results = []
        try:
            google_results = search(search_query, num_results=3, lang="es")
            for url in google_results:
                results.append(url)
        except:
            results = ["Error buscando en Google"]

        # 2. Análisis Web Directo
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
                pass

        # 3. Construcción del Generador de Argumentario
        breakdown = {}
        try:
            if score_entry.news_evidence:
                breakdown = json.loads(score_entry.news_evidence)
        except:
             pass

        pitch = f"Hola, buenos días. Soy voluntario de Cruz Roja en {comp.municipality or 'Alicante'}. "
        pitch += f"Os contactamos porque hemos visto que sois un referente en el sector de {comp.category or comp.modality or 'vuestra actividad'}."
        
        if score_entry.score_total >= 3.0:
            pitch += " Llevamos un tiempo siguiendo vuestra trayectoria y vemos que compartimos valores muy fuertes. "
        elif score_entry.score_total >= 2.0:
            pitch += " Estamos buscando aliados estratégicos en la zona y vuestro perfil encaja perfectamente. "
        
        pitch += "\n\n**Argumento Personalizado:**\n"
        
        if web_keywords:
            keywords_str = ", ".join(web_keywords).upper()
            pitch += f"- HE VISTO EN VUESTRA WEB que dais importancia a conceptos como: {keywords_str}. En Cruz Roja tenemos proyectos de impacto directo justo en esas áreas y nos encantaría sumar esfuerzos.\n"
        
        if isinstance(breakdown, dict):
            if breakdown.get("cre_bonus", 0) > 0:
                pitch += f"- VALORAMOS MUCHO vuestra relación histórica con nosotros. Sois un colaborador con un vínculo ya consolidado y nos gustaría llevarlo al siguiente nivel.\n"
            if breakdown.get("news", 0) > 0:
                pitch += f"- HEMOS VISTO vuestra reciente actividad social en prensa. Es inspirador ver vuestro compromiso activo con el entorno.\n"
        
        if len(results) > 0 and "Error" not in results[0]:
             pitch += f"- HE LEÍDO NOTICIAS sobre vuestra implicación local, por ejemplo en: {results[0]}. Creemos que podemos potenciar juntos esa visibilidad.\n"
        elif isinstance(breakdown, list) and len(breakdown) > 0:
             pitch += f"- HE LEÍDO SOBRE: {breakdown[0]['title']}.\n"

        pitch += "\n\n**Cierre:**\n"
        pitch += "¿Os interesaría tomar un café de 10 minutos para explicaros cómo vuestra RSC puede tener impacto real aquí en nuestra zona?"

        return {
            "company_name": comp.name,
            "pitch": pitch,
            "real_time_results": results,
            "web_detected_keywords": web_keywords
        }
    except Exception as e:
        return {"error": "Error interno al generar el argumentario."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
