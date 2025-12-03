# Módulo de Queries - Documentación

## Descripción General

El módulo `queries.py` proporciona funcionalidad para ejecutar consultas a Airtable basadas en el estado de conversación validado. Este módulo se integra con el sistema de contexto de conversación para ejecutar queries automáticamente cuando están listas.

## Función Principal: `execute_query_from_state`

### Propósito

Esta función lee la información del estado de conversación (`ConversationState`) y ejecuta la consulta correspondiente en Airtable. No modifica el estado; solo devuelve resultados y mensajes.

### Firma

```python
def execute_query_from_state(state: ConversationState) -> Tuple[str, Optional[List[Dict[str, Any]]], Optional[str]]
```

### Parámetros

- **state** (`ConversationState`): Estado de conversación ya validado que debe contener:
  - `state.query["table"]`: Nombre de la tabla de Airtable ("Certificados" o "Kardex")
  - `state.query["filters"]`: Diccionario de filtros normalizados
  - `state.query["fields"]`: Lista de campos a traer (opcional)
  - `state.query["sort"]`: Configuración de ordenamiento (opcional)
  - `state.query["limit"]`: Límite de registros (default: 100)

### Retorno

Tupla con tres elementos:

1. **result_summary** (`str`): Mensaje de texto para el usuario describiendo el resultado
   - Ejemplo: "Encontré 12 certificados de recolección que cumplen con: coordinador Andrés Felipe Ramirez."
   - Ejemplo: "No se encontraron registros en Certificados con los filtros: coordinador TEST."

2. **records** (`List[Dict] | None`): Lista de registros devueltos por Airtable, o `None` si hay error
   - Cada registro contiene `id`, `fields`, `createdTime`

3. **error** (`str | None`): Mensaje de error técnico si algo falló, o `None` si todo bien
   - Usado para guardar en `state.execution["error"]`

### Filtros Soportados

La función construye automáticamente fórmulas de Airtable basadas en los filtros:

| Filtro | Campo Airtable | Ejemplo |
|--------|----------------|---------|
| `fecha_desde` | `fechadevolucion` | `IS_AFTER({fechadevolucion}, '2024-01-01')` |
| `fecha_hasta` | `fechadevolucion` | `IS_BEFORE({fechadevolucion}, '2024-12-31')` |
| `coordinador` | `nombrecoordinador` | `{nombrecoordinador}='Andrés Felipe Ramirez'` |
| `municipio` | `municipiogenerador`, `municipiodevolucion` | `OR({municipiogenerador}='Bogotá', {municipiodevolucion}='Bogotá')` |
| `municipio_generador` | `municipiogenerador` | `{municipiogenerador}='Bogotá'` |
| `municipio_devolucion` | `municipiodevolucion` | `{municipiodevolucion}='Medellín'` |

### Ejemplo de Uso

```python
from conversation_state import ConversationState
from queries import execute_query_from_state

# Crear y configurar estado
state = ConversationState("user123")
state.query["table"] = "Certificados"
state.query["filters"] = {
    "coordinador": "Andrés Felipe Ramirez",
    "fecha_desde": "2024-01-01"
}
state.query["limit"] = 50
state.validate_query()

# Ejecutar consulta
summary, records, error = execute_query_from_state(state)

if error:
    print(f"Error: {error}")
    state.execution["error"] = error
else:
    print(f"Resumen: {summary}")
    print(f"Registros obtenidos: {len(records)}")
    state.execution["result_summary"] = summary
    state.execution["last_run_at"] = datetime.utcnow().isoformat()
```

## Integración con Server API

El endpoint `/api/ask` ejecuta automáticamente las consultas cuando el estado es `READY_TO_EXECUTE`:

