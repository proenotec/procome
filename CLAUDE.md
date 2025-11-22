# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PROCOME (Programa de Control Modular por Electrónica) is a Python application for serial communication with remote control devices using the proprietary PROCOME protocol. It provides a GUI interface (both Tkinter and Qt versions) to monitor analog measurements, digital states, and send control commands over RS-232 serial connections.

## Running the Application

### Development Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
# Tkinter version (original)
./PROCOME_Arranque.py
# or
python3 PROCOME_Arranque.py

# Qt version (newer, with console window)
./run.sh
# or
source .venv/bin/activate && python3 PROCOME_Arranque_Qt.py
```

The `run.sh` script automatically manages the virtual environment for the Qt version.

## Architecture Overview

### Core Components

1. **State Machine (`PROCOME_MaqEstados.py`)**
   - Implements the PROCOME protocol state machine
   - Manages communication states: Enlace (Link), Inicialización (Init), Bucle (Loop), Control
   - Handles timeouts, retries, and periodic synchronization
   - Key constants: `_K_iNrMaxIntentos` (max retries), timeout values for different operations

2. **Frame Construction/Analysis**
   - `PROCOME_ConstruirTramaTrm.py`: Builds transmission frames
   - `PROCOME_ConstruirTramaRcp.py`: Builds reception frame handlers
   - `PROCOME_AnalizarTramaRcp.py`: Analyzes and validates received frames
   - Supports both short frames (5 bytes) and long frames (variable length)

3. **Protocol Constants (`PROCOME_General.py`)**
   - Frame structure definitions (start bytes, checksums, etc.)
   - Protocol addresses: `PROCOME_DIR_MIN` (0), `PROCOME_DIR_MAX` (254), `PROCOME_DIR_UNIVERSAL` (255)
   - Response types: ACK, NACK, DATOSUSUARIO

4. **Configuration Management (`FichConfig.py`)**
   - XML-based configuration file handling (PROCOME.cfg)
   - Parameters: serial port settings, number of measurements/states/orders, protocol address
   - Provides getters/setters with validation

5. **GUI Layers**
   - **Tkinter version** (`PROCOME_FormPpal.py`): Original GUI implementation
   - **Qt version** (`PROCOME_FormPpal_Qt.py`): Newer implementation with PySide6, includes console window for log viewing
   - Both provide: start/stop communication, measurement display, state monitoring, order buttons, configuration dialogs

### Main Entry Points

- `PROCOME_Arranque.py`: Tkinter version launcher
- `PROCOME_Arranque_Qt.py`: Qt version launcher (uses virtual environment)

### File Encoding

All Python files use UTF-8 encoding with `# -*- coding: utf-8 -*-` declaration. Historical issues with character encoding (cp1252 to UTF-8 migration) have been resolved in recent commits.

## Configuration File Structure

`PROCOME.cfg` is an XML file with this structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PROCOME>
  <Medidas NrMedidas="35"/>
  <EstadosDigitales NrEstDig="64"/>
  <Ordenes NrOrdenes="4"/>
  <PuertoSerie Puerto="/dev/ttyUSB0" Baudios="9600" BitsDatos="8" Paridad="E" BitsStop="1"/>
  <Protocolo DirRemota="2"/>
