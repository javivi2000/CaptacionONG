import sqlite3
import json

def view_results():
    conn = sqlite3.connect('data/companies.db')
    cursor = conn.cursor()
    
    rows = cursor.execute("""
        SELECT c.name, s.news_evidence 
        FROM gva_companies c 
        JOIN company_scores s ON c.id=s.company_id 
        WHERE s.news_evidence LIKE '%Web Corporativa%' 
        LIMIT 10
    """).fetchall()
    
    print(f"\n--- HALLAZGOS DEL CRAWLER ({len(rows)}) ---\n")
    for r in rows:
        print(f"Empresa: {r[0]}")
        evidence = json.loads(r[1])
        for e in evidence:
            print(f" -> {e['title']}")
        print("-" * 20)
        
    conn.close()

if __name__ == "__main__":
    view_results()
