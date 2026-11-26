# -*- coding: utf-8 -*-

# #############################################################################################################################
# #### GESTOR MULTI-TARJETA
# #############################################################################################################################
#
# Gestiona hasta 6 tarjetas PROCOME simultáneamente:
# - Cada tarjeta tiene su propio thread con su máquina de estados
# - Comparten un puerto serie RS-485 multi-drop con sincronización mediante Lock
# - Notifican cambios de estado al GUI
# - Integran notificaciones Telegram indicando número de tarjeta

# #############################################################################################################################
# #### Dependencias
# #############################################################################################################################

import threading
import time
import queue
import PROCOME_MaqEstados
import PROCOME_ConstruirTramaRcp
import PROCOME_AnalizarTramaRcp
import PROCOME_Telegram


# #############################################################################################################################
# #### Clase SerialPortWrapper - Envuelve el puerto serie con protección por Lock
# #############################################################################################################################

class BusLock:
  """Turno FIFO para el bus serie.

  threading.Lock no garantiza el orden de espera: un hilo que reintenta
  puede adelantar a los demás y dejarlos sin turno (con una tarjeta muda,
  el resto acaba descartando transmisiones). Esta cola da el turno por
  orden de llegada.
  """

  def __init__(self):
    self._q = queue.Queue()
    self._q.put(True)

  def acquire(self, timeout=None):
    try:
      self._q.get(timeout=timeout)
      return True
    except queue.Empty:
      return False

  def release(self):
    self._q.put(True)


class SerialPortWrapper:
  """Wrapper del puerto serie que protege las transmisiones con Lock y previene cierre accidental"""

  def __init__(self, oSerial, oLock):
    self._oSerial = oSerial
    self._oLock = oLock

  def write(self, data):
    """Escritura protegida con Lock"""
    with self._oLock:
      return self._oSerial.write(data)

  def close(self):
    """NO cierra el puerto serie - en modo multi-tarjeta el puerto es compartido"""
    # Ignorar silenciosamente - el puerto se cierra solo cuando el GestorMultiTarjeta lo decide
    pass

  def __getattr__(self, name):
    """Redirige todos los demás atributos al puerto serie real"""
    return getattr(self._oSerial, name)


# #############################################################################################################################
# #### Clase ThreadTarjeta
# #############################################################################################################################

