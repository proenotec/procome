# Control de Versiones - PROCOME

## Versión Actual: 3.0.0

## Sistema de Versionado

Este proyecto utiliza **Versionado Semántico** (Semantic Versioning) con el formato:

```
MAJOR.MINOR.PATCH
```

### Cuándo incrementar cada número:

- **MAJOR (1.x.x)**: Cambios incompatibles o reestructuración importante
  - Ejemplo: Cambio completo del protocolo de comunicación
  - Ejemplo: Migración a nueva biblioteca incompatible
  - Ejemplo: Cambios que requieren reconfiguración total

- **MINOR (x.1.x)**: Nuevas funcionalidades compatibles con versiones anteriores
  - Ejemplo: Agregar soporte para nuevos tipos de tarjetas
  - Ejemplo: Implementar sistema de notificaciones
  - Ejemplo: Agregar nuevas opciones de configuración

- **PATCH (x.x.1)**: Correcciones de errores y mejoras menores
  - Ejemplo: Corregir bug de rendimiento en consola
  - Ejemplo: Mejorar tolerancia a errores de comunicación
  - Ejemplo: Ajustar colores de indicadores

## Cómo actualizar la versión antes de commit

### 1. Editar el archivo `PROCOME_FormPpal_Qt.py`

Localizar la línea (aproximadamente línea 77):

```python
_VERSION = "1.0.0"
```

### 2. Incrementar según el tipo de cambio

**Para correcciones de errores (PATCH):**
```python
_VERSION = "1.0.0"  →  _VERSION = "1.0.1"
```

**Para nuevas funcionalidades (MINOR):**
```python
_VERSION = "1.0.1"  →  _VERSION = "1.1.0"
```

**Para cambios importantes (MAJOR):**
```python
_VERSION = "1.1.0"  →  _VERSION = "2.0.0"
```

### 3. Actualizar este archivo (VERSION.md)

Cambiar la línea 3:
```markdown
## Versión Actual: 1.0.1
```

### 4. Hacer commit y push

```bash
git add PROCOME_FormPpal_Qt.py VERSION.md
git commit -m "Actualizar versión a v1.0.1 - [Descripción de cambios]"
git push
```

## Historial de Versiones

### v3.0.0 (2026-06-24)
**Arbitraje de bus serial multi-tarjeta + timeout anti-colisión**

Características nuevas:
- ✨ Sistema de arbitraje de bus RS-485 mediante `_oBusLock` (threading.Lock)
- ✨ Jitter aleatorio 0-50ms antes de cada transmisión para desincronizar threads
- ✨ Timeout de 0.2s en adquisición del bus lock (evita bloqueos indefinidos)

Mejoras:
- 🔧 Timeout de recepción (`TmpRcp`) reducido de 1.0s a 0.2s para reintentos más rápidos
- 🔧 Si un hilo no consigue el bus en 0.2s, salta la transmisión y reintenta después
- 🔧 Ciclo completo de reintentos reducido de 10s a 2s cuando un dispositivo no responde

Técnico:
- Nuevo `_oBusLock` en GestorMultiTarjeta, propagado a cada máquina de estados
- `_TransmitirTrama()` adquiere el lock con timeout y libera al volver a `Reposo`
- `LiberarBusSiReposo()` libera el lock automáticamente al finalizar la transacción
- Primera versión con OpenCode

### v2.7.7 (2026-06-24)
**Corrección de bugs en FichConfig y MaqEstados**

Correcciones:
- 🐛 `FichConfig.py:459`: `bHayError = True` → `iHayError = 2` (NameError)
- 🐛 `PROCOME_MaqEstados.py:189`: `self._sEstado[0]` → `self._lEstado[0]` (AttributeError)

### v2.5.1 (2025-12-04)
**Eliminación de mensajes de debug**

Mejoras:
- 🔧 Eliminados mensajes de debug "[DEBUG BEEP] Transmisión" y "[DEBUG BEEP] Recepción"
- 🔧 Consola más limpia sin mensajes innecesarios
- 🔧 Funcionalidad de beeps se mantiene sin cambios

Técnico:
- Removidos print statements de debug en BeepTransmision() y BeepRecepcion()
- Actualizado instalador install.sh a versión 2.5.1

