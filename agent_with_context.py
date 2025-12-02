import os
import json
import requests
from typing import Optional, Tuple
from openai import OpenAI

from conversation_state import ConversationState


def run_agent_with_context(
    question: str,
    state: ConversationState,
    extra: Optional[dict] = None
) -> Tuple[str, ConversationState]:
    """
    Ejecuta el agente con contexto de conversación.
    
    Args:
        question: Pregunta del usuario
        state: Estado actual de la conversación
        extra: Datos adicionales opcionales (max_records, etc.)
    
    Returns:
        Tupla (mensaje_para_usuario, state_actualizado)
    """
    # Configuración
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return "Error: Configuración de Airtable no disponible", state
    
    if not base_id:
        return "Error: Base de datos no configurada", state
    
    if not openai_key:
        return "Error: OpenAI no configurado", state
    
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
        return f"Error consultando Certificados: {error}", state
    
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
        return f"Error consultando Kardex: {error}", state
    
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
    
    # System message: instrucciones del asistente constructor de consultas
    system_instructions = """Eres un asistente inteligente que ayuda a formular consultas a la base de datos de Campolimpio.

TU TRABAJO NO ES SOLO RESPONDER, SINO:

1. Interpretar lo que el usuario quiere consultar
2. Detectar si la petición es ambigua, incompleta o imposible con los datos disponibles
3. Construir y actualizar una consulta normalizada en el state_json
4. Indicar el estado correcto: building, awaiting_clarification, ready_to_execute, executed o cancelled

COMPORTAMIENTO EN CADA TURNO:

- Si la petición es AMBIGUA o FALTA INFORMACIÓN:
  * Pregunta al usuario qué necesitas (periodo, coordinador, municipio, tipo de material, etc.)
  * Actualiza state_json marcando qué falta (issues con tipo missing_filter)
  * Marca status como awaiting_clarification
  
- Si el usuario pide algo IMPOSIBLE (campos inexistentes, cálculos no disponibles):
  * Explica el problema de forma amable
  * Propón alternativas basadas en los datos reales
  * Marca un issue con tipo invalid_field o impossible_request
  
- Si la consulta está COMPLETA Y VÁLIDA:
  * Marca status como ready_to_execute
  * Asegúrate de que query.table, query.type y query.filters estén correctamente definidos
  
- Si el usuario CORRIGE algo:
  * Ajusta el state_json en consecuencia
  * Explica brevemente el cambio

REGLAS CRÍTICAS:

✓ NUNCA inventes nombres de tablas o campos - usa SOLO los que existen en los datos
✓ Usa ÚNICAMENTE estas tablas: "Certificados" (recolección) y "Kardex" (movimientos/disposición)
✓ Mantén mensajes CORTOS y CLAROS, orientados a avanzar en la construcción de la consulta
✓ Actualiza SIEMPRE el state_json de manera consistente en cada turno

CAMPOS VÁLIDOS:

Tabla Certificados: pre_consecutivo, fechadevolucion, nombrecoordinador, rigidos, flexibles, metalicos, embalaje, total, municipiogenerador, municipiodevolucion, observaciones

Tabla Kardex: idkardex, fechakardex, TipoMovimiento, coordinador, MunicipioOrigen, Reciclaje, Incineración, PlasticoContaminado, Flexibles, Lonas, Carton, Metal, Total, CentrodeAcopio, gestor, Observaciones"""

    # Leer contexto de negocio adicional si existe
    business_context = ""
    try:
        with open('agent/system_prompt.txt', 'r', encoding='utf-8') as f:
            business_context = f.read()
    except FileNotFoundError:
        pass  # Opcional, continuar sin contexto adicional
    
    # Construir mensaje del usuario con contexto completo
    user_message = ""
    
    # Añadir contexto de conversación si existe
    if state.history:
        user_message += "=== CONTEXTO DE CONVERSACIÓN PREVIA ===\n"
        user_message += f"Estado actual: {state.get_context_summary()}\n\n"
        
        # Últimos 3 mensajes para contexto
        recent_history = state.history[-3:]
        for msg in recent_history:
            role_label = "Usuario" if msg["role"] == "user" else "Asistente"
            user_message += f"{role_label}: {msg['content']}\n"
        user_message += "\n"
    
    # State JSON actual (para que el agente lo actualice)
    user_message += "=== STATE JSON ACTUAL ===\n"
    user_message += json.dumps(state.to_dict(), indent=2, ensure_ascii=False)
    user_message += "\n\n"
    
    # Pregunta actual del usuario
    user_message += f"=== NUEVA PREGUNTA DEL USUARIO ===\n{question}\n\n"
    
    # Datos disponibles
    user_message += "=== DATOS DISPONIBLES ===\n"
    user_message += f"Tabla Certificados: {len(certificados)} registros\n"
    user_message += f"Tabla Kardex: {len(kardex)} registros\n\n"
    
    # Contexto de negocio adicional
    if business_context:
        user_message += "=== CONTEXTO DE NEGOCIO ===\n"
        user_message += business_context + "\n\n"
    
    user_message += """
RESPONDE CON:
1. Un mensaje_para_usuario claro y corto
2. El state_json actualizado según tu análisis

Formato de respuesta:
MENSAJE: [tu mensaje para el usuario]
STATE_JSON: [el state_json completo actualizado en formato JSON]
"""
    
    # Llamar a OpenAI con system message y user message
    try:
        client = OpenAI()
        response = client.responses.create(
            model="gpt-5.1",
            input=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_message}
            ]
        )
        
        respuesta_completa = response.output_text
        
        # Parsear respuesta para extraer mensaje y state actualizado
        # TODO: Implementar parsing estructurado de MENSAJE y STATE_JSON
        # Por ahora, usar la respuesta completa como mensaje
        mensaje_para_usuario = respuesta_completa
        
        # Actualizar estado de conversación
        state.add_message("agent", mensaje_para_usuario)
        
        # Por ahora marcamos como executed
        # TODO: Parsear el STATE_JSON de la respuesta y actualizar el state real
        state.mark_executed(result_summary=f"Procesó consulta de tipo {state.query.get('type', 'general')}")
        
        return mensaje_para_usuario, state
        
    except Exception as e:
        error_msg = f"Error al consultar OpenAI: {str(e)}"
        state.mark_executed(error=error_msg)
        return error_msg, state


# Mantener la función original para retrocompatibilidad
def run_agent(question: str, extra: Optional[dict] = None):
    """
    Versión sin contexto (legacy).
    Ejecuta el agente de Campolimpio con acceso a tablas Certificados y Kardex.
    
    Args:
        question: Pregunta del usuario
        extra: Datos adicionales opcionales (max_records, etc.)
    
    Returns:
        dict con 'success', 'response', 'error'
    """
    # Crear un estado temporal sin persistencia
    temp_state = ConversationState(user_id="legacy", conversation_id=f"legacy_{question[:20]}")
    temp_state.add_message("user", question)
    
    mensaje, updated_state = run_agent_with_context(question, temp_state, extra)
    
    if updated_state.execution["error"]:
        return {
            "success": False,
            "error": updated_state.execution["error"]
        }
    
    return {
        "success": True,
        "response": mensaje,
        "metadata": {
            "certificados_count": 100,
            "kardex_count": 100
        }
    }
