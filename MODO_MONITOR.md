# Modo Monitor - PROCOME

## Descripción

El **Modo Monitor** es una funcionalidad que permite escuchar pasivamente el tráfico del bus RS-485 sin transmitir datos. Detecta automáticamente dispositivos PROCOME que estén comunicándose en el bus y muestra su actividad en tiempo real.

## Características

- **Escucha pasiva**: No transmite ningún dato al bus, solo lee
- **Detección automática**: Identifica dispositivos por su dirección (1-254)
- **Monitoreo en tiempo real**: Actualiza la tabla cada 2 segundos
- **Detección de timeout**: Marca dispositivos sin actividad durante más de 30 segundos
- **Estadísticas por dispositivo**:
  - Dirección del dispositivo
  - Estado (Activo/Timeout)
  - Tiempo desde última actividad
  - Número de tramas recibidas
  - Tipos de mensajes detectados (ASDU)
  - Tiempo desde primera detección

## Cómo usar

### 1. Abrir la pestaña "Monitor de Bus"

En la interfaz Qt, después de las 6 pestañas de tarjetas, encontrará la pestaña **"Monitor de Bus"**.

### 2. Activar el Modo Monitor

1. Asegúrese de que **NO hay comunicación normal activa**
2. Marque el checkbox **"Activar Modo Monitor"**
3. El sistema abrirá el puerto serie en modo solo lectura
4. La tabla comenzará a mostrar dispositivos detectados automáticamente

### 3. Monitorear dispositivos

La tabla muestra:

| Columna | Descripción |
|---------|-------------|
| **Dirección** | Dirección PROCOME del dispositivo (1-254) |
| **Estado** | Activo (verde) o Timeout (rojo) |
| **Última Act.** | Tiempo transcurrido desde última trama recibida |
| **Tramas Recibidas** | Contador total de tramas del dispositivo |
| **Tipos ASDU** | Tipos de mensajes detectados (100, 103, 121, 5, F0, F1, etc.) |
| **Primera Detección** | Tiempo transcurrido desde que se detectó el dispositivo |

### 4. Controles disponibles

- **Actualizar Tabla**: Fuerza actualización inmediata (normalmente se actualiza cada 2s)
- **Limpiar Historial**: Borra todos los dispositivos detectados y empieza de cero

### 5. Desactivar el Modo Monitor

Desmarque el checkbox **"Activar Modo Monitor"**. Esto:
- Detiene la lectura del puerto
- Cierra el puerto serie
- Limpia la tabla de dispositivos

## Restricciones

- **No se puede usar simultáneamente con comunicación normal**: Solo puede estar activo el Modo Monitor O la comunicación normal, no ambos
- **Solo lectura**: No se puede enviar órdenes ni solicitar datos en modo Monitor
- **Requiere tráfico en el bus**: Si no hay dispositivos transmitiendo, no se detectará nada

## Tipos de mensajes

Los tipos de mensajes que puede detectar incluyen:

- **100**: Petición de medidas y cambios de estado
- **103**: Transmisión de estados digitales de control
- **121**: Confirmación de orden
- **5**: Mensaje de identificación del tipo de equipo
- **F0, F1, F5, F9, F11**: Funciones de trama corta (ACK, NACK, DATOS_USUARIO, etc.)

## Timeout de dispositivos

Un dispositivo se marca como **"Timeout"** (rojo) cuando:
- No se reciben tramas del dispositivo durante **más de 30 segundos**
- Esto indica que el dispositivo dejó de transmitir o fue desconectado

Los dispositivos en timeout permanecen en la tabla hasta que:
- Se use el botón "Limpiar Historial"
- Se desactive el Modo Monitor

## Casos de uso típicos

1. **Diagnóstico de bus**: Verificar qué dispositivos están conectados y activos
2. **Monitoreo de tráfico**: Observar la frecuencia de comunicación de cada dispositivo
3. **Detección de problemas**: Identificar dispositivos que dejan de comunicar
4. **Análisis de protocolo**: Ver qué tipos de mensajes envía cada dispositivo
5. **Verificación de direcciones**: Confirmar las direcciones configuradas en el sistema

## Notas técnicas

- **Thread-safe**: El detector usa locks internos para operación segura con múltiples threads
- **Bajo impacto**: El modo Monitor añade mínima carga al sistema
- **Compatible**: No afecta la funcionalidad normal de PROCOME
- **No persistente**: Los dispositivos detectados se pierden al desactivar el modo

## Solución de problemas

### No se detectan dispositivos
- Verifique que el puerto serie está correctamente configurado
- Asegúrese de que hay tráfico PROCOME en el bus
- Confirme que el cable RS-485 está conectado correctamente

### Dispositivos en timeout constante
- Puede indicar comunicación intermitente
- Verifique la calidad de la conexión RS-485
- Revise la alimentación de los dispositivos

### Error al activar
- Verifique que no hay comunicación normal activa
- Confirme que el puerto serie no está en uso por otra aplicación
- Compruebe permisos de acceso al puerto serie (`dialout` group en Linux)

## Implementación

### Archivos involucrados

- `PROCOME_DetectorDispositivos.py`: Clase de detección y rastreo
- `PROCOME_MaqEstados.py`: Guard para no transmitir en modo Monitor
- `PROCOME_GestorMultiTarjeta.py`: Integración con lectura de puerto
- `PROCOME_FormPpal_Qt.py`: Interfaz gráfica (pestaña Monitor)

### Arquitectura

```
FormPpal_Qt (GUI)
    ↓ (activar/desactivar)
GestorMultiTarjeta
    ↓ (registrar tramas)
DetectorDispositivos
    ├─ Thread Vigilante (actualiza timeouts cada 1s)
    └─ Diccionario de dispositivos (thread-safe)
```

---

**Versión**: 2.6.0
**Fecha**: 2026-01-23