### v2.5.0 (2025-12-04)
**Sistema de beeps sonoros para comunicación**

Características nuevas:
- ✨ Checkbox "Beep" en ventana de consola para activar/desactivar sonidos
- ✨ Beep agudo (SOL - 392 Hz) cuando se transmite una trama
- ✨ Beep grave (RE - 294 Hz) cuando se recibe una trama válida
- ✨ Estado del checkbox se guarda en PROCOME.cfg y persiste entre sesiones
- ✨ Reproducción de audio compatible con Linux (aplay) y Windows (winsound)

Mejoras:
- 🔧 Beeps reproducidos en threads separados (no bloquean la aplicación)
- 🔧 Generación de WAV en memoria (16-bit PCM estéreo)
- 🔧 Arquitectura de callbacks desde MaqEstados hasta FormPpal_Qt
- 🔧 Manejo silencioso de errores de audio

Técnico:
- Parámetro 'Consola.BeepHabilitado' en FichConfig.py
- Callbacks fnBeepTransmision/fnBeepRecepcion pasados por toda la cadena
- Métodos BeepTransmision() y BeepRecepcion() en FormPpal_Qt
- Generación de ondas sinusoidales con módulo math
- Reproducción vía subprocess (Linux) o winsound (Windows)

### v2.4.0 (2025-12-04)
**Selector de modo de mensajes en consola**

Características nuevas:
- ✨ Selector "Modo de los mensajes en consola" en configuración
- ✨ Modo "Solo protocolo HEX": muestra solo tramas hexadecimales con prefijos <<<< y >>>>
- ✨ Modo "Protocolo explicado": muestra mensajes detallados como hasta ahora
- ✨ Configuración se guarda en PROCOME.cfg y persiste entre sesiones

Mejoras:
- 🔧 Supresión completa de mensajes debug/estado en modo HEX
- 🔧 Supresión de mensajes [LECTOR] de errores de recepción en modo HEX
- 🔧 Supresión de mensajes de estado de threads en modo HEX
- 🔧 Modo se aplica automáticamente a todas las tarjetas
- 🔧 Modo se mantiene al reiniciar comunicación

Técnico:
- Parámetro 'Consola.ModoMensajes' en FichConfig.py con validación
- Método SetModoMensajes() en gestor y máquina de estados
- Variable _sModoMensajes almacenada en gestor para aplicar a threads nuevos
- Checks condicionales en todos los print statements según modo
- Métodos _ImprimirTramaTrm() y _ImprimirTramaRcp() en máquina de estados

### v2.3.0 (2025-12-03)
**Versión Qt exclusiva con mejoras en consola**

Cambios importantes:
- 🗑️ Eliminada versión Tkinter (solo Qt desde ahora)
- ✨ Botón "Guardar" en ventana de consola
- ✨ Botón maximizar funcional en ventana de consola

Características nuevas:
- ✨ Guardar contenido completo de consola en archivo de texto
- ✨ Nombre de archivo con timestamp automático
- ✨ Diálogo de confirmación al guardar
- ✨ Ventana de consola totalmente redimensionable

Mejoras:
- 🔧 Ventana de consola con botones minimizar/maximizar/cerrar
- 🔧 Interfaz más limpia con 3 botones: Guardar, Limpiar, Cerrar
- 🔧 Mejor usabilidad de la ventana de consola

Archivos eliminados:
- PROCOME_FormPpal.py (versión Tkinter)
- PROCOME_Arranque.py (lanzador Tkinter)
- procome (script wrapper)

Técnico:
- WindowFlags configurados para ventana completa
- QFileDialog para guardar archivos
- Formato UTF-8 en archivos guardados

### v2.2.1 (2025-12-03)
**Mejora en tiempo de reconexión**

Mejoras:
- 🔧 Tiempo de reintento reducido de 5 segundos a 1 segundo
- 🔧 Reconexión más rápida cuando una tarjeta falla
- 🔧 Mejor respuesta del sistema ante fallos de comunicación

Técnico:
- Ajustado `TmpEspera_seg` de 5.0 a 1.0 en PROCOME_MaqEstados.py (líneas 290 y 786)
- Aplica tanto a estado SinComunicacion como a recepción de NACK

### v2.2.0 (2025-12-03)
**Instalador automático para Ubuntu/Debian**

