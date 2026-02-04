import subprocess
import threading
import sys
import os
from typing import Dict, List, Optional
import time

class ScriptRunner:
    """Gestiona la ejecución de scripts del sistema y captura su salida."""
    
    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.logs: Dict[str, List[str]] = {}
        self.status: Dict[str, str] = {} # 'running', 'completed', 'error'
        self.progress_current: Dict[str, int] = {}
        self.progress_total: Dict[str, int] = {}

    def run_script(self, task_id: str, script_name: str, args: List[str] = None):
        """Inicia un script en un hilo separado."""
        if task_id in self.active_processes and self.status.get(task_id) == 'running':
            return False, "Tarea ya en ejecución"

        self.logs[task_id] = []
        self.status[task_id] = 'running'
        self.progress_current[task_id] = 0
        self.progress_total[task_id] = 0
        
        thread = threading.Thread(target=self._execute, args=(task_id, script_name, args))
        thread.start()
        return True, "Iniciado"

    def _execute(self, task_id: str, script_name: str, args: List[str] = None):
        cmd = [sys.executable, script_name]
        if args:
            cmd.extend(args)
            
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.active_processes[task_id] = process
            
            # Leer salida línea a línea
            for line in process.stdout:
                clean_line = line.strip()
                if clean_line:
                    # Detectar progreso: [PROGRESS] X/Y
                    if "[PROGRESS]" in clean_line:
                        try:
                            parts = clean_line.split("[PROGRESS]")[1].strip().split("/")
                            self.progress_current[task_id] = int(parts[0])
                            self.progress_total[task_id] = int(parts[1])
                            continue # No añadir el log de progreso a la consola para no ensuciar
                        except:
                            pass

                    self.logs[task_id].append(clean_line)
                        
            process.wait()
            
            if process.returncode == 0:
                self.status[task_id] = 'completed'
            else:
                self.status[task_id] = 'error'
                self.logs[task_id].append(f"ERROR: Proceso finalizó con código {process.returncode}")
                
        except Exception as e:
            self.status[task_id] = 'error'
            self.logs[task_id].append(f"EXCEPTION: {str(e)}")
        finally:
            if task_id in self.active_processes:
                del self.active_processes[task_id]

    def get_status(self, task_id: str):
        return {
            "status": self.status.get(task_id, "not_found"),
            "logs": self.logs.get(task_id, []),
            "progress": {
                "current": self.progress_current.get(task_id, 0),
                "total": self.progress_total.get(task_id, 0)
            }
        }

# Instancia global para ser usada por FastAPI
runner = ScriptRunner()
