# Instalador de PROCOME para Ubuntu/Debian

Este documento describe cómo usar el instalador automático de PROCOME que descarga e instala el ejecutable precompilado.

## Requisitos Previos

- Ubuntu 20.04 o superior (también funciona en Debian, Linux Mint, Pop!_OS)
- Conexión a Internet
- `curl` o `wget` instalado (normalmente ya vienen instalados)

## Instalación

### Método 1: Descarga directa del instalador

```bash
# Descargar el instalador
curl -O https://raw.githubusercontent.com/proenotec/procome/main/install_ubuntu.sh

# Dar permisos de ejecución
chmod +x install_ubuntu.sh

# Ejecutar el instalador
./install_ubuntu.sh
```

### Método 2: Desde el repositorio clonado

Si ya tienes el código fuente:

```bash
cd /ruta/a/procome
./install_ubuntu.sh
```

## ¿Qué hace el instalador?

El script `install_ubuntu.sh` realiza las siguientes acciones:

1. **Verifica el sistema**: Comprueba que sea Ubuntu/Debian y que tenga las herramientas necesarias
2. **Descarga la última versión**: Obtiene el ejecutable más reciente desde GitHub Releases
3. **Instala el programa**: Coloca el ejecutable en `/opt/procome/`
4. **Crea acceso global**: Permite ejecutar `procome` desde cualquier terminal
5. **Integra con el menú**: Añade PROCOME al menú de aplicaciones de Ubuntu
6. **Crea el icono**: Genera un icono SVG personalizado
7. **Configura permisos**: Añade el usuario al grupo `dialout` para acceso al puerto serie
8. **Crea desinstalador**: Instala un script para desinstalar fácilmente

## Después de la instalación

### Ejecutar PROCOME

Tienes tres formas de ejecutar PROCOME:

1. **Desde el menú de aplicaciones**:
   - Presiona la tecla Super (tecla de Windows)
   - Busca "PROCOME"
   - Haz clic en el icono

2. **Desde la terminal**:
   ```bash
   procome
   ```

3. **Ruta completa**:
   ```bash
   /opt/procome/procome
   ```

### Permisos del puerto serie

**IMPORTANTE**: Si es tu primera instalación, necesitas **cerrar sesión y volver a entrar** para que los permisos del puerto serie se apliquen correctamente.

Esto es necesario para que PROCOME pueda acceder a `/dev/ttyUSB0` y otros puertos serie.

## Actualización

Para actualizar PROCOME a una versión más reciente, simplemente ejecuta el instalador nuevamente:

```bash
./install_ubuntu.sh
```

El instalador detectará automáticamente que ya está instalado y te preguntará si deseas actualizar.

## Desinstalación

Para desinstalar PROCOME:

```bash
sudo /opt/procome/uninstall.sh
```

Esto eliminará:
- El ejecutable de `/opt/procome/`
- El acceso global desde `/usr/local/bin/procome`
- La entrada del menú de aplicaciones

**Nota**: Los archivos de configuración en `~/.config/procome/` **NO** se eliminan automáticamente. Si deseas eliminarlos también:

```bash
rm -rf ~/.config/procome
```

## Ubicaciones de archivos

| Ubicación | Descripción |
|-----------|-------------|
| `/opt/procome/procome` | Ejecutable principal |
| `/opt/procome/procome.png` | Icono de la aplicación |
| `/opt/procome/version.txt` | Versión instalada |
| `/opt/procome/uninstall.sh` | Script de desinstalación |
| `/usr/local/bin/procome` | Enlace simbólico para acceso global |
| `~/.local/share/applications/procome.desktop` | Entrada del menú |
| `~/.config/procome/` | Configuración del usuario |

## Configuración

PROCOME almacena su configuración en:

```
~/.config/procome/PROCOME.cfg
```

Este archivo se crea automáticamente la primera vez que ejecutas PROCOME y puedes editarlo manualmente si es necesario.

## Solución de problemas

### El instalador no encuentra la última versión

Si obtienes un error al obtener la última versión:

1. Verifica tu conexión a Internet
2. Comprueba que existan releases en: https://github.com/proenotec/procome/releases
3. Asegúrate de que haya un archivo ejecutable Linux en la release

### No puedo acceder al puerto serie

Si obtienes errores de "Permission denied" al intentar usar el puerto serie:

1. Verifica que tu usuario esté en el grupo `dialout`:
   ```bash
   groups $USER
   ```
   Deberías ver `dialout` en la lista.

2. Si no está, el instalador debería haberlo agregado. Cierra sesión y vuelve a entrar.

3. Si el problema persiste, agrégalo manualmente:
   ```bash
   sudo usermod -a -G dialout $USER
   ```
   Luego cierra sesión y vuelve a entrar.

### PROCOME no aparece en el menú

Si no ves PROCOME en el menú de aplicaciones:

1. Actualiza la base de datos del menú:
   ```bash
   update-desktop-database ~/.local/share/applications
   ```

2. Cierra sesión y vuelve a entrar

3. Busca manualmente el archivo:
   ```bash
   ls -la ~/.local/share/applications/procome.desktop
   ```

### Error al descargar

Si el download falla:

1. Verifica tu conexión a Internet
2. Intenta descargar manualmente desde:
   https://github.com/proenotec/procome/releases/latest

3. Coloca el ejecutable en `/opt/procome/procome` manualmente:
   ```bash
   sudo mkdir -p /opt/procome
   sudo cp PROCOME_Linux /opt/procome/procome
   sudo chmod +x /opt/procome/procome
   ```

## Instalación en otras distribuciones

Aunque el instalador está optimizado para Ubuntu/Debian, también funciona en:

- Linux Mint
- Pop!_OS
- Elementary OS
- Otras distribuciones basadas en Ubuntu/Debian

Para otras distribuciones (Fedora, Arch, etc.), el instalador te preguntará si deseas continuar. La mayoría de funcionalidades deberían funcionar, pero puede requerir ajustes manuales.

## Desarrollo

Este instalador es parte del proyecto PROCOME:
https://github.com/proenotec/procome

Para reportar problemas o sugerencias sobre el instalador, abre un issue en GitHub.

## Licencia

Este instalador se distribuye bajo los mismos términos que PROCOME.