Características nuevas:
- ✨ Instalador automático `install_ubuntu.sh` para versión ejecutable
- ✨ Descarga automática desde GitHub Releases
- ✨ Integración completa con menú de aplicaciones de Ubuntu
- ✨ Generación automática de icono SVG personalizado
- ✨ Desinstalador incluido
- ✨ Documentación completa del proceso de instalación

Mejoras:
- 🔧 Archivo .desktop mejorado con más categorías y keywords
- 🔧 Configuración automática de permisos para puerto serie
- 🔧 Detección de versión instalada y actualización inteligente
- 🔧 Soporte para múltiples distribuciones basadas en Debian

Técnico:
- Script bash completo con manejo de errores
- Instalación en `/opt/procome/` con acceso global
- Configuración de usuario en `~/.config/procome/`
- Icono SVG embebido representando placa electrónica

### v2.1.2 (2025-12-02)
**Corrección de scroll en consola tras limpieza de buffer**

Correcciones:
- 🐛 Corregido scroll de consola que saltaba al inicio tras limpieza automática
- 🐛 Ahora la consola permanece mostrando las líneas más recientes después del reset

Técnico:
- Agregado scroll automático al final tras `setPlainText()` en limpieza de buffer
- Mejora de UX: usuario mantiene visibilidad de logs recientes

### v2.1.1 (2025-12-02)
**Mejoras en lógica de indicadores y seguridad de órdenes**

Mejoras:
- 🔧 Indicadores permanecen en rojo si nunca han comunicado
- 🔧 Solo pasan a amarillo en reintentos si ya comunicaron antes
- 🔧 Botones de órdenes solo habilitados en estado verde (comunicando)
- 🔧 Mayor claridad visual del estado real de cada tarjeta

Correcciones:
- 🐛 Corregida lógica de indicador amarillo para tarjetas sin comunicación previa
- 🐛 Evita envío accidental de órdenes a tarjetas no comunicadas

Técnico:
- Nueva variable `_bHaComunicadoAlgunaVez` en máquina de estados
- Marca primera comunicación exitosa al recibir ACK
- Lógica mejorada en método `Comunicando()`

### v2.1.0 (2025-12-02)
**Configuración avanzada y optimización de consola**

Características nuevas:
- ✨ Configuración del buffer de la consola (100-100000 líneas)
- ✨ Nuevo menú "Consola" en configuración
- ✨ Cambio de configuración sin reiniciar la aplicación

Mejoras:
- 🔧 Buffer de consola ahora configurable vía GUI
- 🔧 Límite de líneas se ajusta dinámicamente (20% de margen)
- 🔧 Valores recomendados según recursos del sistema
- 🔧 Configuración se guarda en PROCOME.cfg

### v1.0.0 (2025-12-02)
**Versión inicial del sistema multi-tarjeta**

Características principales:
- ✨ Sistema de gestión de hasta 6 tarjetas PROCOME simultáneas
- 🎨 Indicadores tricolor (rojo/amarillo/verde)
- 🔄 Reconexión automática con 10 intentos
- 🛡️ Tolerancia a errores mejorada
- 📊 Consola con límite automático de líneas (5000)
- ⚙️ Configuración aplicable sin reiniciar
- 📡 Soporte para protocolo PROCOME sobre RS-485
- 🔔 Notificaciones por Telegram
- 📝 Documentación completa de la máquina de estados

Correcciones:
- 🐛 Corrección de tiempo de reintento (5 segundos)
- 🐛 Filtrado inteligente de timeouts por estado
- 🐛 Protección del puerto serie compartido
- 🐛 Optimización de rendimiento de consola

---

## Plantilla para nuevas versiones

Copiar y completar al hacer un nuevo release:

```markdown
### vX.Y.Z (YYYY-MM-DD)
**[Título descriptivo del release]**

Características nuevas:
- ✨ [Descripción de nueva funcionalidad]

Mejoras:
- 🔧 [Descripción de mejora]

Correcciones:
- 🐛 [Descripción de bug corregido]
```

## Notas Importantes

1. **Siempre** actualizar la versión antes de hacer commit
2. **Nunca** hacer commit sin incrementar la versión si hay cambios funcionales
3. La versión se muestra en el título de la ventana principal
4. Mantener este archivo actualizado con el historial de cambios
