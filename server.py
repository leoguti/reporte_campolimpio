import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader
from agent_core import run_agent

app = FastAPI()

# Configurar el entorno de Jinja2
env = Environment(loader=FileSystemLoader('plantillas'))

# Crear carpeta reportes si no existe
os.makedirs('reportes', exist_ok=True)

class ReporteData(BaseModel):
    nombre: str
    fecha: str
    municipio: str
    tipo_caso: str
    descripcion: str

@app.post("/reporte")
async def crear_reporte(data: ReporteData):
    # Imprimir el JSON recibido en consola
    print(data.model_dump())
    
    # Cargar la plantilla
    plantilla = env.get_template('reporte_basico.md.j2')
    
    # Renderizar la plantilla con los datos recibidos
    reporte_generado = plantilla.render(**data.model_dump())
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"reporte_{timestamp}.md"
    ruta_archivo = os.path.join('reportes', nombre_archivo)
    
    # Guardar el reporte en el archivo
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        f.write(reporte_generado)
    
    return {"status": "ok", "reporte": reporte_generado, "file": nombre_archivo}

class PreguntaData(BaseModel):
    question: str
    extra: dict = {}

@app.post("/ask")
async def consultar_agente(data: PreguntaData):
    """Endpoint para consultar al agente IA"""
    result = run_agent(data.question, data.extra)
    return result

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

# Montar carpeta reportes como archivos estáticos
app.mount("/reportes", StaticFiles(directory="reportes"), name="reportes")
