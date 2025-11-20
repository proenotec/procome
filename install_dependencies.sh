#!/bin/bash

################################################################################
# SCRIPT DE INSTALACIÓN DE DEPENDENCIAS - PROCOME
################################################################################
#
# Este script instala todas las dependencias necesarias para ejecutar PROCOME
# en sistemas Linux con Python 3.
#
# Soporta:
# - Debian/Ubuntu (apt)
# - Fedora/RHEL/CentOS (dnf/yum)
# - Arch/Manjaro (pacman)
# - openSUSE (zypper)
#
# Uso: ./install_dependencies.sh
#
################################################################################

set -e  # Salir si hay algún error

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
# DETECCIÓN DEL SISTEMA OPERATIVO
################################################################################

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        print_error "No se pudo detectar el sistema operativo"
        exit 1
    fi
}

################################################################################
# INSTALACIÓN DE DEPENDENCIAS POR DISTRIBUCIÓN
################################################################################

install_debian_ubuntu() {
    print_info "Sistema detectado: Debian/Ubuntu"

    print_info "Actualizando lista de paquetes..."
    sudo apt-get update

    print_info "Instalando Python 3 y pip..."
    sudo apt-get install -y python3 python3-pip python3-dev

    print_info "Instalando dependencias del sistema (tkinter y acceso a puerto serie)..."
    sudo apt-get install -y python3-tk

    print_info "Instalando grupo dialout (para acceso a puerto serie)..."
    sudo usermod -a -G dialout $USER
    print_warning "Necesitarás cerrar sesión y volver a conectarte para que los cambios de grupo se apliquen"

    print_info "Instalando dependencias Python..."
    pip3 install --user pyserial
}

install_fedora_rhel() {
    print_info "Sistema detectado: Fedora/RHEL/CentOS"

    print_info "Instalando Python 3 y pip..."
    sudo dnf install -y python3 python3-pip python3-devel

    print_info "Instalando dependencias del sistema (tkinter)..."
    sudo dnf install -y python3-tkinter

    print_info "Instalando grupo dialout (para acceso a puerto serie)..."
    sudo usermod -a -G dialout $USER
    print_warning "Necesitarás cerrar sesión y volver a conectarte para que los cambios de grupo se apliquen"

    print_info "Instalando dependencias Python..."
    pip3 install --user pyserial
}

install_arch_manjaro() {
    print_info "Sistema detectado: Arch/Manjaro"

    print_info "Instalando Python 3 y pip..."
    sudo pacman -S --noconfirm python python-pip

    print_info "Instalando dependencias del sistema (tkinter)..."
    sudo pacman -S --noconfirm tk

    print_info "Instalando grupo uucp (para acceso a puerto serie)..."
    sudo usermod -a -G uucp $USER
    print_warning "Necesitarás cerrar sesión y volver a conectarte para que los cambios de grupo se apliquen"

    print_info "Instalando dependencias Python..."
    pip3 install --user pyserial
}

install_opensuse() {
    print_info "Sistema detectado: openSUSE"

    print_info "Instalando Python 3 y pip..."
    sudo zypper install -y python3 python3-pip python3-devel

    print_info "Instalando dependencias del sistema (tkinter)..."
    sudo zypper install -y python3-tk

    print_info "Instalando grupo dialout (para acceso a puerto serie)..."
    sudo usermod -a -G dialout $USER
    print_warning "Necesitarás cerrar sesión y volver a conectarte para que los cambios de grupo se apliquen"

    print_info "Instalando dependencias Python..."
    pip3 install --user pyserial
}

################################################################################
# INSTALACIÓN GENÉRICA CON PIP
################################################################################

install_python_dependencies() {
    print_info "Instalando dependencias Python con pip..."
    pip3 install --user pyserial
}

################################################################################
# VERIFICACIÓN POST-INSTALACIÓN
################################################################################

