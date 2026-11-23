# CLAUDE.md

Guía para asistentes de código (Claude Code, OpenCode, etc.).

**La guía técnica completa y actualizada está en [`AGENTS.md`](AGENTS.md).** Este fichero
sólo resume lo imprescindible; si hay discrepancia, manda `AGENTS.md`.

## Resumen

PROCOME es una aplicación **Python + Qt (PySide6)** para comunicarse por puerto serie con
tarjetas de telecontrol usando el protocolo PROCOME (RS-232/RS-485). Es multi-tarjeta
(hasta 6 hilos) con un hilo lector dedicado, arbitraje FIFO del bus y máquina de estados
por tarjeta. Incluye modo monitor pasivo, consola de diagnóstico y avisos por Telegram.

## Ejecutar y compilar

```bash
./run.sh                      # crea/usa .venv, instala deps y arranca
python3 PROCOME_Arranque_Qt.py
./build.sh                    # PyInstaller -> dist/PROCOME
```

La aplicación fuerza `QT_QPA_PLATFORM=xcb` (XWayland) para poder colocar la consola al
40 % (izquierda) y la ventana principal al 60 % (derecha).

## Puntos clave

- **Un solo lector del puerto**: `GestorMultiTarjeta._ThreadLector` reparte las tramas a
  la cola de cada tarjeta. No volver a leer el puerto desde los hilos de tarjeta.
- **Bus**: `BusLock` FIFO; se libera al terminar la transacción, en reintentos y al agotar
  la guardia. No retenerlo durante toda la transacción ni con `threading.Lock` a secas.
- **Timeout adaptativo**: `_TmoRcpPara()` (0,30–2,50 s). No usar un valor fijo pequeño.
- **No vaciar** el buffer del puerto antes de transmitir (es compartido).
- **Tramas inesperadas** se descartan como ruido, no cancelan la comunicación.
- **Ventanas**: `_ColocarVentana()` coloca en coordenadas del marco; no usar
  `setFixedSize()` en la ventana principal.
- **Versión**: actualizar `_VERSION` en `PROCOME_FormPpal_Qt.py` y `VERSION.md` en cada
  cambio funcional.

## Estructura

| Fichero | Papel |
|---|---|
| `PROCOME_Arranque_Qt.py` | Entrada de la aplicación |
| `PROCOME_FormPpal_Qt.py` | GUI, consola y ventanas |
| `PROCOME_GestorMultiTarjeta.py` | Hilos, lector serie, bus, puerto |
| `PROCOME_MaqEstados.py` | Máquina de estados PROCOME |
| `PROCOME_ConstruirTramaTrm/Rcp.py` | Construcción de tramas |
| `PROCOME_AnalizarTramaRcp.py` | Análisis de tramas |
| `FichConfig.py` | Configuración XML |

No hay tests automatizados ni linter; se prueba con hardware real o con un pty (ver
`AGENTS.md`).
