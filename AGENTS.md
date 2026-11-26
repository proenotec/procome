# AGENTS.md — PROCOME

Guía para trabajar en este repositorio. Versión actual: **3.1.1**.

## Estado

No hay bugs conocidos abiertos. Los que había en `FichConfig.py` y `PROCOME_MaqEstados.py`
se corrigieron en v2.7.7 y los de la comunicación serie en la v3.0.1
(ver `VERSION.md` para el historial completo).

## Run / Build

```bash
./run.sh                    # crea/usa .venv, instala dependencias y arranca la app Qt
./build.sh                  # ejecutable standalone con PyInstaller -> dist/PROCOME
python3 PROCOME_Arranque_Qt.py   # arranque directo (requiere PySide6 y pyserial)

# Preparar el entorno a mano
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

No hay tests automatizados ni linter. Se prueba con hardware real o con un puerto
serie virtual (ver **Pruebas**).

### XWayland

La aplicación fuerza `QT_QPA_PLATFORM=xcb` al arrancar (`PROCOME_Arranque_Qt.py` y
`run.sh`). Es necesario: en Wayland nativo el compositor ignora `move()` y
`setGeometry()` y no se pueden colocar las dos ventanas (consola 40 % + principal 60 %).
Para volver a Wayland nativo: `QT_QPA_PLATFORM=wayland ./run.sh` (las ventanas ya no
se colocarán solas).

## Architecture

- **Flat monorepo**, sin paquetes. Los módulos se importan por nombre.
- **Multi-hilo**: cada tarjeta habilitada (1–6) tiene su `ThreadTarjeta` daemon. Todas
  comparten un único puerto serie protegido por `_oSerialLock` (`threading.RLock`).
- **Lector dedicado** (`GestorMultiTarjeta._ThreadLector`): un solo hilo lee el puerto,
  parsea las tramas y las reparte a la cola de cada tarjeta (`_qTramas`). Antes leía el
  hilo de la primera tarjeta y, si estaba esperando el bus, nadie leía y las respuestas
  llegaban tarde a todas.
- **Arbitraje de bus** (`BusLock`): turno **FIFO** (cola) entre los hilos para transmitir
  por RS-485. Cada `_TransmitirTrama()` adquiere el turno con un jitter de 0–20 ms para
  desincronizar los sondeos. Se libera al terminar la transacción (`LiberarBusSiReposo`)
  o al agotarse la guardia (`_GuardiaBus`, 0,5–1 s), para que una tarjeta muda no
  bloquee al resto; también en cada reintento y en errores/parada (`LiberarBusForzado`).
- **Timeout de recepción adaptativo** (`_TmoRcpPara`): 0,30–2,50 s según baudios y tamaño
  estimado de trama (nº de medidas/estados). No usar un valor fijo pequeño.
- **No se vacía el buffer del puerto antes de transmitir**: es compartido y se llevaría
  por delante la respuesta que otra tarjeta está esperando.
- **Tramas no esperadas**: si llega una trama que el estado actual no maneja, se descarta
  como ruido del bus; no debe cancelar la comunicación.
- **Puerto serie**: lo abre y lo cierra `GestorMultiTarjeta` (`ArrancarComunicacion` /
  `PararComunicacion`). Una tarjeta no debe cerrarlo al cancelar.
- **GUI thread-safety**: `SignalEmitter` conecta hilo → GUI con señales Qt
  (`actualizarMedidas`, `actualizarEstados`, …). Nunca llamar a `setText()` desde un hilo.
- **Máquina de estados** (`PROCOME_MaqEstados.py`): jerárquica, 4 super-estados
  (Enlace, Inicializacion, Bucle, Control) × sub-estados. El bucle interno itera
  mientras `sEvento != 'Procesado'`, devolviendo `'ProcesarDeNuevo'` para reentrar.
- **Modo Monitor**: escucha pasiva RS-485 con `_ThreadLectorMonitor` +
  `_ThreadVigilanteTimeouts` y `DetectorDispositivos` (sólo respuestas, PRM=0).

## Ventanas

- La consola es una ventana aparte (`QDialog` con flags de ventana). Al abrirla,
  `_ReorganizarVentanas()` reparte el área útil de la pantalla: **consola 40 % a la
  izquierda, principal 60 % a la derecha**, en coordenadas del **marco** de cada ventana
  (se descuentan bordes y barra de título) y con comprobación final de solape.
- `_ColocarVentana()` es el único punto que mueve/redimensiona: hace `showNormal()`,
  marca `WA_Moved`, suelta la restricción del layout (`SetNoConstraint`), limpia
  mínimos/máximos y aplica `move()` + `resize()` + `setGeometry()`.
- Al cerrar la consola, `_RestaurarVentanaPrincipal()` devuelve la principal a todo el
  área útil.
- La ventana principal **no** debe crearse con `setFixedSize()`: el gestor de ventanas
  deshabilita maximizar/restaurar.

## Entrypoints

| Fichero | Papel |
|---|---|
| `PROCOME_Arranque_Qt.py` | Entrada Qt: config, puerto serie, `FormPpal`; fuerza xcb |
| `PROCOME_FormPpal_Qt.py` | GUI: pestañas por tarjeta, consola, diálogos, ventanas |
| `PROCOME_GestorMultiTarjeta.py` | Hilos de tarjeta, lector dedicado, bus FIFO, puerto |
| `PROCOME_MaqEstados.py` | Máquina de estados PROCOME por tarjeta |
| `FichConfig.py` | Configuración XML con validación por setters |

## Key Conventions

- Todos los ficheros: `# -*- coding: utf-8 -*-`. Cuidado con caracteres acentuados
  doblemente codificados (`Ã`); mejor ASCII en etiquetas.
