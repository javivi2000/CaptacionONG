import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/companies.db')
cursor = conn.cursor()

# 1. Aseguramos que existe la empresa 1 o buscamos la primera
cursor.execute("SELECT id, name FROM gva_companies LIMIT 1")
company = cursor.fetchone()
if company:
    comp_id, comp_name = company
    # 2. Insertamos la noticia de prueba
    cursor.execute("""
        INSERT INTO company_news (company_id, date, title, url, source, category, cre_category, cre_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (comp_id, datetime.now().isoformat(), "Cruz Roja y " + comp_name + " firman un convenio de inclusión", 
          "http://cruzroja.es/aliados", "Nota de Prensa CRE", "Inclusión", "Alianza Humanitaria", 9.5))
    conn.commit()
    print(f"Evidencia de prueba insertada para: {comp_name}")
else:
    print("No hay empresas para insertar pruebas.")

# 3. Mostrar los últimos datos
cursor.execute("""
    SELECT c.name, n.cre_category, n.cre_score, n.title, n.source
    FROM company_news n
    JOIN gva_companies c ON n.company_id = c.id
    ORDER BY n.id DESC
    LIMIT 1
""")
r = cursor.fetchone()
print("\nREGISTRO DE EVIDENCIA ACTUALIZADO:")
print("-" * 80)
print(f"Empresa:     {r[0]}")
print(f"Vínculo CRE: {r[1]}")
print(f"Nota Social: {r[2]}/10")
print(f"Título:      {r[3]}")
print(f"Fuente:      {r[4]}")
print("-" * 80)

conn.close()
