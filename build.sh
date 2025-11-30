#!/bin/bash

# Script para compilar PROCOME Qt a un ejecutable standalone
# Usa PyInstaller para crear un binario con todas las dependencias incluidas

set -e

echo "================================================"
echo "  Compilando PROCOME Qt a ejecutable"
echo "================================================"
echo ""

# Obtener el directorio donde está el script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activar el entorno virtual
if [ ! -d ".venv" ]; then
    echo "ERROR: No se encuentra el entorno virtual (.venv)"
    echo "Ejecuta primero: ./run.sh"
    exit 1
fi

echo "Activando entorno virtual..."
source .venv/bin/activate

# Verificar que PyInstaller está instalado
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller no encontrado. Instalando..."
    pip install pyinstaller
fi

# Limpiar compilaciones anteriores
echo "Limpiando compilaciones anteriores..."
rm -rf build/ dist/ PROCOME.spec

# Compilar con PyInstaller
echo ""
echo "Compilando aplicación..."
echo "Esto puede tardar varios minutos..."
echo ""

pyinstaller \
    --onefile \
    --windowed \
    --name PROCOME \
    --add-data "PROCOME.cfg:." \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtWidgets \
    --hidden-import serial \
    --hidden-import serial.tools.list_ports \
    --collect-all PySide6 \
    PROCOME_Arranque_Qt.py

# Verificar que se compiló correctamente
if [ -f "dist/PROCOME" ]; then
    echo ""
    echo "================================================"
    echo "  ✅ Compilación exitosa!"
    echo "================================================"
    echo ""
    echo "Ejecutable creado en: dist/PROCOME"
    echo "Tamaño: $(du -h dist/PROCOME | cut -f1)"
    echo ""
    echo "Para ejecutar:"
    echo "  ./dist/PROCOME"
    echo ""
    echo "Para distribuir, copia el archivo 'dist/PROCOME' junto con 'PROCOME.cfg'"
    echo ""
else
    echo ""
    echo "❌ ERROR: La compilación falló"
    exit 1
fi

# Desactivar el entorno virtual
deactivate
