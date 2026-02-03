# Sistema de Inteligencia para Captación de Fondos - Cruz Roja Española

Este proyecto es una herramienta avanzada de inteligencia de datos diseñada para optimizar la captación de socios corporativos de Cruz Roja, transformando datos públicos y noticias en prensa en oportunidades de colaboración estratégica.

## 🚀 Funcionalidad Principal

El sistema automatiza el ciclo de vida del prospecto corporativo:
1.  **Sincronización Inteligente**: Descarga y normaliza miles de registros de empresas desde el portal de Open Data de la Generalitat Valenciana (GVA).
2.  **Motor de Impacto Social (IA)**: Analiza miles de noticias en prensa local y nacional utilizando procesamiento de lenguaje natural (NLP) para clasificar a las empresas en categorías de RSC (Empleo, Inclusión, Medioambiente).
3.  **Ranking Priorizado**: Calcula una puntuación única para cada empresa basada en su facturación, ubicación estratégica y, sobre todo, su afinidad social real demostrada en noticias recientes.
4.  **Panel de Control Centralizado**: Una interfaz de terminal para gestionar todos los procesos de datos y servidores con un solo clic.
5.  **Dashboard Visual**: Un cuadro de mando web donde las evidencias de prensa aparecen con enlaces directos, etiquetas rojas de Cruz Roja y la nota de vínculo (0-10), permitiendo a los captadores preparar sus visitas con información fresca y contrastada.
6.  **Vínculo Social CRE**: Un motor de clasificación específico que identifica noticias de Alianzas Humanitarias, Salud, Educación o Inclusión, asignando una nota de afinidad inmediata.

> [!NOTE]
> **Motor Unificado**: El sistema utiliza un único motor de búsqueda e IA (**NewsCollector + NewsClassifier**). Los mismos datos que ves como "Evidencias" en el Dashboard son los que el algoritmo procesa para calcular el *Pilar de Actualidad*.

## 🧠 Algoritmo de Clasificación y Scoring

El sistema utiliza un algoritmo híbrido ponderado para determinar la relevancia de cada empresa:

*   **Pilar Social (60%)**: Analiza el sector de actividad (CNAE). Las empresas de sectores industriales, construcción o servicios intensivos en mano de obra reciben mayor puntuación por su potencial de colaboración en planes de empleo y vulnerabilidad.
*   **Pilar Territorial (20%)**: Prioriza empresas con sede en municipios clave donde Cruz Roja tiene presencia física o necesidades operativas urgentes.
*   **Pilar Económico (10%)**: Añade un bonus de capacidad a empresas con facturación superior a 1 millón de euros, identificándolas como "Grandes Donantes" potenciales.
*   **Pilar Vínculo CRE (Variable)**: Clasifica noticias en tiempo real. Si se detectan palabras clave de *Inclusión, Salud, Educación o Emergencias*, la empresa recibe una **Nota de Vínculo (0-10)**. Una nota superior a 5 suma automáticamente **+1.0 punto extra** al ranking general.
*   **Pilar de Actualidad General**: Pondera la presencia constante en prensa de la empresa.

## 🛤️ Pasos realizados en el Desarrollo

Para llegar al estado actual, hemos seguido un proceso evolutivo y riguroso:

1.  **Cimentación y Datos GVA**: Establecimos la conexión con la API de la GVA y diseñamos la arquitectura de base de datos SQL para almacenar el tejido empresarial de la región.
2.  **Algoritmo de Scoring Inicial**: Definimos los criterios de importancia para Cruz Roja (sectores prioritarios y arraigo territorial).
3.  **Sistema de Vigilancia de Prensa**: Desarrollamos un recolector de noticias capaz de buscar menciones específicas de empresas vinculadas a sus municipios en Google News.
4.  **Integración de IA y Clasificación**: Implementamos un clasificador basado en reglas que detecta el impacto social de las noticias, ignorando el ruido y centrándose en lo relevante para la ONG.
5.  **Dashboard con Enlaces Reales**: Creamos la interfaz web y la conectamos con las noticias reales, permitiendo la trazabilidad total de la información desde la web hasta la fuente original.
6.  **Gestor de Operaciones**: Desarrollamos `gestion.py`, un panel unificado para simplificar tareas complejas (sincronizar, enriquecer, arrancar servidor).
7.  **Filtro por Localidad Estricto**: Refinamos las búsquedas para que el sistema obligue a introducir un municipio, garantizando que el impacto sea siempre local.
8.  **Integración de Vínculo Social CRE**: Implementamos la taxonomía específica de Cruz Roja y la lógica de puntuación 0-10 basada en evidencias.
9.  **Documentación y Despliegue**: Creamos guías de instalación y requisitos para asegurar la portabilidad del sistema.

---
*Este proyecto convierte el ruido mediático en vínculos sociales sólidos.*
