# Actualización Automática de PROCOME

Este documento explica cómo actualizar PROCOME a la última versión disponible en GitHub de forma automática.

## 📥 Script de Actualización Automática

PROCOME incluye un script que descarga e instala automáticamente la última versión desde GitHub.

### Características

- ✅ Detecta la versión instalada actualmente
- ✅ Consulta la última versión disponible en GitHub
- ✅ Descarga el ejecutable automáticamente
- ✅ Preserva tu configuración existente (`PROCOME.cfg`)
- ✅ Actualiza el enlace simbólico y entrada del menú
- ✅ Configura permisos de puerto serie si es necesario

## 🚀 Uso

### Método 1: Desde el repositorio clonado

Si tienes el repositorio clonado:

```bash
cd /ruta/a/procome
sudo ./actualizar_procome.sh
```

### Método 2: Descarga directa (recomendado)

Puedes descargar y ejecutar el script directamente:

```bash
# Descargar el script
wget https://raw.githubusercontent.com/proenotec/procome/main/actualizar_procome.sh

# Dar permisos de ejecución
chmod +x actualizar_procome.sh

# Ejecutar con sudo
sudo ./actualizar_procome.sh
```

O en un solo comando:

```bash
curl -fsSL https://raw.githubusercontent.com/proenotec/procome/main/actualizar_procome.sh | sudo bash
```

## 📋 ¿Qué hace el script?

1. **Verifica** la versión instalada en `/opt/procome/version.txt`
2. **Consulta** la última versión disponible en GitHub
3. **Compara** ambas versiones
4. **Descarga** el ejecutable `PROCOME-Linux` si hay una nueva versión
5. **Hace backup** de tu configuración actual (`PROCOME.cfg`)
6. **Instala** el nuevo ejecutable en `/opt/procome/`
7. **Restaura** tu configuración anterior
8. **Actualiza** el enlace simbólico en `/usr/local/bin/procome`
9. **Actualiza** la entrada del menú de aplicaciones

## 🔧 Requisitos

El script necesita **uno** de estos comandos instalados:
- `curl` (recomendado)
- `wget`
- `gh` (GitHub CLI)

Para instalar curl:
```bash
sudo apt install curl
```

## 💡 Ejemplos de Uso

### Actualizar a la última versión

```bash
sudo ./actualizar_procome.sh
```

Salida esperada:
```
========================================
  Actualizador de PROCOME
========================================

Versión instalada: 2.5.1
→ Consultando última versión en GitHub...
Última versión: 2.6.0

Se actualizará de v2.5.1 a v2.6.0

→ Descargando PROCOME v2.6.0...
PROCOME-Linux      100%[============>] 279M  10.2MB/s    en 28s

→ Haciendo backup de la configuración...
→ Instalando en /opt/procome...
→ Restaurando configuración anterior...
→ Actualizando enlace simbólico...
→ Actualizando entrada en el menú de aplicaciones...

========================================
  ✓ Actualización completada
========================================

PROCOME v2.6.0 instalado en: /opt/procome

Para ejecutar PROCOME:
  procome  (desde cualquier terminal)

O desde el menú de aplicaciones:
  Desarrollo → PROCOME v2.6.0
```

### Reinstalar la misma versión

Si ya tienes la última versión, el script te preguntará si deseas reinstalar:

```bash
sudo ./actualizar_procome.sh
```

```
Versión instalada: 2.6.0
Última versión: 2.6.0

✓ Ya tienes la última versión instalada

¿Deseas reinstalar v2.6.0? (s/N):
```

## 🔒 Seguridad

### Verificaciones del script

El script realiza varias verificaciones de seguridad:

1. ✅ Verifica que se ejecuta con `sudo` (necesario para instalar en `/opt/`)
2. ✅ Descarga desde GitHub oficial (`github.com/proenotec/procome`)
3. ✅ Verifica que el archivo descargado es un ejecutable ELF válido
4. ✅ Usa HTTPS para todas las descargas
5. ✅ Limpia archivos temporales automáticamente

