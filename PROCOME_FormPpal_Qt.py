# -*- coding: utf-8 -*-

# #############################################################################################################################
# ### Dependencias
# #############################################################################################################################

import time
import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton,
                               QLineEdit, QComboBox, QSpinBox, QFrame, QGroupBox,
                               QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox,
                               QFileDialog, QDialog, QTextEdit, QCheckBox, QTabWidget)
from PySide6.QtCore import QTimer, Qt, Signal, QObject
from PySide6.QtGui import QAction
import PROCOME_General
import PROCOME_GestorMultiTarjeta
import PROCOME_AnalizarTramaRcp
import PROCOME_Telegram
import FichConfig


# #############################################################################################################################
# #### Clase para capturar la salida de consola
# #############################################################################################################################

class ConsoleCapture:
  """Clase que captura la salida de print() y la redirige de forma thread-safe"""

  def __init__(self, signal_emitter=None):
    self.signal_emitter = signal_emitter
    self.original_stdout = sys.stdout

  def write(self, text):
    if text.strip():  # Solo si no es solo espacios en blanco
      if self.signal_emitter:
        # Usar señal Qt para thread-safety
        self.signal_emitter.escribirConsola.emit(text)
    self.original_stdout.write(text)

  def flush(self):
    self.original_stdout.flush()

  def isatty(self):
    return False


# #############################################################################################################################
# #### Clase SignalEmitter para señales Qt desde threads
# #############################################################################################################################

class SignalEmitter(QObject):
  """Emite señales Qt para actualizar la GUI desde threads"""
  actualizarEstadoTarjeta = Signal(int, int)  # (iNrTarjeta, iEstadoCom: 0/1/2)
  actualizarMedidas = Signal(int, list)
  actualizarEstados = Signal(int, list)
  actualizarDatosEquipo = Signal(int, str, int, int, str)
  mostrarMensajeOrden = Signal(int, str)
  escribirConsola = Signal(str)  # Señal para escritura thread-safe a consola


# #############################################################################################################################
# #### Clase FormPpal
# #############################################################################################################################

