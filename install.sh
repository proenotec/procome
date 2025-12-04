#!/bin/bash

# Script de instalación de PROCOME v2.5.0
# Instala el ejecutable standalone en /opt/procome

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Versión
VERSION="2.5.1"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Instalador de PROCOME v${VERSION}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar que se ejecuta con sudo
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}Error: Este script debe ejecutarse con sudo${NC}"
   echo "Uso: sudo ./install.sh"
   exit 1
fi

# Detectar directorio temporal
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo -e "${YELLOW}→${NC} Descargando PROCOME v${VERSION}..."
cd "$TEMP_DIR"

# Descargar release
DOWNLOAD_URL="https://github.com/proenotec/procome/releases/download/v${VERSION}/PROCOME-Linux-x64.tar.gz"

if command -v wget &> /dev/null; then
    wget -q --show-progress "$DOWNLOAD_URL" || {
        echo -e "${RED}Error al descargar PROCOME${NC}"
        exit 1
    }
elif command -v curl &> /dev/null; then
    curl -L -# "$DOWNLOAD_URL" -o PROCOME-Linux-x64.tar.gz || {
        echo -e "${RED}Error al descargar PROCOME${NC}"
        exit 1
    }
else
    echo -e "${RED}Error: Se necesita wget o curl para descargar${NC}"
    exit 1
fi

echo -e "${YELLOW}→${NC} Extrayendo archivos..."
tar -xzf PROCOME-Linux-x64.tar.gz

# Verificar que el ejecutable se extrajo correctamente
if [ ! -f "PROCOME-Linux-x64/PROCOME" ]; then
    echo -e "${RED}Error: No se encontró el ejecutable en el archivo descargado${NC}"
    exit 1
fi

# Verificar que es un ejecutable ELF
if ! file "PROCOME-Linux-x64/PROCOME" | grep -q "ELF 64-bit"; then
    echo -e "${RED}Error: El archivo descargado no es un ejecutable válido${NC}"
    exit 1
fi

echo -e "${YELLOW}→${NC} Instalando en /opt/procome..."

# Eliminar instalación anterior si existe
if [ -d "/opt/procome" ]; then
    echo -e "${YELLOW}  Eliminando instalación anterior...${NC}"
    rm -rf /opt/procome
fi

# Copiar archivos
cp -r PROCOME-Linux-x64 /opt/procome
chmod +x /opt/procome/PROCOME

# Crear enlace simbólico
echo -e "${YELLOW}→${NC} Creando enlace simbólico en /usr/local/bin..."
ln -sf /opt/procome/PROCOME /usr/local/bin/procome

# Crear archivo .desktop para el menú de aplicaciones
echo -e "${YELLOW}→${NC} Creando entrada en el menú de aplicaciones..."
cat > /usr/share/applications/procome.desktop <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PROCOME
Comment=Programa de Control Modular por Electrónica
Exec=/opt/procome/PROCOME
Icon=/opt/procome/procome
Terminal=false
Categories=Development;Electronics;
Keywords=procome;rs485;serial;protocol;
EOF

# Crear icono SVG
cat > /opt/procome/procome.svg <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" version="1.1" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
 <rect width="256" height="256" fill="#2c3e50" rx="20"/>
 <rect x="30" y="60" width="196" height="136" fill="#34495e" rx="8"/>
 <circle cx="65" cy="100" r="12" fill="#3498db"/>
 <circle cx="65" cy="130" r="12" fill="#e74c3c"/>
 <circle cx="65" cy="160" r="12" fill="#2ecc71"/>
 <rect x="95" y="95" width="120" height="10" fill="#ecf0f1" rx="2"/>
 <rect x="95" y="125" width="80" height="10" fill="#ecf0f1" rx="2"/>
 <rect x="95" y="155" width="100" height="10" fill="#ecf0f1" rx="2"/>
 <text x="128" y="220" fill="#ecf0f1" font-family="monospace" font-size="24" font-weight="bold" text-anchor="middle">PROCOME</text>
</svg>
EOF

# Convertir SVG a PNG si rsvg-convert está disponible
if command -v rsvg-convert &> /dev/null; then
    rsvg-convert -w 256 -h 256 /opt/procome/procome.svg -o /opt/procome/procome.png
    rm /opt/procome/procome.svg
else
    mv /opt/procome/procome.svg /opt/procome/procome.png
fi

# Guardar versión instalada
echo "$VERSION" > /opt/procome/version.txt

# Configurar permisos para puerto serie
CURRENT_USER="${SUDO_USER:-$USER}"
if [ -n "$CURRENT_USER" ] && [ "$CURRENT_USER" != "root" ]; then
    echo -e "${YELLOW}→${NC} Configurando permisos para puerto serie..."

    # Añadir usuario al grupo dialout
    if getent group dialout > /dev/null 2>&1; then
        usermod -a -G dialout "$CURRENT_USER"
        echo -e "${GREEN}  Usuario '$CURRENT_USER' añadido al grupo 'dialout'${NC}"
    fi

    # Añadir usuario al grupo uucp si existe (en algunas distribuciones)
    if getent group uucp > /dev/null 2>&1; then
        usermod -a -G uucp "$CURRENT_USER"
        echo -e "${GREEN}  Usuario '$CURRENT_USER' añadido al grupo 'uucp'${NC}"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Instalación completada${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "PROCOME v${VERSION} instalado en: ${BLUE}/opt/procome${NC}"
echo ""
echo -e "Para ejecutar PROCOME:"
echo -e "  ${YELLOW}procome${NC}  (desde cualquier terminal)"
echo ""
echo -e "O desde el menú de aplicaciones:"
echo -e "  ${YELLOW}Desarrollo → PROCOME${NC}"
echo ""
if [ -n "$CURRENT_USER" ] && [ "$CURRENT_USER" != "root" ]; then
    echo -e "${YELLOW}IMPORTANTE:${NC} Para que los cambios de grupo surtan efecto, debes:"
    echo -e "  1. Cerrar sesión y volver a iniciarla"
    echo -e "  2. O ejecutar: ${YELLOW}newgrp dialout${NC}"
    echo ""
fi
echo -e "Para desinstalar: ${YELLOW}sudo /opt/procome/uninstall.sh${NC}"
echo ""
