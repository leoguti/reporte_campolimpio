# Suite de Tests - Endpoint /api/ask

Este archivo documenta los escenarios de prueba para el endpoint `/api/ask` y cómo ejecutarlos.

## Configuración de Tests

Para configurar los estados de prueba en la base de datos:

```bash
# En el servidor de producción
cd /opt/reporte_campolimpio
export $(grep -v '^#' .env | xargs)
.venv/bin/python test_scenarios.py
```

Este script crea 4 conversaciones de prueba en diferentes estados.

## Escenarios de Prueba

### ✅ CASO A: Estado con Issues (done=False)

**Escenario:** Conversación con filtros faltantes que requiere aclaraciones.

**Estado configurado:**
- `user_id`: `test_case_a`
- `conversation_id`: `test_case_a_001`
- `status`: `awaiting_clarification`
- `issues`: 1 (missing_filter)
- `ready`: `False`
- `last_run_at`: `None`

**Resultado esperado:**
- ✓ `done = False`
- ✓ `message` = petición de aclaraciones
- ✓ `status` = `awaiting_clarification`
- ✓ `execution.last_run_at` = `null`

**Comando de prueba:**
```bash
curl -X POST https://campolimpio.rumbo.digital/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quiero ver certificados",
    "user_id": "test_case_a",
    "conversation_id": "test_case_a_001"
  }' | jq '{
    done: .done,
    status: .state.status,
    issues: .state.issues | length,
    ready: .state.ready_to_execute,
    message: .message[:150]
  }'
```

**Resultado real:**
```json
{
  "done": false,
  "status": "awaiting_clarification",
  "issues": 1,
  "ready": false,
  "message": "Para poder mostrarte los certificados necesito..."
}
```

---

### ✅ CASO B: Ready to Execute (done=True)

**Escenario:** Consulta lista con toda la información necesaria.

**Estado configurado:**
- `user_id`: `test_case_b`
- `conversation_id`: `test_case_b_001`
- `status`: `ready_to_execute`
- `query.table`: `Certificados`
- `query.filters`: `{"coordinador": "Andrés Felipe Ramirez"}`
- `ready`: `True`
- `last_run_at`: `None`

**Resultado esperado:**
- ✓ Sistema ejecuta `execute_query_from_state` automáticamente
- ✓ `done = True` (después de ejecutar)
- ✓ `message` = resumen de resultados
- ✓ `status` = `executed`
- ✓ `execution.last_run_at` = timestamp
- ✓ `execution.result_summary` = texto legible

**Comando de prueba:**
```bash
curl -X POST https://campolimpio.rumbo.digital/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Ejecuta la consulta",
    "user_id": "test_case_b",
    "conversation_id": "test_case_b_001"
  }' | jq '{
    done: .done,
    status: .state.status,
    ready: .state.ready_to_execute,
    last_run: .state.execution.last_run_at,
    result_summary: .state.execution.result_summary[:100],
    message: .message[:150]
  }'
```

**Resultado real:**
```json
{
  "done": true,
  "status": "executed",
  "ready": true,
  "last_run": "2025-12-03T19:07:04.130612",
  "result_summary": "Encontré 5 certificados de recolección...",
  "message": "Encontré 5 certificados de recolección..."
}
```

---

### ✅ CASO C: Error de Airtable (done=True con error)

**Escenario:** Query lista pero con tabla que no existe o error de API.

**Estado configurado:**
- `user_id`: `test_case_c`
- `conversation_id`: `test_case_c_001`
- `status`: `ready_to_execute`
- `query.table`: `TablaQueNoExiste`
- `ready`: `True`
- `last_run_at`: `None`

**Resultado esperado:**
- ✓ Sistema intenta ejecutar pero falla
- ✓ `done = True` (se intentó ejecutar)
- ✓ `message` = mensaje de error amigable para el usuario
- ✓ `execution.error` = mensaje técnico del error
- ✓ `execution.result_summary` = mensaje amigable

**Comando de prueba:**
```bash
curl -X POST https://campolimpio.rumbo.digital/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Ejecuta la consulta",
    "user_id": "test_case_c",
    "conversation_id": "test_case_c_001"
  }' | jq '{
    done: .done,
    status: .state.status,
    has_error: (.state.execution.error != null),
    error: .state.execution.error[:100],
    result_summary: .state.execution.result_summary,
    message: .message[:200]
  }'
```

**Resultado real:**
```json
{
  "done": true,
  "status": "ready_to_execute",
  "has_error": true,
  "error": "Airtable API error 403: Invalid permissions...",
  "result_summary": "Lo siento, hubo un problema al consultar la base de datos...",
  "message": "Lo siento, hubo un problema al consultar la base de datos..."
}
```

---

### ✅ CASO BONUS: Prevención de Re-ejecución (done=True)

**Escenario:** Consulta ya ejecutada previamente.

