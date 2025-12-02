import os
import sys
import json
import requests
from openai import OpenAI

# Verificar OPENAI_API_KEY
if not os.getenv("OPENAI_API_KEY"):
    print("Error: La variable de entorno OPENAI_API_KEY no está definida.")
    print("Por favor, exporta tu API key con: export OPENAI_API_KEY='tu-api-key'")
    exit(1)

# Leer variables de entorno de Airtable
api_key = os.getenv("AIRTABLE_API_KEY")
base_id = os.getenv("AIRTABLE_BASE_ID")

if not api_key:
    print("Error: La variable de entorno AIRTABLE_API_KEY no está definida.")
    exit(1)

if not base_id:
    print("Error: La variable de entorno AIRTABLE_BASE_ID no está definida.")
    exit(1)

# Leer la pregunta desde argumentos de línea de comandos
if len(sys.argv) < 2:
    print("Error: Debes proporcionar una pregunta como argumento.")
    print('Uso: python test_agent_dual.py "¿Cuál es el consolidado por coordinador?"')
    exit(1)

pregunta = " ".join(sys.argv[1:])

# Función para consultar una tabla de Airtable
def consultar_tabla(table_name, max_records=100):
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    params = {"maxRecords": max_records}
    headers = {"Authorization": f"Bearer {api_key}"}
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code != 200:
        print(f"Error al consultar {table_name}: Status code {response.status_code}")
        print(f"Mensaje: {response.text}")
        return []
    
    return response.json().get("records", [])

# Consultar ambas tablas
print("Consultando datos de Airtable...")

# Tabla Certificados
certificados_records = consultar_tabla("Certificados", 100)
certificados = []
for record in certificados_records:
    fields = record.get("fields", {})
    certificados.append({
        "tabla": "Certificados",
        "pre_consecutivo": fields.get("pre_consecutivo", "N/A"),
        "fechadevolucion": fields.get("fechadevolucion", "N/A"),
        "nombrecoordinador": fields.get("nombrecoordinador", "N/A"),
        "rigidos": fields.get("rigidos", 0),
        "flexibles": fields.get("flexibles", 0),
        "metalicos": fields.get("metalicos", 0),
        "embalaje": fields.get("embalaje", 0),
        "total": fields.get("total", 0),
        "municipiogenerador": fields.get("municipiogenerador", "N/A"),
        "municipiodevolucion": fields.get("municipiodevolucion", "N/A"),
        "observaciones": fields.get("observaciones", "")
    })

# Tabla Kardex
kardex_records = consultar_tabla("Kardex", 100)
kardex = []
for record in kardex_records:
    fields = record.get("fields", {})
    kardex.append({
        "tabla": "Kardex",
        "idkardex": fields.get("idkardex", "N/A"),
        "fechakardex": fields.get("fechakardex", "N/A"),
        "TipoMovimiento": fields.get("TipoMovimiento", "N/A"),
        "coordinador": fields.get("Name (from Coordinador)", "N/A"),
        "MunicipioOrigen": fields.get("MunicipioOrigen", "N/A"),
        "Reciclaje": fields.get("Reciclaje", 0),
        "Incineración": fields.get("Incineración", 0),
        "PlasticoContaminado": fields.get("PlasticoContaminado", 0),
        "Flexibles": fields.get("Flexibles", 0),
        "Lonas": fields.get("Lonas", 0),
        "Carton": fields.get("Carton", 0),
        "Metal": fields.get("Metal", 0),
        "Total": fields.get("Total", 0),
        "CentrodeAcopio": fields.get("NombreCentrodeAcopio", "N/A"),
        "gestor": fields.get("nombregestor", "N/A"),
        "Observaciones": fields.get("Observaciones", "")
    })

print(f"✓ Certificados: {len(certificados)} registros")
print(f"✓ Kardex: {len(kardex)} registros")
print()

# Leer el system prompt
with open('agent/system_prompt.txt', 'r', encoding='utf-8') as f:
    system_prompt = f.read()

# Armar el prompt con ambas tablas
prompt = system_prompt + "\n\n"
prompt += f"El Director de Campolimpio pregunta: {pregunta}\n\n"
prompt += "Tienes acceso a datos de AMBAS tablas:\n\n"
prompt += "=== TABLA CERTIFICADOS (últimos 100 registros) ===\n"
prompt += json.dumps(certificados, indent=2, ensure_ascii=False)
prompt += "\n\n=== TABLA KARDEX (últimos 100 registros) ===\n"
prompt += json.dumps(kardex, indent=2, ensure_ascii=False)
prompt += "\n\nPor favor, responde la pregunta del Director con análisis detallado basado en los datos proporcionados."
prompt += "\nIDENTIFICA AUTOMÁTICAMENTE qué tabla(s) necesitas usar según la pregunta."

# Llamar a la API de OpenAI
print("Consultando al agente...")
client = OpenAI()
response = client.responses.create(
    model="gpt-5.1",
    input=prompt
)

print("\n" + "="*80)
print(f"PREGUNTA: {pregunta}")
print("="*80 + "\n")
print(response.output_text)
print("\n" + "="*80)
