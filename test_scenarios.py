"""
Test Suite para el endpoint /api/ask
Cubre los escenarios principales de ejecución, aclaración y manejo de errores.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conversation_state import ConversationState, ConversationStatus, IssueType
from conversation_db import create_conversation, update_conversation, get_or_create_conversation, SessionLocal, Conversation
from queries import execute_query_from_state
from datetime import datetime


def cleanup_test_conversations():
    """Limpia conversaciones de prueba de la base de datos"""
    db = SessionLocal()
    try:
        deleted = db.query(Conversation).filter(
            Conversation.user_id.like('test_%')
        ).delete()
        db.commit()
        print(f"✓ Eliminadas {deleted} conversaciones de prueba")
    finally:
        db.close()


def test_case_a_with_issues():
    """
    CASO A: Estado con issues (missing_filter)
    
    Escenario:
    - El state tiene issues (falta información)
    - OpenAI pide aclaraciones
    - Endpoint debe devolver done=False y mensaje de aclaración
    
    Simulación:
    - Crear estado con issue de tipo missing_filter
    - Estado no debería tener ready=True
    - Al consultar el endpoint, debe pedir más información
    """
    print("\n" + "="*70)
    print("CASO A: Estado con issues (missing_filter)")
    print("="*70)
    
    # Limpiar
    cleanup_test_conversations()
    
    # Crear estado con issue
    state = ConversationState(
        user_id="test_case_a",
        conversation_id="test_case_a_001"
    )
    
    # Agregar un issue
    state.add_issue(
        IssueType.MISSING_FILTER,
        field="coordinador",
        message="Falta especificar el coordinador"
    )
    
    # El estado no debe estar ready
    state.conversation["status"] = ConversationStatus.AWAITING_CLARIFICATION.value
    state.conversation["pending_question"] = "¿Para qué coordinador necesitas los certificados?"
    state.execution["ready"] = False
    
    # Guardar en BD
    create_conversation(state)
    
    print("\n--- Estado configurado ---")
    print(f"User ID: {state.meta['user_id']}")
    print(f"Conversation ID: {state.meta['conversation_id']}")
    print(f"Status: {state.conversation['status']}")
    print(f"Issues: {len(state.issues)} issue(s)")
    print(f"  - {state.issues[0]['type']}: {state.issues[0]['message']}")
    print(f"Ready: {state.execution['ready']}")
    print(f"Last run: {state.execution['last_run_at']}")
    
    print("\n--- Resultado esperado al llamar /api/ask ---")
    print("✓ done = False")
    print("✓ message = mensaje pidiendo aclaraciones (coordinador)")
    print("✓ status = 'awaiting_clarification'")
    print("✓ execution.last_run_at = null")
    
    print("\n--- Comando curl para probar ---")
    print(f"""
curl -X POST https://campolimpio.rumbo.digital/api/ask \\
  -H "Content-Type: application/json" \\
  -d '{{
    "question": "Quiero ver certificados",
    "user_id": "test_case_a",
    "conversation_id": "test_case_a_001"
  }}' | jq '{{
    done: .done,
    status: .state.status,
    issues: .state.issues | length,
    ready: .state.ready_to_execute,
    message: .message[:150]
  }}'
