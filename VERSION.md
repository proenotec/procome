# Control de Versiones - PROCOME

## Versión Actual: 2.1.2

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
