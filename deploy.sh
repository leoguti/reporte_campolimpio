#!/bin/bash
set -e

cd /opt/reporte_campolimpio

# Crear y activar entorno virtual
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Detener proceso anterior si existe
pkill -f "uvicorn server:app" || true

# Lanzar servidor en segundo plano
nohup uvicorn server:app --host 0.0.0.0 --port 8001 > uvicorn.log 2>&1 &

echo "Servidor ejecutándose en el puerto 8001"
