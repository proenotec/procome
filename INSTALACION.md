# Guía de Instalación - PROCOME

## Requisitos del Sistema

- **Sistema Operativo**: Linux (Debian/Ubuntu, Fedora/RHEL, Arch/Manjaro, openSUSE)
- **Python**: versión 3.6 o superior
- **Dependencias del sistema**: tkinter, acceso a puerto serie

## Instalación Automatizada (Recomendado)

### Opción 1: Script de Instalación (Linux)

El script `install_dependencies.sh` detecta automáticamente tu distribución Linux e instala todas las dependencias necesarias.

```bash
./install_dependencies.sh
```

El script:
- ✅ Detecta automáticamente tu distribución Linux
- ✅ Instala Python 3, pip y tkinter
- ✅ Instala la librería pyserial
- ✅ Configura permisos de acceso al puerto serie
- ✅ Verifica que todo está instalado correctamente

### Opción 2: Instalación Manual con pip

Si prefieres una instalación manual o tu distribución no está soportada:

```bash
# 1. Instalar Python 3 y herramientas de desarrollo
sudo apt-get install python3 python3-pip python3-tk  # Debian/Ubuntu
# o
sudo dnf install python3 python3-pip python3-tkinter  # Fedora/RHEL
# o
sudo pacman -S python python-pip tk                   # Arch/Manjaro
# o
sudo zypper install python3 python3-pip python3-tk    # openSUSE

# 2. Instalar dependencias Python
pip3 install --user -r requirements.txt

# 3. Añadir usuario al grupo dialout (acceso puerto serie)
sudo usermod -a -G dialout $USER

# 4. Cerrar sesión y volver a conectarse para aplicar cambios de grupo
```

### Opción 3: Instalación con conda (Anaconda/Miniconda)

Si tienes Anaconda o Miniconda instalado:

```bash
conda create -n procome python=3.9
conda activate procome
pip install -r requirements.txt
```

## Requisitos Específicos

### Python y pip
- Python 3.6 o superior
- pip (gestor de paquetes Python)

### Librerías Python
- **pyserial** (>=3.5): Para comunicación con puerto serie
- **tkinter**: Interfaz gráfica (incluida en Python)
- Módulos estándar: `os`, `sys`, `time`, `serial`, `xml`

### Acceso a Puerto Serie

Para acceder al puerto serie sin permisos de administrador:

```bash
# Opción 1: Agregar usuario al grupo dialout (Linux)
sudo usermod -a -G dialout $USER

# Opción 2: Agregar usuario al grupo uucp (Arch/Manjaro)
sudo usermod -a -G uucp $USER
```

**Importante**: Después de ejecutar estos comandos, debes cerrar sesión y volver a conectarte para que los cambios tengan efecto.

## Verificación de la Instalación

Para verificar que todo está instalado correctamente:

```bash
python3 -c "import tkinter; print('✓ tkinter OK')"
python3 -c "import serial; print('✓ pyserial OK')"
```

O ejecuta el script de instalación con la opción de verificación:

```bash
./install_dependencies.sh
```

## Ejecución de PROCOME

Una vez instaladas todas las dependencias, puedes ejecutar PROCOME de varias formas:

### Forma 1: Ejecutable directo (recomendado)
```bash
./PROCOME_Arranque.py
```

### Forma 2: Script wrapper
```bash
./procome
```

### Forma 3: Python directo
```bash
python3 PROCOME_Arranque.py
```

### Forma 4: Desde el menú de aplicaciones (opcional)
```bash
sudo cp PROCOME.desktop /usr/share/applications/
```

## Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'serial'"

**Solución**: Instala pyserial
```bash
pip3 install --user pyserial
```

### Error: "ModuleNotFoundError: No module named 'tkinter'"

**Solución**: Instala tkinter para tu distribución
```bash
# Debian/Ubuntu
sudo apt-get install python3-tk

# Fedora/RHEL
sudo dnf install python3-tkinter

# Arch/Manjaro
sudo pacman -S tk

# openSUSE
sudo zypper install python3-tk
```

### Error: "Permission denied" al acceder al puerto serie

**Solución**: Añade tu usuario al grupo dialout/uucp y reinicia sesión
```bash
sudo usermod -a -G dialout $USER   # Debian/Ubuntu/Fedora/openSUSE
# o
sudo usermod -a -G uucp $USER      # Arch/Manjaro

# Luego cierra sesión y vuelve a conectarte
```

### Error: "PROCOME_Arranque.py: Permission denied"

**Solución**: Haz el archivo ejecutable
```bash
chmod +x PROCOME_Arranque.py
```

## Desinstalación

Para desinstalar PROCOME y sus dependencias:

```bash
# Solo desinstalar pyserial (mantiene Python)
pip3 uninstall pyserial

# Para desinstalar completamente (solo si no la necesitas):
sudo apt-get remove python3-tk python3-pip python3  # Debian/Ubuntu
# o similar para tu distribución
```

## Soporte

Si tienes problemas con la instalación:

1. Verifica tu distribución Linux: `cat /etc/os-release`
2. Ejecuta el script de instalación de nuevo
3. Consulta los logs de error

## Distribuciones Soportadas

El script `install_dependencies.sh` soporta automáticamente:

- ✅ **Debian/Ubuntu** (y derivados: Linux Mint, Pop!_OS, etc.)
- ✅ **Fedora/RHEL/CentOS** (y derivados: Rocky Linux, AlmaLinux, etc.)
- ✅ **Arch/Manjaro** (y derivados)
- ✅ **openSUSE** (Leap y Tumbleweed)

Para otras distribuciones, usa la instalación manual con pip.