### Revisar el script antes de ejecutar

Siempre puedes revisar el contenido del script:

```bash
less actualizar_procome.sh
```

O ver el código en GitHub:
https://github.com/proenotec/procome/blob/main/actualizar_procome.sh

## 📁 Ubicación de Archivos

Después de la actualización, los archivos estarán en:

```
/opt/procome/
├── PROCOME              # Ejecutable principal
├── PROCOME.cfg          # Tu configuración (preservada)
├── version.txt          # Versión instalada
├── procome.png          # Icono de la aplicación
└── uninstall.sh         # Script de desinstalación

/usr/local/bin/
└── procome              # Enlace simbólico (para ejecutar desde terminal)

/usr/share/applications/
└── procome.desktop      # Entrada del menú de aplicaciones
```

## 🔄 Preservación de Configuración

El script **SIEMPRE preserva** tu archivo de configuración (`PROCOME.cfg`) durante la actualización:

1. Hace un backup antes de instalar
2. Restaura el backup después de instalar
3. Solo usa la configuración predeterminada si nunca has tenido PROCOME instalado

### Parámetros preservados

- Configuración del puerto serie (puerto, baudios, paridad, etc.)
- Número de medidas, estados y órdenes
- Dirección remota del protocolo
- Configuración de tarjetas multi-tarjeta
- Configuración de Telegram
- Límites de consola

## ⚙️ Opciones Avanzadas

### Instalar una versión específica

Si necesitas instalar una versión específica en lugar de la última, puedes modificar el script temporalmente:

```bash
# Editar el script
nano actualizar_procome.sh

# Cambiar esta línea (aproximadamente línea 48):
ULTIMA_VERSION=$(gh release view --repo "$REPO" ...)

# Por esto (ejemplo para instalar v2.5.0):
ULTIMA_VERSION="2.5.0"
```

### Verificar la instalación

Después de actualizar, verifica la versión instalada:

```bash
cat /opt/procome/version.txt
```

O ejecuta PROCOME y verifica el título de la ventana:
```bash
procome
```

## 🐛 Solución de Problemas

### Error: "No se pudo obtener la última versión"

**Causa**: Problema de conexión a GitHub o API rate limit.

**Solución**:
```bash
# Verifica conexión a internet
ping github.com

# Espera unos minutos y vuelve a intentar
sudo ./actualizar_procome.sh
```

### Error: "El archivo descargado no es un ejecutable válido"

**Causa**: La descarga se interrumpió o GitHub tiene problemas.

**Solución**:
```bash
# Limpia descargas parciales y vuelve a intentar
sudo ./actualizar_procome.sh
```

### Error: "Este script debe ejecutarse con sudo"

**Causa**: No tienes permisos de administrador.

**Solución**:
```bash
# Ejecuta con sudo
sudo ./actualizar_procome.sh
```

### La aplicación no aparece en el menú

**Causa**: El sistema de escritorio necesita actualizar su cache.

**Solución**:
```bash
# Actualizar cache del menú de aplicaciones
update-desktop-database
```

## 📞 Soporte

Si encuentras problemas con el script de actualización:

1. **Revisa los logs**: El script muestra mensajes detallados
2. **Verifica requisitos**: Asegúrate de tener `curl` o `wget`
3. **Comprueba permisos**: Debes ejecutar con `sudo`
4. **Reporta el problema**: https://github.com/proenotec/procome/issues

## 🔗 Enlaces Útiles

- **Releases de GitHub**: https://github.com/proenotec/procome/releases
- **Script de actualización**: https://github.com/proenotec/procome/blob/main/actualizar_procome.sh
- **Repositorio**: https://github.com/proenotec/procome
- **Issues**: https://github.com/proenotec/procome/issues

---

**Última actualización**: 2026-01-23
**Versión del script**: 1.0.0
