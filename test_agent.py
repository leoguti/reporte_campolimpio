import os
from openai import OpenAI

# Verificar que la API key esté definida
if not os.getenv("OPENAI_API_KEY"):
    print("Error: La variable de entorno OPENAI_API_KEY no está definida.")
    print("Por favor, exporta tu API key con: export OPENAI_API_KEY='tu-api-key'")
    exit(1)

client = OpenAI()

# Leer el system prompt
with open('agent/system_prompt.txt', 'r', encoding='utf-8') as f:
    system_prompt = f.read()

# Pedir pregunta al usuario
pregunta = input("Pregunta: ")

# Armar el prompt
prompt = system_prompt + "\n\nUsuario: " + pregunta + "\n\nAgente:"

# Llamar a la API
response = client.responses.create(
    model="gpt-5.1",
    input=prompt
)
print(response.output_text)
