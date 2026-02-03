import sqlite3

def migrate():
    try:
        conn = sqlite3.connect('data/companies.db')
        cursor = conn.cursor()
        
        # Añadir columnas a company_news
        try:
            cursor.execute("ALTER TABLE company_news ADD COLUMN cre_category VARCHAR")
            print("Columna 'cre_category' añadida a company_news.")
        except sqlite3.OperationalError:
            print("La columna 'cre_category' ya existe.")
            
        try:
            cursor.execute("ALTER TABLE company_news ADD COLUMN cre_score FLOAT DEFAULT 0.0")
            print("Columna 'cre_score' añadida a company_news.")
        except sqlite3.OperationalError:
            print("La columna 'cre_score' ya existe.")

        # Añadir columnas a company_scores
        try:
            cursor.execute("ALTER TABLE company_scores ADD COLUMN score_cre_link FLOAT DEFAULT 0.0")
            print("Columna 'score_cre_link' añadida a company_scores.")
        except sqlite3.OperationalError:
            print("La columna 'score_cre_link' ya existe.")
            
        conn.commit()
        conn.close()
        print("Migración completada con éxito.")
    except Exception as e:
        print(f"Error en la migración: {e}")

if __name__ == "__main__":
    migrate()
