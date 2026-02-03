import os
import sys
import subprocess
import time

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("====================================================")
    print("      SISTEMA DE CAPTACIÓN ONG - CRUZ ROJA          ")
    print("           PANEL DE CONTROL CENTRAL                 ")
    print("====================================================\n")

def run_script(script_name, args=None):
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    try:
        # Usamos subprocess.run para que la salida se vea en tiempo real
        subprocess.run(cmd)
    except Exception as e:
        print(f"\n[ERROR] Error al ejecutar {script_name}: {e}")
    input("\nPresiona Enter para volver al menú...")

def main_menu():
    while True:
        clear_screen()
        print_header()
        print("1. [GVA] Sincronizar datos de empresas (sync_gva.py)")
        print("2. [IA] Enriquecer noticias e impacto social (Lote histórico/semanal)")
        print("3. [WEB] Arrancar Servidor API y Dashboard (main.py)")
        print("4. [DATOS] Consultar estado de la base de datos (check_db.py)")
        print("5. [DATOS] Exportar resultados a JSON/CSV (export.py)")
        print("\n0. Salir")
        
        opcion = input("\nSeleccione una opción: ").strip()
        
        if opcion == '1':
            print("\nIniciando sincronización con GVA Open Data...")
            run_script("sync_gva.py")
        
        elif opcion == '2':
            clear_screen()
            print_header()
            run_script("run_weekly_enrichment.py")
            
        elif opcion == '3':
            print("\nArrancando servidor API en http://localhost:8001 ...")
            print("Presiona Ctrl+C para detener el servidor y volver al menú.")
            run_script("main.py")
            
        elif opcion == '4':
            print("\nConsultando estadísticas de la base de datos...")
            run_script("check_db.py")
            
        elif opcion == '5':
            print("\nIniciando proceso de exportación...")
            run_script("export.py")
            
        elif opcion == '0':
            print("\nSaliendo del sistema. ¡Buen día!")
            break
        
        else:
            print("\nOpción no válida.")
            time.sleep(1)

if __name__ == "__main__":
    main_menu()
