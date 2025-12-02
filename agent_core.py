import os
import json
import requests
from typing import Optional
from openai import OpenAI


def run_agent(question: str, extra: Optional[dict] = None):
    """
    Ejecuta el agente de Campolimpio con acceso a tablas Certificados y Kardex.
    
    Args:
        question: Pregunta del usuario
        extra: Datos adicionales opcionales (max_records, etc.)
    
    Returns:
        dict con 'success', 'response', 'error'
    """
    # Configuración
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return {"success": False, "error": "AIRTABLE_API_KEY no definida"}
    
    if not base_id:
        return {"success": False, "error": "AIRTABLE_BASE_ID no definida"}
    
    if not openai_key:
        return {"success": False, "error": "OPENAI_API_KEY no definida"}
    
    # Parámetros
    max_records = (extra or {}).get("max_records", 100)
    
    # Función auxiliar para consultar Airtable
    def consultar_tabla(table_name, max_records):
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        params = {"maxRecords": max_records}
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            return None, f"Error {response.status_code}: {response.text}"
        
        return response.json().get("records", []), None
    
    # Consultar Certificados
    certificados_records, error = consultar_tabla("Certificados", max_records)
    if error:
        return {"success": False, "error": f"Certificados: {error}"}
    
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
    
    # Consultar Kardex
    kardex_records, error = consultar_tabla("Kardex", max_records)
    if error:
        return {"success": False, "error": f"Kardex: {error}"}
    
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
    
    # Leer system prompt
    try:
        with open('agent/system_prompt.txt', 'r', encoding='utf-8') as f:
            system_prompt = f.read()
    except FileNotFoundError:
        return {"success": False, "error": "agent/system_prompt.txt no encontrado"}
    
    # Construir prompt
    prompt = system_prompt + "\n\n"
    prompt += f"El Director de Campolimpio pregunta: {question}\n\n"
    prompt += "Tienes acceso a datos de AMBAS tablas:\n\n"
    prompt += "=== TABLA CERTIFICADOS (últimos 100 registros) ===\n"
    prompt += json.dumps(certificados, indent=2, ensure_ascii=False)
    prompt += "\n\n=== TABLA KARDEX (últimos 100 registros) ===\n"
    prompt += json.dumps(kardex, indent=2, ensure_ascii=False)
    prompt += "\n\nPor favor, responde la pregunta del Director con análisis detallado basado en los datos proporcionados."
    prompt += "\nIDENTIFICA AUTOMÁTICAMENTE qué tabla(s) necesitas usar según la pregunta."
    
    # Llamar a OpenAI
    try:
        client = OpenAI()
        response = client.responses.create(
            model="gpt-5.1",
            input=prompt
        )
        
        return {
            "success": True,
            "response": response.output_text,
            "metadata": {
                "certificados_count": len(certificados),
                "kardex_count": len(kardex)
            }
        }
    except Exception as e:
        return {"success": False, "error": f"OpenAI error: {str(e)}"}
