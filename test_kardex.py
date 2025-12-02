import os
import requests

# Leer variables de entorno
api_key = os.getenv("AIRTABLE_API_KEY")
base_id = os.getenv("AIRTABLE_BASE_ID")

# Verificar que todas las variables estén definidas
if not api_key:
    print("Error: La variable de entorno AIRTABLE_API_KEY no está definida.")
    exit(1)

if not base_id:
    print("Error: La variable de entorno AIRTABLE_BASE_ID no está definida.")
    exit(1)

# Usar la tabla Kardex
table_name = "Kardex"

# Armar la URL
url = f"https://api.airtable.com/v0/{base_id}/{table_name}"

# Parámetros de la petición
params = {
    "maxRecords": 10,
    "pageSize": 10
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

print(f"Se obtuvieron {len(records)} registros de Kardex:\n")

for record in records:
    fields = record.get("fields", {})
    fecha = fields.get("fechakardex", "N/A")
    coordinador = fields.get("Name (from Coordinador)", "N/A")
    tipo_mov = fields.get("TipoMovimiento", "N/A")
    reciclaje = fields.get("Reciclaje", 0)
    incineracion = fields.get("Incineración", 0)
    total = fields.get("Total", "N/A")
    centro = fields.get("NombreCentrodeAcopio", "N/A")
    gestor = fields.get("nombregestor", "N/A")
    
    print(f"Fecha: {fecha} | Coordinador: {coordinador} | Tipo: {tipo_mov}")
    print(f"  Reciclaje: {reciclaje} kg | Incineración: {incineracion} kg | Total: {total} kg")
    print(f"  Centro: {centro} | Gestor: {gestor}")
    print()
