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
                               QFileDialog, QDialog, QTextEdit, QCheckBox)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction
import PROCOME_General
import PROCOME_MaqEstados
import PROCOME_ConstruirTramaRcp
import PROCOME_AnalizarTramaRcp
import PROCOME_Telegram
import FichConfig


# #############################################################################################################################
# #### Clase para capturar la salida de consola
# #############################################################################################################################

class ConsoleCapture:
  """Clase que captura la salida de print() y la redirige a una función callback"""

  def __init__(self, callback=None):
    self.callback = callback
    self.original_stdout = sys.stdout

  def write(self, text):
    if text.strip():  # Solo si no es solo espacios en blanco
      if self.callback:
        self.callback(text)
    self.original_stdout.write(text)

  def flush(self):
    self.original_stdout.flush()

  def isatty(self):
    return False


# #############################################################################################################################
# #### Clase FormPpal
# #############################################################################################################################
#
# [  0] Ventana principal ................................................. (_qtWindow)
#       |
# [ 10] +- Barra de menus ......................................... (_qMenuBar)
# [ 11] |  +- Menu: Archivo ........................................ (_qMenuArchivo)
#       |     +- Comando: Salir ................................... (_MenuArchivoSalir)
#       |
# [ 20] +- Frame Principal ........................................... (_qfrFramePpal)
#          |
#[100]    +- Arrancar/Parar la comunicación ................... (self._qbArrancParar)
#          |
#[110]    +- Medidas .................................................. (_qgbMedidas)
#          |
#[120]    +- Estados .................................................. (_qgbEstados)
#          |
#[130]    +- Ordenes .................................................. (_qgbOrdenes)


