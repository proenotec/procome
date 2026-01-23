#!/bin/bash

# Script de actualización automática de PROCOME desde GitHub
# Descarga e instala la última versión disponible
# Uso: sudo ./actualizar_procome.sh

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración
REPO="proenotec/procome"
INSTALL_DIR="/opt/procome"
BINARY_NAME="PROCOME"
CONFIG_FILE="PROCOME.cfg"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Actualizador de PROCOME${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar que se ejecuta con sudo
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}Error: Este script debe ejecutarse con sudo${NC}"
   echo "Uso: sudo ./actualizar_procome.sh"
   exit 1
fi

# Verificar que hay algún método para descargar
if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null && ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: Se necesita 'curl', 'wget' o 'gh' para descargar${NC}"
    echo ""
    echo "Instala uno de ellos:"
    echo "  curl (recomendado): sudo apt install curl"
    echo "  wget:               sudo apt install wget"
    echo "  gh CLI:             sudo apt install gh"
    exit 1
fi

# Obtener versión instalada
VERSION_INSTALADA="No instalada"
if [ -f "$INSTALL_DIR/version.txt" ]; then
    VERSION_INSTALADA=$(cat "$INSTALL_DIR/version.txt")
fi

echo -e "${CYAN}Versión instalada:${NC} $VERSION_INSTALADA"

# Obtener última versión desde GitHub
echo -e "${YELLOW}→${NC} Consultando última versión en GitHub..."

# Intentar con curl primero (no requiere autenticación)
if command -v curl &> /dev/null; then
    ULTIMA_VERSION=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | sed -E 's/.*"v([^"]+)".*/\1/')
# Intentar con wget si no hay curl
elif command -v wget &> /dev/null; then
    ULTIMA_VERSION=$(wget -qO- "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name"' | sed -E 's/.*"v([^"]+)".*/\1/')
# Usar gh CLI como último recurso (requiere autenticación)
elif command -v gh &> /dev/null; then
    ULTIMA_VERSION=$(gh release view --repo "$REPO" --json tagName --jq '.tagName' 2>/dev/null | sed 's/^v//')
fi

# Verificar que se obtuvo la versión
if [ -z "$ULTIMA_VERSION" ]; then
    echo -e "${RED}Error: No se pudo obtener la última versión${NC}"
    echo ""
    echo "Posibles causas:"
    echo "  - No hay conexión a internet"
    echo "  - GitHub API no está disponible"
    echo "  - Rate limit de GitHub excedido"
    echo ""
    echo "Intenta de nuevo en unos minutos o verifica tu conexión."
    exit 1
fi

echo -e "${CYAN}Última versión:${NC} $ULTIMA_VERSION"
echo ""

# Comparar versiones
if [ "$VERSION_INSTALADA" = "$ULTIMA_VERSION" ]; then
    echo -e "${GREEN}✓ Ya tienes la última versión instalada${NC}"
    echo ""
    read -p "¿Deseas reinstalar v$ULTIMA_VERSION? (s/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
        echo -e "${YELLOW}Actualización cancelada${NC}"
        exit 0
    fi
elif [ "$VERSION_INSTALADA" != "No instalada" ]; then
    echo -e "${YELLOW}Se actualizará de v$VERSION_INSTALADA a v$ULTIMA_VERSION${NC}"
    echo ""
fi

# Crear directorio temporal
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo -e "${YELLOW}→${NC} Descargando PROCOME v${ULTIMA_VERSION}..."
cd "$TEMP_DIR"

# Construir URL de descarga
DOWNLOAD_URL="https://github.com/$REPO/releases/download/v${ULTIMA_VERSION}/PROCOME-Linux"

# Descargar
if command -v wget &> /dev/null; then
    wget -q --show-progress "$DOWNLOAD_URL" -O PROCOME-Linux || {
        echo -e "${RED}Error al descargar PROCOME${NC}"
        echo "URL: $DOWNLOAD_URL"
        exit 1
    }
elif command -v curl &> /dev/null; then
    curl -L -# "$DOWNLOAD_URL" -o PROCOME-Linux || {
        echo -e "${RED}Error al descargar PROCOME${NC}"
        echo "URL: $DOWNLOAD_URL"
        exit 1
    }
fi

# Descargar archivo de configuración si no existe
if [ ! -f "$INSTALL_DIR/$CONFIG_FILE" ]; then
    echo -e "${YELLOW}→${NC} Descargando archivo de configuración..."
    CONFIG_URL="https://github.com/$REPO/releases/download/v${ULTIMA_VERSION}/PROCOME.cfg"
    if command -v wget &> /dev/null; then
        wget -q "$CONFIG_URL" -O PROCOME.cfg 2>/dev/null || echo "  (usando configuración predeterminada)"
    elif command -v curl &> /dev/null; then
        curl -s -L "$CONFIG_URL" -o PROCOME.cfg 2>/dev/null || echo "  (usando configuración predeterminada)"
    fi
fi

# Verificar que el ejecutable se descargó correctamente
if [ ! -f "PROCOME-Linux" ]; then
    echo -e "${RED}Error: No se pudo descargar el ejecutable${NC}"
    exit 1
fi

