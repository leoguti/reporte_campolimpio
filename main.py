import json
from jinja2 import Environment, FileSystemLoader

# Cargar los datos desde el archivo JSON
with open('ejemplo.json', 'r', encoding='utf-8') as f:
    datos = json.load(f)

# Configurar el entorno de Jinja2
env = Environment(loader=FileSystemLoader('plantillas'))

# Cargar la plantilla desde el archivo
plantilla = env.get_template('reporte_basico.md.j2')

# Renderizar la plantilla con los datos del JSON
resultado = plantilla.render(**datos)

print(resultado)
