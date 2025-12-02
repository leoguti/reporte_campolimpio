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
table_name = os.getenv("AIRTABLE_TABLE_NAME")

if not api_key:
    print("Error: La variable de entorno AIRTABLE_API_KEY no está definida.")
    exit(1)

if not base_id:
    print("Error: La variable de entorno AIRTABLE_BASE_ID no está definida.")
    exit(1)

if not table_name:
    print("Error: La variable de entorno AIRTABLE_TABLE_NAME no está definida.")
    exit(1)

# Leer la pregunta desde argumentos de línea de comandos
if len(sys.argv) < 2:
    print("Error: Debes proporcionar una pregunta como argumento.")
    print('Uso: python test_agent_airtable.py "¿Cuál es el consolidado por coordinador?"')
    exit(1)

pregunta = " ".join(sys.argv[1:])

# Hacer petición a Airtable para obtener datos
url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
params = {"maxRecords": 100}  # Aumentado para tener más datos
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.get(url, params=params, headers=headers)

if response.status_code != 200:
    print(f"Error al consultar Airtable: Status code {response.status_code}")
    print(f"Mensaje: {response.text}")
    exit(1)

# Construir lista de diccionarios con más campos
data = response.json()
records = data.get("records", [])

registros = []
for record in records:
    fields = record.get("fields", {})
    registros.append({
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

# Leer el system prompt
with open('agent/system_prompt.txt', 'r', encoding='utf-8') as f:
    system_prompt = f.read()

# Armar el prompt con la pregunta del director
prompt = system_prompt + "\n\n"
prompt += f"El Director de Campolimpio pregunta: {pregunta}\n\n"
prompt += "Tienes acceso a estos datos de la tabla Certificados (últimos 100 registros):\n\n"
prompt += json.dumps(registros, indent=2, ensure_ascii=False)
prompt += "\n\nPor favor, responde la pregunta del Director con análisis detallado basado en los datos proporcionados."

# Llamar a la API de OpenAI
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