verify_installation() {
    print_header "Verificando instalación"

    local all_ok=true

    # Verificar Python 3
    if command -v python3 &> /dev/null; then
        local python_version=$(python3 --version)
        print_success "Python 3 instalado: $python_version"
    else
        print_error "Python 3 no está instalado"
        all_ok=false
    fi

    # Verificar pip3
    if command -v pip3 &> /dev/null; then
        print_success "pip3 instalado"
    else
        print_error "pip3 no está instalado"
        all_ok=false
    fi

    # Verificar tkinter
    if python3 -c "import tkinter" 2>/dev/null; then
        print_success "tkinter instalado"
    else
        print_error "tkinter no está instalado"
        all_ok=false
    fi

    # Verificar pyserial
    if python3 -c "import serial" 2>/dev/null; then
        print_success "pyserial instalado"
    else
        print_error "pyserial no está instalado"
        all_ok=false
    fi

    # Verificar que PROCOME_Arranque.py es ejecutable
    if [ -x "./PROCOME_Arranque.py" ]; then
        print_success "PROCOME_Arranque.py es ejecutable"
    else
        print_warning "PROCOME_Arranque.py no es ejecutable, intentando corregir..."
        chmod +x ./PROCOME_Arranque.py
        print_success "Permisos corregidos"
    fi

    if [ "$all_ok" = true ]; then
        return 0
    else
        return 1
    fi
}

################################################################################
# FUNCIÓN PRINCIPAL
################################################################################

main() {
    print_header "Instalador de Dependencias - PROCOME"

    # Verificar que se ejecuta desde el directorio correcto
    if [ ! -f "PROCOME_Arranque.py" ]; then
        print_error "No se encontró PROCOME_Arranque.py"
        print_info "Ejecuta este script desde el directorio raíz de PROCOME"
        exit 1
    fi

    # Verificar que es Linux
    if [[ ! "$OSTYPE" =~ ^linux ]]; then
        print_error "Este script solo funciona en Linux"
        exit 1
    fi

    # Detectar el sistema operativo
    detect_os
    print_info "OS: $OS (versión $OS_VERSION)"

    # Instalar según el SO
    case "$OS" in
        debian|ubuntu)
            install_debian_ubuntu
            ;;
        fedora|rhel|centos)
            install_fedora_rhel
            ;;
        arch|manjaro)
            install_arch_manjaro
            ;;
        opensuse|opensuse-leap|opensuse-tumbleweed)
            install_opensuse
            ;;
        *)
            print_warning "Distribución no soportada directamente: $OS"
            print_info "Intentando instalación genérica con pip..."

            # Intentar instalar con herramientas disponibles
            if command -v apt-get &> /dev/null; then
                install_debian_ubuntu
            elif command -v dnf &> /dev/null; then
                install_fedora_rhel
            elif command -v pacman &> /dev/null; then
                install_arch_manjaro
            elif command -v zypper &> /dev/null; then
                install_opensuse
            else
                print_error "No se pudo detectar el administrador de paquetes"
                print_info "Por favor, instala manualmente:"
                print_info "  1. Python 3: https://www.python.org/"
                print_info "  2. tkinter (incluido en Python)"
                print_info "  3. pip install pyserial"
                exit 1
            fi
            ;;
    esac

    # Verificar la instalación
    echo ""
    if verify_installation; then
        echo ""
        print_header "Instalación completada exitosamente"
        echo ""
        print_info "Puedes ejecutar PROCOME con:"
        echo "  ./PROCOME_Arranque.py"
        echo "  o"
        echo "  ./procome"
        echo ""
        print_warning "Si agregaste tu usuario al grupo dialout/uucp, cierra sesión y vuelve a conectarte"
        echo ""
    else
        echo ""
        print_header "Algunas dependencias no se instalaron correctamente"
        print_error "Por favor, verifica la salida anterior"
        exit 1
    fi
}

################################################################################
# EJECUTAR
################################################################################

main "$@"