```python
# En server.py
if state_actualizado.conversation["status"] == ConversationStatus.READY_TO_EXECUTE.value:
    query_summary, query_records, query_error = execute_query_from_state(state_actualizado)
    
    if query_error:
        state_actualizado.execution["error"] = query_error
    else:
        state_actualizado.update_status(ConversationStatus.EXECUTED)
        mensaje_para_usuario = f"{mensaje_para_usuario}\n\n{query_summary}"
```

### Respuesta del Endpoint

Cuando se ejecuta una query, el endpoint devuelve:

```json
{
  "message": "Respuesta del agente + resumen de resultados",
  "conversation_id": "uuid-123",
  "state": {
    "status": "executed",
    "query_table": "Certificados",
    "filters": {"coordinador": "Andrés Felipe Ramirez"},
    "execution": {
      "last_run_at": "2024-12-03T17:30:00Z",
      "result_summary": "Encontré 5 certificados...",
      "error": null
    }
  },
  "query_results": {
    "summary": "Encontré 5 certificados de recolección...",
    "count": 5,
    "records": [...]  // Máximo 10 registros
  }
}
```

## Función Auxiliar: `format_records_for_display`

Formatea los registros de Airtable en un formato legible para el usuario.

### Firma

```python
def format_records_for_display(
    records: List[Dict[str, Any]], 
    table_name: str,
    format_type: str = "summary"
) -> str
```

### Parámetros

- **records**: Lista de registros devueltos por Airtable
- **table_name**: "Certificados" o "Kardex"
- **format_type**: 
  - `"summary"`: Formato compacto (una línea por registro)
  - `"detailed"`: Formato completo con todos los campos
  - `"json"`: JSON formateado

### Ejemplo

```python
from queries import format_records_for_display

# Formato resumen
print(format_records_for_display(records, "Certificados", "summary"))
# Output:
# 1. 30962 - Coordinador: Andrés Felipe Ramirez - Total: 85.25 kg
# 2. 13184 - Coordinador: Andrea Villarraga - Total: 400 kg

# Formato detallado
print(format_records_for_display(records, "Certificados", "detailed"))
# Output:
# === Certificado #1 ===
# Consecutivo: 30962
# Fecha devolución: 2024-01-15
# ...
```

## Manejo de Errores

La función captura y maneja diferentes tipos de errores:

### Errores de Configuración

```python
# AIRTABLE_API_KEY no definida
return (
    "Lo siento, hay un problema de configuración en el servidor...",
    None,
    "AIRTABLE_API_KEY no definida"
)
```

### Errores de API

```python
# Error 400, 403, 404, 500, etc.
return (
    "Lo siento, hubo un problema al consultar la base de datos...",
    None,
    "Airtable API error 403: Invalid API key"
)
```

### Timeout

```python
return (
    "Lo siento, la consulta está tardando demasiado...",
    None,
    "Timeout al consultar Airtable"
)
```

### Error de Conexión

```python
return (
    "Lo siento, no puedo conectarme a la base de datos en este momento...",
    None,
    "ConnectionError al consultar Airtable"
)
```

## Variables de Entorno Requeridas

```bash
AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

## Pruebas

### Ejecutar pruebas unitarias

```bash
# Cargar variables de entorno y ejecutar pruebas
export $(grep -v '^#' .env | xargs)
python test_queries.py
```

### Ejecutar pruebas de integración

```bash
# Asegurarse de que el servidor esté corriendo
./deploy.sh

# En otra terminal
python test_integration_queries.py
```

## Próximos Pasos (TODO)

1. **Parsing de STATE_JSON**: Implementar extracción y parseo del STATE_JSON de las respuestas de OpenAI para actualizar dinámicamente el estado de conversación
2. **Análisis de datos**: Agregar funcionalidad para analizar los resultados y generar insights automáticos
3. **Exportación**: Permitir exportar resultados en diferentes formatos (CSV, Excel, PDF)
4. **Cache**: Implementar cache para consultas repetidas
5. **Paginación**: Manejar consultas con muchos resultados (>100 registros)
