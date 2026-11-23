# Guía de Instalación - PROCOME

## Requisitos

- **Linux** (Debian/Ubuntu, Fedora/RHEL, Arch/Manjaro, openSUSE), macOS o Windows
- **Python 3.9 o superior** (probado con 3.14)
- **PySide6**, **pyserial** y **requests**
- Acceso al puerto serie (`dialout` en Debian/Fedora/openSUSE, `uucp` en Arch)

## Instalación rápida (Linux)

```bash
./run.sh
```

La primera vez crea `.venv`, instala `requirements.txt` y arranca la aplicación. En las
siguientes ejecuciones sólo activa el entorno y arranca.

### Instalación manual

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 PROCOME_Arranque_Qt.py
```

### Dependencias de sistema (Qt)

En Linux, Qt necesita algunas bibliotecas X11/xcb:

```bash
# Debian/Ubuntu
sudo apt install python3-venv libxcb-cursor0 libxcb-xinerama0

# Fedora/RHEL
sudo dnf install python3-devel libxcb

# Arch/Manjaro
sudo pacman -S python libxcb

# openSUSE
sudo zypper install python3 libxcb
```

## Permisos del puerto serie

```bash
# Debian/Ubuntu/Fedora/openSUSE
sudo usermod -a -G dialout $USER

# Arch/Manjaro
sudo usermod -a -G uucp $USER
```

**Importante**: cierra sesión y vuelve a entrar para que el grupo se aplique.

## Verificación

```bash
python3 -c "import serial, PySide6, requests; print('dependencias OK')"
ls -l /dev/ttyUSB0        # debe ser accesible por tu usuario
```

Si el puerto no existe, revisa el adaptador USB-serie (`dmesg | tail`).

## Ejecución

```bash
./run.sh                          # recomendado
python3 PROCOME_Arranque_Qt.py    # con el entorno activado
./dist/PROCOME                    # ejecutable standalone
```

Menú de aplicaciones (opcional):

```bash
sudo cp PROCOME.desktop /usr/share/applications/
```

## Wayland

La aplicación fuerza `QT_QPA_PLATFORM=xcb` para poder colocar la consola (40 % izquierda)
y la ventana principal (60 % derecha). En Wayland nativo el compositor ignora la posición
de las ventanas. Si prefieres Wayland nativo:

```bash
QT_QPA_PLATFORM=wayland ./run.sh
```

## Solución de problemas

### `ModuleNotFoundError: No module named 'serial'`

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### `ModuleNotFoundError: No module named 'PySide6'`

Igual que el anterior: instala `requirements.txt` dentro del `.venv`. Si usas
`python3 PROCOME_Arranque_Qt.py` sin activar el entorno, no encontrará PySide6.

### Qt no arranca: `Could not load the Qt platform plugin "xcb"`

Faltan bibliotecas del sistema:

```bash
sudo apt install libxcb-cursor0 libxcb-xinerama0   # Debian/Ubuntu
```

### `Permission denied` al abrir `/dev/ttyUSB0`

Añade el usuario a `dialout`/`uucp` y reinicia sesión (ver arriba).

### Las ventanas no se reparten 40/60

Comprueba que se arranca con `./run.sh` (fuerza xcb) y que no hay
`QT_QPA_PLATFORM=wayland` en el entorno.

### No aparece el botón de maximizar

Corregido en v3.1.1: la ventana ya no se crea con tamaño fijo. Actualiza a la última
versión.

## Desinstalación

```bash
rm -rf .venv                 # entorno de desarrollo
sudo rm -f /usr/local/bin/procome
sudo rm -rf /opt/procome     # instalación del ejecutable
```

## Distribuciones soportadas

- ✅ Debian/Ubuntu y derivados (Mint, Pop!_OS…)
- ✅ Fedora/RHEL/CentOS y derivados (Rocky, AlmaLinux…)
- ✅ Arch/Manjaro
- ✅ openSUSE Leap/Tumbleweed
