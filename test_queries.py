"""
Script de prueba para el módulo queries.py
"""
from conversation_state import ConversationState, ConversationStatus
from queries import execute_query_from_state, format_records_for_display


def test_query_certificados_simple():
    """
    Prueba básica: consultar todos los certificados sin filtros
    """
    print("\n=== TEST 1: Consulta simple a Certificados ===")
    
    # Crear estado
    state = ConversationState(user_id="test_user_1", conversation_id="test_conv_1")
    
    # Configurar query
    state.query["table"] = "Certificados"
    state.query["limit"] = 5  # Solo 5 para prueba
    state.validate_query()
    
    # Ejecutar consulta
    summary, records, error = execute_query_from_state(state)
    
    # Mostrar resultados
    print(f"Resumen: {summary}")
    if error:
        print(f"Error: {error}")
    if records:
        print(f"Registros obtenidos: {len(records)}")
        print("\nPrimeros registros:")
        print(format_records_for_display(records[:3], "Certificados", "summary"))
    
    print("\n" + "="*60)


def test_query_with_filters():
    """
    Prueba con filtros: buscar certificados de un coordinador específico
    """
    print("\n=== TEST 2: Consulta con filtro de coordinador ===")
    
    state = ConversationState(user_id="test_user_2", conversation_id="test_conv_2")
    
    # Configurar query con filtros
    state.query["table"] = "Certificados"
    state.query["filters"] = {
        "coordinador": "OSCAR MANUEL PEREZ MALAGON"
    }
    state.query["limit"] = 10
    state.validate_query()
    
    # Ejecutar
    summary, records, error = execute_query_from_state(state)
    
    print(f"Resumen: {summary}")
    if error:
        print(f"Error: {error}")
    if records:
        print(f"Registros obtenidos: {len(records)}")
        print("\nDetalles:")
        print(format_records_for_display(records[:2], "Certificados", "detailed"))
    
    print("\n" + "="*60)


def test_query_kardex():
    """
    Prueba con tabla Kardex
    """
    print("\n=== TEST 3: Consulta a Kardex ===")
    
    state = ConversationState(user_id="test_user_3", conversation_id="test_conv_3")
    
    state.query["table"] = "Kardex"
    state.query["limit"] = 5
    state.validate_query()
    
    summary, records, error = execute_query_from_state(state)
    
    print(f"Resumen: {summary}")
    if error:
        print(f"Error: {error}")
    if records:
        print(f"Registros obtenidos: {len(records)}")
        print("\nResumen de registros:")
        print(format_records_for_display(records, "Kardex", "summary"))
    
    print("\n" + "="*60)


def test_query_no_results():
    """
    Prueba con filtros que no retornan resultados
    """
    print("\n=== TEST 4: Consulta sin resultados ===")
    
    state = ConversationState(user_id="test_user_4", conversation_id="test_conv_4")
    
    state.query["table"] = "Certificados"
    state.query["filters"] = {
        "coordinador": "COORDINADOR_QUE_NO_EXISTE_12345"
    }
    state.validate_query()
    
    summary, records, error = execute_query_from_state(state)
    
    print(f"Resumen: {summary}")
    if error:
        print(f"Error: {error}")
    print(f"Registros: {records}")
    
    print("\n" + "="*60)


def test_query_invalid_state():
    """
    Prueba con estado inválido (sin tabla)
    """
    print("\n=== TEST 5: Estado inválido (sin tabla) ===")
    
    state = ConversationState(user_id="test_user_5", conversation_id="test_conv_5")
    
    # No configuramos tabla
    state.query["filters"] = {"coordinador": "TEST"}
    
    summary, records, error = execute_query_from_state(state)
    
    print(f"Resumen: {summary}")
    if error:
        print(f"Error: {error}")
    print(f"Registros: {records}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print("="*60)
    print("PRUEBAS DEL MÓDULO QUERIES")
    print("="*60)
    
    # Ejecutar pruebas
    test_query_certificados_simple()
    test_query_with_filters()
    test_query_kardex()
    test_query_no_results()
    test_query_invalid_state()
    
    print("\n✅ Pruebas completadas")