class ThreadTarjeta(threading.Thread):
  """Thread individual para gestionar una tarjeta PROCOME"""

  def __init__(self, iNrTarjeta, iDirRemota, bTestsHabilitados, oCSerie, oSerialLock,
               oTelegram, iDebug, fnCallbackEstado, fnCallbackMedidas, fnCallbackEstados,
               fnCallbackDatosEquipo, fnCallbackOrden, fnCallbackBeepTransmision, fnCallbackBeepRecepcion,
               iNrMedidas, iNrEstados, oGestor, oBusLock=None):

    threading.Thread.__init__(self)
    self.daemon = True  # Thread daemon para que se cierre al cerrar la aplicación

    # Parámetros de configuración
    self._iNrTarjeta = iNrTarjeta
    self._iDirRemota = iDirRemota
    self._bTestsHabilitados = bTestsHabilitados
    self._iNrMedidas = iNrMedidas
    self._iNrEstados = iNrEstados

    # Objetos compartidos
    self._oCSerie = oCSerie
    self._oSerialLock = oSerialLock
    self._oTelegram = oTelegram
    self._oGestor = oGestor  # Referencia al gestor para sistema de turnos
    self._oBusLock = oBusLock  # Lock de arbitraje de bus serial
    self._qTramas = queue.Queue()  # Cola para recibir tramas completas

    # Callbacks al GUI
    self._fnCallbackEstado = fnCallbackEstado
    self._fnCallbackMedidas = fnCallbackMedidas
    self._fnCallbackEstados = fnCallbackEstados
    self._fnCallbackDatosEquipo = fnCallbackDatosEquipo
    self._fnCallbackOrden = fnCallbackOrden
    self._fnCallbackBeepTransmision = fnCallbackBeepTransmision
    self._fnCallbackBeepRecepcion = fnCallbackBeepRecepcion

    # Control de thread
    self._bRunning = False
    self._bComunicando = False
    self._bEstadoAnterior = None  # Para detectar cambios de comunicación

    # Temporizadores (diccionario compartido con la máquina de estados)
    self._dTemp = {
      'TmpRcp_seg': 0.0,
      'TmpEspera_seg': 0.0,
      'TmpSincr_seg': 0.0,
      'TmpPetGral_seg': 0.0,
      'TmpPetEstDig_seg': 0.0
    }

    # Constructor de trama de recepción (cada thread necesita el suyo)
    self._oConstrTramaRcp = PROCOME_ConstruirTramaRcp.PROCOME_ConstruirTramaRcp(0x07)

    # Wrapper del puerto serie con protección de Lock para transmisiones
    self._oSerieWrapper = SerialPortWrapper(oCSerie, oSerialLock)

    # Máquina de estados (usa el wrapper para que las transmisiones estén protegidas)
    self._oMaqEstados = PROCOME_MaqEstados.PROCOME_MaqEstados(
      iDirRemota,
      self._dTemp,
      self._oConstrTramaRcp,
      self._oSerieWrapper,  # Usa el wrapper en lugar del puerto directo
      self,  # Este thread actúa como "FormPpal" para la máquina de estados
      iDebug,
      oTelegram,
      fnCallbackBeepTransmision=self._fnCallbackBeepTransmision,
      fnCallbackBeepRecepcion=self._fnCallbackBeepRecepcion,
      oBusLock=self._oBusLock,
      iNrMedidas=self._iNrMedidas,
      iNrEstados=self._iNrEstados
    )

    # Control de tiempo
    self._fIncrT_TmpAnt = time.monotonic()

    # Cola de eventos para la máquina de estados
    self._qEventos = []
    self._lockEventos = threading.Lock()


  def run(self):
    """Bucle principal del thread"""
    self._bRunning = True
    self._fIncrT_TmpAnt = time.monotonic()

    while self._bRunning:
      try:
        # Procesar eventos pendientes
        self._ProcesarEventosPendientes()

        # Procesar recepción del puerto serie (con lock)
        self._ProcesarRecepcionSerie()

        # Actualizar temporizadores
        self._ActualizarTemporizadores()

        # Garantiza que el bus se libera aunque la respuesta haya llegado por
        # el camino de recepción (que antes no pasaba por LiberarBusSiReposo)
        self._oMaqEstados.LiberarBusSiReposo()

        # Pausa para reducir carga del CPU y contención del lock
        # En multi-tarjeta, múltiples threads compiten por el puerto serie
        time.sleep(0.01)  # 10ms por iteración

      except Exception as e:
        # Mostrar error pero continuar ejecutando (solo en modo explicado)
        if self._oGestor._sModoMensajes != 'hex':
          print(f'[Tarjeta {self._iNrTarjeta}] ERROR en thread: {str(e)}')
        # Si el error deja el bus retenido, liberarlo para no bloquear al resto
        try:
          self._oMaqEstados.LiberarBusForzado()
        except Exception:
          pass
        # Pequeña pausa para evitar loop infinito en caso de error persistente
        time.sleep(0.1)

    # Al salir del bucle, notificar que el thread ha terminado (solo en modo explicado)
    if self._oGestor._sModoMensajes != 'hex':
      print(f'[Tarjeta {self._iNrTarjeta}] Thread finalizado')


  def _ProcesarEventosPendientes(self):
    """Procesa eventos de la cola"""
    # Procesar eventos uno a uno, extrayendo con lock y procesando sin lock
    while True:
      # Extraer un evento de la cola (con lock)
      with self._lockEventos:
        if len(self._qEventos) == 0:
          break
        sEvento, xDato = self._qEventos.pop(0)

      # Procesar el evento SIN mantener el lock de eventos (evita deadlock)
      try:
        # Verificar que el puerto esté abierto para eventos que lo requieren
        if sEvento in ('Arrancar', 'PetOrden'):
          if not self._oCSerie.is_open:
            continue  # Saltar evento si el puerto está cerrado

          # Filtrar PetOrden si la tarjeta no está comunicando (estado 0)
          if sEvento == 'PetOrden' and self._oMaqEstados.Comunicando() == 0:
            if self._oGestor._sModoMensajes != 'hex':
              print(f'[Tarjeta {self._iNrTarjeta}] Orden ignorada: tarjeta sin comunicación')
            continue

          # NO se toma _oSerialLock aquí: _TransmitirTrama ya escribe con el
          # lock serial y toma el bus. Retener el lock serial mientras se
          # espera el bus provocaría una inversión de orden con el lector y
          # deadlock potencial entre threads.
          try:
            Rta = self._oMaqEstados.ProcesarEventos(sEvento, xDato)
            self._ProcesarRespuestaMaqEstados(Rta)
          finally:
            # Liberar el lock del bus si la transacción ha terminado
            self._oMaqEstados.LiberarBusSiReposo()
        else:
          # Para eventos de timeout, verificar también si el puerto está abierto
          if sEvento.startswith('Timeout') and not self._oCSerie.is_open:
            continue  # Saltar timeouts si el puerto está cerrado

          # Filtrar timeouts según el estado actual de la máquina
          if sEvento.startswith('Timeout'):
            lEstado = self._oMaqEstados.EstadoActual()
            sSuperEstado = lEstado[0] if len(lEstado) > 0 else ''
            sEstado = lEstado[1] if len(lEstado) > 1 else ''

            # En SinComunicacion: solo permitir TimeoutEspera
            if sSuperEstado == 'Enlace' and sEstado == 'SinComunicacion':
              if sEvento != 'TimeoutEspera':
                continue

            # En estados de Enlace (excepto SinComunicacion): solo TimeoutRcp y TimeoutEspera
            elif sSuperEstado == 'Enlace':
              if sEvento not in ('TimeoutRcp', 'TimeoutEspera'):
                continue

            # En Inicializacion: solo TimeoutRcp, TimeoutEspera y TimeoutSincr
            elif sSuperEstado == 'Inicializacion':
              if sEvento not in ('TimeoutRcp', 'TimeoutEspera', 'TimeoutSincr'):
                continue

            # En Bucle: todos los timeouts son válidos (no filtrar)
            # En Control: todos los timeouts son válidos (no filtrar)

          Rta = self._oMaqEstados.ProcesarEventos(sEvento, xDato)
          self._ProcesarRespuestaMaqEstados(Rta)
          # Liberar el lock del bus si la transacción ha terminado
          self._oMaqEstados.LiberarBusSiReposo()
      except Exception as e:
        # Solo mostrar error si no es por puerto cerrado (situación esperada al parar)
        # y si no estamos en modo HEX
        if 'not open' not in str(e) and self._oGestor._sModoMensajes != 'hex':
          print(f'[Tarjeta {self._iNrTarjeta}] ERROR procesando evento {sEvento}: {str(e)}')


  def _ProcesarRecepcionSerie(self):
    """Procesa las tramas que el lector dedicado ha puesto en su cola."""
    if not self._oCSerie.is_open:
      return

    # La lectura del puerto la hace GestorMultiTarjeta._ThreadLector: así
    # ningún hilo de tarjeta bloquea la recepción mientras espera el bus.
    self._ProcesarTramasDeCola()


  def _ProcesarTramasDeCola(self):
    """Procesa tramas de la cola (cada thread procesa solo las de su dirección)"""
    try:
      # Procesar todas las tramas pendientes en la cola (sin bloquear)
      while not self._qTramas.empty():
        try:
          lTramaRcp = self._qTramas.get_nowait()
        except queue.Empty:
          break

        # Analizar la trama
        dTramaRcp = PROCOME_AnalizarTramaRcp.AnalizarTrama(lTramaRcp)

        # Solo procesar tramas válidas con MI dirección
        if not dTramaRcp['TramaValida']:
          continue

        if dTramaRcp['Dir'] != self._iDirRemota:
          continue  # No es para mí

        # Si NO es un eco (BitPRM=False significa que es del secundario)
        if not dTramaRcp['BitPRM']:
          iASDU = dTramaRcp['TYP']

          # Procesar según el tipo de ASDU
          if iASDU == 100:  # Medidas y cambios de estado
            dRta = PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_100(lTramaRcp)
            if dRta != -1:
              self._Medidas_ActualizarValor(dRta['Medidas'])
              if dRta['CambiosED']:
                self._Estados_ActualizarValor(dRta['CambiosED'])
              self._DatosDelEquipo_Actualizar(None, len(dRta['Medidas']), None, None)

          elif iASDU == 103:  # Estados digitales
            dRta = PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_103(lTramaRcp)
            if dRta != -1:
              self._Estados_ActualizarValor(dRta['EstadosDig'])
              self._DatosDelEquipo_Actualizar(None, None, len(dRta['EstadosDig']), None)

          elif iASDU == 5:  # Identificación del equipo
            dRta = PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_5(lTramaRcp)
            if dRta != -1:
              self._DatosDelEquipo_Actualizar(dRta['TxtIdEquipo'], None, None, dRta['VersProcome'])

          elif iASDU == 121:  # Confirmación de orden
            dRta = PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_121(lTramaRcp)
            if dRta != -1:
              sMensaje = f"Respuesta a Peticion de orden S{dRta['NrOden'] + 1} a {dRta['TipoOperacion']}: {dRta['ResultadoOper']}"
              self._Ordenes_MostrarMensaje(sMensaje)

        # Procesar trama en la máquina de estados (para gestión del protocolo)
        Rta = self._oMaqEstados.ProcesarEventos('RecibidaTrama', lTramaRcp)
        self._ProcesarRespuestaMaqEstados(Rta)

    except Exception as e:
      if self._oGestor._sModoMensajes != 'hex':
        print(f'[Tarjeta {self._iNrTarjeta}] ERROR en _ProcesarTramasDeCola: {str(e)}')


  def _ActualizarTemporizadores(self):
    """Actualiza los temporizadores de la máquina de estados"""
    # No procesar temporizadores si el thread se está deteniendo
    if not self._bRunning:
      return

    # time.monotonic() es inmune a los saltos del reloj del sistema.
    fTmpAct = time.monotonic()
    fIncrTmp = fTmpAct - self._fIncrT_TmpAnt
    if fIncrTmp < 0:
      fIncrTmp = 0
    # Limitar saltos grandes (por ejemplo, si el thread estuvo bloqueado
    # esperando un lock): así no se disparan todos los timeouts a la vez.
    if fIncrTmp > 0.5:
      fIncrTmp = 0.5
    self._fIncrT_TmpAnt = fTmpAct

    # Obtener estado actual para filtrar timeouts apropiadamente
    lEstado = self._oMaqEstados.EstadoActual()
    sSuperEstado = lEstado[0] if len(lEstado) > 0 else ''

    # Determinar qué timeouts son válidos según el super-estado
    bEnBucle = (sSuperEstado == 'Bucle')
    bEnInicializacion = (sSuperEstado == 'Inicializacion')
    bEnEnlace = (sSuperEstado == 'Enlace')
    # La máquina de estados decide si la sincronización puede interrumpir la
    # petición en curso o si se descarta y se reprograma.

    if fIncrTmp > 0.0:
      # Temporizado TmpRcp - válido en Enlace, Inicializacion y Bucle
      if self._dTemp['TmpRcp_seg'] > 0.0:
        self._dTemp['TmpRcp_seg'] -= fIncrTmp
        if self._dTemp['TmpRcp_seg'] <= 0.0:
          self._dTemp['TmpRcp_seg'] = 0.0
          if bEnEnlace or bEnInicializacion or bEnBucle:
            self.EnviarEvento('TimeoutRcp')

      # Temporizado TmpEspera - SIEMPRE (necesario para reintento de conexión)
      if self._dTemp['TmpEspera_seg'] > 0.0:
        self._dTemp['TmpEspera_seg'] -= fIncrTmp
        if self._dTemp['TmpEspera_seg'] <= 0.0:
          self._dTemp['TmpEspera_seg'] = 0.0
          self.EnviarEvento('TimeoutEspera')

      # Temporizado TmpSincr - en Inicializacion y en Bucle.TiempoLibre
      if self._dTemp['TmpSincr_seg'] > 0.0:
        self._dTemp['TmpSincr_seg'] -= fIncrTmp
        if self._dTemp['TmpSincr_seg'] <= 0.0:
          self._dTemp['TmpSincr_seg'] = 0.0
          if bEnInicializacion or bEnBucle:
            self.EnviarEvento('TimeoutSincr')

      # Temporizado TmpPetGral - solo en Bucle
      if self._dTemp['TmpPetGral_seg'] > 0.0:
        self._dTemp['TmpPetGral_seg'] -= fIncrTmp
        if self._dTemp['TmpPetGral_seg'] <= 0.0:
          self._dTemp['TmpPetGral_seg'] = 0.0
          if bEnBucle:
            self.EnviarEvento('TimeoutPetGral')

      # Temporizado TmpPetEstDig - solo en Bucle
      if self._dTemp['TmpPetEstDig_seg'] > 0.0:
        self._dTemp['TmpPetEstDig_seg'] -= fIncrTmp
        if self._dTemp['TmpPetEstDig_seg'] <= 0.0:
          self._dTemp['TmpPetEstDig_seg'] = 0.0
          if bEnBucle:
            self.EnviarEvento('TimeoutPetEstDig')


  def _ProcesarRespuestaMaqEstados(self, sRespuesta):
    """Procesa respuestas de la máquina de estados"""
    # Mostrar solo errores críticos (solo en modo explicado)
    if sRespuesta != '' and 'ERROR' in sRespuesta.upper() and self._oGestor._sModoMensajes != 'hex':
      print(f'[Tarjeta {self._iNrTarjeta}] {sRespuesta}')

    # Detectar cambios en el estado de comunicación (0=sin comunicación, 1=intentando, 2=comunicando)
    iEstadoCom = self._oMaqEstados.Comunicando()
    if self._bEstadoAnterior != iEstadoCom:
      self._bEstadoAnterior = iEstadoCom

      # Notificar al GUI
      if self._fnCallbackEstado:
        self._fnCallbackEstado(self._iNrTarjeta, iEstadoCom)

      # Notificar por Telegram (solo cuando pasa a comunicando=2 o sin comunicación=0)
      if self._oTelegram and self._oTelegram.Habilitado:
        bComunicandoTelegram = (iEstadoCom == 2)
        self._oTelegram.NotificarEstadoComunicacion(bComunicandoTelegram, self._iDirRemota)


  def EnviarEvento(self, sEvento, xDato=None):
    """Añade un evento a la cola para ser procesado por el thread"""
    with self._lockEventos:
      # Los timeouts no deben duplicarse: un temporizador puede expirar más
      # de una vez antes de que el thread procese el primer evento.
      if sEvento.startswith('Timeout'):
        for sEventoExistente, _xDatoExistente in self._qEventos:
          if sEventoExistente == sEvento:
            return
      self._qEventos.append((sEvento, xDato))


  def Detener(self):
    """Detiene el thread de forma ordenada"""
    # Enviar evento Parar a la máquina de estados
    self.EnviarEvento('Parar')
    time.sleep(0.1)

    # Detener todos los temporizadores para evitar eventos pendientes
    self._dTemp['TmpRcp_seg'] = 0.0
    self._dTemp['TmpEspera_seg'] = 0.0
    self._dTemp['TmpSincr_seg'] = 0.0
    self._dTemp['TmpPetGral_seg'] = 0.0
    self._dTemp['TmpPetEstDig_seg'] = 0.0

    # Limpiar cola de eventos pendientes
    with self._lockEventos:
      self._qEventos.clear()

    # Detener el bucle del thread
    self._bRunning = False
    # Que la máquina de estados suelte el bus de inmediato
    self._oMaqEstados.Detener()


  def Comunicando(self):
    """Devuelve el estado de comunicación: 0=sin comunicación, 1=intentando, 2=comunicando"""
    return self._oMaqEstados.Comunicando() if self._oMaqEstados else 0


  # Métodos de interfaz para que la máquina de estados pueda llamar (actúa como FormPpal)

  def AvanzarPilotoTrm(self):
    """Callback desde la máquina de estados"""
    pass  # El GUI se encarga de esto

  def AvanzarPilotoRcp(self):
    """Callback desde la máquina de estados"""
    pass  # El GUI se encarga de esto

  def _Medidas_ActualizarValor(self, lMedidas):
    """Callback desde la máquina de estados cuando recibe medidas"""
    if self._fnCallbackMedidas:
      self._fnCallbackMedidas(self._iNrTarjeta, lMedidas)

  def _Estados_ActualizarValor(self, lEstadosDig):
    """Callback desde la máquina de estados cuando recibe estados digitales"""
    if self._fnCallbackEstados:
      self._fnCallbackEstados(self._iNrTarjeta, lEstadosDig)

  def _DatosDelEquipo_Actualizar(self, sIdEquipo, iNrMedidas, iNrEstadosDig, sVersProcome):
    """Callback desde la máquina de estados cuando recibe datos del equipo"""
    if self._fnCallbackDatosEquipo:
      self._fnCallbackDatosEquipo(self._iNrTarjeta, sIdEquipo, iNrMedidas, iNrEstadosDig, sVersProcome)

  def _Ordenes_MostrarMensaje(self, sMensaje):
    """Callback desde la máquina de estados cuando hay mensaje de orden"""
    if self._fnCallbackOrden:
      self._fnCallbackOrden(self._iNrTarjeta, sMensaje)


