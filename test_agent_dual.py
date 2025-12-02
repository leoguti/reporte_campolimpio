import sys
from agent_core import run_agent

# Leer la pregunta desde argumentos de línea de comandos
if len(sys.argv) < 2:
    print("Error: Debes proporcionar una pregunta como argumento.")
    print('Uso: python test_agent_dual.py "¿Cuál es el consolidado por coordinador?"')
    exit(1)

pregunta = " ".join(sys.argv[1:])

# Ejecutar el agente
print("Consultando datos de Airtable...")
result = run_agent(pregunta)

if not result["success"]:
    print(f"Error: {result['error']}")
    exit(1)

print(f"✓ Certificados: {result['metadata']['certificados_count']} registros")
print(f"✓ Kardex: {result['metadata']['kardex_count']} registros")
print()

print("Consultando al agente...")
print("\n" + "="*80)
print(f"PREGUNTA: {pregunta}")
print("="*80 + "\n")
print(result["response"])
print("\n" + "="*80)
