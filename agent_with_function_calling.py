"""
Agente conversacional con Function Calling para construir y ejecutar consultas
"""
import os
import json
from typing import Optional, Tuple
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from conversation_state import ConversationState, ConversationStatus
from agent_tools import ALL_TOOLS
from queries import execute_query_from_state


def run_agent_with_function_calling(
    question: str,
    state: ConversationState,
    extra: Optional[dict] = None
) -> Tuple[str, ConversationState]:
    """
    Ejecuta el agente usando Function Calling de OpenAI.
    
    Args:
        question: Pregunta del usuario
        state: Estado actual de la conversación
        extra: Datos adicionales opcionales
    
    Returns:
        Tupla (mensaje_para_usuario, state_actualizado)
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return "Error: OpenAI no configurado", state
    
    client = OpenAI(api_key=openai_key)
    
    # Cargar system prompt
    system_prompt_path = os.path.join(os.path.dirname(__file__), "agent", "system_prompt.txt")
    try:
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        system_prompt = """Eres un asistente que ayuda a construir consultas a la base de datos de Campolimpio.
        
Usa las funciones disponibles para:
1. Actualizar el estado de la consulta (update_query_state)
2. Ejecutar la consulta cuando esté lista (execute_airtable_query)
3. Reportar problemas (report_issue)

Sé claro y conciso. Pregunta solo lo necesario."""
    
    # Agregar contexto del estado actual
    state_context = f"""

ESTADO ACTUAL DE LA CONSULTA:
- Tabla: {state.query.get('table', 'No definida')}
- Tipo: {state.query.get('type', 'No definido')}
- Filtros: {json.dumps(state.query.get('filters', {}), indent=2)}
- Estado: {state.conversation['status']}
- Lista para ejecutar: {state.execution['ready']}
"""
    
    full_system_prompt = system_prompt + state_context
    
    # Agregar mensaje del usuario al historial
    state.add_message("user", question)
    
    # Construir mensajes para OpenAI
    messages = [
        {"role": "system", "content": full_system_prompt}
    ]
    
    # Agregar historial (últimos 10 mensajes para no exceder límite)
    for msg in state.history[-10:]:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    try:
        # Llamar a OpenAI con Function Calling
        response = client.chat.completions.create(
            model="gpt-4o",  # Modelo que soporta function calling
            messages=messages,
            tools=ALL_TOOLS,
            tool_choice="auto"  # El modelo decide si llamar funciones
        )
        
        message = response.choices[0].message
        assistant_message = message.content or ""
        
        # Procesar function calls si existen
        if message.tool_calls:
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"[Function Call] {function_name}: {arguments}")
                
                if function_name == "update_query_state":
                    # Actualizar estado de la consulta
                    if "table" in arguments:
                        state.query["table"] = arguments["table"]
                    
                    if "query_type" in arguments:
                        state.query["type"] = arguments["query_type"]
                    
                    if "filters" in arguments:
                        state.query["filters"].update(arguments["filters"])
                    
                    if "ready_to_execute" in arguments:
                        state.execution["ready"] = arguments["ready_to_execute"]
                        if arguments["ready_to_execute"]:
                            state.update_status(ConversationStatus.READY_TO_EXECUTE)
                        else:
                            state.update_status(ConversationStatus.BUILDING)
                
                elif function_name == "execute_airtable_query":
                    # Ejecutar la consulta
                    if arguments.get("confirm"):
                        query_summary, query_records, query_error = execute_query_from_state(state)
                        
                        state.execution["last_run_at"] = datetime.utcnow().isoformat()
                        
                        if query_error:
                            state.execution["error"] = query_error
                            assistant_message += f"\n\n{query_summary}"
                        else:
                            state.execution["result_summary"] = query_summary
                            assistant_message += f"\n\n{query_summary}"
                            
                            if query_records:
                                assistant_message += "\n\nSi quieres cambiar algún filtro o ver algo más específico, dime qué deseas ajustar."
                        
                        state.update_status(ConversationStatus.EXECUTED)
                
                elif function_name == "report_issue":
                    # Registrar issue
                    issue = {
                        "type": arguments["issue_type"],
                        "field": arguments.get("field"),
                        "message": arguments["message"],
                        "detected_at": datetime.utcnow().isoformat()
                    }
                    state.issues.append(issue)
                    state.update_status(ConversationStatus.AWAITING_CLARIFICATION)
        
        # Agregar respuesta del agente al historial
        state.add_message("agent", assistant_message)
        
        return assistant_message, state
    
    except Exception as e:
        error_msg = f"Error en OpenAI: {str(e)}"
        print(f"[Error] {error_msg}")
        state.add_message("agent", f"Disculpa, tuve un error técnico: {str(e)}")
        return f"Error: {str(e)}", state