class FormPpal:

  # ***************************************************************************************************************************
  # **** VERSIÓN DEL PROGRAMA
  # ***************************************************************************************************************************
  # Incrementar antes de cada commit a GitHub:
  # - MAJOR: Cambios incompatibles o reestructuración importante
  # - MINOR: Nuevas funcionalidades compatibles
  # - PATCH: Correcciones de errores y mejoras menores
  # ***************************************************************************************************************************

  _VERSION = "2.1.1"

  # ***************************************************************************************************************************
  # **** __init__
  # ***************************************************************************************************************************

  def __init__(self, iNrMedidas, iNrEstados, iNrOrdenes, iDirProtocolo, oCSerie, oFichCfg= None):

    # **** Inicializar constantes *********************************************************************************************

    self._K_fTmoTempBuclePeriodico_ms= 50  # Aumentado para multi-tarjeta
    self._K_NR_MAX_TARJETAS= 6

    # Límite de líneas en consola (se lee de configuración)
    dCfgTemp = oFichCfg.Parametros_Get() if oFichCfg else {}
    self._iMaxLineasConsola = dCfgTemp.get('Consola.MaxLineas', 5000)

    self._sColorGris= '#E0E0E0'
    self._sColorFondo= 'white'
    self._sColorBotonAbrir=  'red'
    self._sColorBotonCerrar= 'green'
    #
    self._sColorNoComunica= self._sColorGris
    self._sColorComunicando= '#C0FFC0'
    self._sColorIndicadorRojo= '#FF4444'
    self._sColorIndicadorAmarillo= '#FFFF44'
    self._sColorIndicadorVerde= '#44FF44'
    self._sColorIndicadorGris= '#AAAAAA'
    self._iDEBUG_MaqEstados= 0x03F    # 0x03F

    # **** Inicializar variables **********************************************************************************************

    self._iNrMedidas= iNrMedidas
    self._iNrEstados= iNrEstados
    self._iNrOrdenes= iNrOrdenes
    self._iDirProtocolo= iDirProtocolo
    self._bArranqueClase= True
    self._oCSerie= oCSerie
    self._oFichCfg= oFichCfg if oFichCfg is not None else FichConfig.FichConfig()

    # Variables multi-tarjeta
    self._oGestorTarjetas= None
    self._dIndicadoresEstado= {}  # {iNrTarjeta: QLabel}
    self._dTarjetasGUI= {}  # {iNrTarjeta: {widgets...}}
    self._bComunicacionActiva= False

    # Señales Qt para actualización desde threads
    self._oSignals= SignalEmitter()
    self._oSignals.actualizarEstadoTarjeta.connect(self._ActualizarIndicadorEstado)
    self._oSignals.actualizarMedidas.connect(self._ActualizarMedidasGUI)
    self._oSignals.actualizarEstados.connect(self._ActualizarEstadosGUI)
    self._oSignals.actualizarDatosEquipo.connect(self._ActualizarDatosEquipoGUI)
    self._oSignals.mostrarMensajeOrden.connect(self._MostrarMensajeOrdenGUI)
    self._oSignals.escribirConsola.connect(self._EscribirEnConsolaThreadSafe)

    # **** Variables para la ventana de consola *******************************************************************************

    self._qtConsoleWindow= None
    self._qtConsoleText= None
    self._oConsoleCapture= None

    # **** Crear la aplicación Qt y la ventana gráfica ************************************************************************

    self._qApp = QApplication.instance()
    if self._qApp is None:
      self._qApp = QApplication(sys.argv)

    self._qtWindow = QMainWindow()
    self._qtWindow.setWindowTitle(f'PROCOME - Multi-Tarjeta v{self._VERSION}')

    # **** Construir la Barra de Menus ****************************************************************************************

    self._BarraDeMenus_Construir()

    # **** Construir el Frame principal ***************************************************************************************

    self._FramePrincipal_Construir()

    # **** Ajustar tamaño de la ventana ***************************************************************************************

    self._qtWindow.adjustSize()
    self._qtWindow.setFixedSize(self._qtWindow.size())

    # **** Indicar en la pantalla los datos del canal serie *******************************************************************

    sTxtAux= self._oCSerie.port + ': ' + str(self._oCSerie.baudrate) + ',' + self._oCSerie.parity + ',' + \
             str(self._oCSerie.bytesize) + ',' + str(self._oCSerie.stopbits)
    self._CSerie_MostrarCfg(sTxtAux)

    # **** Crear el cliente de Telegram ****************************************************************************************

    dCfg= self._oFichCfg.Parametros_Get()
    self._oTelegram= PROCOME_Telegram.PROCOME_Telegram(
      bHabilitado = dCfg.get('Telegram.Habilitado', False),
      sToken = dCfg.get('Telegram.Token', ''),
      sChatID = dCfg.get('Telegram.ChatID', ''),
      sNombreBot = dCfg.get('Telegram.NombreBot', '')
    )

    # **** Crear el gestor multi-tarjeta **************************************************************************************

    self._oGestorTarjetas = PROCOME_GestorMultiTarjeta.GestorMultiTarjeta(
      self._oCSerie, self._oFichCfg, self._oTelegram, self._iDEBUG_MaqEstados
    )

    # Configurar callbacks (usando señales Qt para thread-safety)
    self._oGestorTarjetas.SetCallbacks(
      fnEstado=self._CallbackEstadoTarjeta,
      fnMedidas=self._CallbackMedidas,
      fnEstados=self._CallbackEstados,
      fnDatosEquipo=self._CallbackDatosEquipo,
      fnOrden=self._CallbackOrden
    )

    # Inicializar tarjetas según configuración
    self._oGestorTarjetas.InicializarTarjetas()

    # **** Arrancar el temporizado del bucle periodico *************************************************************************

    self._qTimer = QTimer()
    self._qTimer.timeout.connect(self._BuclePeriodico)
    self._qTimer.start(self._K_fTmoTempBuclePeriodico_ms)

    # **** Mostrar la ventana y arrancar el MainLoop de Qt ********************************************************************

    self._bArranqueClase= False
    self._qtWindow.show()
    self._qApp.exec()
    return

  # **** FIN **** __init__*****************************************************************************************************


  # ***************************************************************************************************************************
  # **** Reconstruir GUI tras cambios de configuración
  # ***************************************************************************************************************************

  def _ReconstruirGUI(self):
    """Reconstruye el GUI completo después de cambios de configuración"""

    # Leer nueva configuración
    dCfg = self._oFichCfg.Parametros_Get()
    self._iNrMedidas = dCfg.get('Medidas.NrMedidas', 35)
    self._iNrEstados = dCfg.get('EstadosDigitales.NrEstDig', 64)
    self._iNrOrdenes = dCfg.get('Ordenes.NrOrdenes', 4)

    # Eliminar GUI anterior
    self._EliminarGUIActual()

    # Recrear barra de indicadores
    self._CrearBarraIndicadores()

    # Recrear pestañas
    for iNrTarjeta in range(1, self._K_NR_MAX_TARJETAS + 1):
      bHabilitada = dCfg.get(f'Tarjeta{iNrTarjeta}.Habilitada', False)
      iDirRemota = dCfg.get(f'Tarjeta{iNrTarjeta}.DirRemota', iNrTarjeta)

      # Crear pestaña
      tabWidget = self._CrearPestanaTarjeta(iNrTarjeta, iDirRemota, bHabilitada)
      sTitulo = f'Tarjeta {iNrTarjeta}' + (f' (Dir {iDirRemota})' if bHabilitada else ' (Deshabilitada)')
      self._qtTabWidget.addTab(tabWidget, sTitulo)

    # Reinicializar gestor de tarjetas
    self._oGestorTarjetas.InicializarTarjetas()


  def _EliminarGUIActual(self):
    """Elimina los widgets del GUI actual para permitir reconstrucción"""

    # Eliminar todas las pestañas del TabWidget
    while self._qtTabWidget.count() > 0:
      widget = self._qtTabWidget.widget(0)
      self._qtTabWidget.removeTab(0)
      if widget:
        widget.deleteLater()

    # Limpiar diccionario de tarjetas GUI
    self._dTarjetasGUI.clear()

    # Buscar y eliminar el frame de indicadores existente
    for i in range(self._mainLayout.count()):
      item = self._mainLayout.itemAt(i)
      if item and item.widget():
        widget = item.widget()
        if isinstance(widget, QGroupBox) and widget.title() == 'Estado de Comunicación':
          self._mainLayout.removeWidget(widget)
          widget.deleteLater()
          break

    # Limpiar diccionario de indicadores
    self._dIndicadoresEstado.clear()


  # ***************************************************************************************************************************
  # **** Construir los trozos de la pantalla
  # ***************************************************************************************************************************

  def _BarraDeMenus_Construir(self) :

    self._qMenuBar = self._qtWindow.menuBar()

    # Menu "Archivo"
    self._qMenuArchivo = self._qMenuBar.addMenu('Archivo')
    self._qMenuArchivo.addAction('Salir', self._MenuArchivoSalir)

    # Menu "Configuración"
    self._qMenuConfig = self._qMenuBar.addMenu('Configuración')
    self._qMenuConfig.addAction('Puerto serie', self._MenuCfgPuertoSerie)
    self._qMenuConfig.addAction('Configuración general', self._MenuCfgGeneral)
    self._qMenuConfig.addAction('Configuración de tarjetas', self._MenuCfgTarjetas)
    self._qMenuConfig.addAction('Consola', self._MenuCfgConsola)
    self._qMenuConfig.addAction('Telegram', self._MenuCfgTelegram)


  def _FramePrincipal_Construir(self) :

    # Frame Principal
    self._qfrFramePpal= QWidget()
    self._qfrFramePpal.setStyleSheet("background-color: white; color: black;")
    self._qtWindow.setCentralWidget(self._qfrFramePpal)

    # Layout principal vertical
    self._mainLayout = QVBoxLayout(self._qfrFramePpal)

    # ==== Botones superiores =========================================================================================================

    buttonLayout = QHBoxLayout()

    self._qbArrancParar= QPushButton('Arrancar comunicación')
    self._qbArrancParar.setStyleSheet(f"background-color: {self._sColorNoComunica};")
    self._qbArrancParar.clicked.connect(self._ArrancarPararComunicacion)
    buttonLayout.addWidget(self._qbArrancParar)

    self._qbVerConsola= QPushButton('Ver Consola')
    self._qbVerConsola.setStyleSheet("background-color: #FFE4B5;")
    self._qbVerConsola.clicked.connect(self._AbrirVentanaConsola)
    buttonLayout.addWidget(self._qbVerConsola)

    buttonLayout.addStretch()
    self._mainLayout.addLayout(buttonLayout)

    # ==== Barra de indicadores de estado ============================================================================================

    self._CrearBarraIndicadores()

    # ==== QTabWidget con pestañas para cada tarjeta =================================================================================

    self._qtTabWidget = QTabWidget()
    self._mainLayout.addWidget(self._qtTabWidget)

    # Crear pestañas para las 6 tarjetas
    dCfg = self._oFichCfg.Parametros_Get()
    for iNrTarjeta in range(1, self._K_NR_MAX_TARJETAS + 1):
      bHabilitada = dCfg.get(f'Tarjeta{iNrTarjeta}.Habilitada', False)
      iDirRemota = dCfg.get(f'Tarjeta{iNrTarjeta}.DirRemota', iNrTarjeta)

      # Crear pestaña
      tabWidget = self._CrearPestanaTarjeta(iNrTarjeta, iDirRemota, bHabilitada)
      sTitulo = f'Tarjeta {iNrTarjeta}' + (f' (Dir {iDirRemota})' if bHabilitada else ' (Deshabilitada)')
      self._qtTabWidget.addTab(tabWidget, sTitulo)

    # ==== Barra de estado ============================================================================================================

    self._CrearBarraEstado()

    return


  def _CrearBarraIndicadores(self):
    """Crea la barra de indicadores de estado visual para las 6 tarjetas"""

    indicadoresFrame = QGroupBox('Estado de Comunicación')
    indicadoresFrame.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }} QGroupBox::title {{ color: black; font-weight: bold; }}")
    indicadoresLayout = QHBoxLayout()
    indicadoresFrame.setLayout(indicadoresLayout)

    dCfg = self._oFichCfg.Parametros_Get()

    for i in range(1, self._K_NR_MAX_TARJETAS + 1):
      bHabilitada = dCfg.get(f'Tarjeta{i}.Habilitada', False)
      iDirRemota = dCfg.get(f'Tarjeta{i}.DirRemota', i)

      # Label de número de tarjeta
      lblTarjeta = QLabel(f'T{i}:')
      lblTarjeta.setStyleSheet("color: black; font-weight: bold;")
      indicadoresLayout.addWidget(lblTarjeta)

      # Indicador visual (punto de color)
      indicador = QLabel('●')
      sColor = self._sColorIndicadorGris if not bHabilitada else self._sColorIndicadorRojo
      indicador.setStyleSheet(f"color: {sColor}; font-size: 24px;")
      indicador.setToolTip(f'Tarjeta {i} - Dir {iDirRemota}' + (' (Deshabilitada)' if not bHabilitada else ''))
      self._dIndicadoresEstado[i] = indicador
      indicadoresLayout.addWidget(indicador)

      indicadoresLayout.addSpacing(10)

    indicadoresLayout.addStretch()
    self._mainLayout.addWidget(indicadoresFrame)


  def _CrearPestanaTarjeta(self, iNrTarjeta, iDirRemota, bHabilitada):
    """Crea una pestaña completa para una tarjeta con medidas, estados y órdenes"""

    tabWidget = QWidget()
    tabLayout = QVBoxLayout(tabWidget)

    # Inicializar diccionario para esta tarjeta
    self._dTarjetasGUI[iNrTarjeta] = {
      'Habilitada': bHabilitada,
      'DirRemota': iDirRemota,
      'Medidas': [],
      'Estados': [],
      'Ordenes': []
    }

    if not bHabilitada:
      # Si está deshabilitada, mostrar mensaje
      lblDeshabilitada = QLabel(f'Tarjeta {iNrTarjeta} deshabilitada\n\nPara habilitarla, ir a Configuración → Configuración de tarjetas')
      lblDeshabilitada.setAlignment(Qt.AlignmentFlag.AlignCenter)
      lblDeshabilitada.setStyleSheet("color: #666666; font-size: 14pt; padding: 50px;")
      tabLayout.addWidget(lblDeshabilitada)
      return tabWidget

    # ==== Medidas ================================================================================================================

    qgbMedidas = QGroupBox('Medidas')
    qgbMedidas.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }} QGroupBox::title {{ color: black; }}")
    medidasLayout = QGridLayout()
    qgbMedidas.setLayout(medidasLayout)
    tabLayout.addWidget(qgbMedidas)

    ldMedidas = []
    iElemento = 0
    iFila = 0
    iColumna = 0
    iNrElemPorFila = 5
    iSubColumna = 0

    while iElemento < self._iNrMedidas:
      ldMedidas.append({'Etiqueta': None, 'Valor': None, 'Validez': None})

      ldMedidas[iElemento]['Etiqueta'] = QLabel(f'Medida {iElemento + 1}:')
      ldMedidas[iElemento]['Etiqueta'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      medidasLayout.addWidget(ldMedidas[iElemento]['Etiqueta'], iFila, iSubColumna, Qt.AlignmentFlag.AlignLeft)
      iSubColumna += 1

      ldMedidas[iElemento]['Valor'] = QLabel('xxx.x %')
      ldMedidas[iElemento]['Valor'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      medidasLayout.addWidget(ldMedidas[iElemento]['Valor'], iFila, iSubColumna)
      iSubColumna += 1

      ldMedidas[iElemento]['Validez'] = QLabel('     ')
      ldMedidas[iElemento]['Validez'].setStyleSheet(f"background-color: {self._sColorFondo}; color: red;")
      medidasLayout.addWidget(ldMedidas[iElemento]['Validez'], iFila, iSubColumna)
      iSubColumna += 1

      iElemento += 1
      iColumna += 1
      if iColumna == iNrElemPorFila:
        iColumna = 0
        iSubColumna = 0
        iFila += 1

    self._dTarjetasGUI[iNrTarjeta]['Medidas'] = ldMedidas

    # ==== Estados ================================================================================================================

    qgbEstados = QGroupBox('Estados Digitales')
    qgbEstados.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }} QGroupBox::title {{ color: black; }}")
    estadosLayout = QGridLayout()
    qgbEstados.setLayout(estadosLayout)
    tabLayout.addWidget(qgbEstados)

    ldEstados = []
    iElemento = 0
    iFila = 0
    iColumna = 0
    iNrElemPorFila = 11
    iSubColumna = 0

    while iElemento < self._iNrEstados:
      ldEstados.append({'Etiqueta': None, 'Valor': None, 'Validez': None})

      ldEstados[iElemento]['Etiqueta'] = QLabel(f'E{iElemento + 1}:')
      ldEstados[iElemento]['Etiqueta'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      estadosLayout.addWidget(ldEstados[iElemento]['Etiqueta'], iFila, iSubColumna, Qt.AlignmentFlag.AlignLeft)
      iSubColumna += 1

      ldEstados[iElemento]['Valor'] = QLabel('x')
      ldEstados[iElemento]['Valor'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      estadosLayout.addWidget(ldEstados[iElemento]['Valor'], iFila, iSubColumna)
      iSubColumna += 1

      ldEstados[iElemento]['Validez'] = QLabel('  ')
      ldEstados[iElemento]['Validez'].setStyleSheet(f"background-color: {self._sColorFondo}; color: red;")
      estadosLayout.addWidget(ldEstados[iElemento]['Validez'], iFila, iSubColumna)
      iSubColumna += 1

      iElemento += 1
      iColumna += 1
      if iColumna == iNrElemPorFila:
        iColumna = 0
        iSubColumna = 0
        iFila += 1

    self._dTarjetasGUI[iNrTarjeta]['Estados'] = ldEstados

    # ==== Órdenes ================================================================================================================

    qgbOrdenes = QGroupBox('Órdenes de Control')
    qgbOrdenes.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }} QGroupBox::title {{ color: black; }}")
    ordenesLayout = QGridLayout()
    qgbOrdenes.setLayout(ordenesLayout)
    tabLayout.addWidget(qgbOrdenes)

    ldOrdenes = []
    iElemento = 0
    iFila = 0
    iColumna = 0
    iNrElemPorFila = 7
    iSubColumna = 0
    iUltCol = iSubColumna

    while iElemento < self._iNrOrdenes:
      ldOrdenes.append({'Etiqueta': None, 'Abrir': None, 'Cerrar': None})

      ldOrdenes[iElemento]['Etiqueta'] = QLabel(f'S{iElemento + 1}:')
      ldOrdenes[iElemento]['Etiqueta'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      ordenesLayout.addWidget(ldOrdenes[iElemento]['Etiqueta'], iFila, iSubColumna)
      iSubColumna += 1

      ldOrdenes[iElemento]['Abrir'] = QPushButton('Abrir')
      ldOrdenes[iElemento]['Abrir'].setStyleSheet(f"background-color: {self._sColorGris};")
      ldOrdenes[iElemento]['Abrir'].clicked.connect(lambda checked, t=iNrTarjeta, idx=iElemento: self._OrdenAbrir(t, idx))
      ordenesLayout.addWidget(ldOrdenes[iElemento]['Abrir'], iFila, iSubColumna)
      iSubColumna += 1

      ldOrdenes[iElemento]['Cerrar'] = QPushButton('Cerrar')
      ldOrdenes[iElemento]['Cerrar'].setStyleSheet(f"background-color: {self._sColorGris};")
      ldOrdenes[iElemento]['Cerrar'].clicked.connect(lambda checked, t=iNrTarjeta, idx=iElemento: self._OrdenCerrar(t, idx))
      ordenesLayout.addWidget(ldOrdenes[iElemento]['Cerrar'], iFila, iSubColumna)
      iSubColumna += 1

      if iUltCol < iSubColumna:
        iUltCol = iSubColumna
      iElemento += 1
      if iElemento < self._iNrOrdenes:
        iColumna += 1
        if iColumna == iNrElemPorFila:
          iColumna = 0
          iSubColumna = 0
          iFila += 1

    self._dTarjetasGUI[iNrTarjeta]['Ordenes'] = ldOrdenes

    # Botón limpiar y mensaje
    iFila += 1
    qbLimpiar = QPushButton('Limpiar')
    qbLimpiar.setStyleSheet(f"background-color: {self._sColorGris};")
    qbLimpiar.clicked.connect(lambda: self._LimpiarMensajeOrden(iNrTarjeta))
    ordenesLayout.addWidget(qbLimpiar, iFila, 0, 1, 2)

    qlMensaje = QLabel('')
    qlMensaje.setStyleSheet("background-color: yellow; color: black;")
    ordenesLayout.addWidget(qlMensaje, iFila, 2, 1, iUltCol + 1 - 2)
    self._dTarjetasGUI[iNrTarjeta]['MensajeOrden'] = qlMensaje

    # Colorear botones en gris inicialmente
    self._ColorearBotonesOrden(iNrTarjeta, False)

    return tabWidget


  def _CrearBarraEstado(self):
    """Crea la barra de estado inferior"""

    qgbEstado = QGroupBox('')
    qgbEstado.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }}")
    estadoLayout = QGridLayout()
    qgbEstado.setLayout(estadoLayout)
    self._mainLayout.addWidget(qgbEstado)

    # Canal serie
    qlCanalSerie = QLabel('Canal serie:')
    qlCanalSerie.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(qlCanalSerie, 0, 0, Qt.AlignmentFlag.AlignRight)

    self._qlCSerieCfg = QLabel('...')
    self._qlCSerieCfg.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlCSerieCfg, 0, 1, Qt.AlignmentFlag.AlignLeft)

    return


  # ***************************************************************************************************************************
  # **** CALLBACKS desde GestorMultiTarjeta (llamados desde threads)
  # ***************************************************************************************************************************

  def _CallbackEstadoTarjeta(self, iNrTarjeta, iEstadoCom):
    """Callback desde thread - usa señal Qt para actualizar GUI
    iEstadoCom: 0=sin comunicación, 1=intentando, 2=comunicando"""
    self._oSignals.actualizarEstadoTarjeta.emit(iNrTarjeta, iEstadoCom)

  def _CallbackMedidas(self, iNrTarjeta, lMedidas):
    """Callback desde thread - usa señal Qt para actualizar GUI"""
    self._oSignals.actualizarMedidas.emit(iNrTarjeta, lMedidas)

  def _CallbackEstados(self, iNrTarjeta, lEstados):
    """Callback desde thread - usa señal Qt para actualizar GUI"""
    self._oSignals.actualizarEstados.emit(iNrTarjeta, lEstados)

  def _CallbackDatosEquipo(self, iNrTarjeta, sIdEquipo, iNrMedidas, iNrEstados, sVersProcome):
    """Callback desde thread - usa señal Qt para actualizar GUI"""
    self._oSignals.actualizarDatosEquipo.emit(iNrTarjeta, sIdEquipo or '', iNrMedidas or 0, iNrEstados or 0, sVersProcome or '')

  def _CallbackOrden(self, iNrTarjeta, sMensaje):
    """Callback desde thread - usa señal Qt para actualizar GUI"""
    self._oSignals.mostrarMensajeOrden.emit(iNrTarjeta, sMensaje)


  # ***************************************************************************************************************************
  # **** ACTUALIZACIÓN DE GUI (slots de señales Qt - thread-safe)
  # ***************************************************************************************************************************

  def _ActualizarIndicadorEstado(self, iNrTarjeta, iEstadoCom):
    """Actualiza el indicador visual de estado de una tarjeta
    iEstadoCom: 0=sin comunicación (rojo), 1=intentando (amarillo), 2=comunicando (verde)"""
    if iNrTarjeta in self._dIndicadoresEstado:
      if self._dTarjetasGUI[iNrTarjeta]['Habilitada']:
        # Determinar color según el estado de comunicación
        if iEstadoCom == 0:
          sColor = self._sColorIndicadorRojo
        elif iEstadoCom == 1:
          sColor = self._sColorIndicadorAmarillo
        else:  # iEstadoCom == 2
          sColor = self._sColorIndicadorVerde
      else:
        sColor = self._sColorIndicadorGris

      self._dIndicadoresEstado[iNrTarjeta].setStyleSheet(f"color: {sColor}; font-size: 24px;")

      # Actualizar botones de órdenes (solo habilitar en estado comunicando=2)
      if iNrTarjeta in self._dTarjetasGUI:
        bHabilitarBotones = (iEstadoCom == 2)
        self._ColorearBotonesOrden(iNrTarjeta, bHabilitarBotones)

        # Si no hay comunicación (estado=0), invalidar medidas y estados
        if iEstadoCom == 0:
          self._InvalidarMedidasYEstados(iNrTarjeta)

  def _ActualizarMedidasGUI(self, iNrTarjeta, lMedidas):
    """Actualiza las medidas en la GUI de una tarjeta"""
    if iNrTarjeta not in self._dTarjetasGUI:
      return

    ldMedidas = self._dTarjetasGUI[iNrTarjeta]['Medidas']

    for tMedida in lMedidas:
      iIdPunto = tMedida[0]
      if iIdPunto < len(ldMedidas):
        fValor = ((1000.0 * tMedida[3] / PROCOME_General.MEDIDAS_FONDO_DE_ESCALA) + 0.5) // 10
        ldMedidas[iIdPunto]['Valor'].setText(f'{fValor} %')

        sTexto = 'IV' if tMedida[1] else ''
        sTexto += ' OV' if tMedida[2] else ''
        ldMedidas[iIdPunto]['Validez'].setText(sTexto.strip())

  def _ActualizarEstadosGUI(self, iNrTarjeta, lEstados):
    """Actualiza los estados digitales en la GUI de una tarjeta"""
    if iNrTarjeta not in self._dTarjetasGUI:
      return

    ldEstados = self._dTarjetasGUI[iNrTarjeta]['Estados']
    for tEstado in lEstados:
      iIdPunto = tEstado[0]
      if iIdPunto < len(ldEstados):
        ldEstados[iIdPunto]['Valor'].setText('1' if tEstado[2] else '0')
        ldEstados[iIdPunto]['Validez'].setText(tEstado[1])

  def _ActualizarDatosEquipoGUI(self, iNrTarjeta, sIdEquipo, iNrMedidas, iNrEstados, sVersProcome):
    """Actualiza los datos del equipo en la GUI"""
    # Por ahora no se muestra en la nueva interfaz multi-tarjeta
    pass

  def _InvalidarMedidasYEstados(self, iNrTarjeta):
    """Invalida las medidas y estados cuando se pierde comunicación"""
    if iNrTarjeta not in self._dTarjetasGUI:
      return

    # Invalidar medidas - mostrar xxx.x %
    ldMedidas = self._dTarjetasGUI[iNrTarjeta]['Medidas']
    for dMedida in ldMedidas:
      dMedida['Valor'].setText('xxx.x %')
      dMedida['Validez'].setText('IV')

    # Invalidar estados - mostrar x
    ldEstados = self._dTarjetasGUI[iNrTarjeta]['Estados']
    for dEstado in ldEstados:
      dEstado['Valor'].setText('x')
      dEstado['Validez'].setText('IV')

  def _MostrarMensajeOrdenGUI(self, iNrTarjeta, sMensaje):
    """Muestra un mensaje en la zona de órdenes de una tarjeta"""
    if iNrTarjeta in self._dTarjetasGUI and 'MensajeOrden' in self._dTarjetasGUI[iNrTarjeta]:
      self._dTarjetasGUI[iNrTarjeta]['MensajeOrden'].setText(sMensaje)


  # ***************************************************************************************************************************
  # **** EVENTOS DE USUARIO
  # ***************************************************************************************************************************

  def _ArrancarPararComunicacion(self):
    """Arranca o para la comunicación con todas las tarjetas habilitadas"""

    if self._bArranqueClase:
      return

    if not self._bComunicacionActiva:
      # Arrancar comunicación
      sError = self._oGestorTarjetas.ArrancarComunicacion()
      if sError:
        QMessageBox.critical(self._qtWindow, 'Error', sError)
        return

      self._bComunicacionActiva = True
      self._qbArrancParar.setStyleSheet(f"background-color: {self._sColorComunicando};")
      self._qbArrancParar.setText('Parar comunicación')
    else:
      # Parar comunicación
      self._oGestorTarjetas.PararComunicacion()
      self._bComunicacionActiva = False
      self._qbArrancParar.setStyleSheet(f"background-color: {self._sColorNoComunica};")
      self._qbArrancParar.setText('Arrancar comunicación')

      # Poner todos los indicadores en rojo (estado 0 = sin comunicación)
      for iNrTarjeta in range(1, self._K_NR_MAX_TARJETAS + 1):
        if iNrTarjeta in self._dTarjetasGUI and self._dTarjetasGUI[iNrTarjeta]['Habilitada']:
          self._ActualizarIndicadorEstado(iNrTarjeta, 0)

  def _OrdenAbrir(self, iNrTarjeta, iNrOrden):
    """Envía orden de abrir a una tarjeta específica"""
    if not self._bComunicacionActiva:
      return

    self._oGestorTarjetas.EnviarOrden(iNrTarjeta, iNrOrden, 'OFF')

  def _OrdenCerrar(self, iNrTarjeta, iNrOrden):
    """Envía orden de cerrar a una tarjeta específica"""
    if not self._bComunicacionActiva:
      return

    self._oGestorTarjetas.EnviarOrden(iNrTarjeta, iNrOrden, 'ON')

  def _LimpiarMensajeOrden(self, iNrTarjeta):
    """Limpia el mensaje de órdenes de una tarjeta"""
    if iNrTarjeta in self._dTarjetasGUI and 'MensajeOrden' in self._dTarjetasGUI[iNrTarjeta]:
      self._dTarjetasGUI[iNrTarjeta]['MensajeOrden'].setText('')

  def _ColorearBotonesOrden(self, iNrTarjeta, bColorear):
    """Colorea o descolorea los botones de órdenes de una tarjeta"""
    if iNrTarjeta not in self._dTarjetasGUI:
      return

    ldOrdenes = self._dTarjetasGUI[iNrTarjeta]['Ordenes']
    for dOrden in ldOrdenes:
      if bColorear:
        dOrden['Abrir'].setStyleSheet(f"background-color: {self._sColorBotonAbrir};")
        dOrden['Cerrar'].setStyleSheet(f"background-color: {self._sColorBotonCerrar};")
      else:
        dOrden['Abrir'].setStyleSheet(f"background-color: {self._sColorGris};")
        dOrden['Cerrar'].setStyleSheet(f"background-color: {self._sColorGris};")


  def _CSerie_MostrarCfg(self, sTxtAux):
    """Muestra la configuración del canal serie en la barra de estado"""
    self._qlCSerieCfg.setText(sTxtAux)


  # ***************************************************************************************************************************
  # **** MENUS DE CONFIGURACIÓN
  # ***************************************************************************************************************************

  def _MenuCfgPuertoSerie(self):
    """Menú: Configuración del puerto serie"""

    if self._bArranqueClase:
      return
    if self._bComunicacionActiva:
      QMessageBox.warning(self._qtWindow, 'Advertencia',
        'No se puede cambiar la configuración mientras se está comunicando.\nPara aplicar los cambios: Parar comunicación → Cambiar config → Arrancar comunicación')
      return

    dVentanaCfgPuertoSerie = QDialog(self._qtWindow)
    dVentanaCfgPuertoSerie.setWindowTitle('Configuración - Puerto Serie')
    dVentanaCfgPuertoSerie.setModal(True)

    dCfgActual = self._oCSerie.get_settings()
    sPuertoActual = self._oCSerie.port if self._oCSerie.port else ''
    iBaudiosActual = dCfgActual['baudrate']
    sBitsActual = str(dCfgActual['bytesize'])
    sParidadActual = dCfgActual['parity']
    sBitsStopActual = str(dCfgActual['stopbits'])

    mainLayout = QVBoxLayout(dVentanaCfgPuertoSerie)
    frm_principal = QWidget()
    frm_principal.setStyleSheet("background-color: white; color: black;")
    gridLayout = QGridLayout(frm_principal)
    mainLayout.addWidget(frm_principal)

    # Puerto
    lbl_puerto = QLabel('Puerto:')
    lbl_puerto.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_puerto, 0, 0, Qt.AlignmentFlag.AlignRight)
    ent_puerto = QLineEdit()
    ent_puerto.setText(sPuertoActual)
    gridLayout.addWidget(ent_puerto, 0, 1, Qt.AlignmentFlag.AlignLeft)

    # Baudios
    lbl_baudios = QLabel('Baudios:')
    lbl_baudios.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_baudios, 1, 0, Qt.AlignmentFlag.AlignRight)
    cbx_baudios = QComboBox()
    cbx_baudios.addItems([str(x) for x in [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]])
    cbx_baudios.setCurrentText(str(iBaudiosActual))
    gridLayout.addWidget(cbx_baudios, 1, 1, Qt.AlignmentFlag.AlignLeft)

    # Bits de datos
    lbl_bits = QLabel('Bits de datos:')
    lbl_bits.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_bits, 2, 0, Qt.AlignmentFlag.AlignRight)
    cbx_bits = QComboBox()
    cbx_bits.addItems(['7', '8'])
    cbx_bits.setCurrentText(sBitsActual)
    gridLayout.addWidget(cbx_bits, 2, 1, Qt.AlignmentFlag.AlignLeft)

    # Paridad
    lbl_paridad = QLabel('Paridad:')
    lbl_paridad.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_paridad, 3, 0, Qt.AlignmentFlag.AlignRight)
    cbx_paridad = QComboBox()
    cbx_paridad.addItems(['N (Ninguna)', 'E (Par)', 'O (Impar)'])
    iIndiceParidad = ['N', 'E', 'O'].index(sParidadActual)
    cbx_paridad.setCurrentIndex(iIndiceParidad)
    gridLayout.addWidget(cbx_paridad, 3, 1, Qt.AlignmentFlag.AlignLeft)

    # Bits de parada
    lbl_bits_stop = QLabel('Bits de parada:')
    lbl_bits_stop.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_bits_stop, 4, 0, Qt.AlignmentFlag.AlignRight)
    cbx_bits_stop = QComboBox()
    cbx_bits_stop.addItems(['1', '2'])
    cbx_bits_stop.setCurrentText(sBitsStopActual)
    gridLayout.addWidget(cbx_bits_stop, 4, 1, Qt.AlignmentFlag.AlignLeft)

    # Botones
    buttonLayout = QHBoxLayout()

    def _GuardarCfgPuertoSerie():
      try:
        sPuerto = ent_puerto.text().strip()
        iBaudios = int(cbx_baudios.currentText())
        iBits = int(cbx_bits.currentText())
        sParidad = cbx_paridad.currentText()[0]
        iBitsStop = int(cbx_bits_stop.currentText())

        if not sPuerto:
          QMessageBox.critical(dVentanaCfgPuertoSerie, 'Error', 'El puerto no puede estar vacío')
          return

        self._oCSerie.port = sPuerto
        self._oCSerie.baudrate = iBaudios
        self._oCSerie.bytesize = iBits
        self._oCSerie.parity = sParidad
        self._oCSerie.stopbits = iBitsStop

        sTxtAux = self._oCSerie.port + ': ' + str(self._oCSerie.baudrate) + ',' + self._oCSerie.parity + ',' + \
                 str(self._oCSerie.bytesize) + ',' + str(self._oCSerie.stopbits)
        self._CSerie_MostrarCfg(sTxtAux)

        self._oFichCfg.PuertoSerie_Puerto_Set(sPuerto)
        self._oFichCfg.PuertoSerie_Baudios_Set(iBaudios)
        self._oFichCfg.PuertoSerie_BitsDatos_Set(iBits)
        self._oFichCfg.PuertoSerie_Paridad_Set(sParidad)
        self._oFichCfg.PuertoSerie_BitsStop_Set(iBitsStop)
        self._oFichCfg.SalvarEnFichero()

        dVentanaCfgPuertoSerie.accept()
      except Exception as e:
        QMessageBox.critical(dVentanaCfgPuertoSerie, 'Error', 'Error al guardar la configuración: ' + str(e))

    btn_guardar = QPushButton('Guardar')
    btn_guardar.setStyleSheet("background-color: lightgreen; color: black;")
    btn_guardar.clicked.connect(_GuardarCfgPuertoSerie)
    buttonLayout.addWidget(btn_guardar)

    btn_cancelar = QPushButton('Cancelar')
    btn_cancelar.setStyleSheet("background-color: lightcoral; color: black;")
    btn_cancelar.clicked.connect(dVentanaCfgPuertoSerie.reject)
    buttonLayout.addWidget(btn_cancelar)

    mainLayout.addLayout(buttonLayout)
    dVentanaCfgPuertoSerie.exec()


  def _MenuCfgGeneral(self):
    """Menú: Configuración general (medidas, estados, órdenes)"""

    if self._bArranqueClase:
      return

    dVentanaCfgGeneral = QDialog(self._qtWindow)
    dVentanaCfgGeneral.setWindowTitle('Configuración - General')
    dVentanaCfgGeneral.setModal(True)

    mainLayout = QVBoxLayout(dVentanaCfgGeneral)
    frm_principal = QWidget()
    frm_principal.setStyleSheet("background-color: white; color: black;")
    gridLayout = QGridLayout(frm_principal)
    mainLayout.addWidget(frm_principal)

    # Número de medidas
    lbl_medidas = QLabel('Número de medidas:')
    lbl_medidas.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_medidas, 0, 0, Qt.AlignmentFlag.AlignRight)
    sbx_medidas = QSpinBox()
    sbx_medidas.setRange(1, 256)
    sbx_medidas.setValue(self._iNrMedidas)
    gridLayout.addWidget(sbx_medidas, 0, 1, Qt.AlignmentFlag.AlignLeft)

    # Número de estados
    lbl_estados = QLabel('Número de estados digitales:')
    lbl_estados.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_estados, 1, 0, Qt.AlignmentFlag.AlignRight)
    sbx_estados = QSpinBox()
    sbx_estados.setRange(1, 256)
    sbx_estados.setValue(self._iNrEstados)
    gridLayout.addWidget(sbx_estados, 1, 1, Qt.AlignmentFlag.AlignLeft)

    # Número de órdenes
    lbl_ordenes = QLabel('Número de órdenes:')
    lbl_ordenes.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_ordenes, 2, 0, Qt.AlignmentFlag.AlignRight)
    sbx_ordenes = QSpinBox()
    sbx_ordenes.setRange(1, 256)
    sbx_ordenes.setValue(self._iNrOrdenes)
    gridLayout.addWidget(sbx_ordenes, 2, 1, Qt.AlignmentFlag.AlignLeft)

    # Botones
    buttonLayout = QHBoxLayout()

    def _GuardarCfgGeneral():
      try:
        iNrMedidas = sbx_medidas.value()
        iNrEstados = sbx_estados.value()
        iNrOrdenes = sbx_ordenes.value()

        if iNrMedidas < 1 or iNrMedidas > 256:
          QMessageBox.critical(dVentanaCfgGeneral, 'Error', 'El número de medidas debe estar entre 1 y 256')
          return
        if iNrEstados < 1 or iNrEstados > 256:
          QMessageBox.critical(dVentanaCfgGeneral, 'Error', 'El número de estados debe estar entre 1 y 256')
          return
        if iNrOrdenes < 1 or iNrOrdenes > 256:
          QMessageBox.critical(dVentanaCfgGeneral, 'Error', 'El número de órdenes debe estar entre 1 y 256')
          return

        # Guardar configuración
        self._oFichCfg.NrMedidas_Set(iNrMedidas)
        self._oFichCfg.NrEstDig_Set(iNrEstados)
        self._oFichCfg.NrOrdenes_Set(iNrOrdenes)
        self._oFichCfg.SalvarEnFichero()

        # Guardar estado de comunicación
        bEstabaComunicando = self._bComunicacionActiva

        # Parar comunicación si estaba activa
        if bEstabaComunicando:
          self._oGestorTarjetas.PararComunicacion()
          self._bComunicacionActiva = False

        # Reconstruir GUI con nueva configuración
        self._ReconstruirGUI()

        # Reiniciar comunicación si estaba activa
        if bEstabaComunicando:
          sError = self._oGestorTarjetas.ArrancarComunicacion()
          if not sError:
            self._bComunicacionActiva = True
            self._qbArrancParar.setStyleSheet(f"background-color: {self._sColorComunicando};")
            self._qbArrancParar.setText('Parar comunicación')

        QMessageBox.information(dVentanaCfgGeneral, 'Información',
          'Configuración guardada y aplicada correctamente.')

        dVentanaCfgGeneral.accept()
      except Exception as e:
        QMessageBox.critical(dVentanaCfgGeneral, 'Error', 'Error al guardar la configuración: ' + str(e))

    btn_guardar = QPushButton('Guardar')
    btn_guardar.setStyleSheet("background-color: lightgreen; color: black;")
    btn_guardar.clicked.connect(_GuardarCfgGeneral)
    buttonLayout.addWidget(btn_guardar)

    btn_cancelar = QPushButton('Cancelar')
    btn_cancelar.setStyleSheet("background-color: lightcoral; color: black;")
    btn_cancelar.clicked.connect(dVentanaCfgGeneral.reject)
    buttonLayout.addWidget(btn_cancelar)

    mainLayout.addLayout(buttonLayout)
    dVentanaCfgGeneral.exec()


  def _MenuCfgTarjetas(self):
    """Menú: Configuración de las 6 tarjetas"""

    if self._bArranqueClase:
      return

    dVentanaCfgTarjetas = QDialog(self._qtWindow)
    dVentanaCfgTarjetas.setWindowTitle('Configuración - Tarjetas')
    dVentanaCfgTarjetas.setModal(True)
    dVentanaCfgTarjetas.setMinimumWidth(600)

    mainLayout = QVBoxLayout(dVentanaCfgTarjetas)

    # Título
    lblTitulo = QLabel('Configuración de las 6 tarjetas PROCOME')
    lblTitulo.setStyleSheet("color: black; font-size: 14pt; font-weight: bold; padding: 10px;")
    mainLayout.addWidget(lblTitulo)

    frm_principal = QWidget()
    frm_principal.setStyleSheet("background-color: white; color: black;")
    gridLayout = QGridLayout(frm_principal)
    mainLayout.addWidget(frm_principal)

    # Headers
    gridLayout.addWidget(QLabel('Tarjeta'), 0, 0)
    gridLayout.addWidget(QLabel('Habilitada'), 0, 1)
    gridLayout.addWidget(QLabel('Dirección PROCOME'), 0, 2)
    gridLayout.addWidget(QLabel('Tests Habilitados'), 0, 3)

    # Crear controles para cada tarjeta
    dControles = {}
    dCfg = self._oFichCfg.Parametros_Get()

    for i in range(1, self._K_NR_MAX_TARJETAS + 1):
      # Label número de tarjeta
      lblNr = QLabel(f'Tarjeta {i}:')
      lblNr.setStyleSheet("color: black; font-weight: bold;")
      gridLayout.addWidget(lblNr, i, 0)

      # Checkbox habilitada
      chkHab = QCheckBox()
      chkHab.setChecked(dCfg.get(f'Tarjeta{i}.Habilitada', False))
      gridLayout.addWidget(chkHab, i, 1)

      # SpinBox dirección
      sbxDir = QSpinBox()
      sbxDir.setRange(1, 253)
      sbxDir.setValue(dCfg.get(f'Tarjeta{i}.DirRemota', i))
      gridLayout.addWidget(sbxDir, i, 2)

      # Checkbox tests
      chkTests = QCheckBox()
      chkTests.setChecked(dCfg.get(f'Tarjeta{i}.TestsHabilitados', False))
      gridLayout.addWidget(chkTests, i, 3)

      dControles[i] = {
        'Habilitada': chkHab,
        'DirRemota': sbxDir,
        'Tests': chkTests
      }

    # Botones
    buttonLayout = QHBoxLayout()

    def _GuardarCfgTarjetas():
      try:
        # Validar direcciones únicas entre tarjetas habilitadas
        lDireccionesUsadas = []
        for i in range(1, self._K_NR_MAX_TARJETAS + 1):
          if dControles[i]['Habilitada'].isChecked():
            iDir = dControles[i]['DirRemota'].value()
            if iDir in lDireccionesUsadas:
              QMessageBox.critical(dVentanaCfgTarjetas, 'Error',
                f'La dirección {iDir} está duplicada. Cada tarjeta habilitada debe tener una dirección única.')
              return
            lDireccionesUsadas.append(iDir)

        # Guardar configuración
        for i in range(1, self._K_NR_MAX_TARJETAS + 1):
          bHab = dControles[i]['Habilitada'].isChecked()
          iDir = dControles[i]['DirRemota'].value()
          bTests = dControles[i]['Tests'].isChecked()

          self._oFichCfg.Tarjeta_Habilitada_Set(i, bHab)
          self._oFichCfg.Tarjeta_DirRemota_Set(i, iDir)
          self._oFichCfg.Tarjeta_TestsHabilitados_Set(i, bTests)

        self._oFichCfg.SalvarEnFichero()

        # Guardar estado de comunicación
        bEstabaComunicando = self._bComunicacionActiva

        # Parar comunicación si estaba activa
        if bEstabaComunicando:
          self._oGestorTarjetas.PararComunicacion()
          self._bComunicacionActiva = False

        # Reconstruir GUI con nueva configuración
        self._ReconstruirGUI()

        # Reiniciar comunicación si estaba activa
        if bEstabaComunicando:
          sError = self._oGestorTarjetas.ArrancarComunicacion()
          if not sError:
            self._bComunicacionActiva = True
            self._qbArrancParar.setStyleSheet(f"background-color: {self._sColorComunicando};")
            self._qbArrancParar.setText('Parar comunicación')

        QMessageBox.information(dVentanaCfgTarjetas, 'Información',
          'Configuración de tarjetas guardada y aplicada correctamente.')

        dVentanaCfgTarjetas.accept()
      except Exception as e:
        QMessageBox.critical(dVentanaCfgTarjetas, 'Error', 'Error al guardar la configuración: ' + str(e))

    btn_guardar = QPushButton('Guardar')
    btn_guardar.setStyleSheet("background-color: lightgreen; color: black;")
    btn_guardar.clicked.connect(_GuardarCfgTarjetas)
    buttonLayout.addWidget(btn_guardar)

    btn_cancelar = QPushButton('Cancelar')
    btn_cancelar.setStyleSheet("background-color: lightcoral; color: black;")
    btn_cancelar.clicked.connect(dVentanaCfgTarjetas.reject)
    buttonLayout.addWidget(btn_cancelar)

    mainLayout.addLayout(buttonLayout)
    dVentanaCfgTarjetas.exec()


  def _MenuCfgTelegram(self):
    """Menú: Configuración de Telegram"""

    if self._bArranqueClase:
      return

    dVentanaCfgTelegram = QDialog(self._qtWindow)
    dVentanaCfgTelegram.setWindowTitle('Configuración - Telegram')
    dVentanaCfgTelegram.setModal(True)

    dCfg = self._oFichCfg.Parametros_Get()
    bHabilitadoActual = dCfg.get('Telegram.Habilitado', False)
    sNombreBotActual = dCfg.get('Telegram.NombreBot', '')
    sTokenActual = dCfg.get('Telegram.Token', '')
    sChatIDActual = dCfg.get('Telegram.ChatID', '')

    mainLayout = QVBoxLayout(dVentanaCfgTelegram)
    frm_principal = QWidget()
    frm_principal.setStyleSheet("background-color: white; color: black;")
    gridLayout = QGridLayout(frm_principal)
    mainLayout.addWidget(frm_principal)

    # Checkbox Habilitar
    chk_habilitado = QCheckBox('Habilitar notificaciones por Telegram')
    chk_habilitado.setStyleSheet("color: black;")
    chk_habilitado.setChecked(bHabilitadoActual)
    gridLayout.addWidget(chk_habilitado, 0, 0, 1, 2)

    # Nombre del Bot
    lbl_nombre = QLabel('Nombre del Bot:')
    lbl_nombre.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_nombre, 1, 0, Qt.AlignmentFlag.AlignRight)
    ent_nombre = QLineEdit()
    ent_nombre.setText(sNombreBotActual)
    ent_nombre.setPlaceholderText('Nombre descriptivo (opcional)')
    gridLayout.addWidget(ent_nombre, 1, 1, Qt.AlignmentFlag.AlignLeft)

    # Token
    lbl_token = QLabel('Token del Bot:')
    lbl_token.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_token, 2, 0, Qt.AlignmentFlag.AlignRight)
    ent_token = QLineEdit()
    ent_token.setText(sTokenActual)
    ent_token.setPlaceholderText('1234567890:ABCdefGHIjklMNOpqrsTUVwxyz')
    ent_token.setMinimumWidth(300)
    gridLayout.addWidget(ent_token, 2, 1, Qt.AlignmentFlag.AlignLeft)

    # Chat ID
    lbl_chatid = QLabel('Chat ID:')
    lbl_chatid.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_chatid, 3, 0, Qt.AlignmentFlag.AlignRight)
    ent_chatid = QLineEdit()
    ent_chatid.setText(sChatIDActual)
    ent_chatid.setPlaceholderText('123456789 o -123456789')
    gridLayout.addWidget(ent_chatid, 3, 1, Qt.AlignmentFlag.AlignLeft)

    # Texto informativo
    lbl_info = QLabel('Nota: El Token se obtiene de @BotFather en Telegram.\nEl Chat ID se puede obtener enviando un mensaje al bot y consultando\nla API de Telegram o usando @userinfobot')
    lbl_info.setStyleSheet("color: #666666; font-size: 9pt;")
    gridLayout.addWidget(lbl_info, 4, 0, 1, 2)

    # Botones
    buttonLayout = QHBoxLayout()

    def _GuardarCfgTelegram():
      try:
        bHabilitado = chk_habilitado.isChecked()
        sNombreBot = ent_nombre.text().strip()
        sToken = ent_token.text().strip()
        sChatID = ent_chatid.text().strip()

        self._oFichCfg.Telegram_Habilitado_Set(bHabilitado)
        self._oFichCfg.Telegram_NombreBot_Set(sNombreBot)
        self._oFichCfg.Telegram_Token_Set(sToken)
        self._oFichCfg.Telegram_ChatID_Set(sChatID)
        self._oFichCfg.SalvarEnFichero()

        # Actualizar el objeto Telegram
        self._oTelegram.ActualizarConfiguracion(bHabilitado, sToken, sChatID, sNombreBot)

        dVentanaCfgTelegram.accept()
      except Exception as e:
        QMessageBox.critical(dVentanaCfgTelegram, 'Error', 'Error al guardar la configuración: ' + str(e))

    btn_guardar = QPushButton('Guardar')
    btn_guardar.setStyleSheet("background-color: lightgreen; color: black;")
    btn_guardar.clicked.connect(_GuardarCfgTelegram)
    buttonLayout.addWidget(btn_guardar)

    btn_cancelar = QPushButton('Cancelar')
    btn_cancelar.setStyleSheet("background-color: lightcoral; color: black;")
    btn_cancelar.clicked.connect(dVentanaCfgTelegram.reject)
    buttonLayout.addWidget(btn_cancelar)

    mainLayout.addLayout(buttonLayout)
    dVentanaCfgTelegram.exec()


  def _MenuCfgConsola(self):
    """Menú: Configuración de la consola"""

    if self._bArranqueClase:
      return

    dVentanaCfgConsola = QDialog(self._qtWindow)
    dVentanaCfgConsola.setWindowTitle('Configuración - Consola')
    dVentanaCfgConsola.setModal(True)

    dCfg = self._oFichCfg.Parametros_Get()
    iMaxLineasActual = dCfg.get('Consola.MaxLineas', 5000)

    mainLayout = QVBoxLayout(dVentanaCfgConsola)
    frm_principal = QWidget()
    frm_principal.setStyleSheet("background-color: white; color: black;")
    gridLayout = QGridLayout(frm_principal)
    mainLayout.addWidget(frm_principal)

    # Título
    lbl_titulo = QLabel('Configuración del buffer de la consola')
    lbl_titulo.setStyleSheet("color: black; font-size: 12pt; font-weight: bold;")
    gridLayout.addWidget(lbl_titulo, 0, 0, 1, 2)

    # Número máximo de líneas
    lbl_maxlineas = QLabel('Número máximo de líneas:')
    lbl_maxlineas.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_maxlineas, 1, 0, Qt.AlignmentFlag.AlignRight)

    sbx_maxlineas = QSpinBox()
    sbx_maxlineas.setRange(100, 100000)
    sbx_maxlineas.setSingleStep(1000)
    sbx_maxlineas.setValue(iMaxLineasActual)
    gridLayout.addWidget(sbx_maxlineas, 1, 1, Qt.AlignmentFlag.AlignLeft)

    # Texto informativo
    lbl_info = QLabel(
      'Nota: Un valor alto (>10000) puede causar problemas de rendimiento.\n'
      'Valores recomendados:\n'
      '  • 1000-2000: Sistemas con poca RAM\n'
      '  • 5000: Balance óptimo (recomendado)\n'
      '  • 10000+: Si necesitas mucho historial\n\n'
      'Los cambios se aplican inmediatamente sin reiniciar.'
    )
    lbl_info.setStyleSheet("color: #666666; font-size: 9pt;")
    gridLayout.addWidget(lbl_info, 2, 0, 1, 2)

    # Botones
    buttonLayout = QHBoxLayout()

    def _GuardarCfgConsola():
      try:
        iMaxLineas = sbx_maxlineas.value()

        if iMaxLineas < 100 or iMaxLineas > 100000:
          QMessageBox.critical(dVentanaCfgConsola, 'Error',
            'El número de líneas debe estar entre 100 y 100000')
          return

        # Guardar en configuración
        self._oFichCfg.Consola_MaxLineas_Set(iMaxLineas)
        self._oFichCfg.SalvarEnFichero()

        # Aplicar cambio inmediatamente
        self._iMaxLineasConsola = iMaxLineas

        QMessageBox.information(dVentanaCfgConsola, 'Información',
          f'Configuración guardada.\nNuevo límite: {iMaxLineas} líneas.')

        dVentanaCfgConsola.accept()
      except Exception as e:
        QMessageBox.critical(dVentanaCfgConsola, 'Error',
          'Error al guardar la configuración: ' + str(e))

    btn_guardar = QPushButton('Guardar')
    btn_guardar.setStyleSheet("background-color: lightgreen; color: black;")
    btn_guardar.clicked.connect(_GuardarCfgConsola)
    buttonLayout.addWidget(btn_guardar)

    btn_cancelar = QPushButton('Cancelar')
    btn_cancelar.setStyleSheet("background-color: lightcoral; color: black;")
    btn_cancelar.clicked.connect(dVentanaCfgConsola.reject)
    buttonLayout.addWidget(btn_cancelar)

    mainLayout.addLayout(buttonLayout)
    dVentanaCfgConsola.exec()


  def _MenuArchivoSalir(self):
    """Menú: Salir de la aplicación"""
    if self._qtWindow:
      self._qtWindow.close()
    if self._qApp:
      self._qApp.quit()


  # ***************************************************************************************************************************
  # **** BUCLE PERIODICO
  # ***************************************************************************************************************************

  def _BuclePeriodico(self):
    """Bucle periódico de actualización (ya no gestiona comunicación, solo GUI)"""
    # El gestor multi-tarjeta maneja la comunicación en threads separados
    # Este bucle solo se usa para mantener la GUI responsive
    pass


  # ***************************************************************************************************************************
  # **** VENTANA DE CONSOLA
  # ***************************************************************************************************************************

  def _AbrirVentanaConsola(self):
    """Abre o trae al frente la ventana de consola"""

    if self._qtConsoleWindow is not None:
      self._qtConsoleWindow.raise_()
      self._qtConsoleWindow.activateWindow()
      self._ReorganizarVentanas()
      return

    self._qtConsoleWindow = QDialog(self._qtWindow)
    self._qtConsoleWindow.setWindowTitle('Consola')
    self._qtConsoleWindow.finished.connect(self._LimpiarRecursosConsola)

    mainLayout = QVBoxLayout(self._qtConsoleWindow)

    self._qtConsoleText = QTextEdit()
    self._qtConsoleText.setReadOnly(True)
    self._qtConsoleText.setStyleSheet("background-color: black; color: white; font-family: 'Courier';")
    mainLayout.addWidget(self._qtConsoleText)

    buttonLayout = QHBoxLayout()

    btn_limpiar = QPushButton('Limpiar')
    btn_limpiar.setStyleSheet("background-color: #FFB6C1; color: black;")
    btn_limpiar.clicked.connect(self._LimpiarConsola)
    buttonLayout.addWidget(btn_limpiar)

    btn_cerrar = QPushButton('Cerrar')
    btn_cerrar.setStyleSheet("background-color: #FFB6C1; color: black;")
    btn_cerrar.clicked.connect(self._CerrarConsola)
    buttonLayout.addWidget(btn_cerrar)

    mainLayout.addLayout(buttonLayout)

    self._oConsoleCapture = ConsoleCapture(signal_emitter=self._oSignals)
    sys.stdout = self._oConsoleCapture

    self._EscribirEnConsolaThreadSafe('Consola abierta - Sistema Multi-Tarjeta\n')

    self._qtConsoleWindow.show()
    self._ReorganizarVentanas()

  def _ReorganizarVentanas(self):
    """Reorganiza las ventanas en la pantalla"""
    screen = self._qApp.primaryScreen()
    screenGeometry = screen.availableGeometry()

    mainWindowWidth = self._qtWindow.width()
    mainWindowHeight = self._qtWindow.height()

    mainWindowX = screenGeometry.width() - mainWindowWidth
    mainWindowY = 0

    self._qtWindow.move(mainWindowX, mainWindowY)

    consoleX = 0
    consoleY = 0
    consoleWidth = screenGeometry.width() - mainWindowWidth
    consoleHeight = screenGeometry.height()

    if self._qtConsoleWindow is not None:
      self._qtConsoleWindow.setGeometry(consoleX, consoleY, consoleWidth, consoleHeight)

  def _EscribirEnConsolaThreadSafe(self, texto):
    """Escribe texto en la ventana de consola (thread-safe, llamado vía señal Qt)"""
    if self._qtConsoleText is not None:
      # Verificar número de líneas actuales
      iNrLineas = self._qtConsoleText.document().blockCount()

      # Si supera el límite, eliminar las líneas más antiguas
      if iNrLineas >= self._iMaxLineasConsola:
        # Deshabilitar actualizaciones temporalmente para mejor rendimiento
        self._qtConsoleText.setUpdatesEnabled(False)

        try:
          # Obtener todo el texto actual
          sTextoActual = self._qtConsoleText.toPlainText()

          # Dividir en líneas y mantener solo las últimas (dejando margen del 20%)
          lLineas = sTextoActual.split('\n')
          iLineasAMantener = int(self._iMaxLineasConsola * 0.8)

          if len(lLineas) > iLineasAMantener:
            # Mantener solo las últimas líneas
            lLineasRecientes = lLineas[-iLineasAMantener:]
            sTextoReducido = '\n'.join(lLineasRecientes)

            # Reemplazar contenido
            self._qtConsoleText.setPlainText(sTextoReducido)
        finally:
          # Re-habilitar actualizaciones
          self._qtConsoleText.setUpdatesEnabled(True)

      # Agregar el nuevo texto
      self._qtConsoleText.insertPlainText(texto)

      # Auto-scroll al final
      scrollbar = self._qtConsoleText.verticalScrollBar()
      scrollbar.setValue(scrollbar.maximum())

      # Actualizar widget
      self._qtConsoleText.update()

  def _LimpiarConsola(self):
    """Limpia el contenido de la consola"""
    if self._qtConsoleText is not None:
      self._qtConsoleText.clear()

  def _CerrarConsola(self):
    """Cierra la ventana de consola"""
    if self._qtConsoleWindow is not None:
      self._qtConsoleWindow.close()

  def _LimpiarRecursosConsola(self):
    """Limpia los recursos de la consola cuando se cierra"""
    if self._oConsoleCapture is not None:
      sys.stdout = self._oConsoleCapture.original_stdout
      self._oConsoleCapture = None

    self._qtConsoleWindow = None
    self._qtConsoleText = None

# #############################################################################################################################
