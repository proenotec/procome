# Ejecutable PROCOME - Guía de Uso

## Compilar

```bash
./build.sh
```

El script:

1. Activa el `.venv` (créalo antes con `./run.sh` si no existe).
2. Instala PyInstaller si falta.
3. Limpia `build/`, `dist/` y `PROCOME.spec`.
4. Compila con PyInstaller en modo `--onefile --windowed`.
5. Deja el binario en `dist/PROCOME` (unos 290 MB: incluye Qt/PySide6 completo).

Compilar tarda varios minutos. Los avisos de PyInstaller sobre bibliotecas Qt opcionales
son normales.

## Ejecutar

```bash
./dist/PROCOME                  # desde el directorio del proyecto
./PROCOME                       # si lo copias junto a PROCOME.cfg
```

El binario lleva `PROCOME.cfg` embebido como copia inicial; si existe un `PROCOME.cfg`
junto al ejecutable se usa ese (tu configuración).

## Distribución

Hay que distribuir dos ficheros:

1. **PROCOME** — el ejecutable
2. **PROCOME.cfg** — la configuración (se puede editar con la aplicación)

No hace falta Python ni dependencias en el equipo destino. En Linux hacen falta las
bibliotecas de sistema habituales de Qt; si al arrancar falla por `xcb`, instala:

```bash
sudo apt install libxcb-cursor0 libxcb-xinerama0
```

## Wayland y XWayland

La aplicación fuerza `QT_QPA_PLATFORM=xcb` (XWayland) porque en Wayland nativo el
compositor ignora la posición de las ventanas y no se puede repartir la pantalla
consola 40 % / principal 60 %. Si el equipo no tiene XWayland, se puede forzar Wayland:

```bash
QT_QPA_PLATFORM=wayland ./PROCOME
```

En ese caso las ventanas no se colocarán automáticamente.

## Releases

El lanzamiento público se publica en GitHub (`proenotec/procome`) con estos assets:

| Asset | Contenido |
|---|---|
| `PROCOME-Linux` | Binario Linux x86_64 |
| `PROCOME-Windows.exe` | Binario Windows (lo genera el CI) |
| `PROCOME.cfg` | Configuración por defecto |

`actualizar_procome.sh` descarga `PROCOME-Linux` de la release más reciente y conserva
el `PROCOME.cfg` del equipo.

## Características del binario

- ✅ Standalone (no requiere Python instalado)
- ✅ PySide6, pyserial y requests incluidos
- ✅ Interfaz Qt completa y ventana de consola
- ✅ Linux x86_64 (y Windows x64 vía CI)
- ✅ Fuerza XWayland para poder colocar las ventanas

## Notas

- El binario es un ELF que se puede ejecutar directamente.
- La primera ejecución tarda unos segundos mientras extrae los recursos empaquetados.
- Para depurar, ejecútalo desde una terminal: la salida de la consola interna también
  se escribe en la terminal.
