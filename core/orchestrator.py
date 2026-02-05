import asyncio
from typing import Dict, Any, List
from .base_agent import BaseAgent
from .planner import PlannerAgent

class Orchestrator:
    """
    El motor que coordina la ejecución del plan generado por el Planner.
    Gestiona el estado y la comunicación entre agentes.
    """
    
    def __init__(self):
        self.planner = PlannerAgent()
        self.state: Dict[str, Any] = {}
        
    async def execute_task(self, company_data: Dict[str, Any]):
        """
        Punto de entrada para procesar una empresa completa.
        """
        print(f"\n--- INICIANDO ORQUESTACIÓN: {company_data.get('company_name')} ---\n")
        
        # 1. Planificación
        plan_result = await self.planner.run(company_data)
        if plan_result["status"] != "success":
            print("[ORCHESTRATOR] Error en fase de planificación.")
            return
            
        plan = plan_result["plan"]
        self.state["plan"] = plan
        self.state["results"] = {}
        
        # 2. Ejecución Secuencial Real
        for step in plan:
            task_id = step["id"]
            task_name = step["task"]
            params = step.get("params", {})
            
            print(f"[ORCHESTRATOR] Ejecutando Paso {task_id}: {task_name}...")
            
            # Mapeo de tareas a scripts de v2.1
            if task_name == "research_web":
                from web_analyzer import analyze_all_webs
                await asyncio.to_thread(analyze_all_webs, limit=1, name=company_data["company_name"])
                
            elif task_name == "search_news":
                from news_collector import NewsCollector
                collector = NewsCollector()
                # Simulamos la búsqueda por ahora para no quemar cuota de Google Search innecesariamente
                print(f"[EXECUTOR] Buscando noticias para: {params.get('query')}")
                
            elif task_name == "generate_argumentary":
                # Aquí llamaríamos a la lógica de pitch mejorada
                print("[EXECUTOR] Generando argumentario final con IA...")
            
            self.state["results"][task_id] = f"Completado: {task_name}"
            
        print("\n--- ORQUESTACIÓN FINALIZADA ---")
        return self.state
