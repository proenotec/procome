#!/bin/bash

################################################################################
# SCRIPT DE INSTALACIÓN DE DEPENDENCIAS - PROCOME (macOS)
################################################################################
#
# Este script instala todas las dependencias necesarias para ejecutar PROCOME
# en macOS.
#
# Requisitos previos:
# - Homebrew: https://brew.sh/
#
# Uso: ./install_dependencies_mac.sh
#
################################################################################

set -e

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

################################################################################
# FUNCIONES AUXILIARES
################################################################################

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}        $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

################################################################################
# FUNCIÓN PRINCIPAL
################################################################################

main() {
    print_header "Instalador de Dependencias - PROCOME (macOS)"

    # Verificar que se ejecuta desde el directorio correcto
    if [ ! -f "PROCOME_Arranque.py" ]; then
        print_error "No se encontró PROCOME_Arranque.py"
        print_info "Ejecuta este script desde el directorio raíz de PROCOME"
        exit 1
    fi

    # Verificar que es macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_error "Este script solo funciona en macOS"
        exit 1
    fi

    print_info "Sistema detectado: macOS"

    # Verificar si Homebrew está instalado
    if ! command -v brew &> /dev/null; then
        print_error "Homebrew no está instalado"
        print_info "Por favor, instala Homebrew primero:"
        print_info "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi

    print_success "Homebrew detectado"

    # Actualizar Homebrew
    print_info "Actualizando Homebrew..."
    brew update

    # Instalar Python 3
    print_info "Instalando Python 3..."
    if command -v python3 &> /dev/null; then
        print_success "Python 3 ya está instalado"
    else
        brew install python3
    fi

    # Instalar dependencias Python
    print_info "Instalando pyserial..."
    pip3 install --user pyserial

    # tkinter viene incluido con Python 3.9+ en macOS
    print_info "Verificando tkinter..."
    if python3 -c "import tkinter" 2>/dev/null; then
        print_success "tkinter está disponible"
    else
        print_warning "tkinter no está disponible"
        print_info "Intenta instalar la versión de Python desde python.org"
        print_info "https://www.python.org/downloads/macos/"
    fi

    # Hacer PROCOME_Arranque.py ejecutable
    if [ ! -x "./PROCOME_Arranque.py" ]; then
        print_info "Haciendo PROCOME_Arranque.py ejecutable..."
        chmod +x ./PROCOME_Arranque.py
    fi

    # Verificación post-instalación
    echo ""
    print_header "Verificando instalación"

    local all_ok=true

    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version)
        print_success "Python 3 instalado: $python_version"
    else
        print_error "Python 3 no está instalado"
        all_ok=false
    fi

    if python3 -c "import tkinter" 2>/dev/null; then
        print_success "tkinter instalado"
    else
        print_error "tkinter no está instalado"
        all_ok=false
    fi

    if python3 -c "import serial" 2>/dev/null; then
        print_success "pyserial instalado"
    else
        print_error "pyserial no está instalado"
        all_ok=false
    fi

    echo ""

    if [ "$all_ok" = true ]; then
        print_header "Instalación completada exitosamente"
        echo ""
        print_info "Puedes ejecutar PROCOME con:"
        echo "  ./PROCOME_Arranque.py"
        echo "  o"
        echo "  python3 PROCOME_Arranque.py"
        echo ""
    else
        print_header "Algunas dependencias no se instalaron correctamente"
        print_error "Por favor, verifica la salida anterior"
        exit 1
    fi
}

################################################################################
# EJECUTAR
################################################################################

main "$@"