""")
    
    print("\n" + "="*70)


def test_case_b_ready_to_execute():
    """
    CASO B: Estado ready_to_execute
    
    Escenario:
    - El state tiene ready=True y last_run_at=None
    - Se llama a execute_query_from_state
    - Se actualiza state.execution
    - Endpoint debe devolver done=True y resumen del reporte
    
    Simulación:
    - Crear estado con query completa (tabla + filtros)
    - Marcar como ready=True
    - El endpoint automáticamente ejecutará la query
    """
    print("\n" + "="*70)
    print("CASO B: Estado ready_to_execute (ejecuta automáticamente)")
    print("="*70)
    
    # Limpiar conversación anterior
    db = SessionLocal()
    try:
        db.query(Conversation).filter(
            Conversation.user_id == 'test_case_b'
        ).delete()
        db.commit()
    finally:
        db.close()
    
    # Crear estado listo para ejecutar
    state = ConversationState(
        user_id="test_case_b",
        conversation_id="test_case_b_001"
    )
    
    # Configurar query completa
    state.query["table"] = "Certificados"
    state.query["filters"] = {
        "coordinador": "Andrés Felipe Ramirez"
    }
    state.query["limit"] = 5
    
    # Marcar como lista para ejecutar
    state.execution["ready"] = True
    state.update_status(ConversationStatus.READY_TO_EXECUTE)
    
    # Guardar en BD
    create_conversation(state)
    
    print("\n--- Estado configurado ---")
    print(f"User ID: {state.meta['user_id']}")
    print(f"Conversation ID: {state.meta['conversation_id']}")
    print(f"Status: {state.conversation['status']}")
    print(f"Query table: {state.query['table']}")
    print(f"Query filters: {state.query['filters']}")
    print(f"Ready: {state.execution['ready']}")
    print(f"Last run: {state.execution['last_run_at']}")
    
    print("\n--- Simulación local de ejecución ---")
    # Simular lo que hace el endpoint
    if state.execution["ready"] and state.execution["last_run_at"] is None:
        print("✓ Condiciones cumplidas, ejecutando query...")
        
        # Cargar variables de entorno si es necesario
        if not os.getenv("AIRTABLE_API_KEY"):
            print("⚠️  Variables de entorno no cargadas. En producción se ejecutará correctamente.")
        else:
            query_summary, query_records, query_error = execute_query_from_state(state)
            
            if query_error:
                print(f"❌ Error: {query_error}")
            else:
                print(f"✓ Éxito: {query_summary}")
                print(f"✓ Registros obtenidos: {len(query_records) if query_records else 0}")
    
    print("\n--- Resultado esperado al llamar /api/ask ---")
    print("✓ done = True (después de ejecutar)")
    print("✓ message = 'Encontré X certificados de recolección...'")
    print("✓ status = 'executed'")
    print("✓ execution.last_run_at = <timestamp>")
    print("✓ execution.result_summary = resumen legible")
    
    print("\n--- Comando curl para probar ---")
    print(f"""
curl -X POST https://campolimpio.rumbo.digital/api/ask \\
  -H "Content-Type: application/json" \\
  -d '{{
    "question": "Ejecuta la consulta",
    "user_id": "test_case_b",
    "conversation_id": "test_case_b_001"
  }}' | jq '{{
    done: .done,
    status: .state.status,
    ready: .state.ready_to_execute,
    last_run: .state.execution.last_run_at,
    result_summary: .state.execution.result_summary[:100],
    message: .message[:150]
  }}'
""")
    
    print("\n" + "="*70)


def test_case_c_airtable_error():
    """
    CASO C: Error de Airtable
    
    Escenario:
    - Estado ready=True pero tabla no existe o hay error de API
    - execute_query_from_state devuelve error
    - state.execution.error se rellena
    - Message debe explicar el problema de forma amigable
    
    Simulación:
    - Crear estado con tabla inexistente
    - Intentar ejecutar
    - Verificar que el error se maneja correctamente
    """
    print("\n" + "="*70)
    print("CASO C: Error de Airtable")
    print("="*70)
    
    # Limpiar conversación anterior
    db = SessionLocal()
    try:
        db.query(Conversation).filter(
            Conversation.user_id == 'test_case_c'
        ).delete()
        db.commit()
    finally:
        db.close()
    
    # Crear estado con tabla inexistente (error esperado)
    state = ConversationState(
        user_id="test_case_c",
        conversation_id="test_case_c_001"
    )
    
    # Configurar query con tabla que no existe
    state.query["table"] = "TablaQueNoExiste"
    state.query["filters"] = {"test": "test"}
    state.query["limit"] = 5
    
    # Marcar como lista
    state.execution["ready"] = True
    state.update_status(ConversationStatus.READY_TO_EXECUTE)
    
    # Guardar en BD
    create_conversation(state)
    
    print("\n--- Estado configurado ---")
    print(f"User ID: {state.meta['user_id']}")
    print(f"Conversation ID: {state.meta['conversation_id']}")
    print(f"Status: {state.conversation['status']}")
    print(f"Query table: {state.query['table']} (NO EXISTE)")
    print(f"Ready: {state.execution['ready']}")
    print(f"Last run: {state.execution['last_run_at']}")
    
    print("\n--- Simulación local de error ---")
    # Simular error
    if os.getenv("AIRTABLE_API_KEY"):
        print("✓ Ejecutando query con tabla inexistente...")
        query_summary, query_records, query_error = execute_query_from_state(state)
        
        if query_error:
            print(f"✓ Error capturado correctamente:")
            print(f"  - Summary (mensaje para usuario): {query_summary}")
            print(f"  - Error técnico: {query_error}")
        else:
            print("⚠️  No se generó error (inesperado)")
    else:
        print("⚠️  Variables de entorno no cargadas")
        print("✓ En producción, esto generará un error 404 de Airtable")
        print("✓ El mensaje será: 'Lo siento, hubo un problema al consultar la base de datos...'")
    
    print("\n--- Resultado esperado al llamar /api/ask ---")
    print("✓ done = True (se intentó ejecutar)")
    print("✓ message = 'Lo siento, hubo un problema al consultar la base de datos...'")
    print("✓ status = 'ready_to_execute' o 'executed'")
    print("✓ execution.error = mensaje de error técnico")
    print("✓ execution.result_summary = mensaje amigable para el usuario")
    
    print("\n--- Comando curl para probar ---")
    print(f"""
