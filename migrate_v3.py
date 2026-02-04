import sqlite3
import yaml
import os

def migrate():
    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    db_path = config["database"]["url"].replace("sqlite:///", "")
    print(f"Conectando a base de datos: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Añadiendo columna 'web_keywords' a la tabla 'company_scores'...")
        cursor.execute("ALTER TABLE company_scores ADD COLUMN web_keywords TEXT")
        conn.commit()
        print("Migración completada con éxito.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Aviso: La columna 'web_keywords' ya existe.")
        else:
            print(f"Error en migración: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
