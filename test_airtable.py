import os
import requests

# Leer variables de entorno
api_key = os.getenv("AIRTABLE_API_KEY")
base_id = os.getenv("AIRTABLE_BASE_ID")
table_name = os.getenv("AIRTABLE_TABLE_NAME")

# Verificar que todas las variables estén definidas
if not api_key:
    print("Error: La variable de entorno AIRTABLE_API_KEY no está definida.")
    exit(1)

if not base_id:
    print("Error: La variable de entorno AIRTABLE_BASE_ID no está definida.")
    exit(1)

if not table_name:
    print("Error: La variable de entorno AIRTABLE_TABLE_NAME no está definida.")
    exit(1)

# Armar la URL
url = f"https://api.airtable.com/v0/{base_id}/{table_name}"

# Parámetros de la petición
params = {
    "maxRecords": 5,
    "pageSize": 5
}

# Headers con autorización
headers = {
    "Authorization": f"Bearer {api_key}"
}

# Hacer la petición GET
response = requests.get(url, params=params, headers=headers)

# Verificar el status code
if response.status_code != 200:
    print(f"Error: Status code {response.status_code}")
    print(f"Mensaje: {response.text}")
    exit(1)

# Procesar los registros
data = response.json()
records = data.get("records", [])

print(f"Se obtuvieron {len(records)} registros:\n")

for record in records:
    fields = record.get("fields", {})
    fecha = fields.get("fechacertificado", "N/A")
    coordinador = fields.get("nombrecoordinador", "N/A")
    total = fields.get("total", "N/A")
    
    print(f"Fecha: {fecha} | Coordinador: {coordinador} | Total: {total}")