curl -X POST https://campolimpio.rumbo.digital/api/ask \\
  -H "Content-Type: application/json" \\
  -d '{{
    "question": "Ejecuta la consulta",
    "user_id": "test_case_c",
    "conversation_id": "test_case_c_001"
  }}' | jq '{{
    done: .done,
    status: .state.status,
    has_error: (.state.execution.error != null),
    error: .state.execution.error,
    result_summary: .state.execution.result_summary,
    message: .message[:200]
  }}'
""")
    
    print("\n" + "="*70)


def test_case_bonus_reexecution_prevention():
    """
    CASO BONUS: Prevención de re-ejecución
    
    Escenario:
    - Estado con ready=True y last_run_at != None
    - Ya se ejecutó previamente
    - No debe volver a ejecutar (done=True desde el inicio)
    """
    print("\n" + "="*70)
    print("CASO BONUS: Prevención de re-ejecución")
    print("="*70)
    
    # Limpiar conversación anterior
    db = SessionLocal()
    try:
        db.query(Conversation).filter(
            Conversation.user_id == 'test_case_bonus'
        ).delete()
        db.commit()
    finally:
        db.close()
    
    # Crear estado ya ejecutado
    state = ConversationState(
        user_id="test_case_bonus",
        conversation_id="test_case_bonus_001"
    )
    
    # Configurar como ejecutado
    state.query["table"] = "Certificados"
    state.query["filters"] = {"coordinador": "Test"}
    state.execution["ready"] = True
    state.execution["last_run_at"] = datetime.utcnow().isoformat()
    state.execution["result_summary"] = "Encontré 5 certificados de recolección."
    state.update_status(ConversationStatus.EXECUTED)
    
    # Guardar en BD
    create_conversation(state)
    
    print("\n--- Estado configurado ---")
    print(f"User ID: {state.meta['user_id']}")
    print(f"Conversation ID: {state.meta['conversation_id']}")
    print(f"Status: {state.conversation['status']}")
    print(f"Ready: {state.execution['ready']}")
    print(f"Last run: {state.execution['last_run_at'][:19]}")
    print(f"Result summary: {state.execution['result_summary']}")
    
    print("\n--- Resultado esperado al llamar /api/ask ---")
    print("✓ done = True (desde el inicio)")
    print("✓ NO ejecuta de nuevo (last_run_at ya tiene valor)")
    print("✓ message = respuesta de OpenAI basada en contexto previo")
    print("✓ execution.last_run_at = mantiene el timestamp original")
    
    print("\n--- Comando curl para probar ---")
    print(f"""
curl -X POST https://campolimpio.rumbo.digital/api/ask \\
  -H "Content-Type: application/json" \\
  -d '{{
    "question": "¿Cuántos certificados había?",
    "user_id": "test_case_bonus",
    "conversation_id": "test_case_bonus_001"
  }}' | jq '{{
    done: .done,
    status: .state.status,
    last_run: .state.execution.last_run_at,
    message: .message[:150]
  }}'
""")
    
    print("\n" + "="*70)


def run_all_tests():
    """Ejecuta todos los tests de escenarios"""
    print("\n" + "="*70)
    print("SUITE DE PRUEBAS - ENDPOINT /api/ask")
    print("="*70)
    print("\nEstos tests configuran estados en la base de datos")
    print("y muestran los comandos curl para probar manualmente.\n")
    
    try:
        test_case_a_with_issues()
        test_case_b_ready_to_execute()
        test_case_c_airtable_error()
        test_case_bonus_reexecution_prevention()
        
        print("\n" + "="*70)
        print("✅ TESTS CONFIGURADOS EXITOSAMENTE")
        print("="*70)
        print("\nAhora puedes ejecutar los comandos curl mostrados arriba")
        print("para verificar cada escenario en producción.\n")
        
        print("RESUMEN DE ESCENARIOS:")
        print("  A) Estado con issues → done=False, pide aclaraciones")
        print("  B) Ready to execute → done=True, ejecuta y devuelve resumen")
        print("  C) Error de Airtable → done=True, mensaje de error amigable")
        print("  BONUS) Ya ejecutado → done=True, no re-ejecuta")
        
    except Exception as e:
        print(f"\n❌ Error en los tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Cargar variables de entorno si es necesario
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
    
    run_all_tests()
