"""
Definición de las herramientas (tools) para Function Calling de OpenAI
"""

# Herramienta 1: Actualizar estado de la consulta
TOOL_UPDATE_QUERY_STATE = {
    "type": "function",
    "function": {
        "name": "update_query_state",
        "description": """Actualiza el estado de la consulta cuando identificas parámetros suficientes del usuario.
        
Llama esta función cuando:
- Identifiques la tabla a consultar (Certificados o Kardex)
- El usuario especifique filtros (coordinador, fecha, municipio, etc.)
- Determines el tipo de consulta (listado detallado, consolidado, ranking)
- Tengas TODA la información necesaria para ejecutar (marca ready_to_execute=true)

IMPORTANTE: Solo marca ready_to_execute=true cuando tengas:
1. Tabla definida
2. Al menos UN filtro significativo O sea un query agregado (consolidado/ranking)
3. El usuario haya confirmado o dado toda la información""",
        "parameters": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "enum": ["Certificados", "Kardex"],
                    "description": "Tabla de Airtable a consultar"
                },
                "query_type": {
                    "type": "string",
                    "enum": ["listado_detallado", "consolidado", "ranking", "analisis"],
                    "description": "Tipo de consulta que el usuario quiere"
                },
                "filters": {
                    "type": "object",
                    "properties": {
                        "coordinador": {
                            "type": "string",
                            "description": "Nombre del coordinador a filtrar"
                        },
                        "fecha_desde": {
                            "type": "string",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                            "description": "Fecha inicio en formato YYYY-MM-DD"
                        },
                        "fecha_hasta": {
                            "type": "string",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                            "description": "Fecha fin en formato YYYY-MM-DD"
                        },
                        "municipio": {
                            "type": "string",
                            "description": "Municipio a filtrar"
                        },
                        "municipio_generador": {
                            "type": "string",
                            "description": "Municipio generador (Certificados)"
                        },
                        "municipio_devolucion": {
                            "type": "string",
                            "description": "Municipio devolución (Certificados)"
                        },
                        "tipo_movimiento": {
                            "type": "string",
                            "enum": ["ENTRADA", "SALIDA", "TRANSFERENCIA"],
                            "description": "Tipo de movimiento (Kardex)"
                        }
                    },
                    "description": "Filtros a aplicar en la consulta"
                },
                "ready_to_execute": {
                    "type": "boolean",
                    "description": "True solo cuando tengas TODA la información necesaria y el usuario haya confirmado"
                }
            },
            "required": ["table"]
        }
    }
}

# Herramienta 2: Ejecutar consulta en Airtable
TOOL_EXECUTE_QUERY = {
    "type": "function",
    "function": {
        "name": "execute_airtable_query",
        "description": """Ejecuta la consulta en Airtable con los parámetros del estado actual.
        
Llama esta función SOLO cuando:
- El estado de la consulta esté marcado como ready_to_execute=true
- El usuario haya dado confirmación final
- Tengas todos los parámetros necesarios

Esta función ejecutará la consulta real y retornará los resultados de Airtable.""",
        "parameters": {
            "type": "object",
            "properties": {
                "confirm": {
                    "type": "boolean",
                    "description": "Confirmación de que se debe ejecutar ahora"
                }
            },
            "required": ["confirm"]
        }
    }
}

# Herramienta 3: Registrar issue o problema (opcional, para logging)
TOOL_REPORT_ISSUE = {
    "type": "function",
    "function": {
        "name": "report_issue",
        "description": """Registra un problema o ambigüedad en la solicitud del usuario.
        
Usa esta función cuando:
- Falte información crítica
- El usuario pida algo imposible con los datos disponibles
- Haya ambigüedad que requiera clarificación""",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_type": {
                    "type": "string",
                    "enum": ["missing_filter", "invalid_field", "ambiguous_request", "impossible_request"],
                    "description": "Tipo de problema detectado"
                },
                "field": {
                    "type": "string",
                    "description": "Campo relacionado con el problema (si aplica)"
                },
                "message": {
                    "type": "string",
                    "description": "Descripción del problema para el log"
                }
            },
            "required": ["issue_type", "message"]
        }
    }
}

# Lista de todas las herramientas
ALL_TOOLS = [
    TOOL_UPDATE_QUERY_STATE,
    TOOL_EXECUTE_QUERY,
    TOOL_REPORT_ISSUE
]
