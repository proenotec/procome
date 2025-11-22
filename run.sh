#!/bin/bash

# Script para ejecutar PROCOME

# Obtener el directorio donde está el script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Verificar que existe el entorno virtual
if [ ! -d ".venv" ]; then
    echo "ERROR: No se encuentra el entorno virtual (.venv)"
    echo "Ejecuta primero: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activar el entorno virtual
echo "Activando entorno virtual..."
source .venv/bin/activate

# Verificar que se activó correctamente
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: No se pudo activar el entorno virtual"
    exit 1
fi

# Ejecutar el programa principal
echo "Iniciando PROCOME..."
python3 PROCOME_Arranque_Qt.py

# Desactivar el entorno virtual al finalizar
deactivate
