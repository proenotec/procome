#!/bin/bash

################################################################################
# INSTALADOR/ACTUALIZADOR DE PROCOME PARA UBUNTU
################################################################################
#
# Este script descarga e instala la última versión del ejecutable de PROCOME
# desde GitHub Releases e integra la aplicación en el menú de Ubuntu.
#
# Características:
# - Descarga automática desde GitHub Releases
# - Instalación en /opt/procome/
# - Integración con el menú de aplicaciones
# - Actualización automática si ya está instalado
# - Desinstalador incluido
#
# Uso: ./install_ubuntu.sh
#
################################################################################

set -e  # Salir si hay algún error

# Configuración
REPO_OWNER="proenotec"
REPO_NAME="procome"
APP_NAME="PROCOME"
INSTALL_DIR="/opt/procome"
EXECUTABLE_NAME="procome"
DESKTOP_FILE="$HOME/.local/share/applications/procome.desktop"
ICON_PATH="$INSTALL_DIR/procome.png"

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

################################################################################
# FUNCIONES AUXILIARES
################################################################################

print_header() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  $1"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

################################################################################
# VERIFICACIONES PREVIAS
################################################################################

check_requirements() {
    print_info "Verificando requisitos del sistema..."

    # Verificar que es Ubuntu/Debian
    if [ ! -f /etc/os-release ]; then
        print_error "No se pudo detectar el sistema operativo"
        exit 1
    fi

    . /etc/os-release
    if [[ ! "$ID" =~ ^(ubuntu|debian|linuxmint|pop)$ ]]; then
        print_warning "Este instalador está optimizado para Ubuntu/Debian"
        print_info "Detectado: $ID"
        read -p "¿Desea continuar de todos modos? (s/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            exit 1
        fi
    fi

    # Verificar curl o wget
    if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
        print_error "Se requiere curl o wget para descargar archivos"
        print_info "Instala curl con: sudo apt install curl"
        exit 1
    fi

    print_success "Requisitos verificados"
}

################################################################################
# OBTENCIÓN DE LA ÚLTIMA VERSIÓN
################################################################################

get_latest_release() {
    print_info "Obteniendo información de la última versión..."

    # Obtener la última release desde GitHub API
    local api_url="https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest"

    if command -v curl &> /dev/null; then
        RELEASE_INFO=$(curl -s "$api_url")
    else
        RELEASE_INFO=$(wget -qO- "$api_url")
    fi

    # Extraer versión
    VERSION=$(echo "$RELEASE_INFO" | grep '"tag_name":' | sed -E 's/.*"tag_name": "v?([^"]+)".*/\1/')

    if [ -z "$VERSION" ]; then
        print_error "No se pudo obtener información de la última versión"
        print_info "Verifica que existan releases en: https://github.com/$REPO_OWNER/$REPO_NAME/releases"
        exit 1
    fi

    # Buscar el ejecutable Linux en los assets
    DOWNLOAD_URL=$(echo "$RELEASE_INFO" | grep "browser_download_url.*Linux" | head -n 1 | cut -d '"' -f 4)

    if [ -z "$DOWNLOAD_URL" ]; then
        print_error "No se encontró ejecutable Linux en la release"
        print_info "Assets disponibles:"
        echo "$RELEASE_INFO" | grep "browser_download_url" | cut -d '"' -f 4
        exit 1
    fi

    print_success "Versión encontrada: v$VERSION"
    print_info "URL: $DOWNLOAD_URL"
}

################################################################################
# VERIFICAR SI YA ESTÁ INSTALADO
################################################################################

check_installed_version() {
    if [ -f "$INSTALL_DIR/version.txt" ]; then
        INSTALLED_VERSION=$(cat "$INSTALL_DIR/version.txt")
        print_info "Versión instalada actualmente: v$INSTALLED_VERSION"

        if [ "$INSTALLED_VERSION" = "$VERSION" ]; then
            print_warning "Ya tienes la última versión instalada (v$VERSION)"
            read -p "¿Deseas reinstalar? (s/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Ss]$ ]]; then
                print_info "Instalación cancelada"
                exit 0
            fi
        else
            print_info "Se actualizará de v$INSTALLED_VERSION a v$VERSION"
        fi
    else
        print_info "Primera instalación de PROCOME"
    fi
}

################################################################################
# DESCARGA E INSTALACIÓN
################################################################################

