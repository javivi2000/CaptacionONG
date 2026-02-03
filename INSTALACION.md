# Guía de Instalación y Despliegue - Captación ONG (Cruz Roja)

Este documento detalla los pasos necesarios para instalar y poner en marcha el sistema de análisis de impacto y captación de empresas.

## Requisitos Previos

- **Python 3.10 o superior** (Optimizado para Python 3.14).
- **Acceso a Internet** (Para descarga de datos GVA y búsqueda de noticias).
- **Sistema Operativo**: Windows, Linux o macOS.

## Paso 1: Clonar o Descargar el Proyecto
Asegúrate de tener todos los archivos en un directorio local:
```bash
c:/Users/jrgue/Desarrollo/CaptacionONG
```

## Paso 2: Crear un Entorno Virtual (Recomendado)
Para mantener las dependencias aisladas y evitar conflictos:
```bash
python -m venv .venv
# Activar en Windows:
.venv\Scripts\activate
# Activar en Linux/macOS:
source .venv/bin/activate
```

## Paso 3: Instalar Dependencias
Utiliza el archivo `requirements.txt` actualizado:
```bash
pip install -r requirements.txt
```

### Paso 3.1: Inicializar/Migrar Base de Datos
Si es una instalación nueva, la base de datos se creará sola. Si estás actualizando desde una versión anterior, ejecuta el script de migración para habilitar los nuevos campos de Cruz Roja:
```bash
python migrate_v2.py
```

## Paso 4: Configuración
Revisa el archivo `config.yaml` para asegurar que las rutas y parámetros son correctos:
- **database/url**: Define dónde se guardará la base de datos SQLite (por defecto en `./data/companies.db`).
- **scoring**: Pesos y prioridades para el ranking de empresas.

## Paso 5: Puesta en Marcha (Panel de Control)
El sistema incluye un menú centralizado para facilitar todas las operaciones. Lánzalo con:
```bash
python gestion.py
```

### Orden de Operaciones Recomendado:
1.  **Opción 1**: Sincroniza los datos oficiales de la Generalitat Valenciana.
1.5 **Migrar** (opcional): Ejecuta `python migrate_v2.py` si vienes de la Semana 1.
2.  **Opción 2**: Realiza la carga inicial de noticias (elige el periodo de 180 días). El sistema clasificará automáticamente el "Vínculo CRE".
3.  **Opción 3**: Arranca el servidor web para ver el Dashboard.

## Acceso al Dashboard
Una vez arrancado el servidor (Opción 3), abre tu navegador en:
**http://localhost:8001/dashboard**

---
*Desarrollado para Cruz Roja Española - Sistema de Inteligencia de Captación.*
