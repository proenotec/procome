#!/bin/bash

# Script de desinstalación de PROCOME

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Desinstalador de PROCOME${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar que se ejecuta con sudo
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}Error: Este script debe ejecutarse con sudo${NC}"
   echo "Uso: sudo ./uninstall.sh"
   exit 1
fi

# Verificar si PROCOME está instalado
if [ ! -d "/opt/procome" ]; then
    echo -e "${YELLOW}PROCOME no está instalado en /opt/procome${NC}"
    exit 0
fi

# Mostrar versión instalada si existe
if [ -f "/opt/procome/version.txt" ]; then
    VERSION=$(cat /opt/procome/version.txt)
    echo -e "Versión instalada: ${YELLOW}v${VERSION}${NC}"
    echo ""
fi

# Pedir confirmación
read -p "¿Desea desinstalar PROCOME? (s/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Desinstalación cancelada${NC}"
    echo ""
    exit 0
fi

echo ""
echo -e "${YELLOW}→${NC} Eliminando archivos de PROCOME..."

# Eliminar enlace simbólico
if [ -L "/usr/local/bin/procome" ]; then
    rm /usr/local/bin/procome
    echo -e "${GREEN}  ✓${NC} Enlace simbólico eliminado"
fi

# Eliminar entrada del menú
if [ -f "/usr/share/applications/procome.desktop" ]; then
    rm /usr/share/applications/procome.desktop
    echo -e "${GREEN}  ✓${NC} Entrada del menú eliminada"
fi

# Eliminar entrada del menú de usuario
if [ -f "/usr/local/share/applications/procome.desktop" ]; then
    rm /usr/local/share/applications/procome.desktop
    echo -e "${GREEN}  ✓${NC} Entrada del menú de usuario eliminada"
fi

# Eliminar directorio de instalación
if [ -d "/opt/procome" ]; then
    rm -rf /opt/procome
    echo -e "${GREEN}  ✓${NC} Directorio /opt/procome eliminado"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Desinstalación completada${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Nota:${NC} La configuración de usuario en ~/.config/procome/ no se eliminó"
echo -e "      Si deseas eliminarla manualmente:"
echo -e "      ${YELLOW}rm -rf ~/.config/procome/${NC}"
echo ""
