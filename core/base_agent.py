import abc
from typing import Dict, Any, List, Optional
import json

class BaseAgent(abc.ABC):
    """
    Clase base para todos los agentes del sistema "Frontera Agéntica".
    Sigue una arquitectura Vanilla: pura, legible y modular.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        
    @abc.abstractmethod
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método principal que debe implementar cada agente.
        Recibe un diccionario con datos de entrada y devuelve un resultado procesado.
        """
        pass

    def log_step(self, message: str):
        """Emite un log estructurado para que el orquestador pueda capturarlo."""
        print(f"[{self.name.upper()}] {message}")