download_and_install() {
    print_header "Descargando PROCOME v$VERSION"

    # Crear directorio temporal
    TMP_DIR=$(mktemp -d)
    trap "rm -rf $TMP_DIR" EXIT

    # Descargar ejecutable
    print_info "Descargando desde GitHub..."
    if command -v curl &> /dev/null; then
        curl -L -o "$TMP_DIR/$EXECUTABLE_NAME" "$DOWNLOAD_URL" --progress-bar
    else
        wget -O "$TMP_DIR/$EXECUTABLE_NAME" "$DOWNLOAD_URL" --show-progress
    fi

    if [ ! -f "$TMP_DIR/$EXECUTABLE_NAME" ]; then
        print_error "Error al descargar el ejecutable"
        exit 1
    fi

    print_success "Descarga completada"

    # Crear directorio de instalación
    print_info "Instalando en $INSTALL_DIR..."
    sudo mkdir -p "$INSTALL_DIR"

    # Mover ejecutable
    sudo mv "$TMP_DIR/$EXECUTABLE_NAME" "$INSTALL_DIR/$EXECUTABLE_NAME"
    sudo chmod +x "$INSTALL_DIR/$EXECUTABLE_NAME"

    # Guardar versión instalada
    echo "$VERSION" | sudo tee "$INSTALL_DIR/version.txt" > /dev/null

    # Crear directorio para configuración del usuario
    mkdir -p "$HOME/.config/procome"

    print_success "Ejecutable instalado"

    # Crear symlink en /usr/local/bin (opcional, para acceso global)
    if [ ! -L "/usr/local/bin/$EXECUTABLE_NAME" ]; then
        print_info "Creando acceso global..."
        sudo ln -sf "$INSTALL_DIR/$EXECUTABLE_NAME" "/usr/local/bin/$EXECUTABLE_NAME"
        print_success "Ahora puedes ejecutar '$EXECUTABLE_NAME' desde cualquier terminal"
    fi
}

################################################################################
# CREAR ICONO
################################################################################

create_icon() {
    print_info "Creando icono de la aplicación..."

    # Crear un icono SVG simple (representando una placa electrónica)
    sudo tee "$ICON_PATH" > /dev/null << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="128" height="128" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg">
  <!-- Fondo placa -->
  <rect x="10" y="10" width="108" height="108" rx="8" fill="#2d5016" stroke="#1a3009" stroke-width="2"/>

  <!-- Pistas (circuitos) -->
  <path d="M 30 40 L 50 40 L 50 60 L 70 60" stroke="#c9b037" stroke-width="3" fill="none"/>
  <path d="M 50 60 L 50 80 L 70 80" stroke="#c9b037" stroke-width="3" fill="none"/>
  <path d="M 90 40 L 90 70 L 70 70" stroke="#c9b037" stroke-width="3" fill="none"/>

  <!-- Componentes -->
  <!-- IC Central -->
  <rect x="55" y="55" width="30" height="30" rx="2" fill="#1a1a1a" stroke="#333" stroke-width="1"/>
  <line x1="60" y1="60" x2="60" y2="80" stroke="#666" stroke-width="1"/>
  <line x1="65" y1="60" x2="65" y2="80" stroke="#666" stroke-width="1"/>
  <line x1="70" y1="60" x2="70" y2="80" stroke="#666" stroke-width="1"/>
  <line x1="75" y1="60" x2="75" y2="80" stroke="#666" stroke-width="1"/>
  <line x1="80" y1="60" x2="80" y2="80" stroke="#666" stroke-width="1"/>

  <!-- Resistencias -->
  <rect x="25" y="37" width="10" height="6" fill="#d4af37" stroke="#8b7500" stroke-width="1"/>
  <rect x="85" y="37" width="10" height="6" fill="#d4af37" stroke="#8b7500" stroke-width="1"/>

  <!-- LEDs -->
  <circle cx="90" cy="25" r="4" fill="#ff4444"/>
  <circle cx="100" cy="25" r="4" fill="#44ff44"/>
  <circle cx="110" cy="25" r="4" fill="#4444ff"/>

  <!-- Condensadores -->
  <rect x="25" y="75" width="3" height="12" fill="#4a90e2" stroke="#2d5a8f" stroke-width="1"/>
  <rect x="30" y="75" width="3" height="12" fill="#4a90e2" stroke="#2d5a8f" stroke-width="1"/>

  <!-- Texto PROCOME -->
  <text x="64" y="110" font-family="Arial, sans-serif" font-size="12" font-weight="bold"
        text-anchor="middle" fill="#c9b037">PROCOME</text>
</svg>
EOF

    print_success "Icono creado"
}

################################################################################
# INTEGRACIÓN CON EL MENÚ
################################################################################

create_desktop_entry() {
    print_info "Creando entrada en el menú de aplicaciones..."

    # Crear directorio si no existe
    mkdir -p "$(dirname "$DESKTOP_FILE")"

    # Crear archivo .desktop
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.1
Type=Application
Name=PROCOME
GenericName=Control Modular Electrónico
Comment=Programa de Control Modular por Electrónica - Sistema de comunicación serial
Exec=$INSTALL_DIR/$EXECUTABLE_NAME
Icon=$ICON_PATH
Terminal=false
Categories=Development;Electronics;Utility;
Keywords=serial;electronics;control;modbus;scada;
StartupNotify=true
StartupWMClass=procome
EOF

    chmod +x "$DESKTOP_FILE"

    # Actualizar base de datos de aplicaciones
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    fi

    print_success "Entrada de menú creada"
    print_info "PROCOME aparecerá en el menú de aplicaciones"
}

