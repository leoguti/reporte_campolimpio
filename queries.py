"""
Módulo para ejecutar consultas a Airtable basadas en el estado de conversación.
"""
import os
import requests
from typing import Dict, List, Any, Tuple, Optional
from conversation_state import ConversationState


def execute_query_from_state(state: ConversationState) -> Tuple[str, Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Ejecuta una consulta a Airtable basada en el estado de conversación validado.
    
    Esta función lee la información de state.query (tabla, filtros, campos, etc.)
    y construye la llamada apropiada a la API de Airtable. No modifica el estado;
    solo devuelve resultados y mensajes.
    
    Args:
        state: ConversationState ya validado con query.table, query.filters, etc.
    
    Returns:
        Tupla con tres elementos:
        - result_summary (str): Mensaje de texto para el usuario describiendo el resultado
        - records (List[Dict] | None): Lista de registros devueltos por Airtable, o None si hay error
        - error (str | None): Mensaje de error si algo falló, o None si todo bien
    
    Ejemplo:
        >>> state = ConversationState("user123")
        >>> state.query["table"] = "Certificados"
        >>> state.query["filters"] = {"coordinador": "Juan Pérez"}
        >>> state.validate_query()
        >>> summary, records, error = execute_query_from_state(state)
        >>> print(summary)
        'Encontré 12 registros de certificados para Juan Pérez.'
    
    Notas:
        - Requiere variables de entorno: AIRTABLE_API_KEY, AIRTABLE_BASE_ID
        - Si hay error de API, timeout, etc., captura la excepción y devuelve
          un result_summary amigable y un mensaje de error técnico
        - Los filtros en state.query.filters deben estar normalizados 
          (fechas en formato ISO, nombres exactos, etc.)
    """
    # Validar configuración
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    
    if not api_key:
        return (
            "Lo siento, hay un problema de configuración en el servidor (falta API key de Airtable).",
            None,
            "AIRTABLE_API_KEY no definida"
        )
    
    if not base_id:
        return (
            "Lo siento, hay un problema de configuración en el servidor (falta Base ID de Airtable).",
            None,
            "AIRTABLE_BASE_ID no definida"
        )
    
    # Extraer información de la query
    table_name = state.query.get("table")
    if not table_name:
        return (
            "No se puede ejecutar la consulta porque no se ha especificado la tabla.",
            None,
            "table no definida en state.query"
        )
    
    filters = state.query.get("filters", {})
    fields = state.query.get("fields", [])
    sort_config = state.query.get("sort", [])
    limit = state.query.get("limit", 100)
    
    try:
        # Construir URL
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        
        # Construir headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Construir parámetros
        params = {
            "maxRecords": limit
        }
        
        # Agregar filtros como fórmula de Airtable
        if filters:
            formula_parts = []
            for key, value in filters.items():
                # Construir condiciones según el tipo de filtro
                if key == "fecha_desde":
                    formula_parts.append(f"IS_AFTER({{fechadevolucion}}, '{value}')")
                elif key == "fecha_hasta":
                    formula_parts.append(f"IS_BEFORE({{fechadevolucion}}, '{value}')")
                elif key == "coordinador":
                    formula_parts.append(f"{{nombrecoordinador}}='{value}'")
                elif key == "municipio":
                    # Puede ser municipio generador o de devolución
                    formula_parts.append(
                        f"OR({{municipiogenerador}}='{value}', {{municipiodevolucion}}='{value}')"
                    )
                elif key == "municipio_generador":
                    formula_parts.append(f"{{municipiogenerador}}='{value}'")
                elif key == "municipio_devolucion":
                    formula_parts.append(f"{{municipiodevolucion}}='{value}'")
                else:
                    # Filtro genérico: buscar campo con el nombre del key
                    formula_parts.append(f"{{{key}}}='{value}'")
            
            # Combinar todas las partes con AND
            if formula_parts:
                if len(formula_parts) == 1:
                    params["filterByFormula"] = formula_parts[0]
                else:
                    params["filterByFormula"] = f"AND({', '.join(formula_parts)})"
        
        # Agregar campos específicos si están definidos
        if fields:
            # Airtable acepta fields[] como parámetro repetido
            for field in fields:
                params.setdefault("fields[]", []).append(field)
        
        # Agregar ordenamiento si está definido
        if sort_config:
            # Airtable acepta sort[0][field], sort[0][direction], etc.
            for i, sort_item in enumerate(sort_config):
                params[f"sort[{i}][field]"] = sort_item.get("field", "")
                params[f"sort[{i}][direction]"] = sort_item.get("direction", "asc")
        
        # Ejecutar la consulta
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        # Verificar respuesta
        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_message = error_json.get("error", {}).get("message", error_detail)
            except:
                error_message = error_detail
            
            return (
                f"Lo siento, hubo un problema al consultar la base de datos (código {response.status_code}). Por favor, intenta de nuevo más tarde.",
                None,
                f"Airtable API error {response.status_code}: {error_message}"
            )
        
        # Procesar resultados
        data = response.json()
        records = data.get("records", [])
        
        # Construir resumen para el usuario
        if not records:
            # Construir descripción de los filtros aplicados
            filter_description = _build_filter_description(filters)
            result_summary = f"No se encontraron registros en {table_name}"
            if filter_description:
                result_summary += f" con los filtros: {filter_description}"
            result_summary += "."
        else:
            count = len(records)
            filter_description = _build_filter_description(filters)
            
            # Personalizar mensaje según la tabla
            if table_name == "Certificados":
                result_summary = f"Encontré {count} certificado{'s' if count != 1 else ''} de recolección"
            elif table_name == "Kardex":
                result_summary = f"Encontré {count} registro{'s' if count != 1 else ''} de movimientos"
            else:
                result_summary = f"Encontré {count} registro{'s' if count != 1 else ''} en {table_name}"
            
            if filter_description:
                result_summary += f" que cumple{'n' if count != 1 else ''} con: {filter_description}"
            
            result_summary += "."
        
        # Devolver resultados
        return (result_summary, records, None)
        
    except requests.exceptions.Timeout:
        return (
            "Lo siento, la consulta está tardando demasiado. Por favor, intenta de nuevo o usa filtros más específicos.",
            None,
            "Timeout al consultar Airtable"
        )
    except requests.exceptions.ConnectionError:
        return (
            "Lo siento, no puedo conectarme a la base de datos en este momento. Por favor, verifica tu conexión a internet e intenta de nuevo.",
            None,
            "ConnectionError al consultar Airtable"
        )
    except Exception as e:
        return (
            "Lo siento, ocurrió un error inesperado al ejecutar la consulta. Por favor, intenta de nuevo.",
            None,
            f"Error inesperado: {type(e).__name__}: {str(e)}"
        )


def _build_filter_description(filters: Dict[str, Any]) -> str:
    """
    Construye una descripción legible de los filtros aplicados.
    
    Args:
        filters: Diccionario de filtros aplicados
    
    Returns:
        String con descripción amigable de los filtros
    """
    if not filters:
        return ""
    
    descriptions = []
    
    for key, value in filters.items():
        if key == "fecha_desde":
            descriptions.append(f"desde {value}")
        elif key == "fecha_hasta":
            descriptions.append(f"hasta {value}")
        elif key == "coordinador":
            descriptions.append(f"coordinador {value}")
        elif key == "municipio":
            descriptions.append(f"municipio {value}")
        elif key == "municipio_generador":
            descriptions.append(f"municipio generador {value}")
        elif key == "municipio_devolucion":
            descriptions.append(f"municipio de devolución {value}")
        else:
            descriptions.append(f"{key} = {value}")
    
    return ", ".join(descriptions)


def format_records_for_display(
    records: List[Dict[str, Any]], 
    table_name: str,
    format_type: str = "summary"
) -> str:
    """
    Formatea los registros de Airtable en un formato legible para el usuario.
    
    Args:
        records: Lista de registros devueltos por Airtable
        table_name: Nombre de la tabla ("Certificados" o "Kardex")
        format_type: Tipo de formato - "summary" (resumen), "detailed" (detallado), "json"
    
    Returns:
        String formateado con la información de los registros
    """
    if not records:
        return "No hay registros para mostrar."
    
    if format_type == "json":
        import json
        return json.dumps(records, indent=2, ensure_ascii=False)
    
    # Formato de resumen o detallado
    output_lines = []
    
    if table_name == "Certificados":
        for i, record in enumerate(records, 1):
            fields = record.get("fields", {})
            if format_type == "summary":
                output_lines.append(
                    f"{i}. {fields.get('pre_consecutivo', 'N/A')} - "
                    f"Coordinador: {fields.get('nombrecoordinador', 'N/A')} - "
                    f"Total: {fields.get('total', 0)} kg"
                )
            else:  # detailed
                output_lines.append(f"\n=== Certificado #{i} ===")
                output_lines.append(f"Consecutivo: {fields.get('pre_consecutivo', 'N/A')}")
                output_lines.append(f"Fecha devolución: {fields.get('fechadevolucion', 'N/A')}")
                output_lines.append(f"Coordinador: {fields.get('nombrecoordinador', 'N/A')}")
                output_lines.append(f"Municipio generador: {fields.get('municipiogenerador', 'N/A')}")
                output_lines.append(f"Municipio devolución: {fields.get('municipiodevolucion', 'N/A')}")
                output_lines.append(f"Materiales:")
                output_lines.append(f"  - Rígidos: {fields.get('rigidos', 0)} kg")
                output_lines.append(f"  - Flexibles: {fields.get('flexibles', 0)} kg")
                output_lines.append(f"  - Metálicos: {fields.get('metalicos', 0)} kg")
                output_lines.append(f"  - Embalaje: {fields.get('embalaje', 0)} kg")
                output_lines.append(f"Total: {fields.get('total', 0)} kg")
    
    elif table_name == "Kardex":
        for i, record in enumerate(records, 1):
            fields = record.get("fields", {})
            if format_type == "summary":
                output_lines.append(
                    f"{i}. {fields.get('idkardex', 'N/A')} - "
                    f"{fields.get('TipoMovimiento', 'N/A')} - "
                    f"Total: {fields.get('Total', 0)} kg"
                )
            else:  # detailed
                output_lines.append(f"\n=== Movimiento #{i} ===")
                output_lines.append(f"ID Kardex: {fields.get('idkardex', 'N/A')}")
                output_lines.append(f"Fecha: {fields.get('fechakardex', 'N/A')}")
                output_lines.append(f"Tipo movimiento: {fields.get('TipoMovimiento', 'N/A')}")
                output_lines.append(f"Coordinador: {fields.get('Name (from Coordinador)', 'N/A')}")
                output_lines.append(f"Municipio origen: {fields.get('MunicipioOrigen', 'N/A')}")
                output_lines.append(f"Centro de acopio: {fields.get('NombreCentrodeAcopio', 'N/A')}")
                output_lines.append(f"Gestor: {fields.get('nombregestor', 'N/A')}")
                output_lines.append(f"Disposición:")
                output_lines.append(f"  - Reciclaje: {fields.get('Reciclaje', 0)} kg")
                output_lines.append(f"  - Incineración: {fields.get('Incineración', 0)} kg")
                output_lines.append(f"  - Plástico contaminado: {fields.get('PlasticoContaminado', 0)} kg")
                output_lines.append(f"Materiales:")
                output_lines.append(f"  - Flexibles: {fields.get('Flexibles', 0)} kg")
                output_lines.append(f"  - Lonas: {fields.get('Lonas', 0)} kg")
                output_lines.append(f"  - Cartón: {fields.get('Carton', 0)} kg")
                output_lines.append(f"  - Metal: {fields.get('Metal', 0)} kg")
                output_lines.append(f"Total: {fields.get('Total', 0)} kg")
    else:
        # Tabla desconocida - formato genérico
        for i, record in enumerate(records, 1):
            fields = record.get("fields", {})
            output_lines.append(f"\n=== Registro #{i} ===")
            for key, value in fields.items():
                output_lines.append(f"{key}: {value}")
    
    return "\n".join(output_lines)