- Español mezclado con identificadores en inglés: `_bHayTransmision`, `_lTramaRcp`.
- Depuración: máscara `iDEBUG_MaqEstados` en `PROCOME_FormPpal_Qt.py` (por defecto
  `0x03F`). Flags: `0x01` eventos, `0x02` estados, `0x04` tipos tx, `0x08` mensajes tx,
  `0x10` tipos rx, `0x20` mensajes rx, `0x80` extra.
- Modo de mensajes (`_sModoMensajes`): `'explicado'` o `'hex'`; se propaga con
  `GestorMultiTarjeta.SetModoMensajes()`.
- Configuración en `PROCOME.cfg` (XML). Para cambiarla: parar comunicación → cambiar →
  guardar → arrancar.
- **Versión**: incrementar `_VERSION` en `PROCOME_FormPpal_Qt.py` y añadir la entrada en
  `VERSION.md` antes de cada commit funcional (MAJOR/MINOR/PATCH).

## Telegram

- `PROCOME_Telegram` envía avisos asíncronos (un hilo por mensaje) con `parse_mode=HTML`.
- Estado recordado **por dirección**: la primera observación se guarda sin avisar; sólo se
  notifica el cambio.
- **Modo normal**: `GestorMultiTarjeta._ProcesarRespuestaMaqEstados` llama a
  `NotificarEstadoComunicacion(estado == 2, dirección)`. La máquina de estados **no** debe
  notificar (se duplicaría).
- **Modo Monitor**: `_ThreadVigilanteTimeouts` pasa el estado de cada dispositivo cada
  segundo a `NotificarEstadoMonitor(dirección, estado == 'Activo')`.
- Configuración: `Telegram.Habilitado/Token/ChatID/NombreBot` en `PROCOME.cfg` (o diálogo
  Configuración → Telegram, que tiene botón **Probar**). Sin `Habilitado=True` no se envía nada.

## Serial Port

- pyserial con lecturas no bloqueantes (`timeout=0`, `write_timeout=0`).
- El usuario de Linux debe estar en el grupo `dialout` (o `uucp` en Arch).
- RS-485: `rts = True` justo antes de escribir la trama; el retorno a `False` tras
  escribir está comentado en el código (se pone a `False` al arrancar la comunicación).
- `_oSerialLock` protege accesos al puerto; el `BusLock` garantiza que sólo una tarjeta
  transmite a la vez y espera su respuesta.
- Configuración típica de campo: `/dev/ttyUSB0`, 9600, 8, **paridad E**, 2 bits de parada.

## Pruebas

Sin hardware se puede usar un **pty** (`os.openpty()`) como puerto serie y un hilo que
responda a las peticiones con tramas PROCOME válidas:

- `PROCOME_ConstruirTramaTrm.TramaCorta_Construir` / `TramaLarga_Construir` para las
  respuestas (PRM=0).
- Trama corta (reset, FC=0) → ACK corto (FC=0).
- Petición larga TYP 100 → respuesta TYP 100 con 1 medida; TYP 103 → ASDU 103 de 16
  bytes con 0 estados.
- Reiniciar el parser (`PROCOME_ConstruirTramaRcp.Reset()`) después de cada trama
  completa; si no, la siguiente da error -14.
- Comprobar que el estado llega a `Bucle`, que se reciben medidas/estados y que al parar
  no queda ningún hilo vivo.

Las ventanas se comprueban con Qt sobre X11/XWayland (`QT_QPA_PLATFORM=xcb`) y, si se
quiere, con `xprop -id <win> _NET_WM_ALLOWED_ACTIONS` para verificar maximizar.

## Dependencies

| Paquete | Para |
|---|---|
| `pyserial>=3.5` | Siempre |
| `requests>=2.25.0` | Notificaciones Telegram |
| `PySide6>=6.5.0` | GUI Qt |

## Releases

- `origin` es **Forgejo** (`git.proenotec.com`, instancia privada: la API exige token).
  Etiqueta `vX.Y.Z` sobre `main` y push; el lanzamiento interno se crea con la API de
  Forgejo (`POST /api/v1/repos/manuel/procome/releases`) adjuntando `PROCOME-Linux` y
  `PROCOME.cfg`.
- El "lanzamiento" público se publica en GitHub `proenotec/procome` con el mismo binario;
  `actualizar_procome.sh` descarga de ahí
  (`https://github.com/proenotec/procome/releases/download/vX.Y.Z/PROCOME-Linux`), porque
  la instancia de Forgejo requiere iniciar sesión.
- El workflow `.github/workflows/build.yml` compila Linux y Windows al crear un release.