# Verificar que es un ejecutable ELF
if ! file "PROCOME-Linux" | grep -q "ELF 64-bit"; then
    echo -e "${RED}Error: El archivo descargado no es un ejecutable válido${NC}"
    exit 1
fi

# Hacer backup de la configuración si existe
if [ -f "$INSTALL_DIR/$CONFIG_FILE" ]; then
    echo -e "${YELLOW}→${NC} Haciendo backup de la configuración..."
    cp "$INSTALL_DIR/$CONFIG_FILE" "$TEMP_DIR/PROCOME.cfg.backup"
fi

# Instalar
echo -e "${YELLOW}→${NC} Instalando en $INSTALL_DIR..."

# Crear directorio si no existe
mkdir -p "$INSTALL_DIR"

# Copiar ejecutable
cp PROCOME-Linux "$INSTALL_DIR/$BINARY_NAME"
chmod +x "$INSTALL_DIR/$BINARY_NAME"

# Restaurar configuración o copiar nueva
if [ -f "$TEMP_DIR/PROCOME.cfg.backup" ]; then
    echo -e "${YELLOW}→${NC} Restaurando configuración anterior..."
    cp "$TEMP_DIR/PROCOME.cfg.backup" "$INSTALL_DIR/$CONFIG_FILE"
elif [ -f "PROCOME.cfg" ]; then
    cp PROCOME.cfg "$INSTALL_DIR/"
fi

# Guardar versión instalada
echo "$ULTIMA_VERSION" > "$INSTALL_DIR/version.txt"

# Crear/actualizar enlace simbólico
echo -e "${YELLOW}→${NC} Actualizando enlace simbólico..."
ln -sf "$INSTALL_DIR/$BINARY_NAME" /usr/local/bin/procome

# Actualizar entrada en el menú de aplicaciones
echo -e "${YELLOW}→${NC} Actualizando entrada en el menú de aplicaciones..."
cat > /usr/share/applications/procome.desktop <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PROCOME v${ULTIMA_VERSION}
Comment=Programa de Control Modular por Electrónica
Exec=$INSTALL_DIR/$BINARY_NAME
Icon=$INSTALL_DIR/procome.png
Terminal=false
Categories=Development;Electronics;
Keywords=procome;rs485;serial;protocol;
EOF

# Crear icono si no existe
if [ ! -f "$INSTALL_DIR/procome.png" ]; then
    cat > "$INSTALL_DIR/procome.svg" <<'EOF'
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
        rsvg-convert -w 256 -h 256 "$INSTALL_DIR/procome.svg" -o "$INSTALL_DIR/procome.png"
        rm "$INSTALL_DIR/procome.svg"
    else
        mv "$INSTALL_DIR/procome.svg" "$INSTALL_DIR/procome.png"
    fi
fi

# Configurar permisos para puerto serie si es necesario
CURRENT_USER="${SUDO_USER:-$USER}"
if [ -n "$CURRENT_USER" ] && [ "$CURRENT_USER" != "root" ]; then
    # Verificar si el usuario ya está en el grupo dialout
    if ! groups "$CURRENT_USER" | grep -q '\bdialout\b'; then
        echo -e "${YELLOW}→${NC} Configurando permisos para puerto serie..."

        if getent group dialout > /dev/null 2>&1; then
            usermod -a -G dialout "$CURRENT_USER"
            echo -e "${GREEN}  Usuario '$CURRENT_USER' añadido al grupo 'dialout'${NC}"
            GRUPO_MODIFICADO=true
        fi

        if getent group uucp > /dev/null 2>&1; then
            usermod -a -G uucp "$CURRENT_USER"
            echo -e "${GREEN}  Usuario '$CURRENT_USER' añadido al grupo 'uucp'${NC}"
            GRUPO_MODIFICADO=true
        fi
    fi
fi

# Crear script de desinstalación
cat > "$INSTALL_DIR/uninstall.sh" <<'UNINSTALL_EOF'
#!/bin/bash
echo "Desinstalando PROCOME..."
rm -f /usr/local/bin/procome
rm -f /usr/share/applications/procome.desktop
rm -rf /opt/procome
echo "PROCOME desinstalado correctamente"
UNINSTALL_EOF

chmod +x "$INSTALL_DIR/uninstall.sh"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Actualización completada${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "PROCOME ${CYAN}v${ULTIMA_VERSION}${NC} instalado en: ${BLUE}$INSTALL_DIR${NC}"
echo ""
echo -e "Para ejecutar PROCOME:"
echo -e "  ${YELLOW}procome${NC}  (desde cualquier terminal)"
echo ""
echo -e "O desde el menú de aplicaciones:"
echo -e "  ${YELLOW}Desarrollo → PROCOME v${ULTIMA_VERSION}${NC}"
echo ""

if [ -n "$GRUPO_MODIFICADO" ]; then
    echo -e "${YELLOW}IMPORTANTE:${NC} Se han modificado grupos de usuario."
    echo -e "Para que los cambios surtan efecto, debes:"
    echo -e "  1. Cerrar sesión y volver a iniciarla"
    echo -e "  2. O ejecutar: ${YELLOW}newgrp dialout${NC}"
    echo ""
fi

echo -e "Para desinstalar: ${YELLOW}sudo $INSTALL_DIR/uninstall.sh${NC}"
echo ""
