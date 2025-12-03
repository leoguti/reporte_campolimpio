"""
Script de prueba para el flujo completo de consultas con contexto
"""
import requests
import json


BASE_URL = "http://localhost:8001"


def test_complete_flow_certificados():
    """
    Prueba el flujo completo:
    1. Usuario hace una pregunta inicial
    2. Agente pide clarificaciones
    3. Usuario responde
    4. Cuando la query está lista, se ejecuta automáticamente
    """
    print("\n" + "="*70)
    print("TEST: Flujo completo de consulta de certificados")
    print("="*70)
    
    # Paso 1: Pregunta inicial ambigua
    print("\n--- Paso 1: Pregunta inicial ---")
    payload = {
        "question": "Quiero ver certificados de recolección",
        "user_id": "test_user_flow_1",
        "conversation_id": "test_conv_flow_1"
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    data = response.json()
    
    print(f"Usuario: {payload['question']}")
    print(f"Agente: {data['message']}")
    print(f"Status: {data['state']['status']}")
    print(f"Pending Question: {data['state']['pending_question']}")
    
    # Paso 2: Dar más detalles (coordinador)
    print("\n--- Paso 2: Especificar coordinador ---")
    payload = {
        "question": "Del coordinador Andrés Felipe Ramirez",
        "user_id": "test_user_flow_1",
        "conversation_id": "test_conv_flow_1"
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    data = response.json()
    
    print(f"Usuario: {payload['question']}")
    print(f"Agente: {data['message']}")
    print(f"Status: {data['state']['status']}")
    print(f"Query table: {data['state']['query_table']}")
    print(f"Filters: {data['state']['filters']}")
    
    # Ver si se ejecutó la query
    if 'query_results' in data:
        print(f"\n🎉 QUERY EJECUTADA!")
        print(f"Summary: {data['query_results']['summary']}")
        print(f"Count: {data['query_results']['count']}")
        if data['query_results']['count'] > 0:
            print(f"\nPrimer registro:")
            print(json.dumps(data['query_results']['records'][0], indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)


def test_kardex_flow():
    """
    Prueba con tabla Kardex
    """
    print("\n" + "="*70)
    print("TEST: Flujo de consulta a Kardex")
    print("="*70)
    
    print("\n--- Consulta a Kardex ---")
    payload = {
        "question": "Muéstrame movimientos de entrada",
        "user_id": "test_user_kardex_1",
        "conversation_id": "test_conv_kardex_1"
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    data = response.json()
    
    print(f"Usuario: {payload['question']}")
    print(f"Agente: {data['message']}")
    print(f"Status: {data['state']['status']}")
    
    if 'query_results' in data:
        print(f"\n🎉 QUERY EJECUTADA!")
        print(f"Summary: {data['query_results']['summary']}")
        print(f"Count: {data['query_results']['count']}")
    
    print("\n" + "="*70)


def test_direct_query():
    """
    Prueba con pregunta específica que puede generar query inmediatamente
    """
    print("\n" + "="*70)
    print("TEST: Query directa (sin ambigüedad)")
    print("="*70)
    
    print("\n--- Pregunta directa ---")
    payload = {
        "question": "Necesito todos los certificados del último mes",
        "user_id": "test_user_direct",
        "conversation_id": "test_conv_direct"
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    data = response.json()
    
    print(f"Usuario: {payload['question']}")
    print(f"Agente: {data['message']}")
    print(f"Status: {data['state']['status']}")
    
    if 'query_results' in data:
        print(f"\n🎉 QUERY EJECUTADA!")
        print(f"Summary: {data['query_results']['summary']}")
        print(f"Count: {data['query_results']['count']}")
    else:
        print(f"\n⏳ Query no ejecutada aún")
        print(f"Pending: {data['state']['pending_question']}")
    
    print("\n" + "="*70)


def test_health():
    """
    Verifica que el servidor esté funcionando
    """
    print("\n" + "="*70)
    print("TEST: Health check")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        print(f"✅ Servidor funcionando: {data}")
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        print("Asegúrate de que el servidor esté corriendo con: ./deploy.sh")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PRUEBAS DE INTEGRACIÓN - QUERIES CON CONTEXTO")
    print("="*70)
    
    # Verificar que el servidor esté corriendo
    test_health()
    
    # Ejecutar pruebas
    try:
        test_complete_flow_certificados()
        test_kardex_flow()
        test_direct_query()
        
        print("\n✅ Todas las pruebas completadas")
    except requests.exceptions.ConnectionError:
        print("\n❌ No se pudo conectar al servidor")
        print("Inicia el servidor con: ./deploy.sh")
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
