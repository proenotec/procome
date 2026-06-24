# AGENTS.md — PROCOME

## Bugs (fix these first)

- `FichConfig.py:459`: `bHayError = True` is undefined and will crash. Should be `iHayError = 2`.
- `PROCOME_MaqEstados.py:189`: `self._sEstado` does not exist. Should be `self._lEstado`.

## Run / Build

```bash
# Qt version (newer, requires .venv)
./run.sh                          # auto-creates .venv, installs deps, runs Qt version

# Tkinter version (legacy, no extra deps)
python3 PROCOME_Arranque.py

# Standalone executable via PyInstaller
./build.sh                        # outputs dist/PROCOME

# Setup only
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

No tests, no linter, no typechecker exist. Test manually with real serial hardware or virtual serial ports.

## Architecture

- **Flat monorepo**, no Python package structure. All modules are standalone `.py` files importing each other by name.
- **Multi-threaded**: Each enabled tarjeta (1–6) runs its own `ThreadTarjeta` daemon thread. All threads share one serial port, protected by `threading.RLock()` (`_oSerialLock`). Only thread 0 reads the port and distributes frames to all threads via `queue.Queue`.
- **GUI thread-safety**: `SignalEmitter` class bridges thread → GUI via Qt signals (`actualizarMedidas`, `actualizarEstados`, etc.). Never call `setText()` from a thread directly.
- **State machine** (`PROCOME_MaqEstados.py`): Hierarchical — 4 super-states (Enlace, Inicializacion, Bucle, Control) × sub-states. Event loop iterates via `while(sEvento != 'Procesado')` returning `'ProcesarDeNuevo'` to re-enter.
- **Modo Monitor**: Passive RS-485 listener. Uses a separate `_ThreadLectorMonitor` + `_ThreadVigilanteTimeouts`. Detects devices via `DetectorDispositivos.py`, filtered to PRM=0 (secondary/slave responses) only.

## Entrypoints

| File | Role |
|---|---|
| `PROCOME_Arranque_Qt.py` | Qt app entrypoint (loads config, creates serial port, launches `FormPpal`) |
| `PROCOME_FormPpal_Qt.py` | Main GUI: tabbed interface (one per tarjeta), console window, all dialogs |
| `PROCOME_GestorMultiTarjeta.py` | Orchestrates threads, distributes frames, owns `_oSerialLock` |
| `PROCOME_MaqEstados.py` | PROCOME protocol state machine per tarjeta |
| `FichConfig.py` | XML config read/write with type validation via setter methods |

## Key Conventions

- All files: `# -*- coding: utf-8 -*-` — but **watch for double-encoded Spanish characters** (`Ã` bytes) in string literals. Use plain ASCII for labels if possible.
- Spanish mixed with English identifiers: `_bHayTransmision`, `_lTramaRcp`, `_iIntentosTrmQuedan`.
- Debug verbosity: `iDEBUG_MaqEstados` bitmask at `PROCOME_FormPpal_Qt.py:111` (default `0x03F` — all on). Flags: `0x01` events, `0x02` states, `0x04` tx types, `0x08` tx msgs, `0x10` rx types, `0x20` rx msgs, `0x80` extra.
- Message display mode (`_sModoMensajes`): `'explicado'` (detailed) or `'hex'` (only `<<<<` / `>>>>` hex lines). Mode propagates to all threads via `GestorMultiTarjeta.SetModoMensajes()`.
- Config lives in `PROCOME.cfg` (XML). To change at runtime: stop comms → change → save → restart comms.

## Serial Port

- pyserial with non-blocking reads (`timeout=0`), `write_timeout=0`.
- Linux user must be in `dialout` group.
- RTS is set to `False` before transmit (RS-485 control).
- Serial port is opened once in `GestorMultiTarjeta.ArrancarComunicacion()` under lock, closed in `PararComunicacion()`.

## Dependencies

| Package | Required for |
|---|---|
| `pyserial>=3.5` | Always |
| `requests>=2.25.0` | Telegram notifications |
| `PySide6>=6.5.0` | Qt GUI (only if using Qt version) |

tkinter is stdlib; the Tkinter version (`PROCOME_FormPpal.py` + `PROCOME_Arranque.py`) does **not exist** anymore in recent commits — only Qt remains.
