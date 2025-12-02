#!/bin/bash

# Script para actualizar la versión de PROCOME antes de hacer commit
# Uso: ./actualizar_version.sh [major|minor|patch]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Archivos a modificar
ARCHIVO_GUI="PROCOME_FormPpal_Qt.py"
ARCHIVO_VERSION="VERSION.md"

# Función para mostrar uso
mostrar_uso() {
    echo -e "${YELLOW}Uso:${NC} $0 [major|minor|patch]"
    echo ""
    echo "  major  - Incrementa versión MAJOR (1.0.0 -> 2.0.0)"
    echo "  minor  - Incrementa versión MINOR (1.0.0 -> 1.1.0)"
    echo "  patch  - Incrementa versión PATCH (1.0.0 -> 1.0.1)"
    echo ""
    exit 1
}

# Verificar argumento
if [ $# -eq 0 ]; then
    mostrar_uso
fi

TIPO=$1

if [ "$TIPO" != "major" ] && [ "$TIPO" != "minor" ] && [ "$TIPO" != "patch" ]; then
    echo -e "${RED}Error:${NC} Tipo de versión inválido: $TIPO"
    mostrar_uso
fi

# Verificar que los archivos existen
if [ ! -f "$ARCHIVO_GUI" ]; then
    echo -e "${RED}Error:${NC} No se encuentra $ARCHIVO_GUI"
    exit 1
fi

if [ ! -f "$ARCHIVO_VERSION" ]; then
    echo -e "${RED}Error:${NC} No se encuentra $ARCHIVO_VERSION"
    exit 1
fi

# Extraer versión actual del archivo GUI
VERSION_ACTUAL=$(grep -E '_VERSION = "[0-9]+\.[0-9]+\.[0-9]+"' "$ARCHIVO_GUI" | sed -E 's/.*"([0-9]+\.[0-9]+\.[0-9]+)".*/\1/')

if [ -z "$VERSION_ACTUAL" ]; then
    echo -e "${RED}Error:${NC} No se pudo extraer la versión actual"
    exit 1
fi

echo -e "${BLUE}Versión actual:${NC} $VERSION_ACTUAL"

# Dividir versión en componentes
IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION_ACTUAL"

# Incrementar según el tipo
case "$TIPO" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
esac

VERSION_NUEVA="$MAJOR.$MINOR.$PATCH"

echo -e "${GREEN}Nueva versión:${NC} $VERSION_NUEVA"
echo ""

# Pedir confirmación
read -p "¿Desea actualizar la versión? (s/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
    echo -e "${YELLOW}Operación cancelada${NC}"
    exit 0
fi

# Actualizar archivo GUI
echo -e "${BLUE}Actualizando${NC} $ARCHIVO_GUI..."
sed -i "s/_VERSION = \"$VERSION_ACTUAL\"/_VERSION = \"$VERSION_NUEVA\"/" "$ARCHIVO_GUI"

# Actualizar archivo VERSION.md
echo -e "${BLUE}Actualizando${NC} $ARCHIVO_VERSION..."
sed -i "s/## Versión Actual: $VERSION_ACTUAL/## Versión Actual: $VERSION_NUEVA/" "$ARCHIVO_VERSION"

echo ""
echo -e "${GREEN}✓ Versión actualizada exitosamente a v$VERSION_NUEVA${NC}"
echo ""
echo "Próximos pasos:"
echo "  1. Revisar los cambios: git diff"
echo "  2. Hacer commit: git add $ARCHIVO_GUI $ARCHIVO_VERSION"
echo "  3. Commit: git commit -m \"Actualizar versión a v$VERSION_NUEVA - [Descripción]\""
echo "  4. Push: git push"
echo ""