</PROCOME>
```

Configuration can be modified via GUI (Menu → Configuración) or by editing the XML file directly.

## Key Implementation Details

### PROCOME Protocol State Machine

The protocol operates as a hierarchical state machine with four super-states:

1. **Enlace (Link)**: Connection management (Reposo, SinComunicacion, RstLinRemota, VaciarBufferClase1)
2. **Inicialización**: Synchronization, initial state/measurement requests
3. **Bucle (Loop)**: Main operation loop with periodic polling
4. **Control**: Shutdown/control states

Events drive state transitions: Procesado, RecibidaTramaValida, RecibidaTramaErronea, Arrancar, Parar, Timeouts, etc.

### Serial Communication

- Uses pyserial library
- Configurable: port, baud rate (300-115200), data bits (7/8), parity (None/Even/Odd), stop bits (1/2)
- Non-blocking reads with timeout management
- Access requires user to be in `dialout` group (Linux)

### GUI Architecture

Both GUI versions follow similar patterns:
- Main window with menu bar (Archivo, Configuración)
- Central frame with start/stop button
- Three main display areas: Measurements (analog values), States (digital I/O), Orders (control buttons)
- Status bar showing connection info and device address
- Configuration dialogs for runtime parameter changes

Qt version adds:
- Console window widget to display print() output
- ConsoleCapture class redirects stdout to GUI
- More modern look and feel

### Dual GUI Strategy

The codebase maintains both Tkinter and Qt versions:
- **Tkinter**: More portable, no extra dependencies (included with Python)
- **Qt (PySide6)**: Modern UI, better logging (console window), requires virtual environment

When modifying GUI logic, consider updating both versions to maintain feature parity.

## Development Workflow

### Adding New Features

1. For protocol changes: modify `PROCOME_MaqEstados.py` and related frame handlers
2. For GUI changes: update both `PROCOME_FormPpal.py` and `PROCOME_FormPpal_Qt.py` if applicable
3. For configuration parameters: extend `FichConfig.py` and add GUI dialogs
4. Always test with actual serial hardware or use serial port emulators for testing

### Testing

- No automated test suite exists
- Test manually with serial hardware or virtual serial ports
- Verify both Tkinter and Qt versions if GUI changes are made
- Test configuration save/load functionality after parameter changes

### Debugging

Enable debug messages by setting `iDEBUG_MaqEstados` flags in FormPpal:
- `0x01`: Events
- `0x02`: State changes
- `0x04`: Transmission message types
- `0x08`: Transmission messages
- `0x10`: Reception message types
- `0x20`: Reception messages
- `0x80`: Additional debug info

Default is `0x03F` (all enabled). Qt version displays these in console window.

## Common Patterns

### Character Encoding

All text must be UTF-8. Avoid using accented characters directly in GUI labels if compatibility is a concern. Recent commits fixed double-encoding issues with Spanish characters (á, é, í, ó, ú, ñ).

### Configuration Changes at Runtime

1. Stop communication first (prevents serial port conflicts)
2. Modify parameters via GUI or reload config file
3. Restart communication (new parameters take effect)
4. Changes can be persisted to PROCOME.cfg via "Guardar configuración"

### Adding New Measurements/States/Orders

To change the number of monitored items:
1. Modify PROCOME.cfg or use GUI configuration dialog
2. Restart application or reload configuration
3. GUI dynamically creates widgets based on these values

## Platform-Specific Notes

### Linux
- Serial ports typically: `/dev/ttyUSB0`, `/dev/ttyS0`, `/dev/ttyACM0`
- User must be in `dialout` or `uucp` group for serial access
- Installation scripts provided for multiple distros (Debian, Fedora, Arch, openSUSE)

### macOS
- Serial ports typically: `/dev/tty.usbserial-*`, `/dev/cu.usbserial-*`
- Installation script uses Homebrew

### Windows
- Use WSL (Windows Subsystem for Linux) for best compatibility
- Native Windows support may require different serial port handling (COM1, COM2, etc.)

## Git Workflow

Recent commits show focus on:
- UTF-8 encoding fixes for Spanish characters
- Adding console window to Qt version for log visibility
- GUI configuration dialogs
- Installation automation

When committing, use descriptive Spanish or English commit messages reflecting the changes made.

## Dependencies

- **Core**: Python 3.6+
- **Required**: pyserial >= 3.5
- **GUI (Tkinter)**: tkinter (bundled with Python)
- **GUI (Qt)**: PySide6 (installed in .venv for Qt version)
- **Standard library**: time, sys, os, xml.dom.minidom, serial

Install via: `pip install -r requirements.txt` (handles pyserial; PySide6 must be added to requirements.txt if using Qt version).
