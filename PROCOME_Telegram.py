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
    self._bUltimoComunicando = None  # Estado anterior de comunicación

    # Validar configuración
    self._bConfiguracionValida = self._ValidarConfiguracion()

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
        print(f'TELEGRAM: Mensaje enviado correctamente')
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
  # **** Notificar cambio de estado de comunicación
  # ***************************************************************************************************************************

  def NotificarEstadoComunicacion(self, bComunicando, iDireccion):
    """
    Notifica cambios en el estado de comunicación con la tarjeta

    Args:
        bComunicando: True si está comunicando, False si no
        iDireccion: Dirección PROCOME de la tarjeta
    """
    if not self._bConfiguracionValida:
      return

    # Solo enviar notificación si hay un cambio de estado
    if self._bUltimoComunicando == bComunicando:
      return

    self._bUltimoComunicando = bComunicando

    # Generar el mensaje
    sFecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if bComunicando:
      # La tarjeta volvió a estar disponible
      sMensaje = f"<b>✅ TARJETA DISPONIBLE</b>\n\n"
      sMensaje += f"La tarjeta PROCOME ha vuelto a responder.\n\n"
      sMensaje += f"📍 Dirección: {iDireccion}\n"
      sMensaje += f"🕐 Fecha: {sFecha}"
    else:
      # La tarjeta dejó de estar disponible
      sMensaje = f"<b>⚠️ TARJETA NO DISPONIBLE</b>\n\n"
      sMensaje += f"La tarjeta PROCOME ha dejado de responder.\n\n"
      sMensaje += f"📍 Dirección: {iDireccion}\n"
      sMensaje += f"🕐 Fecha: {sFecha}"

    # Agregar nombre del bot si está configurado
    if self._sNombreBot:
      sMensaje += f"\n🤖 Bot: {self._sNombreBot}"

    # Enviar el mensaje
    self._EnviarMensaje(sMensaje)

# #############################################################################################################################
