from typing import List, Dict, Any, Optional
import google.generativeai as genai
import yaml
import json
from .base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """
    El 'Pensador' del sistema. Utiliza un LLM para generar un plan de acción
    basado en el objetivo y los datos de la empresa.
    """
    
    def __init__(self):
        super().__init__(name="Planner")
        self._load_config()
        
    def _load_config(self):
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            
        ai_config = config.get("ai", {})
        self.api_key = ai_config.get("api_key")
        self.model_name = ai_config.get("model_name", "gemini-1.5-flash")
        
        if self.api_key and self.api_key != "TU_API_KEY_AQUI":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
            self.log_step("ADVERTENCIA: API Key no configurada correctamente.")

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        target_company = input_data.get("company_name", "Desconocida")
        objective = input_data.get("objective", "Preparar visita de captación estratégica para Cruz Roja")
        
        self.log_step(f"Generando plan inteligente para {target_company}...")
        
        if not self.model:
            return {"status": "error", "message": "IA no configurada"}

        prompt = f"""
        Como experto captador de fondos para Cruz Roja Española, tu tarea es planificar la investigación de una empresa.
        
        EMPRESA: {target_company}
        UBICACIÓN: {input_data.get('municipality', 'Alicante')}
        WEB: {input_data.get('web', 'Desconocida')}
        OBJETIVO: {objective}
        
        Genera un plan de pasos técnicos a seguir. Responde ÚNICAMENTE con un JSON válido que sea una lista de objetos.
        Cada objeto debe tener:
        - id: (int)
        - task: (string, una de: 'research_web', 'search_news', 'analyze_sustainability', 'generate_argumentary')
        - params: (dict con parámetros relevantes como 'query', 'url', etc.)
        
        Ejemplo:
        [
          {{"id": 1, "task": "research_web", "params": {{"url": "..."}}}},
          {{"id": 2, "task": "search_news", "params": {{"query": "..."}}}}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Limpiar el texto por si el modelo añade markdown wrappers
            text = response.text.replace("```json", "").replace("```", "").strip()
            plan = json.loads(text)
            
            return {
                "status": "success",
                "plan": plan,
                "metadata": {"model": self.model_name}
            }
        except Exception as e:
            self.log_step(f"Error llamando a Gemini: {str(e)}")
            return {"status": "error", "message": str(e)}
