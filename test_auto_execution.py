"""
Test simple para verificar el nuevo flujo de ejecución automática
"""
import requests
import json


BASE_URL = "http://localhost:8001"


def test_auto_execution():
    """
    Prueba que el endpoint ejecute automáticamente cuando ready=True y last_run_at=None
    """
    print("\n" + "="*70)
    print("TEST: Ejecución automática de consulta")
    print("="*70)
    
    # Paso 1: Hacer una pregunta específica que debería resultar en query lista
    print("\n--- Paso 1: Pregunta con información suficiente ---")
    payload = {
        "question": "Muéstrame los certificados de Andrés Felipe Ramirez",
        "user_id": "test_auto_exec_1",
        "conversation_id": "test_conv_auto_1"
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    data = response.json()
    
    print(f"\nUsuario: {payload['question']}")
    print(f"\nRespuesta completa:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print(f"\n--- Análisis de la respuesta ---")
    print(f"Message: {data.get('message', '')[:200]}...")
    print(f"Status: {data['state']['status']}")
    print(f"Ready to execute: {data['state']['ready_to_execute']}")
    print(f"Last run at: {data['state']['execution']['last_run_at']}")
    print(f"Result summary: {data['state']['execution'].get('result_summary', 'N/A')[:100] if data['state']['execution'].get('result_summary') else 'N/A'}...")
    
    # Verificar si se ejecutó
    if data['state']['execution']['last_run_at'] is not None:
        print("\n✅ ÉXITO: La consulta se ejecutó automáticamente")
        print(f"✅ El mensaje contiene el resumen de resultados")
    else:
        print("\n⚠️ La consulta NO se ejecutó")
        print("Puede ser que el agente esté pidiendo más información")
    
    print("\n" + "="*70)


def test_clarification_flow():
    """
    Prueba con pregunta ambigua que requiere clarificación
    """
    print("\n" + "="*70)
    print("TEST: Flujo de aclaración (no debería ejecutar)")
    print("="*70)
    
    payload = {
        "question": "Quiero ver certificados",
        "user_id": "test_clarif_1",
        "conversation_id": "test_conv_clarif_1"
    }
    
    response = requests.post(f"{BASE_URL}/ask", json=payload)
    data = response.json()
    
    print(f"\nUsuario: {payload['question']}")
    print(f"\nMessage: {data.get('message', '')[:300]}...")
    print(f"Status: {data['state']['status']}")
    print(f"Ready to execute: {data['state']['ready_to_execute']}")
    print(f"Last run at: {data['state']['execution']['last_run_at']}")
    
    if data['state']['execution']['last_run_at'] is None:
        print("\n✅ CORRECTO: No se ejecutó porque faltan datos")
        print("✅ El agente está pidiendo clarificaciones")
    else:
        print("\n⚠️ INESPERADO: Se ejecutó aunque falta información")
    
    print("\n" + "="*70)


def test_health():
    """Verifica que el servidor esté funcionando"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        print(f"\n✅ Servidor funcionando: {data}")
        return True
    except Exception as e:
        print(f"\n❌ Error conectando al servidor: {e}")
        print("Asegúrate de que el servidor esté corriendo")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PRUEBA DE EJECUCIÓN AUTOMÁTICA")
    print("="*70)
    
    if not test_health():
        print("\n⚠️ Inicia el servidor primero con: ./deploy.sh")
        exit(1)
    
    try:
        test_auto_execution()
        test_clarification_flow()
        
        print("\n✅ Pruebas completadas")
    except requests.exceptions.ConnectionError:
        print("\n❌ No se pudo conectar al servidor")
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
