# PROCOME

**Programa de Control Modular por Electrónica**

Software para conectar a tarjetas de telecontrol usando el protocolo PROCOME mediante comunicación por puerto serie.

## Características

- 📡 Comunicación serie RS-232 con protocolo PROCOME
- 🎮 Interfaz gráfica con Tkinter
- 📊 Monitoreo de medidas analógicas
- 🔘 Control de órdenes digitales
- 📈 Lectura de estados digitales
- ⚙️ Configuración flexible (Puerto serie, Baudios, Medidas, Estados, Órdenes)
- 💾 Guardado/Carga de configuración en XML
- 🚀 Ejecutable directamente sin necesidad de consola

## Requisitos

- **Sistema Operativo**: Linux, macOS o Windows (con WSL)
- **Python**: 3.6 o superior
- **Dependencias**: pyserial, tkinter

## Instalación Rápida

### Linux (Debian/Ubuntu, Fedora, Arch, openSUSE)

```bash
./install_dependencies.sh
```

### macOS

```bash
./install_dependencies_mac.sh
```

### Instalación Manual

```bash
# Instalar Python 3 y pip (ya incluye tkinter)
pip3 install --user -r requirements.txt
```

Consulta [INSTALACION.md](INSTALACION.md) para instrucciones detalladas.

## Uso

### Opción 1: Ejecutable directo (recomendado)
```bash
./PROCOME_Arranque.py
```

### Opción 2: Script wrapper
```bash
./procome
```

### Opción 3: Con Python
```bash
python3 PROCOME_Arranque.py
```

## Configuración

Edita `PROCOME.cfg` o usa el menú **Configuración** en la aplicación para cambiar:

- **Puerto serie**: Puerto de conexión (ej: `/dev/ttyUSB0`)
- **Baudios**: Velocidad de comunicación
- **Bits de datos**: Bits por carácter
- **Paridad**: Tipo de paridad (Ninguna, Par, Impar)
- **Bits de parada**: Bits de parada
- **Medidas**: Número de medidas analógicas
- **Estados**: Número de estados digitales
- **Órdenes**: Número de órdenes de control
- **Dirección PROCOME**: Dirección del dispositivo remoto

### Aplicar cambios

Después de cambiar la configuración:
1. **Parar** la comunicación (botón principal)
2. **Cambiar** parámetros (Menú → Configuración)
3. **Arrancar** la comunicación

No es necesario reiniciar la aplicación.

## Estructura del Proyecto

```
procome/
├── PROCOME_Arranque.py          # Punto de entrada (ejecutable)
├── PROCOME_FormPpal.py          # Interfaz gráfica principal
├── PROCOME_MaqEstados.py        # Máquina de estados del protocolo
├── PROCOME_ConstruirTramaRcp.py # Construcción de tramas de recepción
├── PROCOME_ConstruirTramaTrm.py # Construcción de tramas de transmisión
├── PROCOME_AnalizarTramaRcp.py  # Análisis de tramas de recepción
├── PROCOME_General.py           # Utilidades generales
├── FichConfig.py                # Gestión de configuración XML
├── PROCOME.cfg                  # Archivo de configuración
├── requirements.txt             # Dependencias Python
├── install_dependencies.sh      # Script instalador (Linux)
├── install_dependencies_mac.sh  # Script instalador (macOS)
├── procome                      # Script wrapper bash
├── PROCOME.desktop              # Integración con menú de aplicaciones
├── INSTALACION.md               # Guía de instalación detallada
└── README.md                    # Este archivo
```

## Menús

### Menú Archivo
- **Salir**: Cerrar la aplicación

### Menú Configuración
- **Puerto serie**: Cambiar parámetros del puerto serie
- **Configuración general**: Cambiar número de medidas, estados, órdenes y dirección
- **Guardar configuración**: Persistir cambios en PROCOME.cfg
- **Cargar configuración**: Restaurar configuración desde PROCOME.cfg

## Interfaz Gráfica

La interfaz muestra:

1. **Botón Principal**: Arrancar/Parar comunicación
2. **Frame Medidas**: Valores analógicos del dispositivo
3. **Frame Estados**: Estados digitales del dispositivo
4. **Frame Órdenes**: Botones para enviar órdenes de control
5. **Barra de Estado**: Información de conexión y dispositivo

## Solución de Problemas

Consulta [INSTALACION.md](INSTALACION.md) para soluciones de problemas comunes.

## Desarrollo

El código está organizado en módulos:

- **PROCOME_MaqEstados.py**: Implementa la máquina de estados del protocolo
- **PROCOME_ConstruirTramaTrm/Rcp.py**: Construcción y análisis de tramas
- **PROCOME_FormPpal.py**: Interfaz de usuario
- **FichConfig.py**: Persistencia de configuración

## Licencia

[Tu licencia aquí]

## Contacto

[Tu contacto aquí]