class FormPpal:

  # ***************************************************************************************************************************
  # **** __init__
  # ***************************************************************************************************************************

  def __init__(self, iNrMedidas, iNrEstados, iNrOrdenes, iDirProtocolo, oCSerie, oFichCfg= None):

    # **** Inicializar constantes *********************************************************************************************

    self._K_fTmoTempBuclePeriodico_ms= 15

    self._sColorGris= '#E0E0E0'
    self._sColorFondo= 'white'
    self._sColorBotonAbrir=  'red'
    self._sColorBotonCerrar= 'green'
    #
    self._sColorNoComunica= self._sColorGris
    self._sColorComunicando= '#C0FFC0'
    self._iDEBUG_MaqEstados= 0x03F    # 0x03F

    # **** Inicializar variables **********************************************************************************************

    self._iNrMedidas= iNrMedidas
    self._iNrEstados= iNrEstados
    self._iNrOrdenes= iNrOrdenes
    self._iDirProtocolo= iDirProtocolo
    self._bArranqueClase= True
    self._oCSerie= oCSerie
    self._oFichCfg= oFichCfg if oFichCfg is not None else FichConfig.FichConfig()
    #
    self._dTemp= {'TmpRcp_seg' : 0,
                  'TmpEspera_seg' : 0,
                  'TmpSincr_seg' : 0,
                  'TmpPetGral_seg' : 0,
                  'TmpPetEstDig_seg' : 0
                 }
    self._oConstrTramaRcp= None
    self._oMaqEstados= None

    # **** Variables para la ventana de consola *******************************************************************************

    self._qtConsoleWindow= None
    self._qtConsoleText= None
    self._oConsoleCapture= None

    # **** Crear la aplicación Qt y la ventana gráfica ************************************************************************
    #
    # De momento solo se abre por si es necesario dar algún mensaje

    self._qApp = QApplication.instance()
    if self._qApp is None:
      self._qApp = QApplication(sys.argv)

    self._qtWindow = QMainWindow()
    self._qtWindow.setWindowTitle('PROCOME')
    # No se permite al usuario que cambie el tamaño de la pantalla - ajustaremos después de construir

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

    # **** Crear el objeto de construir la trama de recepción *****************************************************************

    self._oConstrTramaRcp= PROCOME_ConstruirTramaRcp.PROCOME_ConstruirTramaRcp(0x07)

    # **** Crear el cliente de Telegram ****************************************************************************************

    dCfg= self._oFichCfg.Parametros_Get()
    self._oTelegram= PROCOME_Telegram.PROCOME_Telegram(
      bHabilitado = dCfg.get('Telegram.Habilitado', False),
      sToken = dCfg.get('Telegram.Token', ''),
      sChatID = dCfg.get('Telegram.ChatID', ''),
      sNombreBot = dCfg.get('Telegram.NombreBot', '')
    )

    # **** Crear la maquina de estados *******************************************************************************************

    self._oMaqEstados= PROCOME_MaqEstados.PROCOME_MaqEstados(self._iDirProtocolo, self._dTemp, self._oConstrTramaRcp, self._oCSerie, self, self._iDEBUG_MaqEstados, self._oTelegram)
    #iRta= self.oMaqEstados.ProcesarEventos('Arrancar')
    #DEBUG_bHayUnaTrm= (iRta == 10)


    # **** Arrancar el temporizado del bucle periodico *************************************************************************
    #
    # Se pone un tiempo de 15 milisegundos porque es lo mínimo que soporta WXP

    self._fIncrT_TmpAnt= time.time()
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
  # **** Construir los trozos de la pantalla
  # ***************************************************************************************************************************

  # ===========================================================================================================================
  # ==== Construir la barra de menus
  # ===========================================================================================================================

  def _BarraDeMenus_Construir(self) :

    # [ 10] --- Barra de menus -----------------------------------------------------------
    #
    self._qMenuBar = self._qtWindow.menuBar()

    # [ 11] --- Barra de menus: Menu "Archivo" -------------------------------------------
    #
    #
    self._qMenuArchivo = self._qMenuBar.addMenu('Archivo')
    # self._qMenuArchivo.addAction('Leer la configuración', self._MenuArchivoLeer)
    # self._qMenuArchivo.addAction('Salvar la configuración', self._MenuArchivoSalvar)
    self._qMenuArchivo.addAction('Salir', self._MenuArchivoSalir)

    # [ 12] --- Barra de menus: Menu "Configuración" -----------------------------------------------
    #
    self._qMenuConfig = self._qMenuBar.addMenu('Configuración')
    self._qMenuConfig.addAction('Puerto serie', self._MenuCfgPuertoSerie)
    self._qMenuConfig.addAction('Configuración general', self._MenuCfgGeneral)
    self._qMenuConfig.addAction('Telegram', self._MenuCfgTelegram)


  # ===========================================================================================================================
  # ==== Construir el Frame principal
  # ===========================================================================================================================

  def _FramePrincipal_Construir(self) :

    # [ 20] ==== Frame Principal =========================================================
    #
    self._qfrFramePpal= QWidget()
    self._qfrFramePpal.setStyleSheet("background-color: white; color: black;")
    self._qtWindow.setCentralWidget(self._qfrFramePpal)

    # Layout principal vertical
    self._mainLayout = QVBoxLayout(self._qfrFramePpal)


    # [100] ==== Botón de arranque/Parada =====================================================================================

    buttonLayout = QHBoxLayout()

    self._qbArrancParar= QPushButton('Arrancar la comunicación')
    self._qbArrancParar.setStyleSheet(f"background-color: {self._sColorNoComunica};")
    self._qbArrancParar.clicked.connect(self._ArrancarPararComunicacion)
    buttonLayout.addWidget(self._qbArrancParar)

    # [101] ==== Botón Ver Consola ====================================================================================================

    self._qbVerConsola= QPushButton('Ver Consola')
    self._qbVerConsola.setStyleSheet("background-color: #FFE4B5;")
    self._qbVerConsola.clicked.connect(self._AbrirVentanaConsola)
    buttonLayout.addWidget(self._qbVerConsola)

    buttonLayout.addStretch()
    self._mainLayout.addLayout(buttonLayout)


    # [110] ==== Frame: Medidas ==========================================================

    self._qgbMedidas= QGroupBox('Medidas')
    self._qgbMedidas.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }} QGroupBox::title {{ color: black; }}")
    medidasLayout = QGridLayout()
    self._qgbMedidas.setLayout(medidasLayout)
    self._mainLayout.addWidget(self._qgbMedidas)

    self._ldMedidas=[]
    iElemento= 0
    iFila= 0
    iColumna= 0
    iNrElemPorFila= 5
    iSubColumna= 0

    while (iElemento < self._iNrMedidas):

      self._ldMedidas.append({'Etiqueta' : None, 'Valor' : None, 'Validez' : None})

      # ---- Label: Medida x.Etiqueta ----------------------------------------------------

      self._ldMedidas[iElemento]['Etiqueta']= QLabel('Medida ' + str(iElemento + 1) + ':')
      self._ldMedidas[iElemento]['Etiqueta'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      medidasLayout.addWidget(self._ldMedidas[iElemento]['Etiqueta'], iFila, iSubColumna, Qt.AlignmentFlag.AlignLeft)
      iSubColumna+=1

      # ---- Label: Medida x.Valor -------------------------------------------------------

      self._ldMedidas[iElemento]['Valor']= QLabel('xxx.x %')
      self._ldMedidas[iElemento]['Valor'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      medidasLayout.addWidget(self._ldMedidas[iElemento]['Valor'], iFila, iSubColumna)
      iSubColumna+=1

      # ---- Label: Medida x.Validez -------------------------------------------------------

      self._ldMedidas[iElemento]['Validez']= QLabel('IV OV')
      self._ldMedidas[iElemento]['Validez'].setStyleSheet(f"background-color: {self._sColorFondo}; color: red;")
      medidasLayout.addWidget(self._ldMedidas[iElemento]['Validez'], iFila, iSubColumna)
      iSubColumna+=1

      # ---- Preparar la siguiente iteración ----------------------------------------------------------------------------------

      iElemento+= 1
      iColumna+= 1
      if (iColumna == iNrElemPorFila) :
        iColumna= 0
        iSubColumna= 0
        iFila+= 1

    self._Medidas_BorrarValores()


    # [120] ==== Frame: Estados ===============================================================================================

    self._qgbEstados= QGroupBox('Estados')
    self._qgbEstados.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }} QGroupBox::title {{ color: black; }}")
    estadosLayout = QGridLayout()
    self._qgbEstados.setLayout(estadosLayout)
    self._mainLayout.addWidget(self._qgbEstados)

    self._ldEstados=[]
    iElemento= 0
    iFila= 0
    iColumna= 0
    iNrElemPorFila= 11
    iSubColumna= 0

    while (iElemento < self._iNrEstados):

      self._ldEstados.append({'Etiqueta' : None, 'Valor' : None, 'Validez' : None})

      # ---- Label: Estado x.Etiqueta -----------------------------------------------------------------------------------------

      self._ldEstados[iElemento]['Etiqueta']= QLabel('E' + str(iElemento + 1) + ':')
      self._ldEstados[iElemento]['Etiqueta'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      estadosLayout.addWidget(self._ldEstados[iElemento]['Etiqueta'], iFila, iSubColumna, Qt.AlignmentFlag.AlignLeft)
      iSubColumna+=1

      # ---- Label: Estado x.Valor --------------------------------------------------------------------------------------------

      self._ldEstados[iElemento]['Valor']= QLabel('x')
      self._ldEstados[iElemento]['Valor'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      estadosLayout.addWidget(self._ldEstados[iElemento]['Valor'], iFila, iSubColumna)
      iSubColumna+=1

      # ---- Label: Estado x.Validez ------------------------------------------------------------------------------------------

      self._ldEstados[iElemento]['Validez']= QLabel('IV')
      self._ldEstados[iElemento]['Validez'].setStyleSheet(f"background-color: {self._sColorFondo}; color: red;")
      estadosLayout.addWidget(self._ldEstados[iElemento]['Validez'], iFila, iSubColumna)
      iSubColumna+=1

      # ---- Preparar la siguiente iteración ----------------------------------------------------------------------------------

      iElemento+= 1
      iColumna+= 1
      if (iColumna == iNrElemPorFila) :
        iColumna= 0
        iSubColumna= 0
        iFila+= 1

    self._Estados_BorrarValores()


    # [130] ==== Frame: Ordenes ===============================================================================================

    self._qgbOrdenes= QGroupBox('Ordenes')
    self._qgbOrdenes.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }} QGroupBox::title {{ color: black; }}")
    ordenesLayout = QGridLayout()
    self._qgbOrdenes.setLayout(ordenesLayout)
    self._mainLayout.addWidget(self._qgbOrdenes)

    self._ldOrdenes=[]
    iElemento= 0
    iFila= 0
    iColumna= 0
    iNrElemPorFila= 7
    iSubColumna= 0
    iUltCol= iSubColumna

    # ---- Dibujar los elementos de cada una de las ordenes --------------------------------------------------------------------

    while (iElemento < self._iNrOrdenes):

      self._ldOrdenes.append({'Etiqueta' : None, 'Abrir' : None, 'Cerrar' : None})

      #  Label: Orden x.Etiqueta

      self._ldOrdenes[iElemento]['Etiqueta']= QLabel('S' + str(iElemento + 1) + ':')
      self._ldOrdenes[iElemento]['Etiqueta'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      ordenesLayout.addWidget(self._ldOrdenes[iElemento]['Etiqueta'], iFila, iSubColumna)
      iSubColumna+=1

      #  Button: Orden x.Abrir

      self._ldOrdenes[iElemento]['Abrir']= QPushButton('Abrir')
      self._ldOrdenes[iElemento]['Abrir'].setStyleSheet(f"background-color: {self._sColorGris};")
      self._ldOrdenes[iElemento]['Abrir'].clicked.connect(lambda checked, idx=iElemento: self._OrdenAbrir(idx))
      ordenesLayout.addWidget(self._ldOrdenes[iElemento]['Abrir'], iFila, iSubColumna)
      iSubColumna+=1

      #  Button: Orden x.Cerrar

      self._ldOrdenes[iElemento]['Cerrar']= QPushButton('Cerrar')
      self._ldOrdenes[iElemento]['Cerrar'].setStyleSheet(f"background-color: {self._sColorGris};")
      self._ldOrdenes[iElemento]['Cerrar'].clicked.connect(lambda checked, idx=iElemento: self._OrdenCerrar(idx))
      ordenesLayout.addWidget(self._ldOrdenes[iElemento]['Cerrar'], iFila, iSubColumna)
      iSubColumna+=1

      #  Preparar la siguiente iteración

      if (iUltCol < iSubColumna) : iUltCol= iSubColumna
      iElemento+= 1
      if (iElemento < self._iNrOrdenes):
        iColumna+= 1
        if (iColumna == iNrElemPorFila) :
          iColumna= 0
          iSubColumna= 0
          iFila+= 1

    self._Ordenes_ColorearBotones(False)

    # ---- Botón de "Limpiar" --------------------------------------------------------------------------------------------------

    iFila+= 1
    self._qbOrdenes_Limpiar= QPushButton('Limpiar')
    self._qbOrdenes_Limpiar.setStyleSheet(f"background-color: {self._sColorGris};")
    self._qbOrdenes_Limpiar.clicked.connect(self._Orden_LimpiarMensaje)
    ordenesLayout.addWidget(self._qbOrdenes_Limpiar, iFila, 0, 1, 2)

    # ---- Dibujar la zona de mensajes -----------------------------------------------------------------------------------------

    self._qlOrdenes_Mensaje= QLabel('...')
    self._qlOrdenes_Mensaje.setStyleSheet("background-color: yellow; color: black;")
    ordenesLayout.addWidget(self._qlOrdenes_Mensaje, iFila, 2, 1, iUltCol + 1 -2)
    self._Ordenes_MostrarMensaje('')


    # [140] ==== Frame: Barra de estado =======================================================================================

    self._qgbEstado= QGroupBox('')
    self._qgbEstado.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }}")
    estadoLayout = QGridLayout()
    self._qgbEstado.setLayout(estadoLayout)
    self._mainLayout.addWidget(self._qgbEstado)

    # ---- Canal serie --------------------------------------------------------------------------------------------------------

    #  Label: Canal serie

    self._qlCanalSerie= QLabel('Canal serie:')
    self._qlCanalSerie.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlCanalSerie, 0, 0, Qt.AlignmentFlag.AlignRight)

    #  Label: Configuración del canal serie

    self._qlCSerieCfg= QLabel('...')
    self._qlCSerieCfg.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlCSerieCfg, 0, 1, Qt.AlignmentFlag.AlignLeft)

    #  Label: Piloto de la Transmisión

    self._qlCSerieTrmF= QLabel('Trm:')
    self._qlCSerieTrmF.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlCSerieTrmF, 0, 2, Qt.AlignmentFlag.AlignRight)

    self._qlCSerieTrmM= QLabel('.')
    self._qlCSerieTrmM.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlCSerieTrmM, 0, 3)

    #  Label: Piloto de la Recepción

    self._qlCSerieRcpF= QLabel('Rcp:')
    self._qlCSerieRcpF.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlCSerieRcpF, 0, 4, Qt.AlignmentFlag.AlignRight)

    self._qlCSerieRcpM= QLabel('.')
    self._qlCSerieRcpM.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlCSerieRcpM, 0, 5)

    #  Label: Dirección PROCOME

    self._qlDirProcome= QLabel('Dirección PROCOME:')
    self._qlDirProcome.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlDirProcome, 0, 6, Qt.AlignmentFlag.AlignRight)

    self._qlDirProc_Valor= QLabel('..')
    self._qlDirProc_Valor.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlDirProc_Valor, 0, 7)
    self._qlDirProc_Valor.setText(str(self._iDirProtocolo))

    # ---- Equipo -------------------------------------------------------------------------------------------------------------

    #  Label: Equipo

    self._qlEquipo= QLabel('Equipo:')
    self._qlEquipo.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlEquipo, 1, 0, Qt.AlignmentFlag.AlignLeft)

    #  Label: Equipo. Valor

    self._qlEquipoValor= QLabel('........')
    self._qlEquipoValor.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlEquipoValor, 1, 1, Qt.AlignmentFlag.AlignLeft)

    #  Label: Nº de medidas

    self._qlEqNrMed= QLabel('Nr. medidas:')
    self._qlEqNrMed.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlEqNrMed, 1, 2)

    #  Label: Nº de medidas.Valor

    self._qlEqNrMed_Valor= QLabel('..')
    self._qlEqNrMed_Valor.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlEqNrMed_Valor, 1, 3)

    #  Label: Nº de estados digitales

    self._qlEqNrEstD= QLabel('Nr. estados dig:')
    self._qlEqNrEstD.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlEqNrEstD, 1, 4)

    #  Label: Nº de estados digitales.Valor

    self._qlEqNrEstD_Valor= QLabel('..')
    self._qlEqNrEstD_Valor.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlEqNrEstD_Valor, 1, 5)

    #  Label: Version PROCOME

    self._qlVersionP= QLabel('Versión PROCOME')
    self._qlVersionP.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlVersionP, 1, 6)

    #  Label: Version PROCOME.Valor

    self._qlVersP_Valor= QLabel('...')
    self._qlVersP_Valor.setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
    estadoLayout.addWidget(self._qlVersP_Valor, 1, 7)

    return


  # ===========================================================================================================================
  # ==== Arrancar/Parar la comunicacion
  # ===========================================================================================================================

  def _ArrancarPararComunicacion(self):

    # **** Comprobaciones iniciales *******************************************************************************************

    if (self._bArranqueClase) : return

    # **** Arrancar la comunicación *******************************************************************************************

    if (not self._oMaqEstados.Comunicando()) :
      self._Medidas_BorrarValores()
      self._Estados_BorrarValores()
      self._Ordenes_MostrarMensaje('')
      self._Ordenes_ColorearBotones(True)
      QApplication.processEvents()
      Rta= self._oMaqEstados.ProcesarEventos('Arrancar')
      self._ProcesarRespuestaMaqEstados(Rta)
      if (self._oMaqEstados.Comunicando()) :
        self._qbArrancParar.setStyleSheet(f"background-color: {self._sColorComunicando};")
        self._qbArrancParar.setText('Parar la comunicación')

    # **** Parar la comunicación ***********************************************************************************************
    else :
      self._Ordenes_ColorearBotones(False)
      Rta= self._oMaqEstados.ProcesarEventos('Parar')
      self._ProcesarRespuestaMaqEstados(Rta)
      if (not self._oMaqEstados.Comunicando()) :
        self._qbArrancParar.setStyleSheet(f"background-color: {self._sColorNoComunica};")
        self._qbArrancParar.setText('Arrancar la comunicación')

    return


  # ***************************************************************************************************************************
  # **** FRAME DE MEDIDAS: EVENTOS Y FUNCIONES
  # ***************************************************************************************************************************

  # **** Cambiar el valor de las medidas **************************************************************************************
  #
  # El parametro de entrada debe ser una lista de tuplas. Cada tupla es una medida
  # En cada tupla viene:
  # - IdPunto
  # - Flag IV
  # - Flag OV
  # - Valor de la medida, de -MEDIDAS_FONDO_DE_ESCALA a + MEDIDAS_FONDO_DE_ESCALA

  def _Medidas_ActualizarValor(self, lMedidas):

    for tMedida in lMedidas :
      iIdPunto= tMedida[0]
      if  (iIdPunto < self._iNrMedidas) :
        self._ldMedidas[iIdPunto]['Valor'].setText(str(((1000.0 * tMedida[3]/PROCOME_General.MEDIDAS_FONDO_DE_ESCALA) + 0.5) // 10) + ' %')
        sTexto= 'IV' if (tMedida[1]) else ''
        sTexto+= ' OV' if (tMedida[2]) else ''
        self._ldMedidas[iIdPunto]['Validez'].setText(sTexto.strip())

    return


  # **** Borrar valores ******************************************************************************************************

  def _Medidas_BorrarValores(self):

    for iIndice in range(0, self._iNrMedidas) :
      self._ldMedidas[iIndice]['Valor'].setText('xxx.x %')
      self._ldMedidas[iIndice]['Validez'].setText('     ')
    return


  # ***************************************************************************************************************************
  # **** FRAME DE ESTADOS: EVENTOS Y FUNCIONES
  # ***************************************************************************************************************************

  # **** Cambiar el valor de los estados **************************************************************************************
  #
  # El parametro de entrada debe ser una lista de tuplas. Cada tupla es una medida
  # En cada tupla viene: [(iIdPunto, sIV, iValor)]
  # - IdPunto
  # - Flag IV
  # - Valor del estado

  def _Estados_ActualizarValor(self, lEstadosDig):

    for tEstado in lEstadosDig :
      iIdPunto= tEstado[0]
      if  (iIdPunto < self._iNrEstados) :
        self._ldEstados[iIdPunto]['Valor'].setText('1' if tEstado[2] else '0')
        self._ldEstados[iIdPunto]['Validez'].setText(tEstado[1])

    return


  # **** Borrar valores ******************************************************************************************************

  def _Estados_BorrarValores(self):

    for iIndice in range(0, self._iNrEstados) :
      self._ldEstados[iIndice]['Valor'].setText('.')
      self._ldEstados[iIndice]['Validez'].setText('  ')
    return



  # ***************************************************************************************************************************
  # **** FRAME DE ORDENES: EVENTOS Y FUNCIONES
  # ***************************************************************************************************************************

  # **** Pulsado el botón de "Abrir" ******************************************************************************************

  def _OrdenAbrir(self, iNrOrden):

    if (self._bArranqueClase) : return
    if (not self._oMaqEstados.Comunicando()) : return

    Rta= self._oMaqEstados.ProcesarEventos('PetOrden', [iNrOrden, 'OFF'])
    self._ProcesarRespuestaMaqEstados(Rta)
    return

  # **** Pulsado el botón de "Cerrar" ******************************************************************************************

  def _OrdenCerrar(self, iNrOrden):

    if (self._bArranqueClase) : return
    if (not self._oMaqEstados.Comunicando()) : return

    Rta= self._oMaqEstados.ProcesarEventos('PetOrden', [iNrOrden, 'ON'])
    self._ProcesarRespuestaMaqEstados(Rta)
    return

  # **** Mostar un mensaje en la zona de mensajes ******************************************************************************

  def _Ordenes_MostrarMensaje(self, sMensaje):

    self._qlOrdenes_Mensaje.setText(sMensaje)
    return

  # **** Limpiar la zona de mensajes *******************************************************************************************

  def _Orden_LimpiarMensaje(self) :
    self._qlOrdenes_Mensaje.setText('')
    return



  # **** Colorear botones ******************************************************************************************************

  def _Ordenes_ColorearBotones(self, bColorear):

    for iIndice in range(0, self._iNrOrdenes):
      if (bColorear) :
        self._ldOrdenes[iIndice]['Abrir'].setStyleSheet(f"background-color: {self._sColorBotonAbrir};")
        self._ldOrdenes[iIndice]['Cerrar'].setStyleSheet(f"background-color: {self._sColorBotonCerrar};")
      else :
        self._ldOrdenes[iIndice]['Abrir'].setStyleSheet(f"background-color: {self._sColorGris};")
        self._ldOrdenes[iIndice]['Cerrar'].setStyleSheet(f"background-color: {self._sColorGris};")


  # ***************************************************************************************************************************
  # **** FRAME DE LA BARRA DE ESTADO: EVENTOS Y FUNCIONES
  # ***************************************************************************************************************************

  # ===========================================================================================================================
  # ==== Canal serie
  # ===========================================================================================================================

  # **** Mostrar configuración del canal serie en la barra de estado **********************************************************

  def _CSerie_MostrarCfg(self, sTxtAux):
    self._qlCSerieCfg.setText(sTxtAux)
    pass

  # **** Avanzar el "Piloto de transmisión" ***********************************************************************************

  def AvanzarPilotoTrm(self):
    sJuegoCaracteres= '-\\|/'
    iPosic= sJuegoCaracteres.find(self._qlCSerieTrmM.text()) + 1
    if (iPosic >= len(sJuegoCaracteres)) : iPosic= 0
    self._qlCSerieTrmM.setText(sJuegoCaracteres[iPosic])
    return

  # **** Avanzar el "Piloto de recepción" *************************************************************************************

  def AvanzarPilotoRcp(self):
    sJuegoCaracteres= '-\\|/'
    iPosic= sJuegoCaracteres.find(self._qlCSerieRcpM.text()) + 1
    if (iPosic >= len(sJuegoCaracteres)) : iPosic= 0
    self._qlCSerieRcpM.setText(sJuegoCaracteres[iPosic])
    return


  # ===========================================================================================================================
  # ==== Equipo
  # ===========================================================================================================================

  def _ActualizarDatosEquipo(self, sIdEquipo, iNrMedidas, iNrEstados, sVersProcome):
    if (sIdEquipo is not None)  : self._qlEquipoValor.setText(sIdEquipo)
    if (iNrMedidas is not None) : self._qlEqNrMed_Valor.setText(str(iNrMedidas))
    if (iNrEstados is not None) : self._qlEqNrEstD_Valor.setText(str(iNrEstados))
    if (sVersProcome is not None) : self._qlVersP_Valor.setText(sVersProcome)
    return


  # ***************************************************************************************************************************
  # **** PROCESAR EVENTOS DE MENU
  # ***************************************************************************************************************************

  # ===========================================================================================================================
  # ==== Menus - Configuracion - Puerto Serie
  # ===========================================================================================================================

  def _MenuCfgPuertoSerie(self):

    if (self._bArranqueClase) : return
    if (self._oMaqEstados.Comunicando()) :
      QMessageBox.warning(self._qtWindow, 'Advertencia', 'No se puede cambiar la configuracion mientras se esta comunicando.\nPara aplicar los cambios: Parar comunicacion -> Cambiar config -> Arrancar comunicacion')
      return

    # **** Crear la ventana de dialogo ****

    dVentanaCfgPuertoSerie= QDialog(self._qtWindow)
    dVentanaCfgPuertoSerie.setWindowTitle('Configuracion - Puerto Serie')
    dVentanaCfgPuertoSerie.setModal(True)

    # **** Obtener valores actuales ****

    dCfgActual= self._oCSerie.get_settings()
    sPuertoActual= self._oCSerie.port if self._oCSerie.port else ''
    iBaudiosActual= dCfgActual['baudrate']
    sBitsActual= str(dCfgActual['bytesize'])
    sParidadActual= dCfgActual['parity']
    sBitsStopActual= str(dCfgActual['stopbits'])

    # **** Layout principal ****

    mainLayout = QVBoxLayout(dVentanaCfgPuertoSerie)

    frm_principal= QWidget()
    frm_principal.setStyleSheet("background-color: white; color: black;")
    gridLayout = QGridLayout(frm_principal)
    mainLayout.addWidget(frm_principal)

    # **** Puerto ****

    lbl_puerto = QLabel('Puerto:')
    lbl_puerto.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_puerto, 0, 0, Qt.AlignmentFlag.AlignRight)
    ent_puerto= QLineEdit()
    ent_puerto.setText(sPuertoActual)
    gridLayout.addWidget(ent_puerto, 0, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Baudios ****

    lbl_baudios = QLabel('Baudios:')
    lbl_baudios.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_baudios, 1, 0, Qt.AlignmentFlag.AlignRight)
    cbx_baudios= QComboBox()
    cbx_baudios.addItems([str(x) for x in [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]])
    cbx_baudios.setCurrentText(str(iBaudiosActual))
    gridLayout.addWidget(cbx_baudios, 1, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Bits de datos ****

    lbl_bits = QLabel('Bits de datos:')
    lbl_bits.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_bits, 2, 0, Qt.AlignmentFlag.AlignRight)
    cbx_bits= QComboBox()
    cbx_bits.addItems(['7', '8'])
    cbx_bits.setCurrentText(sBitsActual)
    gridLayout.addWidget(cbx_bits, 2, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Paridad ****

    lbl_paridad = QLabel('Paridad:')
    lbl_paridad.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_paridad, 3, 0, Qt.AlignmentFlag.AlignRight)
    cbx_paridad= QComboBox()
    cbx_paridad.addItems(['N (Ninguna)', 'E (Par)', 'O (Impar)'])
    iIndiceParidad= ['N', 'E', 'O'].index(sParidadActual)
    cbx_paridad.setCurrentIndex(iIndiceParidad)
    gridLayout.addWidget(cbx_paridad, 3, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Bits de parada ****

    lbl_bits_stop = QLabel('Bits de parada:')
    lbl_bits_stop.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_bits_stop, 4, 0, Qt.AlignmentFlag.AlignRight)
    cbx_bits_stop= QComboBox()
    cbx_bits_stop.addItems(['1', '2'])
    cbx_bits_stop.setCurrentText(sBitsStopActual)
    gridLayout.addWidget(cbx_bits_stop, 4, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Botones ****

    buttonLayout = QHBoxLayout()

    def _GuardarCfgPuertoSerie():
      try:
        sPuerto= ent_puerto.text().strip()
        iBaudios= int(cbx_baudios.currentText())
        iBits= int(cbx_bits.currentText())
        sParidad= cbx_paridad.currentText()[0]
        iBitsStop= int(cbx_bits_stop.currentText())

        if not sPuerto:
          QMessageBox.critical(dVentanaCfgPuertoSerie, 'Error', 'El puerto no puede estar vacio')
          return

        # Guardar en la configuracion del puerto serie
        self._oCSerie.port= sPuerto
        self._oCSerie.baudrate= iBaudios
        self._oCSerie.bytesize= iBits
        self._oCSerie.parity= sParidad
        self._oCSerie.stopbits= iBitsStop

        # Actualizar la pantalla
        sTxtAux= self._oCSerie.port + ': ' + str(self._oCSerie.baudrate) + ',' + self._oCSerie.parity + ',' + \
                 str(self._oCSerie.bytesize) + ',' + str(self._oCSerie.stopbits)
        self._CSerie_MostrarCfg(sTxtAux)

        # Guardar automáticamente en el archivo de configuración
        self._oFichCfg.PuertoSerie_Puerto_Set(sPuerto)
        self._oFichCfg.PuertoSerie_Baudios_Set(iBaudios)
        self._oFichCfg.PuertoSerie_BitsDatos_Set(iBits)
        self._oFichCfg.PuertoSerie_Paridad_Set(sParidad)
        self._oFichCfg.PuertoSerie_BitsStop_Set(iBitsStop)
        self._oFichCfg.SalvarEnFichero()

        dVentanaCfgPuertoSerie.accept()
      except Exception as e:
        QMessageBox.critical(dVentanaCfgPuertoSerie, 'Error', 'Error al guardar la configuracion: ' + str(e))

    btn_guardar= QPushButton('Guardar')
    btn_guardar.setStyleSheet("background-color: lightgreen; color: black;")
    btn_guardar.clicked.connect(_GuardarCfgPuertoSerie)
    buttonLayout.addWidget(btn_guardar)

    btn_cancelar= QPushButton('Cancelar')
    btn_cancelar.setStyleSheet("background-color: lightcoral; color: black;")
    btn_cancelar.clicked.connect(dVentanaCfgPuertoSerie.reject)
    buttonLayout.addWidget(btn_cancelar)

    mainLayout.addLayout(buttonLayout)

    dVentanaCfgPuertoSerie.exec()

    return

  # ===========================================================================================================================
  # ==== Menus - Configuracion - Configuracion General
  # ===========================================================================================================================

  def _MenuCfgGeneral(self):

    if (self._bArranqueClase) : return
    if (self._oMaqEstados.Comunicando()) :
      QMessageBox.warning(self._qtWindow, 'Advertencia', 'No se puede cambiar la configuracion mientras se esta comunicando.\nPara aplicar los cambios: Parar comunicacion -> Cambiar config -> Arrancar comunicacion')
      return

    # **** Crear la ventana de dialogo ****

    dVentanaCfgGeneral= QDialog(self._qtWindow)
    dVentanaCfgGeneral.setWindowTitle('Configuracion - General')
    dVentanaCfgGeneral.setModal(True)

    # **** Layout principal ****

    mainLayout = QVBoxLayout(dVentanaCfgGeneral)

    frm_principal= QWidget()
    frm_principal.setStyleSheet("background-color: white; color: black;")
    gridLayout = QGridLayout(frm_principal)
    mainLayout.addWidget(frm_principal)

    # **** Numero de medidas ****

    lbl_medidas = QLabel('Numero de medidas:')
    lbl_medidas.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_medidas, 0, 0, Qt.AlignmentFlag.AlignRight)
    sbx_medidas= QSpinBox()
    sbx_medidas.setRange(1, 256)
    sbx_medidas.setValue(self._iNrMedidas)
    gridLayout.addWidget(sbx_medidas, 0, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Numero de estados ****

    lbl_estados = QLabel('Numero de estados digitales:')
    lbl_estados.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_estados, 1, 0, Qt.AlignmentFlag.AlignRight)
    sbx_estados= QSpinBox()
    sbx_estados.setRange(1, 256)
    sbx_estados.setValue(self._iNrEstados)
    gridLayout.addWidget(sbx_estados, 1, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Numero de ordenes ****

    lbl_ordenes = QLabel('Numero de ordenes:')
    lbl_ordenes.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_ordenes, 2, 0, Qt.AlignmentFlag.AlignRight)
    sbx_ordenes= QSpinBox()
    sbx_ordenes.setRange(1, 256)
    sbx_ordenes.setValue(self._iNrOrdenes)
    gridLayout.addWidget(sbx_ordenes, 2, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Direccion PROCOME ****

    lbl_dirprocome = QLabel('Direccion PROCOME:')
    lbl_dirprocome.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_dirprocome, 3, 0, Qt.AlignmentFlag.AlignRight)
    sbx_dirprocome= QSpinBox()
    sbx_dirprocome.setRange(1, 253)
    sbx_dirprocome.setValue(self._iDirProtocolo)
    gridLayout.addWidget(sbx_dirprocome, 3, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Botones ****

    buttonLayout = QHBoxLayout()

    def _GuardarCfgGeneral():
      try:
        iNrMedidas= sbx_medidas.value()
        iNrEstados= sbx_estados.value()
        iNrOrdenes= sbx_ordenes.value()
        iDirProcome= sbx_dirprocome.value()

        if iNrMedidas < 1 or iNrMedidas > 256:
          QMessageBox.critical(dVentanaCfgGeneral, 'Error', 'El numero de medidas debe estar entre 1 y 256')
          return
        if iNrEstados < 1 or iNrEstados > 256:
          QMessageBox.critical(dVentanaCfgGeneral, 'Error', 'El numero de estados debe estar entre 1 y 256')
          return
        if iNrOrdenes < 1 or iNrOrdenes > 256:
          QMessageBox.critical(dVentanaCfgGeneral, 'Error', 'El numero de ordenes debe estar entre 1 y 256')
          return
        if iDirProcome < 1 or iDirProcome > 253:
          QMessageBox.critical(dVentanaCfgGeneral, 'Error', 'La direccion PROCOME debe estar entre 1 y 253')
          return

        # Guardar valores temporales
        self._iNrMedidas= iNrMedidas
        self._iNrEstados= iNrEstados
        self._iNrOrdenes= iNrOrdenes
        self._iDirProtocolo= iDirProcome

        # Actualizar la dirección en la máquina de estados
        if self._oMaqEstados is not None:
          self._oMaqEstados.ActualizarDireccion(iDirProcome)

        # Actualizar la pantalla con los nuevos valores
        self._qlDirProc_Valor.setText(str(self._iDirProtocolo))

        # Reconstruir los frames con los nuevos valores
        self._ReconstruirFrames()

        # Guardar automáticamente en el archivo de configuración
        self._oFichCfg.NrMedidas_Set(iNrMedidas)
        self._oFichCfg.NrEstDig_Set(iNrEstados)
        self._oFichCfg.NrOrdenes_Set(iNrOrdenes)
        self._oFichCfg.Protocolo_DirRemota_Set(iDirProcome)
        self._oFichCfg.SalvarEnFichero()

        dVentanaCfgGeneral.accept()
      except ValueError:
        QMessageBox.critical(dVentanaCfgGeneral, 'Error', 'Ingrese valores numericos validos')
      except Exception as e:
        QMessageBox.critical(dVentanaCfgGeneral, 'Error', 'Error al guardar la configuracion: ' + str(e))

    btn_guardar= QPushButton('Guardar')
    btn_guardar.setStyleSheet("background-color: lightgreen;")
    btn_guardar.clicked.connect(_GuardarCfgGeneral)
    buttonLayout.addWidget(btn_guardar)

    btn_cancelar= QPushButton('Cancelar')
    btn_cancelar.setStyleSheet("background-color: lightcoral;")
    btn_cancelar.clicked.connect(dVentanaCfgGeneral.reject)
    buttonLayout.addWidget(btn_cancelar)

    mainLayout.addLayout(buttonLayout)

    dVentanaCfgGeneral.exec()

    return

  # ===========================================================================================================================
  # ==== Menus - Configuracion - Guardar Configuracion
  # ===========================================================================================================================

  def _MenuCfgGuardar(self):

    if (self._bArranqueClase) : return

    try:
      # **** Actualizar los parametros en el objeto FichConfig ****

      self._oFichCfg.NrMedidas_Set(self._iNrMedidas)
      self._oFichCfg.NrEstDig_Set(self._iNrEstados)
      self._oFichCfg.NrOrdenes_Set(self._iNrOrdenes)
      self._oFichCfg.Protocolo_DirRemota_Set(self._iDirProtocolo)

      # **** Actualizar los parametros del puerto serie ****

      self._oFichCfg.PuertoSerie_Puerto_Set(self._oCSerie.port)
      self._oFichCfg.PuertoSerie_Baudios_Set(self._oCSerie.baudrate)
      self._oFichCfg.PuertoSerie_BitsDatos_Set(self._oCSerie.bytesize)
      self._oFichCfg.PuertoSerie_Paridad_Set(self._oCSerie.parity)
      self._oFichCfg.PuertoSerie_BitsStop_Set(int(self._oCSerie.stopbits))

      # **** Guardar la configuracion en el fichero ****

      if (self._oFichCfg.SalvarEnFichero()) :
        QMessageBox.information(self._qtWindow, 'Exito', 'Configuracion guardada correctamente en:\n' + self._oFichCfg.NombreFichCfg_Get())
      else :
        QMessageBox.critical(self._qtWindow, 'Error', 'No se pudo guardar la configuracion en:\n' + self._oFichCfg.NombreFichCfg_Get())

    except Exception as e:
      QMessageBox.critical(self._qtWindow, 'Error', 'Error al guardar la configuracion: ' + str(e))

  # ===========================================================================================================================
  # ==== Menus - Configuracion - Cargar Configuracion
  # ===========================================================================================================================

  def _MenuCfgCargar(self):

    if (self._bArranqueClase) : return
    if (self._oMaqEstados.Comunicando()) :
      QMessageBox.warning(self._qtWindow, 'Advertencia', 'No se puede cambiar la configuracion mientras se esta comunicando.\nPara aplicar los cambios: Parar comunicacion -> Cargar config -> Arrancar comunicacion')
      return

    try:
      # **** Cargar la configuracion desde el fichero ****

      sError= self._oFichCfg.LeerDeFichero()

      if (sError != '') :
        QMessageBox.critical(self._qtWindow, 'Error', 'Error al leer la configuracion:\n' + sError)
        return

      # **** Obtener los parametros leidos ****

      dCfg= self._oFichCfg.Parametros_Get()

      # **** Actualizar la configuracion del puerto serie ****

      self._oCSerie.port= dCfg['PuertoSerie.Puerto']
      self._oCSerie.baudrate= dCfg['PuertoSerie.Baudios']
      self._oCSerie.bytesize= dCfg['PuertoSerie.BitsDatos']
      self._oCSerie.parity= dCfg['PuertoSerie.Paridad']
      self._oCSerie.stopbits= dCfg['PuertoSerie.BitsStop']

      # **** Actualizar la configuracion general ****

      self._iNrMedidas= dCfg['Medidas.NrMedidas']
      self._iNrEstados= dCfg['EstadosDigitales.NrEstDig']
      self._iNrOrdenes= dCfg['Ordenes.NrOrdenes']
      self._iDirProtocolo= dCfg['Protocolo.DirRemota']

      # **** Actualizar la dirección en la máquina de estados ****

      if self._oMaqEstados is not None:
        self._oMaqEstados.ActualizarDireccion(self._iDirProtocolo)

      # **** Actualizar la pantalla ****

      sTxtAux= self._oCSerie.port + ': ' + str(self._oCSerie.baudrate) + ',' + self._oCSerie.parity + ',' + \
               str(self._oCSerie.bytesize) + ',' + str(self._oCSerie.stopbits)
      self._CSerie_MostrarCfg(sTxtAux)
      self._qlDirProc_Valor.setText(str(self._iDirProtocolo))

      QMessageBox.information(self._qtWindow, 'Exito', 'Configuracion cargada correctamente desde:\n' + self._oFichCfg.NombreFichCfg_Get() + '\nLos cambios se aplicarán inmediatamente (no es necesario reiniciar)')

    except Exception as e:
      QMessageBox.critical(self._qtWindow, 'Error', 'Error al cargar la configuracion: ' + str(e))

  # ===========================================================================================================================
  # ==== Menus - Configuracion - Telegram
  # ===========================================================================================================================

  def _MenuCfgTelegram(self):

    if (self._bArranqueClase) : return

    # **** Crear la ventana de dialogo ****

    dVentanaCfgTelegram= QDialog(self._qtWindow)
    dVentanaCfgTelegram.setWindowTitle('Configuracion - Telegram')
    dVentanaCfgTelegram.setModal(True)

    # **** Obtener valores actuales ****

    dCfg= self._oFichCfg.Parametros_Get()
    bHabilitadoActual= dCfg.get('Telegram.Habilitado', False)
    sNombreBotActual= dCfg.get('Telegram.NombreBot', '')
    sTokenActual= dCfg.get('Telegram.Token', '')
    sChatIDActual= dCfg.get('Telegram.ChatID', '')

    # **** Layout principal ****

    mainLayout = QVBoxLayout(dVentanaCfgTelegram)

    frm_principal= QWidget()
    frm_principal.setStyleSheet("background-color: white; color: black;")
    gridLayout = QGridLayout(frm_principal)
    mainLayout.addWidget(frm_principal)

    # **** Checkbox: Habilitar Telegram ****

    chk_habilitado = QCheckBox('Habilitar notificaciones por Telegram')
    chk_habilitado.setStyleSheet("color: black;")
    chk_habilitado.setChecked(bHabilitadoActual)
    gridLayout.addWidget(chk_habilitado, 0, 0, 1, 2)

    # **** Nombre del Bot ****

    lbl_nombre = QLabel('Nombre del Bot:')
    lbl_nombre.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_nombre, 1, 0, Qt.AlignmentFlag.AlignRight)
    ent_nombre= QLineEdit()
    ent_nombre.setText(sNombreBotActual)
    ent_nombre.setPlaceholderText('Nombre descriptivo (opcional)')
    gridLayout.addWidget(ent_nombre, 1, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Token del Bot ****

    lbl_token = QLabel('Token del Bot:')
    lbl_token.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_token, 2, 0, Qt.AlignmentFlag.AlignRight)
    ent_token= QLineEdit()
    ent_token.setText(sTokenActual)
    ent_token.setPlaceholderText('1234567890:ABCdefGHIjklMNOpqrsTUVwxyz')
    ent_token.setMinimumWidth(300)
    gridLayout.addWidget(ent_token, 2, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Chat ID ****

    lbl_chatid = QLabel('Chat ID:')
    lbl_chatid.setStyleSheet("color: black;")
    gridLayout.addWidget(lbl_chatid, 3, 0, Qt.AlignmentFlag.AlignRight)
    ent_chatid= QLineEdit()
    ent_chatid.setText(sChatIDActual)
    ent_chatid.setPlaceholderText('123456789 o -123456789')
    gridLayout.addWidget(ent_chatid, 3, 1, Qt.AlignmentFlag.AlignLeft)

    # **** Texto informativo ****

    lbl_info = QLabel('Nota: El Token se obtiene de @BotFather en Telegram.\nEl Chat ID se puede obtener enviando un mensaje al bot y consultando\nla API de Telegram o usando @userinfobot')
    lbl_info.setStyleSheet("color: #666666; font-size: 9pt;")
    gridLayout.addWidget(lbl_info, 4, 0, 1, 2)

    # **** Botones ****

    buttonLayout = QHBoxLayout()

    def _GuardarCfgTelegram():
      try:
        bHabilitado= chk_habilitado.isChecked()
        sNombreBot= ent_nombre.text().strip()
        sToken= ent_token.text().strip()
        sChatID= ent_chatid.text().strip()

        # Guardar en la configuracion
        self._oFichCfg.Telegram_Habilitado_Set(bHabilitado)
        self._oFichCfg.Telegram_NombreBot_Set(sNombreBot)
        self._oFichCfg.Telegram_Token_Set(sToken)
        self._oFichCfg.Telegram_ChatID_Set(sChatID)
        self._oFichCfg.SalvarEnFichero()

        # Actualizar el objeto de Telegram con la nueva configuración
        self._oTelegram.ActualizarConfiguracion(bHabilitado, sToken, sChatID, sNombreBot)

        # Actualizar en la máquina de estados
        if self._oMaqEstados is not None:
          self._oMaqEstados.ActualizarTelegram(self._oTelegram)

        dVentanaCfgTelegram.accept()
      except Exception as e:
        QMessageBox.critical(dVentanaCfgTelegram, 'Error', 'Error al guardar la configuracion: ' + str(e))

    btn_guardar= QPushButton('Guardar')
    btn_guardar.setStyleSheet("background-color: lightgreen; color: black;")
    btn_guardar.clicked.connect(_GuardarCfgTelegram)
    buttonLayout.addWidget(btn_guardar)

    btn_cancelar= QPushButton('Cancelar')
    btn_cancelar.setStyleSheet("background-color: lightcoral; color: black;")
    btn_cancelar.clicked.connect(dVentanaCfgTelegram.reject)
    buttonLayout.addWidget(btn_cancelar)

    mainLayout.addLayout(buttonLayout)

    dVentanaCfgTelegram.exec()

    return

  # ===========================================================================================================================
  # ==== Menus - Archivo - Salir
  # ===========================================================================================================================
  #
  # Acciones a realizar cuando se sale del programa

  def _MenuArchivoSalir(self):
    # self._oFichCfg.SalvarEnFichero()
    if self._qtWindow:
      self._qtWindow.close()
    if self._qApp:
      self._qApp.quit()


  # ***************************************************************************************************************************
  # **** BUCLE PERIODICO
  # ***************************************************************************************************************************

  # ===========================================================================================================================
  # ==== Bucle
  # ===========================================================================================================================

  def _BuclePeriodico(self):

    # -------------------------------------------------------------------------------------------------------------------------
    # ---- Canal serie. Recepción
    # -------------------------------------------------------------------------------------------------------------------------
    #
    # Solo se procesa cuando el canal serie está abierto
    # Se procesa todo lo recibido hasta el momento

    if (self._oCSerie.is_open) :
      while (self._oCSerie.in_waiting != 0) :

        # **** Leer un dato del puerto serie y construir una trama ************************************************************

        iRcpCSerie= ord(self._oCSerie.read(1))
        xRta= self._oConstrTramaRcp.ConstruirTrama(iRcpCSerie)

        # **** Si se detecta algún error dar un mensaje y despreciar lo procesadoo hasta ahora ********************************

        if (type(xRta) == int) :
          if (xRta < 0) :
            print('ERROR= ', str(xRta))
            self._oConstrTramaRcp.Reset()

        # **** Si no parece que haya error procesar la trama ******************************************************************

        else :
          self.AvanzarPilotoRcp()
          lTramaRcp= xRta.copy()
          self._oConstrTramaRcp.Reset()

          # ==== Mostrar la trama en hexadecimal ==============================================================================

          # sSalida= 'Trama recibida'
          # for Campo in lTramaRcp : sSalida+= ' ' + hex(Campo).replace('x', '0')[-2:]
          # print(sSalida)

          # ==== Analizar la trama para ver que hay que hacer con ella ========================================================

          dTramaRcp= PROCOME_AnalizarTramaRcp.AnalizarTrama(lTramaRcp)

          # ==== Trama válida (a nivel de la capa de enlace) y con la dirección adecuada ======================================

          if (dTramaRcp['TramaValida'] and (dTramaRcp['Dir'] == self._iDirProtocolo)) :

            # ---- Si es un eco de la transmisión no es necesario procesarla --------------------------------------------------

            if (dTramaRcp['BitPRM']) :
              # oCSerie.rts= False
              pass

            # ---- Si es un mensaje de "Secundario" procesarlo para ver si hay que visualizar algo ----------------------------

            else :

              iASDU= dTramaRcp['TYP']

              #  Tiene ASDU= 100 (Medidas y cambios de estado)

              if (iASDU == 100) :
                dRta= PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_100(lTramaRcp)
                self._Medidas_ActualizarValor(dRta['Medidas'])
                self._Estados_ActualizarValor(dRta['CambiosED'])
                self._ActualizarDatosEquipo(None, len(dRta['Medidas']), None, None)
                # QApplication.processEvents()

              #  ASDU 103 (Transmisión de estados digitales de control)

              elif (iASDU == 103) :
                dRta= PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_103(lTramaRcp)
                self._Estados_ActualizarValor(dRta['EstadosDig'])
                self._ActualizarDatosEquipo(None, None, len(dRta['EstadosDig']), None)
                # QApplication.processEvents()

              #  ASDU 5 (Transmisión de estados digitales de control)

              elif (iASDU == 5) :
                dRta= PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_5(lTramaRcp)
                self._ActualizarDatosEquipo(dRta['TxtIdEquipo'], None, None, dRta['VersProcome'])
                # QApplication.processEvents()

              #  ASDU 121 (Confirmación de orden)

              elif (iASDU == 121) :
                dRta= PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_121(lTramaRcp)
                self._Ordenes_MostrarMensaje('Respuesta a Peticion de orden S' + str(dRta['NrOden'] + 1) + ' a ' + dRta['TipoOperacion'] + ': ' + dRta['ResultadoOper'])
                # QApplication.processEvents()

          # ==== Procesar todas las tramas en la máquina de estados ===========================================================

          Rta= self._oMaqEstados.ProcesarEventos('RecibidaTrama', lTramaRcp)
          self._ProcesarRespuestaMaqEstados(Rta)

        if (not self._oCSerie.is_open) : break


    # -------------------------------------------------------------------------------------------------------------------------
    # ---- Temporizaciones
    # -------------------------------------------------------------------------------------------------------------------------

    # **** Calcular el incremento de tiempo desde el ciclo anterior ***********************************************************

    fTmpAct= time.time()
    fIncrTmp= fTmpAct - self._fIncrT_TmpAnt
    if (fIncrTmp < 0) : fIncrTmp= 0
    self._fIncrT_TmpAnt= fTmpAct

    if (fIncrTmp > 0.0) :

      #**** Temporizado TmpRcp ************************************************************************************************

      if (self._dTemp['TmpRcp_seg'] > 0.0) :
        self._dTemp['TmpRcp_seg']-= fIncrTmp
        if (self._dTemp['TmpRcp_seg'] <= 0.0) :
          # print('Temporizado <TmpRcp> finalizado')
          Rta= self._oMaqEstados.ProcesarEventos('TimeoutRcp')
          self._ProcesarRespuestaMaqEstados(Rta)

      #**** Temporizado TmpEspera **********************************************************************************************

      if (self._dTemp['TmpEspera_seg'] > 0.0) :
        self._dTemp['TmpEspera_seg']-= fIncrTmp
        if (self._dTemp['TmpEspera_seg'] <= 0.0) :
          # print('Temporizado <TmpEspera> finalizado')
          Rta= self._oMaqEstados.ProcesarEventos('TimeoutEspera')
          self._ProcesarRespuestaMaqEstados(Rta)

      #**** Temporizado TmpSincr ***********************************************************************************************

      if (self._dTemp['TmpSincr_seg'] > 0.0) :
        self._dTemp['TmpSincr_seg']-= fIncrTmp
        if (self._dTemp['TmpSincr_seg'] <= 0.0) :
          # print('Temporizado <TmpSincr> finalizado')
          Rta= self._oMaqEstados.ProcesarEventos('TimeoutSincr')
          self._ProcesarRespuestaMaqEstados(Rta)

      #**** Temporizado TmpPetGral *********************************************************************************************

      if (self._dTemp['TmpPetGral_seg'] > 0.0) :
        self._dTemp['TmpPetGral_seg']-= fIncrTmp
        if (self._dTemp['TmpPetGral_seg'] <= 0.0) :
          # print('Temporizado <TmpPetGral> finalizado')
          Rta= self._oMaqEstados.ProcesarEventos('TimeoutPetGral')
          self._ProcesarRespuestaMaqEstados(Rta)

      #**** Temporizado TmpPetEstDig *******************************************************************************************

      if (self._dTemp['TmpPetEstDig_seg'] > 0.0) :
        self._dTemp['TmpPetEstDig_seg']-= fIncrTmp
        if (self._dTemp['TmpPetEstDig_seg'] <= 0.0) :
          # print('Temporizado <TmpPetEstDig> finalizado')
          Rta= self._oMaqEstados.ProcesarEventos('TimeoutPetEstDig')
          self._ProcesarRespuestaMaqEstados(Rta)

  # ===========================================================================================================================
  # ==== Procesar las respuestas de la máquina de estados
  # ===========================================================================================================================

  def _ProcesarRespuestaMaqEstados(self, sRespuesta):
    if (sRespuesta != '') :
      print(sRespuesta)
      if (not self._oMaqEstados.Comunicando()) :
        self._qbArrancParar.setStyleSheet(f"background-color: {self._sColorNoComunica};")
        self._qbArrancParar.setText('Arrancar la comunicación')

    return

  # ===========================================================================================================================
  # ==== Reconstruir frames dinámicamente
  # ===========================================================================================================================

  def _ReconstruirFrames(self):
    """Reconstruye los frames de Medidas, Estados y Órdenes con los nuevos valores"""
    # Reconstruir cada frame
    self._ReconstruirFrameMedidas()
    self._ReconstruirFrameEstados()
    self._ReconstruirFrameOrdenes()

    # Ajustar el tamaño de la ventana
    self._qtWindow.adjustSize()
    self._qtWindow.setFixedSize(self._qtWindow.size())

  def _ReconstruirFrameMedidas(self):
    """Reconstruye el frame de medidas con el nuevo número de medidas"""
    # Eliminar el widget anterior
    self._mainLayout.removeWidget(self._qgbMedidas)
    self._qgbMedidas.deleteLater()

    # Crear el nuevo frame
    self._qgbMedidas= QGroupBox('Medidas')
    self._qgbMedidas.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }} QGroupBox::title {{ color: black; }}")
    medidasLayout = QGridLayout()
    self._qgbMedidas.setLayout(medidasLayout)

    # Insertar en la posición correcta (después de los botones, antes de estados)
    self._mainLayout.insertWidget(1, self._qgbMedidas)

    # Crear los widgets
    self._ldMedidas=[]
    iElemento= 0
    iFila= 0
    iColumna= 0
    iNrElemPorFila= 5
    iSubColumna= 0

    while (iElemento < self._iNrMedidas):
      self._ldMedidas.append({'Etiqueta' : None, 'Valor' : None, 'Validez' : None})

      self._ldMedidas[iElemento]['Etiqueta']= QLabel('Medida ' + str(iElemento + 1) + ':')
      self._ldMedidas[iElemento]['Etiqueta'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      medidasLayout.addWidget(self._ldMedidas[iElemento]['Etiqueta'], iFila, iSubColumna, Qt.AlignmentFlag.AlignLeft)
      iSubColumna+=1

      self._ldMedidas[iElemento]['Valor']= QLabel('xxx.x %')
      self._ldMedidas[iElemento]['Valor'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      medidasLayout.addWidget(self._ldMedidas[iElemento]['Valor'], iFila, iSubColumna)
      iSubColumna+=1

      self._ldMedidas[iElemento]['Validez']= QLabel('IV OV')
      self._ldMedidas[iElemento]['Validez'].setStyleSheet(f"background-color: {self._sColorFondo}; color: red;")
      medidasLayout.addWidget(self._ldMedidas[iElemento]['Validez'], iFila, iSubColumna)
      iSubColumna+=1

      iElemento+= 1
      iColumna+= 1
      if (iColumna == iNrElemPorFila) :
        iColumna= 0
        iSubColumna= 0
        iFila+= 1

    self._Medidas_BorrarValores()

  def _ReconstruirFrameEstados(self):
    """Reconstruye el frame de estados con el nuevo número de estados"""
    # Eliminar el widget anterior
    self._mainLayout.removeWidget(self._qgbEstados)
    self._qgbEstados.deleteLater()

    # Crear el nuevo frame
    self._qgbEstados= QGroupBox('Estados')
    self._qgbEstados.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }} QGroupBox::title {{ color: black; }}")
    estadosLayout = QGridLayout()
    self._qgbEstados.setLayout(estadosLayout)

    # Insertar en la posición correcta (después de medidas, antes de órdenes)
    self._mainLayout.insertWidget(2, self._qgbEstados)

    # Crear los widgets
    self._ldEstados=[]
    iElemento= 0
    iFila= 0
    iColumna= 0
    iNrElemPorFila= 11
    iSubColumna= 0

    while (iElemento < self._iNrEstados):
      self._ldEstados.append({'Etiqueta' : None, 'Valor' : None, 'Validez' : None})

      self._ldEstados[iElemento]['Etiqueta']= QLabel('E' + str(iElemento + 1) + ':')
      self._ldEstados[iElemento]['Etiqueta'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      estadosLayout.addWidget(self._ldEstados[iElemento]['Etiqueta'], iFila, iSubColumna, Qt.AlignmentFlag.AlignLeft)
      iSubColumna+=1

      self._ldEstados[iElemento]['Valor']= QLabel('x')
      self._ldEstados[iElemento]['Valor'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      estadosLayout.addWidget(self._ldEstados[iElemento]['Valor'], iFila, iSubColumna)
      iSubColumna+=1

      self._ldEstados[iElemento]['Validez']= QLabel('IV')
      self._ldEstados[iElemento]['Validez'].setStyleSheet(f"background-color: {self._sColorFondo}; color: red;")
      estadosLayout.addWidget(self._ldEstados[iElemento]['Validez'], iFila, iSubColumna)
      iSubColumna+=1

      iElemento+= 1
      iColumna+= 1
      if (iColumna == iNrElemPorFila) :
        iColumna= 0
        iSubColumna= 0
        iFila+= 1

    self._Estados_BorrarValores()

  def _ReconstruirFrameOrdenes(self):
    """Reconstruye el frame de órdenes con el nuevo número de órdenes"""
    # Eliminar el widget anterior
    self._mainLayout.removeWidget(self._qgbOrdenes)
    self._qgbOrdenes.deleteLater()

    # Crear el nuevo frame
    self._qgbOrdenes= QGroupBox('Ordenes')
    self._qgbOrdenes.setStyleSheet(f"QGroupBox {{ background-color: {self._sColorFondo}; color: black; }} QGroupBox::title {{ color: black; }}")
    ordenesLayout = QGridLayout()
    self._qgbOrdenes.setLayout(ordenesLayout)

    # Insertar en la posición correcta (después de estados, antes de barra de estado)
    self._mainLayout.insertWidget(3, self._qgbOrdenes)

    # Crear los widgets
    self._ldOrdenes=[]
    iElemento= 0
    iFila= 0
    iColumna= 0
    iNrElemPorFila= 7
    iSubColumna= 0
    iUltCol= iSubColumna

    while (iElemento < self._iNrOrdenes):
      self._ldOrdenes.append({'Etiqueta' : None, 'Abrir' : None, 'Cerrar' : None})

      self._ldOrdenes[iElemento]['Etiqueta']= QLabel('S' + str(iElemento + 1) + ':')
      self._ldOrdenes[iElemento]['Etiqueta'].setStyleSheet(f"background-color: {self._sColorFondo}; color: black;")
      ordenesLayout.addWidget(self._ldOrdenes[iElemento]['Etiqueta'], iFila, iSubColumna)
      iSubColumna+=1

      self._ldOrdenes[iElemento]['Abrir']= QPushButton('Abrir')
      self._ldOrdenes[iElemento]['Abrir'].setStyleSheet(f"background-color: {self._sColorGris};")
      self._ldOrdenes[iElemento]['Abrir'].clicked.connect(lambda checked, idx=iElemento: self._OrdenAbrir(idx))
      ordenesLayout.addWidget(self._ldOrdenes[iElemento]['Abrir'], iFila, iSubColumna)
      iSubColumna+=1

      self._ldOrdenes[iElemento]['Cerrar']= QPushButton('Cerrar')
      self._ldOrdenes[iElemento]['Cerrar'].setStyleSheet(f"background-color: {self._sColorGris};")
      self._ldOrdenes[iElemento]['Cerrar'].clicked.connect(lambda checked, idx=iElemento: self._OrdenCerrar(idx))
      ordenesLayout.addWidget(self._ldOrdenes[iElemento]['Cerrar'], iFila, iSubColumna)
      iSubColumna+=1

      if (iUltCol < iSubColumna) : iUltCol= iSubColumna
      iElemento+= 1
      if (iElemento < self._iNrOrdenes):
        iColumna+= 1
        if (iColumna == iNrElemPorFila) :
          iColumna= 0
          iSubColumna= 0
          iFila+= 1

    self._Ordenes_ColorearBotones(False)

    # Botón de limpiar
    iFila+= 1
    self._qbOrdenes_Limpiar= QPushButton('Limpiar')
    self._qbOrdenes_Limpiar.setStyleSheet(f"background-color: {self._sColorGris};")
    self._qbOrdenes_Limpiar.clicked.connect(self._Orden_LimpiarMensaje)
    ordenesLayout.addWidget(self._qbOrdenes_Limpiar, iFila, 0, 1, 2)

    # Zona de mensajes
    self._qlOrdenes_Mensaje= QLabel('...')
    self._qlOrdenes_Mensaje.setStyleSheet("background-color: yellow; color: black;")
    ordenesLayout.addWidget(self._qlOrdenes_Mensaje, iFila, 2, 1, iUltCol + 1 -2)
    self._Ordenes_MostrarMensaje('')

  # ===========================================================================================================================
  # ==== Ventana de Consola
  # ===========================================================================================================================

  def _AbrirVentanaConsola(self):
    """Abre o trae al frente la ventana de consola"""

    # Si la ventana ya existe, traerla al frente y reorganizar ventanas
    if self._qtConsoleWindow is not None:
      self._qtConsoleWindow.raise_()
      self._qtConsoleWindow.activateWindow()
      self._ReorganizarVentanas()
      return

    # Crear la nueva ventana
    self._qtConsoleWindow = QDialog(self._qtWindow)
    self._qtConsoleWindow.setWindowTitle('Consola')

    # Conectar el evento de cierre para limpiar correctamente
    self._qtConsoleWindow.finished.connect(self._LimpiarRecursosConsola)

    # Layout principal
    mainLayout = QVBoxLayout(self._qtConsoleWindow)

    # Widget Text para mostrar la salida
    self._qtConsoleText = QTextEdit()
    self._qtConsoleText.setReadOnly(True)
    self._qtConsoleText.setStyleSheet("background-color: black; color: white; font-family: 'Courier';")
    mainLayout.addWidget(self._qtConsoleText)

    # Frame de botones
    buttonLayout = QHBoxLayout()

    btn_limpiar = QPushButton('Limpiar')
    btn_limpiar.setStyleSheet("background-color: #FFB6C1;")
    btn_limpiar.clicked.connect(self._LimpiarConsola)
    buttonLayout.addWidget(btn_limpiar)

    btn_cerrar = QPushButton('Cerrar')
    btn_cerrar.setStyleSheet("background-color: #FFB6C1;")
    btn_cerrar.clicked.connect(self._CerrarConsola)
    buttonLayout.addWidget(btn_cerrar)

    mainLayout.addLayout(buttonLayout)

    # Capturar la salida de print
    self._oConsoleCapture = ConsoleCapture(callback=self._EscribirEnConsola)
    sys.stdout = self._oConsoleCapture

    # Escribir mensaje inicial
    self._EscribirEnConsola('Consola abierta\n')

    # Mostrar la ventana y reorganizar el layout
    self._qtConsoleWindow.show()
    self._ReorganizarVentanas()

  def _ReorganizarVentanas(self):
    """Reorganiza las ventanas: principal en la esquina superior derecha, consola en el resto del espacio"""
    # Obtener la geometría de la pantalla
    screen = self._qApp.primaryScreen()
    screenGeometry = screen.availableGeometry()

    # Obtener el tamaño de la ventana principal
    mainWindowWidth = self._qtWindow.width()
    mainWindowHeight = self._qtWindow.height()

    # Calcular posición de la ventana principal (esquina superior derecha)
    mainWindowX = screenGeometry.width() - mainWindowWidth
    mainWindowY = 0

    # Posicionar la ventana principal
    self._qtWindow.move(mainWindowX, mainWindowY)

    # Calcular geometría de la ventana de consola (resto del espacio)
    consoleX = 0
    consoleY = 0
    consoleWidth = screenGeometry.width() - mainWindowWidth
    consoleHeight = screenGeometry.height()

    # Posicionar y redimensionar la ventana de consola
    if self._qtConsoleWindow is not None:
      self._qtConsoleWindow.setGeometry(consoleX, consoleY, consoleWidth, consoleHeight)

  def _EscribirEnConsola(self, texto):
    """Escribe texto en la ventana de consola"""
    if self._qtConsoleText is not None:
      self._qtConsoleText.insertPlainText(texto)
      # Auto-scroll al final
      scrollbar = self._qtConsoleText.verticalScrollBar()
      scrollbar.setValue(scrollbar.maximum())
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
    """Limpia los recursos de la consola cuando se cierra la ventana (ya sea con X o con botón Cerrar)"""
    # Restaurar stdout
    if self._oConsoleCapture is not None:
      sys.stdout = self._oConsoleCapture.original_stdout
      self._oConsoleCapture = None

    # Limpiar referencias
    self._qtConsoleWindow = None
    self._qtConsoleText = None

# #############################################################################################################################
