import os
from datetime import datetime
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader
from agent_core import run_agent
from agent_with_context import run_agent_with_context
from conversation_db import get_or_create_conversation, update_conversation
from conversation_state import ConversationStatus
from queries import execute_query_from_state

app = FastAPI()

# Configurar el entorno de Jinja2
env = Environment(loader=FileSystemLoader('plantillas'))

# Crear carpeta reportes si no existe
os.makedirs('reportes', exist_ok=True)

class ReporteData(BaseModel):
    nombre: str
    fecha: str
    municipio: str
    tipo_caso: str
    descripcion: str

@app.post("/reporte")
async def crear_reporte(data: ReporteData):
    # Imprimir el JSON recibido en consola
    print(data.model_dump())
    
    # Cargar la plantilla
    plantilla = env.get_template('reporte_basico.md.j2')
    
    # Renderizar la plantilla con los datos recibidos
    reporte_generado = plantilla.render(**data.model_dump())
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"reporte_{timestamp}.md"
    ruta_archivo = os.path.join('reportes', nombre_archivo)
    
    # Guardar el reporte en el archivo
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        f.write(reporte_generado)
    
    return {"status": "ok", "reporte": reporte_generado, "file": nombre_archivo}

class PreguntaData(BaseModel):
    question: str
    extra: dict = {}

class PreguntaConContextoData(BaseModel):
    question: str
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    extra: dict = {}

@app.post("/ask")
async def consultar_agente(data: PreguntaConContextoData):
    """
    Endpoint para consultar al agente IA con contexto de conversación.
    
    Recibe:
        - question: Pregunta del usuario
        - user_id: ID del usuario (ej. whatsapp:+573012345678 desde TextIt)
        - conversation_id: ID de la conversación (ej. ID del flujo en TextIt)
        - extra: Parámetros adicionales opcionales
    
    Devuelve:
        - message: Respuesta del agente para el usuario
        - state: Estado actualizado de la conversación (status, step, issues, etc.)
        - conversation_id: ID de la conversación (para referencia)
        - query_results: Resultados de la consulta (si se ejecutó)
    """
    # Generar user_id por defecto si no viene
    user_id = data.user_id or "default_user"
    
    # 1. Cargar o crear el estado de conversación desde la BD
    state = get_or_create_conversation(user_id, data.conversation_id)
    
    # 2. Actualizar el mensaje del usuario en el estado
    state.add_message("user", data.question)
    
    # 3. Ejecutar el agente con contexto
    mensaje_para_usuario, state_actualizado = run_agent_with_context(
        data.question,
        state,
        data.extra
    )
    
    # 4. Si el estado indica que la query está lista, ejecutarla
    query_summary = None
    query_records = None
    query_error = None
    
    if state_actualizado.conversation["status"] == ConversationStatus.READY_TO_EXECUTE.value:
        # Ejecutar la consulta a Airtable
        query_summary, query_records, query_error = execute_query_from_state(state_actualizado)
        
        # Actualizar el estado con los resultados
        if query_error:
            state_actualizado.execution["error"] = query_error
            state_actualizado.execution["result_summary"] = query_summary
        else:
            state_actualizado.execution["result_summary"] = query_summary
            state_actualizado.execution["last_run_at"] = datetime.utcnow().isoformat()
            state_actualizado.update_status(ConversationStatus.EXECUTED)
            
            # Agregar el resumen de resultados al mensaje del agente
            # (el agente ya dio su mensaje, ahora agregamos los resultados)
            if query_records is not None:
                mensaje_para_usuario = f"{mensaje_para_usuario}\n\n{query_summary}"
    
    # 5. Guardar el estado actualizado en la BD
    update_conversation(state_actualizado)
    
    # 6. Preparar respuesta para el cliente
    response = {
        "message": mensaje_para_usuario,
        "conversation_id": state_actualizado.meta["conversation_id"],
        "state": {
            "status": state_actualizado.conversation["status"],
            "step": state_actualizado.conversation["step"],
            "pending_question": state_actualizado.conversation["pending_question"],
            "query_type": state_actualizado.query["type"],
            "query_table": state_actualizado.query["table"],
            "filters": state_actualizado.query["filters"],
            "issues": state_actualizado.issues,
            "ready_to_execute": state_actualizado.execution["ready"],
            "execution": {
                "last_run_at": state_actualizado.execution.get("last_run_at"),
                "result_summary": state_actualizado.execution.get("result_summary"),
                "error": state_actualizado.execution.get("error")
            }
        }
    }
    
    # Agregar resultados de la query si se ejecutó
    if query_records is not None:
        response["query_results"] = {
            "summary": query_summary,
            "count": len(query_records),
            "records": query_records[:10]  # Limitar a 10 registros en la respuesta
        }
    
    return response

@app.post("/ask_legacy")
async def consultar_agente_legacy(data: PreguntaData):
    """Endpoint legacy sin contexto (retrocompatibilidad)"""
    result = run_agent(data.question, data.extra)
    return result

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

# Montar carpeta reportes como archivos estáticos
app.mount("/reportes", StaticFiles(directory="reportes"), name="reportes")
