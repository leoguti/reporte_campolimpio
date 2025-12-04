import os
from datetime import datetime
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader
from agent_core import run_agent
from agent_with_context import run_agent_with_context
from agent_with_function_calling import run_agent_with_function_calling
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
    
    # 3. Ejecutar el agente con Function Calling
    mensaje_para_usuario, state_actualizado = run_agent_with_function_calling(
        data.question,
        state,
        data.extra
    )
    
    # 4. Guardar el estado actualizado en la BD (después de OpenAI)
    update_conversation(state_actualizado)
    
    # NOTA: La ejecución automática ya NO es necesaria aquí
    # porque el agente con Function Calling ejecuta directamente
    # cuando llama a execute_airtable_query()
            
            # Agregar sugerencia para ajustar filtros
            if query_records is not None and len(query_records) > 0:
                mensaje_para_usuario += "\n\nSi quieres cambiar algún filtro o ver algo más específico, dime qué deseas ajustar."
        
        # Guardar estado actualizado con la información de ejecución
        update_conversation(state_actualizado)
    
    # 6. Preparar respuesta para el cliente
    # Indicador 'done': True cuando la consulta ya se ejecutó (ready=True y last_run_at no es None)
    # Útil para clientes como TextIt para decidir si continuar preguntando o cerrar el flujo
    done = (state_actualizado.execution["ready"] and 
            state_actualizado.execution.get("last_run_at") is not None)
    
    response = {
        "message": mensaje_para_usuario,
        "done": done,
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
