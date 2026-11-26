# -*- coding: utf-8 -*-

# #############################################################################################################################
# #### Módulo para envío de notificaciones por Telegram
# #############################################################################################################################

import requests
import threading
from datetime import datetime

# #############################################################################################################################
# #### Clase PROCOME_Telegram
# #############################################################################################################################

class PROCOME_Telegram:

  # ***************************************************************************************************************************
  # **** Constructor
  # ***************************************************************************************************************************

  def __init__(self, bHabilitado=False, sToken='', sChatID='', sNombreBot=''):
    """
    Inicializa el cliente de Telegram

    Args:
        bHabilitado: Si las notificaciones están habilitadas
        sToken: Token del bot de Telegram
        sChatID: ID del chat donde enviar mensajes
        sNombreBot: Nombre descriptivo del bot (opcional)
    """
    self._bHabilitado = bHabilitado
    self._sToken = sToken.strip()
    self._sChatID = sChatID.strip()
    self._sNombreBot = sNombreBot.strip()

    # Estado anterior por dirección: {direccion: bool comunicando}
    # (antes era un único flag compartido por todas las tarjetas, con lo que
    # las notificaciones de unas interferían con las de otras)
    self._dUltimoComunicando = {}

    # Estado anterior por dirección en modo Monitor: {direccion: bool activo}
    self._dUltimoMonitor = {}

    # Validar configuración
    self._bConfiguracionValida = self._ValidarConfiguracion()

  # ***************************************************************************************************************************
  # **** Propiedad Habilitado
  # ***************************************************************************************************************************

  @property
  def Habilitado(self):
    return bool(self._bHabilitado)

  @property
  def ConfiguracionValida(self):
    return bool(self._bConfiguracionValida)

  # ***************************************************************************************************************************
  # **** Validar configuración
  # ***************************************************************************************************************************

  def _ValidarConfiguracion(self):
    """Valida que la configuración de Telegram sea correcta"""
    if not self._bHabilitado:
      return False

    if not self._sToken or not self._sChatID:
      print('TELEGRAM: Configuración incompleta. Token o Chat ID vacío.')
      return False

    # Validar formato básico del token
    if ':' not in self._sToken:
      print('TELEGRAM: Token inválido. Formato esperado: 1234567890:ABCdef...')
      return False

    return True

  # ***************************************************************************************************************************
  # **** Actualizar configuración
  # ***************************************************************************************************************************

  def ActualizarConfiguracion(self, bHabilitado, sToken, sChatID, sNombreBot=''):
    """Actualiza la configuración del cliente de Telegram"""
    self._bHabilitado = bHabilitado
    self._sToken = sToken.strip()
    self._sChatID = sChatID.strip()
    self._sNombreBot = sNombreBot.strip()
    self._bConfiguracionValida = self._ValidarConfiguracion()

  # ***************************************************************************************************************************
  # **** Enviar mensaje
  # ***************************************************************************************************************************

  def _EnviarMensaje(self, sMensaje):
    """
    Envía un mensaje por Telegram de forma asíncrona

    Args:
        sMensaje: Texto del mensaje a enviar
    """
    if not self._bConfiguracionValida:
      return

    # Enviar en un hilo separado para no bloquear la aplicación
    thread = threading.Thread(target=self._EnviarMensajeSync, args=(sMensaje,))
    thread.daemon = True
    thread.start()

  def _EnviarMensajeSync(self, sMensaje):
    """
    Envía un mensaje por Telegram de forma síncrona (se ejecuta en hilo separado)

    Args:
        sMensaje: Texto del mensaje a enviar
    """
    try:
      url = f'https://api.telegram.org/bot{self._sToken}/sendMessage'
      datos = {
        'chat_id': self._sChatID,
        'text': sMensaje,
        'parse_mode': 'HTML'
      }

      respuesta = requests.post(url, data=datos, timeout=10)

      if respuesta.status_code == 200:
        print('TELEGRAM: Mensaje enviado correctamente')
      else:
        print(f'TELEGRAM: Error al enviar mensaje. Código: {respuesta.status_code}')
        print(f'TELEGRAM: Respuesta: {respuesta.text}')

    except requests.exceptions.Timeout:
      print('TELEGRAM: Timeout al enviar mensaje')
    except requests.exceptions.RequestException as e:
      print(f'TELEGRAM: Error de conexión: {e}')
    except Exception as e:
      print(f'TELEGRAM: Error inesperado: {e}')

  # ***************************************************************************************************************************
  # **** Enviar un mensaje de prueba
  # ***************************************************************************************************************************

  def EnviarMensajePrueba(self):
    """Envía un mensaje de prueba para validar la configuración"""
    if not self._bConfiguracionValida:
      return False

    sFecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sMensaje = '<b>🔔 PROCOME</b>\n\n'
    sMensaje += 'Notificaciones configuradas correctamente.\n\n'
    sMensaje += f'🕐 Fecha: {sFecha}'
    if self._sNombreBot:
      sMensaje += f'\n🤖 Bot: {self._sNombreBot}'
    self._EnviarMensaje(sMensaje)
    return True

  # ***************************************************************************************************************************
  # **** Notificar cambio de estado de comunicación (modo normal)
  # ***************************************************************************************************************************

  def NotificarEstadoComunicacion(self, bComunicando, iDireccion):
    """
    Notifica cambios en el estado de comunicación con la tarjeta.

    Sólo envía mensaje cuando el estado cambia respecto al anterior de esa
    misma dirección; la primera observación se guarda sin notificar.

    Args:
        bComunicando: True si está comunicando, False si no
        iDireccion: Dirección PROCOME de la tarjeta
    """
    if not self._bConfiguracionValida:
      return

    bAhora = bool(bComunicando)
    bAnterior = self._dUltimoComunicando.get(iDireccion)
    self._dUltimoComunicando[iDireccion] = bAhora

    # Primera observación o sin cambios: no notificar
    if bAnterior is None or bAnterior == bAhora:
      return

    sFecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if bAhora:
      sMensaje = '<b>✅ TARJETA DISPONIBLE</b>\n\n'
      sMensaje += 'La tarjeta PROCOME ha vuelto a responder.\n\n'
    else:
      sMensaje = '<b>⚠️ TARJETA NO DISPONIBLE</b>\n\n'
      sMensaje += 'La tarjeta PROCOME ha dejado de responder.\n\n'

    sMensaje += f'📍 Dirección: {iDireccion}\n'
    sMensaje += f'🕐 Fecha: {sFecha}'

    if self._sNombreBot:
      sMensaje += f'\n🤖 Bot: {self._sNombreBot}'

    self._EnviarMensaje(sMensaje)

  # ***************************************************************************************************************************
  # **** Notificar cambio de estado en modo Monitor
  # ***************************************************************************************************************************

  def NotificarEstadoMonitor(self, iDireccion, bActivo):
    """
    Notifica cambios ACTIVO <-> TIMEOUT de un dispositivo en modo Monitor.

    Args:
        iDireccion: Dirección PROCOME del dispositivo
        bActivo: True si ha vuelto a dar señal, False si ha entrado en timeout
    """
    if not self._bConfiguracionValida:
      return

    bAhora = bool(bActivo)
    bAnterior = self._dUltimoMonitor.get(iDireccion)
    self._dUltimoMonitor[iDireccion] = bAhora

    if bAnterior is None or bAnterior == bAhora:
      return

    sFecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if bAhora:
      sMensaje = '<b>📡 TARJETA ACTIVA DE NUEVO</b>\n\n'
      sMensaje += 'El dispositivo ha vuelto a transmitir en el bus (fin del timeout).\n\n'
    else:
      sMensaje = '<b>📡 TARJETA EN TIMEOUT</b>\n\n'
      sMensaje += 'El dispositivo ha dejado de transmitir en el bus.\n\n'

    sMensaje += f'📍 Dirección: {iDireccion}\n'
    sMensaje += f'🕐 Fecha: {sFecha}'
    sMensaje += '\n👁️ Modo: Monitor pasivo'

    if self._sNombreBot:
      sMensaje += f'\n🤖 Bot: {self._sNombreBot}'

    self._EnviarMensaje(sMensaje)

  # ***************************************************************************************************************************
  # **** Olvidar el estado de un dispositivo (al limpiar el historial)
  # ***************************************************************************************************************************

  def OlvidarEstadoMonitor(self):
    """Borra el estado recordado del modo Monitor (tras 'Limpiar Historial')"""
    self._dUltimoMonitor.clear()

# #############################################################################################################################