# #############################################################################################################################
# #### Clase GestorMultiTarjeta
# #############################################################################################################################

class GestorMultiTarjeta:
  """Gestor de múltiples tarjetas PROCOME"""

  def __init__(self, oCSerie, oFichCfg, oTelegram, iDebug=0x03F):

    # Objetos compartidos
    self._oCSerie = oCSerie
    self._oFichCfg = oFichCfg
    self._oTelegram = oTelegram
    self._iDebug = iDebug

    # Lock para sincronizar acceso al puerto serie compartido
    self._oSerialLock = threading.RLock()  # RLock para permitir reentrada desde el mismo thread

    # Turno FIFO para arbitraje de bus serial entre threads (evita colisiones en RS-485)
    self._oBusLock = BusLock()

    # Threads de las tarjetas (máximo 6)
    self._lThreads = []

    # Sistema de turnos para lectura del puerto serie
    self._iTurnoActual = 0

    # Callbacks del GUI
    self._fnCallbackEstado = None
    self._fnCallbackMedidas = None
    self._fnCallbackEstados = None
    self._fnCallbackDatosEquipo = None
    self._fnCallbackOrden = None
    self._fnCallbackBeepTransmision = None
    self._fnCallbackBeepRecepcion = None

    # Configuración de tarjetas
    self._iNrMedidas = 35
    self._iNrEstados = 64

    # Modo de visualización de mensajes en consola
    self._sModoMensajes = 'explicado'  # Modo por defecto

    # Modo Monitor
    self._bModoMonitor = False
    self._oDetectorDispositivos = None
    self._threadVigilante = None
    self._threadLectorMonitor = None
    self._bLectorMonitorRunning = False
    self._threadLector = None
    self._bLectorRunning = False
    self._dEstadosMonitor = {}   # {direccion: 'Activo'|'Timeout'} en modo Monitor


  def SetCallbacks(self, fnEstado=None, fnMedidas=None, fnEstados=None, fnDatosEquipo=None, fnOrden=None, fnBeepTransmision=None, fnBeepRecepcion=None):
    """Configura los callbacks para notificar al GUI"""
    self._fnCallbackEstado = fnEstado
    self._fnCallbackMedidas = fnMedidas
    self._fnCallbackEstados = fnEstados
    self._fnCallbackDatosEquipo = fnDatosEquipo
    self._fnCallbackOrden = fnOrden
    self._fnCallbackBeepTransmision = fnBeepTransmision
    self._fnCallbackBeepRecepcion = fnBeepRecepcion


  def SetModoMensajes(self, sModo):
    """Configura el modo de visualización de mensajes en todas las tarjetas"""
    # Guardar el modo para aplicarlo a threads futuros
    self._sModoMensajes = sModo
    # Aplicar a threads existentes
    for oThread in self._lThreads:
      if oThread and hasattr(oThread, '_oMaqEstados'):
        oThread._oMaqEstados.SetModoMensajes(sModo)


  def ActivarModoMonitor(self, bActivar=True):
    """Activa o desactiva el modo Monitor pasivo"""
    self._bModoMonitor = bActivar

    if bActivar:
      import PROCOME_DetectorDispositivos
      fTimeout = 30.0
      if self._oFichCfg is not None:
        fTimeout = float(self._oFichCfg.Parametros_Get().get('Monitor.TimeoutSegundos', 30))
      self._oDetectorDispositivos = PROCOME_DetectorDispositivos.DetectorDispositivos(fTimeout)
      self._dEstadosMonitor = {}
    else:
      # Detener thread vigilante si existe
      if self._threadVigilante and self._threadVigilante.is_alive():
        self._bModoMonitor = False  # Esto hará que el thread se detenga
        self._threadVigilante.join(timeout=2.0)
      self._threadVigilante = None
      self._oDetectorDispositivos = None


  def InicializarTarjetas(self):
    """Inicializa los threads para las tarjetas habilitadas según configuración"""

    # Limpiar lista de threads antiguos si existen
    self._lThreads = []
    self._iTurnoActual = 0

    # Leer parámetros generales
    dCfg = self._oFichCfg.Parametros_Get()
    self._iNrMedidas = dCfg.get('Medidas.NrMedidas', 35)
    self._iNrEstados = dCfg.get('EstadosDigitales.NrEstDig', 64)

    # Crear threads para cada tarjeta habilitada
    for iNrTarjeta in range(1, 7):
      bHabilitada = dCfg.get(f'Tarjeta{iNrTarjeta}.Habilitada', False)

      if bHabilitada:
        iDirRemota = dCfg.get(f'Tarjeta{iNrTarjeta}.DirRemota', iNrTarjeta)
        bTestsHab = dCfg.get(f'Tarjeta{iNrTarjeta}.TestsHabilitados', False)

        oThread = ThreadTarjeta(
          iNrTarjeta=iNrTarjeta,
          iDirRemota=iDirRemota,
          bTestsHabilitados=bTestsHab,
          oCSerie=self._oCSerie,
          oSerialLock=self._oSerialLock,
          oTelegram=self._oTelegram,
          iDebug=self._iDebug,
          fnCallbackEstado=self._fnCallbackEstado,
          fnCallbackMedidas=self._fnCallbackMedidas,
          fnCallbackEstados=self._fnCallbackEstados,
          fnCallbackDatosEquipo=self._fnCallbackDatosEquipo,
          fnCallbackOrden=self._fnCallbackOrden,
          fnCallbackBeepTransmision=self._fnCallbackBeepTransmision,
          fnCallbackBeepRecepcion=self._fnCallbackBeepRecepcion,
          iNrMedidas=self._iNrMedidas,
          iNrEstados=self._iNrEstados,
          oGestor=self,
          oBusLock=self._oBusLock
        )

        # Aplicar el modo de mensajes configurado
        oThread._oMaqEstados.SetModoMensajes(self._sModoMensajes)

        self._lThreads.append(oThread)


  def ArrancarComunicacion(self):
    """Arranca la comunicación de todas las tarjetas habilitadas"""

    # Abrir puerto serie si no está abierto (con lock para thread-safety)
    with self._oSerialLock:
      if not self._oCSerie.is_open:
        try:
          self._oCSerie.open()
        except Exception as e:
          return f'ERROR al abrir puerto serie: {str(e)}'

      # Limpiar buffers del puerto
      try:
        self._oCSerie.reset_input_buffer()
        self._oCSerie.reset_output_buffer()
      except Exception as e:
        if self._sModoMensajes != 'hex':
          print(f'Advertencia al limpiar buffers: {e}')

    # MODO MONITOR: Solo escuchar, NO arrancar threads de tarjetas
    if self._bModoMonitor and self._oDetectorDispositivos:
      print('[MODO MONITOR] Escuchando pasivamente el bus RS-485...')
      print('[MODO MONITOR] NO se transmitirá ningún dato')

      # Iniciar thread lector para modo monitor
      if self._threadLectorMonitor is None or not self._threadLectorMonitor.is_alive():
        self._threadLectorMonitor = threading.Thread(
          target=self._ThreadLectorMonitor,
          daemon=True
        )
        self._threadLectorMonitor.start()

      # Iniciar thread vigilante para timeouts
      if self._threadVigilante is None or not self._threadVigilante.is_alive():
        self._threadVigilante = threading.Thread(
          target=self._ThreadVigilanteTimeouts,
          daemon=True
        )
        self._threadVigilante.start()

      return ''

    # MODO NORMAL: Arrancar threads de tarjetas
    # Si los threads están muertos o vacíos, recrearlos
    bNecesitaReinicializar = len(self._lThreads) == 0
    if not bNecesitaReinicializar:
      # Verificar si algún thread está muerto
      for oThread in self._lThreads:
        if not oThread.is_alive():
          bNecesitaReinicializar = True
          break

    if bNecesitaReinicializar:
      self.InicializarTarjetas()

    # Lector dedicado del puerto serie (independiente del turno del bus)
    if self._threadLector is None or not self._threadLector.is_alive():
      self._bLectorRunning = True
      self._threadLector = threading.Thread(
        target=self._ThreadLector,
        name='LectorSerie',
        daemon=True
      )
      self._threadLector.start()

    # Iniciar todos los threads
    for oThread in self._lThreads:
      if not oThread.is_alive():
        oThread.start()

    # Dar tiempo a que los threads arranquen
    time.sleep(0.3)

    # Enviar evento "Arrancar" a cada tarjeta con pequeño delay entre ellas
    for idx, oThread in enumerate(self._lThreads):
      oThread.EnviarEvento('Arrancar')
      # Pequeño delay para evitar que ambas tarjetas transmitan exactamente al mismo tiempo
      if idx < len(self._lThreads) - 1:
        time.sleep(0.1)

    return ''


  def PararComunicacion(self):
    """Para la comunicación de todas las tarjetas"""
    # Detener thread lector de monitor si existe
    self._bLectorMonitorRunning = False

    # Detener el lector dedicado del modo normal
    self._bLectorRunning = False
    if self._threadLector is not None and self._threadLector.is_alive():
      self._threadLector.join(timeout=1.0)

    # Detener todos los threads de tarjetas
    for oThread in self._lThreads:
      oThread.Detener()

    # Esperar a que los threads terminen realmente (con timeout)
    for oThread in self._lThreads:
      if oThread.is_alive():
        oThread.join(timeout=3.0)

    # Los threads ya pararon: liberar el bus si alguno lo retenía aún
    for oThread in self._lThreads:
      oThread._oMaqEstados.LiberarBusForzado()

    # Cerrar puerto serie después de que los threads hayan parado
    with self._oSerialLock:
      if self._oCSerie.is_open:
        try:
          self._oCSerie.close()
        except Exception as e:
          if self._sModoMensajes != 'hex':
            print(f'Error al cerrar puerto serie: {e}')

    return ''


  def _ThreadVigilanteTimeouts(self):
    """Actualiza los timeouts del modo Monitor y avisa de los cambios de estado"""
    while self._bModoMonitor and self._oDetectorDispositivos:
      try:
        self._oDetectorDispositivos.ActualizarTimeouts()

        dDispositivos = self._oDetectorDispositivos.ObtenerDispositivos()
        bAvisar = self._oTelegram is not None and self._oTelegram.Habilitado

        for iDireccion, dInfo in dDispositivos.items():
          sEstado = dInfo.get('Estado', 'Timeout')
          sAnterior = self._dEstadosMonitor.get(iDireccion)
          self._dEstadosMonitor[iDireccion] = sEstado

          if sAnterior is not None and sAnterior != sEstado:
            print(f'[MONITOR] Tarjeta {iDireccion}: {sAnterior} -> {sEstado}')

          # Se pasa siempre: Telegram guarda la primera observación sin avisar
          # y notifica a partir del primer cambio real.
          if bAvisar:
            self._oTelegram.NotificarEstadoMonitor(iDireccion, sEstado == 'Activo')

        # Olvidar dispositivos que ya no están (p. ej. tras "Limpiar Historial")
        for iDireccion in list(self._dEstadosMonitor):
          if iDireccion not in dDispositivos:
            del self._dEstadosMonitor[iDireccion]

        time.sleep(1.0)
      except:
        break


  def _ThreadLector(self):
    """Lee el puerto serie una sola vez y reparte las tramas a cada tarjeta.

    Antes leía el hilo de la primera tarjeta; si éste esperaba el turno del
    bus, nadie leía y las respuestas llegaban tarde a todas.
    """
    oConstr = PROCOME_ConstruirTramaRcp.PROCOME_ConstruirTramaRcp(0)

    while self._bLectorRunning:
      try:
        if not self._oCSerie.is_open:
          time.sleep(0.05)
          continue

        with self._oSerialLock:
          if not self._oCSerie.is_open:
            continue
          iBytesDisponibles = self._oCSerie.in_waiting
          lBytes = []
          if iBytesDisponibles > 0:
            lBytes = list(self._oCSerie.read(min(iBytesDisponibles, 4096)))

        if not lBytes:
          time.sleep(0.005)
          continue

        for byDato in lBytes:
          xRta = oConstr.ConstruirTrama(byDato)
          if type(xRta) == int:
            if xRta < 0:
              oConstr.Reset()
            continue

          lTramaRcp = xRta.copy()
          oConstr.Reset()

          if self._bModoMonitor and self._oDetectorDispositivos:
            self._oDetectorDispositivos.RegistrarTrama(lTramaRcp)
            continue

          for oThread in self._lThreads:
            oThread._qTramas.put(lTramaRcp)

      except Exception as e:
        if 'not open' not in str(e) and self._sModoMensajes != 'hex':
          print(f'[LECTOR] ERROR: {str(e)}')
        time.sleep(0.05)

    print('[LECTOR] Thread lector finalizado')


  def _ThreadLectorMonitor(self):
    """Thread que lee del puerto serie en modo monitor y registra tramas"""
    import PROCOME_ConstruirTramaRcp

    print('[LECTOR MONITOR] Thread iniciado')

    # Crear constructor de tramas propio para este thread
    oConstrTramaRcp = PROCOME_ConstruirTramaRcp.PROCOME_ConstruirTramaRcp(0x07)

    self._bLectorMonitorRunning = True
    iContadorIteraciones = 0
    iUltimoReporte = 0

    while self._bLectorMonitorRunning and self._bModoMonitor:
      try:
        # Verificar que el puerto esté abierto
        if not self._oCSerie.is_open:
          time.sleep(0.1)
          continue

        with self._oSerialLock:
          # Verificar de nuevo dentro del lock
          if not self._oCSerie.is_open:
            continue

          iBytesDisponibles = self._oCSerie.in_waiting
          if iBytesDisponibles == 0:
            continue

          # Leer todos los bytes disponibles de una vez (máximo 4096)
          lBytesRcpCSerie = []
          try:
            lBytesRcpCSerie = list(self._oCSerie.read(min(iBytesDisponibles, 4096)))
          except Exception as e:
            if self._sModoMensajes != 'hex':
              print(f'[LECTOR MONITOR] Error al leer puerto serie: {str(e)}')
            continue

        # Procesar bytes recibidos (fuera del lock)
        iNumBytes = len(lBytesRcpCSerie)
        iTramasCompletadas = 0
        iErrores = 0

        for idx, iByte in enumerate(lBytesRcpCSerie):
          xRta = oConstrTramaRcp.ConstruirTrama(iByte)

          # ConstruirTrama devuelve:
          # - 0: trama incompleta (aún esperando más bytes)
          # - valor negativo: error
          # - lista: trama completa

          if xRta == 0:
            # Trama incompleta, seguir esperando bytes
            pass
          elif type(xRta) is int and xRta < 0:
            # Error en construcción
            iErrores += 1
            print(f'[LECTOR MONITOR] Error {xRta} en byte {idx+1}/{iNumBytes} (0x{iByte:02X})')
            oConstrTramaRcp.Reset()
          elif type(xRta) is list:
            # Trama recibida completa
            iTramasCompletadas += 1
            lTramaRcp = xRta.copy()
            oConstrTramaRcp.Reset()

            # Mostrar trama construida
            sHexTrama = ' '.join([f'{b:02X}' for b in lTramaRcp])
            print(f'[LECTOR MONITOR] Trama construida ({len(lTramaRcp)} bytes): {sHexTrama}')

            # Registrar en detector de dispositivos
            if self._oDetectorDispositivos:
              bRegistrado = self._oDetectorDispositivos.RegistrarTrama(lTramaRcp)
              print(f'[LECTOR MONITOR] Trama registrada: {bRegistrado}')
          else:
            # Respuesta inesperada del constructor
            print(f'[LECTOR MONITOR] Constructor devolvió valor inesperado: {xRta} (tipo: {type(xRta)})')

        # Pausa para reducir carga del CPU
        time.sleep(0.01)  # 10ms

      except Exception as e:
        import traceback
        print(f'[LECTOR MONITOR] EXCEPCIÓN CAPTURADA: {str(e)}')
        print(f'[LECTOR MONITOR] Modo mensajes: {self._sModoMensajes}')
        print(f'[LECTOR MONITOR] Traceback completo:')
        traceback.print_exc()
        time.sleep(0.1)

    if self._sModoMensajes != 'hex':
      print('[LECTOR MONITOR] Thread finalizado')


  def ObtenerDispositivosDetectados(self):
    """Devuelve diccionario de dispositivos detectados"""
    if self._oDetectorDispositivos:
      return self._oDetectorDispositivos.ObtenerDispositivos()
    return {}


  def EnviarOrden(self, iNrTarjeta, iNrOrden, sTipoOperacion):
    """Envía una orden a una tarjeta específica"""
    for oThread in self._lThreads:
      if oThread._iNrTarjeta == iNrTarjeta:
        oThread.EnviarEvento('PetOrden', [iNrOrden, sTipoOperacion])
        return True
    return False


  def ObtenerEstadoTarjetas(self):
    """Devuelve el estado de comunicación de todas las tarjetas"""
    dEstados = {}
    for oThread in self._lThreads:
      dEstados[oThread._iNrTarjeta] = oThread.Comunicando()
    return dEstados


  def ActualizarConfiguracion(self, oFichCfg):
    """Actualiza la configuración (requiere parar y reiniciar)"""
    self._oFichCfg = oFichCfg


# #############################################################################################################################