################################################################################
# CONFIGURAR PERMISOS PARA PUERTO SERIE
################################################################################

setup_serial_permissions() {
    print_info "Configurando permisos para puerto serie..."

    if groups "$USER" | grep -q '\bdialout\b'; then
        print_success "Usuario ya pertenece al grupo dialout"
    else
        print_warning "Agregando usuario al grupo dialout..."
        sudo usermod -a -G dialout "$USER"
        print_success "Usuario agregado al grupo dialout"
        print_warning "IMPORTANTE: Necesitas cerrar sesión y volver a entrar para aplicar los cambios"
        NEED_LOGOUT=true
    fi
}

################################################################################
# CREAR DESINSTALADOR
################################################################################

create_uninstaller() {
    print_info "Creando desinstalador..."

    sudo tee "$INSTALL_DIR/uninstall.sh" > /dev/null << 'UNINSTALL_SCRIPT'
#!/bin/bash

echo "=========================================="
echo "  Desinstalador de PROCOME"
echo "=========================================="
echo ""

read -p "¿Estás seguro de que deseas desinstalar PROCOME? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "Desinstalación cancelada"
    exit 0
fi

echo "Desinstalando PROCOME..."

# Eliminar directorio de instalación
if [ -d "/opt/procome" ]; then
    sudo rm -rf "/opt/procome"
    echo "✓ Directorio de instalación eliminado"
fi

# Eliminar symlink
if [ -L "/usr/local/bin/procome" ]; then
    sudo rm "/usr/local/bin/procome"
    echo "✓ Acceso global eliminado"
fi

# Eliminar entrada del menú
if [ -f "$HOME/.local/share/applications/procome.desktop" ]; then
    rm "$HOME/.local/share/applications/procome.desktop"
    echo "✓ Entrada del menú eliminada"
fi

# Actualizar base de datos de aplicaciones
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo ""
echo "PROCOME ha sido desinstalado completamente"
echo ""
echo "Nota: Los archivos de configuración en ~/.config/procome NO han sido eliminados"
echo "Si deseas eliminarlos también, ejecuta: rm -rf ~/.config/procome"
echo ""
UNINSTALL_SCRIPT

    sudo chmod +x "$INSTALL_DIR/uninstall.sh"

    print_success "Desinstalador creado en $INSTALL_DIR/uninstall.sh"
}

################################################################################
# RESUMEN FINAL
################################################################################

print_summary() {
    print_header "Instalación completada exitosamente"

    echo -e "${GREEN}PROCOME v$VERSION instalado correctamente${NC}"
    echo ""
    echo "Ubicación: $INSTALL_DIR/$EXECUTABLE_NAME"
    echo ""
    echo "Formas de ejecutar PROCOME:"
    echo "  1. Desde el menú de aplicaciones (busca 'PROCOME')"
    echo "  2. Desde la terminal: $EXECUTABLE_NAME"
    echo "  3. Ruta completa: $INSTALL_DIR/$EXECUTABLE_NAME"
    echo ""
    echo "Configuración: ~/.config/procome/"
    echo ""
    echo "Para desinstalar: sudo $INSTALL_DIR/uninstall.sh"
    echo ""

    if [ "${NEED_LOGOUT:-false}" = true ]; then
        echo -e "${YELLOW}┌────────────────────────────────────────────────────┐${NC}"
        echo -e "${YELLOW}│  ⚠  IMPORTANTE: CIERRA SESIÓN Y VUELVE A ENTRAR  │${NC}"
        echo -e "${YELLOW}│     para que los permisos del puerto serie        │${NC}"
        echo -e "${YELLOW}│     se apliquen correctamente                     │${NC}"
        echo -e "${YELLOW}└────────────────────────────────────────────────────┘${NC}"
        echo ""
    fi
}

################################################################################
# FUNCIÓN PRINCIPAL
################################################################################

main() {
    print_header "Instalador de PROCOME para Ubuntu/Debian"

    # Verificaciones
    check_requirements

    # Obtener última versión
    get_latest_release

    # Verificar versión instalada
    check_installed_version

    # Confirmar instalación
    echo ""
    read -p "¿Deseas instalar PROCOME v$VERSION? (S/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_info "Instalación cancelada"
        exit 0
    fi

    # Descargar e instalar
    download_and_install

    # Crear icono
    create_icon

    # Integrar con el menú
    create_desktop_entry

    # Configurar permisos
    setup_serial_permissions

    # Crear desinstalador
    create_uninstaller

    # Resumen
    print_summary
}

################################################################################
# EJECUTAR
################################################################################

main "$@"
