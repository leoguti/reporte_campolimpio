"""
Script para probar manualmente la ejecución automática
modificando directamente el estado de conversación
"""
import sys
sys.path.insert(0, '/opt/reporte_campolimpio')

from conversation_state import ConversationState, ConversationStatus
from conversation_db import create_conversation, update_conversation
from queries import execute_query_from_state


def test_manual_query():
    """
    Prueba manual: crear un estado con query lista y verificar ejecución
    """
    print("\n" + "="*70)
    print("TEST MANUAL: Verificar ejecución automática")
    print("="*70)
    
    # Crear estado con query completa
    state = ConversationState(
        user_id="manual_test_user",
        conversation_id="manual_test_conv_001"
    )
    
    # Configurar query manualmente (simulando lo que OpenAI debería hacer)
    state.query["table"] = "Certificados"
    state.query["filters"] = {
        "coordinador": "Andrés Felipe Ramirez"
    }
    state.query["limit"] = 10
    
    # Marcar como lista
    state.execution["ready"] = True
    state.update_status(ConversationStatus.READY_TO_EXECUTE)
    
    print("\n--- Estado configurado ---")
    print(f"Table: {state.query['table']}")
    print(f"Filters: {state.query['filters']}")
    print(f"Ready: {state.execution['ready']}")
    print(f"Last run: {state.execution['last_run_at']}")
    print(f"Status: {state.conversation['status']}")
    
    # Guardar en BD
    create_conversation(state)
    print("\n✅ Estado guardado en BD")
    
    # Simular la lógica del endpoint
    print("\n--- Simulando lógica del endpoint ---")
    if state.execution["ready"] and state.execution["last_run_at"] is None:
        print("✅ Condiciones cumplidas: ejecutando query...")
        
        # Ejecutar query
        query_summary, query_records, query_error = execute_query_from_state(state)
        
        # Actualizar estado
        from datetime import datetime
        state.execution["last_run_at"] = datetime.utcnow().isoformat()
        
        if query_error:
            print(f"❌ Error: {query_error}")
            state.execution["error"] = query_error
            state.execution["result_summary"] = query_summary
        else:
            print(f"✅ Éxito!")
            print(f"\nResumen: {query_summary}")
            print(f"Registros obtenidos: {len(query_records) if query_records else 0}")
            
            state.execution["result_summary"] = query_summary
            state.execution["error"] = None
            state.update_status(ConversationStatus.EXECUTED)
            
            # Mostrar algunos registros
            if query_records and len(query_records) > 0:
                print(f"\n--- Primer registro ---")
                fields = query_records[0].get("fields", {})
                print(f"Consecutivo: {fields.get('pre_consecutivo', 'N/A')}")
                print(f"Coordinador: {fields.get('nombrecoordinador', 'N/A')}")
                print(f"Total: {fields.get('total', 0)} kg")
        
        # Actualizar en BD
        update_conversation(state)
        print("\n✅ Estado actualizado en BD con resultados de ejecución")
    else:
        print("⚠️ No se cumplen las condiciones para ejecutar")
        print(f"  ready={state.execution['ready']}")
        print(f"  last_run_at={state.execution['last_run_at']}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    test_manual_query()