**Estado configurado:**
- `user_id`: `test_case_bonus`
- `conversation_id`: `test_case_bonus_001`
- `status`: `executed`
- `ready`: `True`
- `last_run_at`: `<timestamp>` (YA TIENE VALOR)
- `result_summary`: `"Encontré 5 certificados..."`

**Resultado esperado:**
- ✓ `done = True` (desde el inicio)
- ✓ NO ejecuta de nuevo (condición `last_run_at != None` no se cumple)
- ✓ `message` = respuesta contextual de OpenAI
- ✓ `execution.last_run_at` = mantiene timestamp original

**Comando de prueba:**
```bash
curl -X POST https://campolimpio.rumbo.digital/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuántos certificados había?",
    "user_id": "test_case_bonus",
    "conversation_id": "test_case_bonus_001"
  }' | jq '{
    done: .done,
    status: .state.status,
    last_run: .state.execution.last_run_at,
    message: .message[:150]
  }'
```

**Resultado real:**
```json
{
  "done": true,
  "status": "ready_to_execute",
  "last_run": "2025-12-03T19:06:22.081766",
  "message": "En la consulta anterior, con el filtro aplicado..."
}
```

---

## Resumen de Comportamiento

| Escenario | `ready` | `last_run_at` | `done` | Acción |
|-----------|---------|---------------|--------|---------|
| **Caso A** | `false` | `null` | `false` | Pedir aclaraciones |
| **Caso B** | `true` | `null` | `true` | Ejecutar query automáticamente |
| **Caso C** | `true` | `null` (error) | `true` | Intentar ejecutar, capturar error |
| **Bonus** | `true` | `<timestamp>` | `true` | NO re-ejecutar, usar contexto |

## Lógica de Decisión en el Endpoint

```python
# En server.py, línea ~95-125
if state.execution["ready"] and state.execution["last_run_at"] is None:
    # EJECUTAR QUERY AUTOMÁTICAMENTE
    query_summary, query_records, query_error = execute_query_from_state(state)
    
    state.execution["last_run_at"] = datetime.utcnow().isoformat()
    
    if query_error:
        # CASO C: Error
        state.execution["error"] = query_error
        mensaje_para_usuario = query_summary  # Mensaje amigable
    else:
        # CASO B: Éxito
        state.execution["result_summary"] = query_summary
        state.update_status(ConversationStatus.EXECUTED)
        mensaje_para_usuario = query_summary + sugerencia
else:
    # CASO A o BONUS: No ejecutar
    # Usar mensaje de OpenAI (aclaración o contexto)
```

## Cálculo del Campo `done`

```python
# En server.py, línea ~130
done = (state.execution["ready"] and 
        state.execution.get("last_run_at") is not None)
```

**Significado:**
- `done=True`: La consulta fue ejecutada (o intentada). El flujo puede cerrarse.
- `done=False`: Todavía en fase de construcción de query. Continuar conversación.

## Integración con TextIt

```python
# Pseudocódigo para flujo de TextIt
response = call_api("/api/ask", {
    "question": user_message,
    "user_id": contact.urns.whatsapp,
    "conversation_id": run.uuid
})

if response["done"]:
    # Mostrar resultado final
    send_message(response["message"])
    complete_flow()
else:
    # Continuar conversación
    send_message(response["message"])
    wait_for_reply()
```

## Ejecución de Tests

```bash
# 1. Configurar estados de prueba
ssh leonardo@campolimpio.rumbo.digital "cd /opt/reporte_campolimpio && export \$(grep -v '^#' .env | xargs) && .venv/bin/python test_scenarios.py"

# 2. Ejecutar pruebas con curl (copiar comandos de arriba)

# 3. Limpiar conversaciones de prueba (opcional)
ssh leonardo@campolimpio.rumbo.digital "cd /opt/reporte_campolimpio && export \$(grep -v '^#' .env | xargs) && .venv/bin/python -c \"
from conversation_db import SessionLocal, Conversation
db = SessionLocal()
db.query(Conversation).filter(Conversation.user_id.like('test_%')).delete()
db.commit()
print('Conversaciones de prueba eliminadas')
\""
```

## Verificación Rápida

Para verificar rápidamente todos los casos:

```bash
# Test completo
for case in test_case_a test_case_b test_case_c test_case_bonus; do
  echo "=== Testing $case ==="
  curl -s -X POST https://campolimpio.rumbo.digital/api/ask \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"Test\", \"user_id\": \"$case\", \"conversation_id\": \"${case}_001\"}" \
    | jq '{done: .done, status: .state.status}'
  echo
done
```

## Notas

- Los tests están diseñados para ejecutarse en producción contra la base de datos real
- Cada caso crea un estado específico en la BD que simula diferentes situaciones
- El campo `done` es crítico para que clientes externos sepan cuándo terminar el flujo
- Todos los errores se manejan de forma amigable para el usuario final
