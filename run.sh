#!/bin/bash

# Script para ejecutar PROCOME

# Obtener el directorio donde está el script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Verificar que existe el entorno virtual, si no existe lo crea
if [ ! -d ".venv" ]; then
    echo "No se encuentra el entorno virtual (.venv)"
    echo "Creando entorno virtual..."
    python3 -m venv .venv
    
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo crear el entorno virtual"
        echo "Asegúrate de tener python3-venv instalado: sudo apt install python3-venv"
        exit 1
    fi
    
    echo "Entorno virtual creado exitosamente"
    echo "Activando entorno virtual..."
    source .venv/bin/activate
    
    echo "Instalando dependencias desde requirements.txt..."
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudieron instalar las dependencias"
        exit 1
    fi
    
    echo "Dependencias instaladas exitosamente"
else
    # Activar el entorno virtual existente
    echo "Activando entorno virtual..."
    source .venv/bin/activate
fi

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
