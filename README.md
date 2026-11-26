# PROCOME

**Programa de Control Modular por Electrónica**

Software para conectar a tarjetas de telecontrol mediante el protocolo PROCOME por
puerto serie. Interfaz gráfica Qt (PySide6), multi-tarjeta (hasta 6) y modo monitor
pasivo para el bus RS-485.

## Características

- 📡 Comunicación serie RS-232/RS-485 con protocolo PROCOME
- 🖥️ Interfaz gráfica Qt (PySide6), una pestaña por tarjeta
- 🧵 Multi-tarjeta: hasta 6 tarjetas simultáneas compartiendo el puerto
- 📊 Monitorización de medidas analógicas y estados digitales
- 🔘 Envío de órdenes de control
- 🪟 Consola de diagnóstico (40 % de la pantalla a la izquierda; principal 60 % a la derecha)
- 👁️ Modo monitor pasivo para detectar dispositivos en el bus
- 🔔 Avisos por Telegram y beeps
- 💾 Configuración en XML (`PROCOME.cfg`)

## Requisitos

- **Linux** (probado en GNOME con XWayland), macOS o Windows
- **Python 3.9** o superior (probado con 3.14)
- **pyserial**, **requests** y **PySide6** (ver `requirements.txt`)
- Puerto serie accesible: el usuario debe estar en el grupo `dialout` (o `uucp`)

## Instalación rápida

```bash
# 1. Crear el entorno e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Permisos del puerto serie (requiere cerrar y volver a abrir sesión)
sudo usermod -a -G dialout $USER

# 3. Ejecutar
./run.sh
```

`./run.sh` crea el `.venv` automáticamente si no existe e instala las dependencias.

Consulta [INSTALACION.md](INSTALACION.md) para instrucciones por distribución.

## Uso

```bash
./run.sh                        # recomendado (gestiona el .venv)
python3 PROCOME_Arranque_Qt.py  # si ya tienes las dependencias instaladas
./dist/PROCOME                  # ejecutable standalone (ver EJECUTABLE.md)
```

> **Wayland:** la aplicación fuerza `QT_QPA_PLATFORM=xcb` porque en Wayland nativo el
> compositor no permite colocar las ventanas (consola 40 % / principal 60 %). Si
> prefieres Wayland nativo: `QT_QPA_PLATFORM=wayland ./run.sh` (las ventanas se
> colocarán donde decida el escritorio).

## Configuración

Edita `PROCOME.cfg` o usa el menú **Configuración** de la aplicación:

- **Puerto serie**: `/dev/ttyUSB0`, `COM3`, …
- **Baudios**: 300 … 115200 (por defecto 9600)
- **Bits de datos / Paridad / Bits de parada** (por defecto 8, E, 2)
- **Medidas / Estados / Órdenes** y **dirección PROCOME**
- **Tarjetas**: habilitar y dirección de cada una (hasta 6)
- **Telegram**: bot, token y chat
- **Monitor**: timeout sin actividad (5–3600 s) para marcar tarjetas en TIMEOUT
- **Consola**: líneas máximas, modo de mensajes (`explicado`/`hex`), beeps

Para aplicar cambios: **parar** la comunicación, cambiar, **guardar** y **arrancar**.
No hace falta reiniciar la aplicación.

## Estructura del proyecto

```
procome/
├── PROCOME_Arranque_Qt.py       # Punto de entrada Qt
├── PROCOME_FormPpal_Qt.py       # GUI principal y ventana de consola
├── PROCOME_GestorMultiTarjeta.py# Hilos de tarjeta, lector serie y arbitraje del bus
├── PROCOME_MaqEstados.py        # Máquina de estados del protocolo
├── PROCOME_ConstruirTramaTrm.py # Construcción de tramas a transmitir
├── PROCOME_ConstruirTramaRcp.py # Ensamblado de tramas recibidas
├── PROCOME_AnalizarTramaRcp.py  # Análisis de tramas recibidas
├── PROCOME_DetectorDispositivos.py # Modo monitor
├── PROCOME_General.py           # Constantes y utilidades
├── PROCOME_Telegram.py          # Notificaciones
├── FichConfig.py                # Configuración XML
├── PROCOME.cfg                  # Configuración por defecto
├── requirements.txt             # Dependencias Python
├── run.sh / build.sh            # Ejecutar / compilar
├── VERSION.md                   # Historial de versiones
└── AGENTS.md                    # Guía técnica del código
```

## Compilar el ejecutable

```bash
./build.sh          # PyInstaller -> dist/PROCOME
```

Detalles en [EJECUTABLE.md](EJECUTABLE.md).

## Actualización

`actualizar_procome.sh` descarga la última versión publicada en
`github.com/proenotec/procome` (assets `PROCOME-Linux` y `PROCOME.cfg`) y conserva tu
configuración. Ver [ACTUALIZACION.md](ACTUALIZACION.md).

## Solución de problemas

- **`Permission denied` en `/dev/ttyUSB0`** → añade el usuario a `dialout` y reinicia
  sesión.
- **No aparece el botón de maximizar** → la ventana no debe crearse con `setFixedSize()`
  (corregido en v3.1.1).
- **Las ventanas no se colocan 40/60** → comprueba que no estás en Wayland nativo; usa
  `./run.sh` (fuerza xcb).

Más casos en [INSTALACION.md](INSTALACION.md).

## Licencia

[Tu licencia aquí]

## Contacto

[Tu contacto aquí]
