import re
import unicodedata

class NewsClassifier:
    def __init__(self):
        # Definición de diccionarios de impacto social (Español de España)
        self.categories = {
            "Empleo": [
                "empleo", "contratacion", "puestos de trabajo", "plantilla", "vacantes", 
                "creación de puestos", "mercado laboral", "contratar", "despido", "ere", 
                "empleabilidad", "formación profesional", "practicas"
            ],
            "Inclusión": [
                "inclusion", "diversidad", "discapacidad", "accesibilidad", "igualdad", 
                "colectivos vulnerables", "integración", "genero", "brecha salarial", 
                "conciliación", "solidaridad", "donacion", "voluntariado", "cruz roja",
                "proyectos sociales", "comunidad", "sin hogar", "ayuda humanitaria"
            ],
            "Medioambiente": [
                "medio ambiente", "sostenibilidad", "ecologia", "cambio climatico", 
                "emisiones", "descarbonización", "energias renovables", "fotovoltaica", 
                "reciclaje", "residuos", "economia circular", "huella de carbono",
                "eficiencia energetica", "verde", "planeta"
            ]
        }

        # Taxonomía específica de Vínculo CRE
        self.cre_categories = {
            "Alianza Humanitaria": ["donacion", "solidaridad", "ayuda humanitaria", "patrocinio", "aliado", "convenio", "colaboracion"],
            "Salud y Emergencias": ["salud", "hospital", "socorros", "emergencias", "primeros auxilios", "ambulancia", "prevencion"],
            "Inclusión Social": ["vulnerabilidad", "sin hogar", "pobreza", "exclusion", "igualdad", "asistencia social"],
            "Educación y Juventud": ["juventud", "infancia", "educacion", "becas", "talleres", "formacion", "jovenes"],
            "Sostenibilidad": ["ods", "agenda 2030", "impacto positivo", "rse", "responsabilidad social"]
        }

    def _normalize_text(self, text):
        """Limpia tildes, caracteres especiales y pasa a minúsculas para mejor coincidencia"""
        if not text:
            return ""
        # Quitar tildes y normalizar
        text = "".join(c for c in unicodedata.normalize('NFD', text.lower())
                      if unicodedata.category(c) != 'Mn')
        return text

    def classify(self, title, content_text=""):
        """
        Analiza el título y el contenido para asignar categorías de impacto.
        Devuelve una lista de categorías encontradas y un score de confianza.
        """
        combined_text = self._normalize_text(f"{title} {content_text}")
        found_categories = {}
        
        for category, keywords in self.categories.items():
            matches = 0
            for kw in keywords:
                # Normalizar palabra clave también por si acaso
                kw_norm = self._normalize_text(kw)
                # Búsqueda exacta de palabra completa para evitar "verde" en "verderon"
                if re.search(rf"\b{re.escape(kw_norm)}\b", combined_text):
                    matches += 1
            
            if matches > 0:
                # Confianza basada en número de menciones distintas
                found_categories[category] = matches
        
        # Devolver categorías ordenadas por relevancia
        sorted_cats = sorted(found_categories.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_cats:
            return ["Otros"], 1.0
            
        return [cat for cat, count in sorted_cats], float(sum(found_categories.values()))

    def calculate_cre_score(self, title, content_text=""):
        """
        Calcula una nota de 0 a 10 basada en la afinidad con Cruz Roja (CRE).
        """
        text = self._normalize_text(f"{title} {content_text}")
        score = 0
        best_category = "General"
        
        # 1. Puntos por categorías específicas
        for cat, keywords in self.cre_categories.items():
            cat_matches = 0
            for kw in keywords:
                kw_norm = self._normalize_text(kw)
                if re.search(rf"\b{re.escape(kw_norm)}\b", text):
                    cat_matches += 1
            
            if cat_matches > 0:
                score += 2  # Cada categoría detectada suma puntos base
                best_category = cat

        # 2. Bonus por mención directa a Cruz Roja (Fundamental)
        if "cruz roja" in text or "cre" in text:
            score += 4
        
        # 3. Limitar a 10
        final_score = min(score, 10)
        
        # Si no hay nada, devolvemos un mínimo si parece positivo
        if final_score == 0 and len(text) > 20:
            final_score = 1.0

        return best_category, float(final_score)

if __name__ == "__main__":
    # Prueba rápida de clasificación
    classifier = NewsClassifier()
    test_title = "La empresa ha donado 10.000 euros a la Cruz Roja para proyectos de inclusión"
    categories, score = classifier.classify(test_title)
    print(f"Categorías: {categories}, Score: {score}")
    
    test_title_env = "Nueva planta fotovoltaica para reducir emisiones y cuidar el medio ambiente"
    categories, score = classifier.classify(test_title_env)
    print(f"Categorías: {categories}, Score: {score}")
