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
               iNrMedidas, iNrEstados, oGestor):

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
      fnCallbackBeepRecepcion=self._fnCallbackBeepRecepcion
    )

    # Control de tiempo
    self._fIncrT_TmpAnt = time.time()

    # Cola de eventos para la máquina de estados
    self._qEventos = []
    self._lockEventos = threading.Lock()


  def run(self):
    """Bucle principal del thread"""
    self._bRunning = True
    self._fIncrT_TmpAnt = time.time()

    while self._bRunning:
      try:
        # Procesar eventos pendientes
        self._ProcesarEventosPendientes()

        # Procesar recepción del puerto serie (con lock)
        self._ProcesarRecepcionSerie()

        # Actualizar temporizadores
        self._ActualizarTemporizadores()

        # Pausa para reducir carga del CPU y contención del lock
        # En multi-tarjeta, múltiples threads compiten por el puerto serie
        time.sleep(0.02)  # 20ms por iteración

      except Exception as e:
        # Mostrar error pero continuar ejecutando (solo en modo explicado)
        if self._oGestor._sModoMensajes != 'hex':
          print(f'[Tarjeta {self._iNrTarjeta}] ERROR en thread: {str(e)}')
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

          # Intentar adquirir el lock con timeout para evitar bloqueos indefinidos
          bLockAdquirido = self._oSerialLock.acquire(timeout=2.0)
          if not bLockAdquirido:
            if self._oGestor._sModoMensajes != 'hex':
              print(f'[Tarjeta {self._iNrTarjeta}] TIMEOUT esperando lock serial para {sEvento}')
            continue

          try:
            Rta = self._oMaqEstados.ProcesarEventos(sEvento, xDato)
            self._ProcesarRespuestaMaqEstados(Rta)
          finally:
            self._oSerialLock.release()
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
      except Exception as e:
        # Solo mostrar error si no es por puerto cerrado (situación esperada al parar)
        # y si no estamos en modo HEX
        if 'not open' not in str(e) and self._oGestor._sModoMensajes != 'hex':
          print(f'[Tarjeta {self._iNrTarjeta}] ERROR procesando evento {sEvento}: {str(e)}')


  def _ProcesarRecepcionSerie(self):
    """Procesa datos recibidos del puerto serie (con distribución centralizada)"""
    if not self._oCSerie.is_open:
      return

    # Solo el primer thread lee del puerto y distribuye tramas
    bSoyLector = False
    with self._oGestor._lockTurno:
      if len(self._oGestor._lThreads) > 0 and self._oGestor._lThreads[0]._iNrTarjeta == self._iNrTarjeta:
        bSoyLector = True

    if bSoyLector:
      # Leer del puerto y distribuir tramas a todos los threads
      self._LeerYDistribuirTramas()

    # Todos los threads procesan tramas de su cola
    self._ProcesarTramasDeCola()


  def _LeerYDistribuirTramas(self):
    """Lee del puerto serie y distribuye tramas completas a todos los threads"""
    try:
      # Verificar que el puerto esté abierto antes de intentar leer
      if not self._oCSerie.is_open:
        return

      with self._oSerialLock:
        # Verificar de nuevo dentro del lock (por si se cerró mientras esperábamos)
        if not self._oCSerie.is_open:
          return

        iBytesDisponibles = self._oCSerie.in_waiting
        if iBytesDisponibles == 0:
          return

        # Leer TODOS los bytes disponibles
        lBytesRcpCSerie = []
        try:
          for _ in range(min(iBytesDisponibles, 100)):  # Máximo 100 bytes por iteración
            lBytesRcpCSerie.append(ord(self._oCSerie.read(1)))
        except:
          if len(lBytesRcpCSerie) == 0:
            return

      # Procesar los bytes fuera del lock y construir tramas
      iContadorErrores = 0  # Contador para agrupar errores
      for iRcpCSerie in lBytesRcpCSerie:
        xRta = self._oConstrTramaRcp.ConstruirTrama(iRcpCSerie)

        if type(xRta) == int:
          if xRta < 0:
            iContadorErrores += 1
            self._oConstrTramaRcp.Reset()
        else:
          # Si había errores acumulados, mostrar resumen (solo en modo explicado)
          if iContadorErrores > 0 and self._oGestor._sModoMensajes != 'hex':
            print(f'[LECTOR] {iContadorErrores} errores de recepción')
            iContadorErrores = 0

          # Trama recibida completa - distribuir a TODOS los threads
          lTramaRcp = xRta.copy()
          self._oConstrTramaRcp.Reset()

          # Distribuir la trama a todos los threads (cada uno filtrará por dirección)
          for oThread in self._oGestor._lThreads:
            oThread._qTramas.put(lTramaRcp)

      # Mostrar resumen final si había errores (solo en modo explicado)
      if iContadorErrores > 0 and self._oGestor._sModoMensajes != 'hex':
        print(f'[LECTOR] {iContadorErrores} errores de recepción acumulados')

    except Exception as e:
      # Solo mostrar error si no es por descriptor cerrado (esperado al parar)
      # y si no estamos en modo HEX
      if ('Descriptor' not in str(e) and 'descriptor' not in str(e) and
          self._oGestor._sModoMensajes != 'hex'):
        print(f'[LECTOR] ERROR en _LeerYDistribuirTramas: {str(e)}')


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

    fTmpAct = time.time()
    fIncrTmp = fTmpAct - self._fIncrT_TmpAnt
    if fIncrTmp < 0:
      fIncrTmp = 0
    self._fIncrT_TmpAnt = fTmpAct

    # Obtener estado actual para filtrar timeouts apropiadamente
    lEstado = self._oMaqEstados.EstadoActual()
    sSuperEstado = lEstado[0] if len(lEstado) > 0 else ''

    # Determinar qué timeouts son válidos según el super-estado
    bEnBucle = (sSuperEstado == 'Bucle')
    bEnInicializacion = (sSuperEstado == 'Inicializacion')
    bEnEnlace = (sSuperEstado == 'Enlace')

    if fIncrTmp > 0.0:
      # Temporizado TmpRcp - válido en Enlace, Inicializacion y Bucle
      if self._dTemp['TmpRcp_seg'] > 0.0:
        self._dTemp['TmpRcp_seg'] -= fIncrTmp
        if self._dTemp['TmpRcp_seg'] <= 0.0:
          if bEnEnlace or bEnInicializacion or bEnBucle:
            self.EnviarEvento('TimeoutRcp')

      # Temporizado TmpEspera - SIEMPRE (necesario para reintento de conexión)
      if self._dTemp['TmpEspera_seg'] > 0.0:
        self._dTemp['TmpEspera_seg'] -= fIncrTmp
        if self._dTemp['TmpEspera_seg'] <= 0.0:
          self.EnviarEvento('TimeoutEspera')

      # Temporizado TmpSincr - solo en Inicializacion
      if self._dTemp['TmpSincr_seg'] > 0.0:
        self._dTemp['TmpSincr_seg'] -= fIncrTmp
        if self._dTemp['TmpSincr_seg'] <= 0.0:
          if bEnInicializacion:
            self.EnviarEvento('TimeoutSincr')

      # Temporizado TmpPetGral - solo en Bucle
      if self._dTemp['TmpPetGral_seg'] > 0.0:
        self._dTemp['TmpPetGral_seg'] -= fIncrTmp
        if self._dTemp['TmpPetGral_seg'] <= 0.0:
          if bEnBucle:
            self.EnviarEvento('TimeoutPetGral')

      # Temporizado TmpPetEstDig - solo en Bucle
      if self._dTemp['TmpPetEstDig_seg'] > 0.0:
        self._dTemp['TmpPetEstDig_seg'] -= fIncrTmp
        if self._dTemp['TmpPetEstDig_seg'] <= 0.0:
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
      if self._oTelegram and self._oTelegram._bHabilitado:
        bComunicandoTelegram = (iEstadoCom == 2)
        self._oTelegram.NotificarEstadoComunicacion(bComunicandoTelegram, self._iDirRemota)


  def EnviarEvento(self, sEvento, xDato=None):
    """Añade un evento a la cola para ser procesado por el thread"""
    with self._lockEventos:
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

    # Threads de las tarjetas (máximo 6)
    self._lThreads = []

    # Sistema de turnos para lectura del puerto serie
    self._iTurnoActual = 0
    self._lockTurno = threading.Lock()

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
          oGestor=self
        )

        # Aplicar el modo de mensajes configurado
        oThread._oMaqEstados.SetModoMensajes(self._sModoMensajes)

        self._lThreads.append(oThread)


  def ArrancarComunicacion(self):
    """Arranca la comunicación de todas las tarjetas habilitadas"""

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
    # Detener todos los threads
    for oThread in self._lThreads:
      oThread.Detener()

    # Esperar a que los threads terminen correctamente (con timeout)
    tInicio = time.time()
    while time.time() - tInicio < 2.0:  # Timeout de 2 segundos
      bTodosParados = True
      for oThread in self._lThreads:
        if oThread._bRunning:
          bTodosParados = False
          break
      if bTodosParados:
        break
      time.sleep(0.05)

    # Cerrar puerto serie después de que los threads hayan parado
    with self._oSerialLock:
      if self._oCSerie.is_open:
        try:
          self._oCSerie.close()
        except Exception as e:
          if self._sModoMensajes != 'hex':
            print(f'Error al cerrar puerto serie: {e}')

    return ''


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
