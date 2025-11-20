# -*- coding: cp1252 -*-

# #############################################################################################################################
# ### Dependencias
# #############################################################################################################################

import time
import sys
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
import PROCOME_General
import PROCOME_MaqEstados
import PROCOME_ConstruirTramaRcp
import PROCOME_AnalizarTramaRcp


# #############################################################################################################################
# #### Clase FormPpal
# #############################################################################################################################
#
# [  0] Ventana principal ................................................. (_tkWindow)
#       |
# [ 10] +- Barra de menus ......................................... (_tkmbBarraDeMenus)
# [ 11] |  +- Menu: Archivo ........................................ (_tkmbMenuArchivo)
#       |     +- Comando: Salir ................................... (_MenuArchivoSalir)
#       |
# [ 20] +- Frame Principal ........................................... (_tkfrFramePpal)
#          |
# [100]    +- Arrancar/Parar la comunicación ................... (self._tkbArrancParar)
#          |
# [110]    +- Medidas .................................................. (_tklfMedidas)
#          |
# [120]    +- Estados .................................................. (_tklfEstados)
#          |
# [130]    +- Ordenes .................................................. (_tklfOrdenes)


class FormPpal:

  # ***************************************************************************************************************************
  # **** __init__ 
  # ***************************************************************************************************************************

  def __init__(self, iNrMedidas, iNrEstados, iNrOrdenes, iDirProtocolo, oCSerie):

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
    #
    self._dTemp= {'TmpRcp_seg' : 0,
                  'TmpEspera_seg' : 0,
                  'TmpSincr_seg' : 0,
                  'TmpPetGral_seg' : 0,
                  'TmpPetEstDig_seg' : 0
                 }
    self._oConstrTramaRcp= None
    self._oMaqEstados= None

    # **** Crear la ventana grafica *******************************************************************************************
    #
    # De momento solo se abre por si es necesario dar algún mensaje

    self._tkWindow = tk.Tk()
    self._tkWindow.title('PROCOME')
    self._tkWindow.resizable(False,False)       # No se permite al usuario que cambie el tamaño de la pantalla
    self._tkWindow.protocol('WM_DELETE_WINDOW', self._MenuArchivoSalir)
    # self._tkWindow.state('icon')

    # **** Construir la Barra de Menus ****************************************************************************************
    
    self._BarraDeMenus_Construir()

    # **** Construir el Frame principal ***************************************************************************************
    
    self._FramePrincipal_Construir()
    
    # **** Indicar en la pantalla los datos del canal serie *******************************************************************

    sTxtAux= self._oCSerie.port + ': ' + str(self._oCSerie.baudrate) + ',' + self._oCSerie.parity + ',' + \
             str(self._oCSerie.bytesize) + ',' + str(self._oCSerie.stopbits)
    self._CSerie_MostrarCfg(sTxtAux)
    
    # **** Crear el objeto de construir la trama de recepción *****************************************************************
  
    self._oConstrTramaRcp= PROCOME_ConstruirTramaRcp.PROCOME_ConstruirTramaRcp(0x07)

    # **** Crear la maquina de estados *******************************************************************************************
  
    self._oMaqEstados= PROCOME_MaqEstados.PROCOME_MaqEstados(self._iDirProtocolo, self._dTemp, self._oConstrTramaRcp, self._oCSerie, self, self._iDEBUG_MaqEstados)
    #iRta= self.oMaqEstados.ProcesarEventos('Arrancar')
    #DEBUG_bHayUnaTrm= (iRta == 10)


    # **** Arracar el temporizado del bucle periodico *************************************************************************
    #
    # Se pone un tiempo de 15 milisegundos porque es lo mínimo que soporta WXP

    self._fIncrT_TmpAnt= time.time()
    self._tkWindow.after(self._K_fTmoTempBuclePeriodico_ms, self._BuclePeriodico)

    # **** Arrancar el MainLoop de tkinter ************************************************************************************

    self._bArranqueClase= False
    self._tkWindow.mainloop()
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
    self._tkWindow.option_add('*tearOff', False)     # Para quitar una linea que sale 
    self._tkmbBarraDeMenus= tk.Menu(self._tkWindow)
    self._tkWindow['menu']= self._tkmbBarraDeMenus

    # [ 11] --- Barra de menus: Menu "Archivo" -------------------------------------------
    #
    #
    self._tkmbMenuArchivo= tk.Menu(self._tkmbBarraDeMenus)
    self._tkmbBarraDeMenus.add_cascade(menu= self._tkmbMenuArchivo, label= 'Archivo')
    # self._tkmbMenuArchivo.add_command(label='Leer la configuración', command= self._MenuArchivoLeer)
    # self._tkmbMenuArchivo.add_command(label='Salvar la configuración', command= self._MenuArchivoSalvar)
    self._tkmbMenuArchivo.add_command(label='Salir', command= self._MenuArchivoSalir)
    
    # [ 12] --- Barra de menus: Menu "Configuración" -----------------------------------------------
    #
    # self._tkmbMenuConfig= tk.Menu(self._tkmbBarraDeMenus)
    # self._tkmbBarraDeMenus.add_cascade(menu= self._tkmbMenuConfig, label= 'Configuración')
    # self._tkmbMenuConfig.add_command(label= 'Puerto serie', command= self._MenuCfgPuertoSerie)


  # ===========================================================================================================================
  # ==== Construir el Frame principal
  # ===========================================================================================================================
    
  def _FramePrincipal_Construir(self) :

    # [ 20] ==== Frame Principal =========================================================
    #
    self._tkfrFramePpal= tk.LabelFrame(self._tkWindow, bg= 'white')
    self._tkfrFramePpal.grid(row= 0, column= 0, sticky='nswe')

    
    # [100] ==== Botón de arranque/Parada =====================================================================================

    self._tkbArrancParar= tk.Button(self._tkfrFramePpal, text= 'Arrancar la comunicación', bg= self._sColorNoComunica)
    self._tkbArrancParar.grid(padx= 2, pady= 2, row= 0, column= 0, sticky='w')
    self._tkbArrancParar.bind('<ButtonRelease>', self._ArrancarPararComunicacion)


    # [110] ==== Frame: Medidas ==========================================================

    self._tklfMedidas= tk.LabelFrame(self._tkfrFramePpal, text= 'Medidas', bg= self._sColorFondo)
    self._tklfMedidas.grid(padx= 2, pady= 2, row=1, column= 0, sticky='wens')

    self._ldMedidas=[]
    iElemento= 0
    iFila= 0
    iColumna= 0
    iNrElemPorFila= 5
    iSubColumna= 0

    while (iElemento < self._iNrMedidas): 

      self._ldMedidas.append({'Etiqueta' : None, 'Valor' : None, 'Validez' : None})

      # ---- Label: Medida x.Etiqueta ----------------------------------------------------

      self._ldMedidas[iElemento]['Etiqueta']= tk.Label(self._tklfMedidas, text= 'Medida ' + str(iElemento + 1) + ':', bg= self._sColorFondo)
      self._ldMedidas[iElemento]['Etiqueta'].grid(padx= 2, pady= 2, row= iFila, column= iSubColumna, sticky='w')
      iSubColumna+=1

      # ---- Label: Medida x.Valor -------------------------------------------------------

      self._ldMedidas[iElemento]['Valor']= tk.Label(self._tklfMedidas, text= 'xxx.x %', bg= self._sColorFondo)
      self._ldMedidas[iElemento]['Valor'].grid(padx= 2, pady= 2, row= iFila, column= iSubColumna, sticky='we')
      iSubColumna+=1

      # ---- Label: Medida x.Validez -------------------------------------------------------
       
      self._ldMedidas[iElemento]['Validez']= tk.Label(self._tklfMedidas, text= 'IV OV', bg= self._sColorFondo, fg= 'red')
      self._ldMedidas[iElemento]['Validez'].grid(padx= 2, pady= 2, row= iFila, column= iSubColumna, sticky='we')
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

    self._tklfEstados= tk.LabelFrame(self._tkfrFramePpal, text= 'Estados', bg= self._sColorFondo)
    self._tklfEstados.grid(padx= 2, pady= 2, row=2, column= 0, sticky='wens')
    
    self._ldEstados=[]
    iElemento= 0
    iFila= 0
    iColumna= 0
    iNrElemPorFila= 11
    iSubColumna= 0

    while (iElemento < self._iNrEstados): 

      self._ldEstados.append({'Etiqueta' : None, 'Valor' : None, 'Validez' : None})

      # ---- Label: Estado x.Etiqueta -----------------------------------------------------------------------------------------

      self._ldEstados[iElemento]['Etiqueta']= tk.Label(self._tklfEstados, text= 'E' + str(iElemento + 1) + ':', bg= self._sColorFondo)
      self._ldEstados[iElemento]['Etiqueta'].grid(padx= 2, pady= 2, row= iFila, column= iSubColumna, sticky='w')
      iSubColumna+=1

      # ---- Label: Estado x.Valor --------------------------------------------------------------------------------------------

      self._ldEstados[iElemento]['Valor']= tk.Label(self._tklfEstados, text= 'x', bg= self._sColorFondo)
      self._ldEstados[iElemento]['Valor'].grid(padx= 2, pady= 2, row= iFila, column= iSubColumna, sticky='we')
      iSubColumna+=1

      # ---- Label: Estado x.Validez ------------------------------------------------------------------------------------------

      self._ldEstados[iElemento]['Validez']= tk.Label(self._tklfEstados, text= 'IV', bg= self._sColorFondo, fg= 'red')
      self._ldEstados[iElemento]['Validez'].grid(padx= 2, pady= 2, row= iFila, column= iSubColumna, sticky='we')
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
    
    self._tklfOrdenes= tk.LabelFrame(self._tkfrFramePpal, text= 'Ordenes', bg= self._sColorFondo)
    self._tklfOrdenes.grid(padx= 2, pady= 2, row=3, column= 0, sticky='nswe')

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

      # ···· Label: Ordén x.Etiqueta ···························································································

      self._ldOrdenes[iElemento]['Etiqueta']= tk.Label(self._tklfOrdenes, text= 'S' + str(iElemento + 1) + ':', bg= self._sColorFondo)
      self._ldOrdenes[iElemento]['Etiqueta'].grid(padx= 2, pady= 2, row= iFila, column= iSubColumna, sticky='')
      iSubColumna+=1

      # ···· Button: Orden x.Abrir ·····························································································

      self._ldOrdenes[iElemento]['Abrir']= tk.Button(self._tklfOrdenes, text= 'Abrir', bg= self._sColorGris)
      self._ldOrdenes[iElemento]['Abrir'].grid(padx= 2, pady= 2, row= iFila, column= iSubColumna, sticky='')
      self._ldOrdenes[iElemento]['Abrir'].bind('<ButtonRelease>', self._OrdenAbrir)
      iSubColumna+=1

      # ···· Button: Orden x.Cerrar ····························································································

      self._ldOrdenes[iElemento]['Cerrar']= tk.Button(self._tklfOrdenes, text= 'Cerrar', bg= self._sColorGris)
      self._ldOrdenes[iElemento]['Cerrar'].grid(padx= 2, pady= 2, row= iFila, column= iSubColumna, sticky='')
      self._ldOrdenes[iElemento]['Cerrar'].bind('<ButtonRelease>', self._OrdenCerrar)
      iSubColumna+=1
    
      # ···· Preparar la siguiente iteración ···················································································

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
    self._tkbOrdenes_Limpiar= tk.Button(self._tklfOrdenes, text= 'Limpiar', bg= self._sColorGris, command= self._Orden_LimpiarMensaje)
    self._tkbOrdenes_Limpiar.grid(padx= 2, pady= 2, row= iFila, column= 0, columnspan= 2, sticky='we')

    # ---- Dibujar la zona de mensajes -----------------------------------------------------------------------------------------

    self._tklOrdenes_Mensaje= tk.Label(self._tklfOrdenes, text= '...', bg= 'yellow') # 0self._sColorFondo)
    self._tklOrdenes_Mensaje.grid(padx= 2, pady= 2, row= iFila, column= 2, columnspan= iUltCol + 1 -2, sticky='we') 
    self._Ordenes_MostrarMensaje('')


    # [140] ==== Frame: Barra de estado =======================================================================================
    
    self._tklfEstado= tk.LabelFrame(self._tkfrFramePpal, text= '', bg= self._sColorFondo)
    self._tklfEstado.grid(padx= 2, pady= 2, row=4, column= 0, sticky='nswe')
    
    # ---- Canal serie --------------------------------------------------------------------------------------------------------

    # ···· Label: Canal serie ·································································································
     
    self._tklCanalSerie= tk.Label(self._tklfEstado, text= 'Canal serie:', bg= self._sColorFondo)
    self._tklCanalSerie.grid(padx= 2, pady= 2, row= 0, column= 0, sticky='e')

    # ···· Label: Configuración del canal serie ···············································································

    self._tklCSerieCfg= tk.Label(self._tklfEstado, text= '...', bg= self._sColorFondo)
    self._tklCSerieCfg.grid(padx= 2, pady= 2, row= 0, column= 1, sticky='w')
    
    # ···· Label: Piloto de la Transmisión ····················································································

    self._tklCSerieTrmF= tk.Label(self._tklfEstado, text= 'Trm:', bg= self._sColorFondo)
    self._tklCSerieTrmF.grid(padx= 2, pady= 2, row= 0, column= 2, sticky='e')

    self._tklCSerieTrmM= tk.Label(self._tklfEstado, text= '.', bg= self._sColorFondo)
    self._tklCSerieTrmM.grid(padx= 2, pady= 2, row= 0, column= 3, sticky='')
    
    # ···· Label: Piloto de la Recepción ······················································································

    self._tklCSerieRcpF= tk.Label(self._tklfEstado, text= 'Rcp:', bg= self._sColorFondo)
    self._tklCSerieRcpF.grid(padx= 2, pady= 2, row= 0, column= 4, sticky='e')

    self._tklCSerieRcpM= tk.Label(self._tklfEstado, text= '.', bg= self._sColorFondo)
    self._tklCSerieRcpM.grid(padx= 2, pady= 2, row= 0, column= 5, sticky='')

    # ···· Label: Dirección PROCOME ···························································································

    self._tklDirProcome= tk.Label(self._tklfEstado, text= 'Dirección PROCOME:', bg= self._sColorFondo)
    self._tklDirProcome.grid(padx= 2, pady= 2, row= 0, column= 6, sticky='e')

    self._tklDirProc_Valor= tk.Label(self._tklfEstado, text= '..', bg= self._sColorFondo)
    self._tklDirProc_Valor.grid(padx= 2, pady= 2, row= 0, column= 7, sticky='')
    self._tklDirProc_Valor['text']= str(self._iDirProtocolo)

    # ---- Equipo -------------------------------------------------------------------------------------------------------------

    # ···· Label: Equipo ······································································································

    self._tklEquipo= tk.Label(self._tklfEstado, text= 'Equipo:', bg= self._sColorFondo)
    self._tklEquipo.grid(padx= 2, pady= 2, row= 1, column= 0, sticky='w')

    # ···· Label: Equipo. Valor  ······························································································

    self._tklEquipoValor= tk.Label(self._tklfEstado, text= '........', bg= self._sColorFondo)
    self._tklEquipoValor.grid(padx= 2, pady= 2, row= 1, column= 1, sticky='w')
    
    # ···· Label: Nº de medidas ·······························································································

    self._tklEqNrMed= tk.Label(self._tklfEstado, text= 'Nr. medidas:', bg= self._sColorFondo)
    self._tklEqNrMed.grid(padx= 2, pady= 2, row= 1, column= 2, sticky='')
    
    # ···· Label: Nº de medidas.Valor ·························································································

    self._tklEqNrMed_Valor= tk.Label(self._tklfEstado, text= '..', bg= self._sColorFondo)
    self._tklEqNrMed_Valor.grid(padx= 2, pady= 2, row= 1, column= 3, sticky='')

    # ···· Label: Nº de estados digitales ·····················································································

    self._tklEqNrEstD= tk.Label(self._tklfEstado, text= 'Nr. estados dig:', bg= self._sColorFondo)
    self._tklEqNrEstD.grid(padx= 2, pady= 2, row= 1, column= 4, sticky='')
    
    # ···· Label: Nº de estados digitales.Valor ·························································································

    self._tklEqNrEstD_Valor= tk.Label(self._tklfEstado, text= '..', bg= self._sColorFondo)
    self._tklEqNrEstD_Valor.grid(padx= 2, pady= 2, row= 1, column= 5, sticky='')

    # ···· Label: Version PROCOME ·····························································································
    
    self._tklVersionP= tk.Label(self._tklfEstado, text= 'Versión PROCOME', bg= self._sColorFondo)
    self._tklVersionP.grid(padx= 2, pady= 2, row= 1, column= 6, sticky='')

    # ···· Label: Version PROCOME.Valor ·······················································································
    
    self._tklVersP_Valor= tk.Label(self._tklfEstado, text= '...', bg= self._sColorFondo)
    self._tklVersP_Valor.grid(padx= 2, pady= 2, row= 1, column= 7, sticky='')

    return


  # ===========================================================================================================================
  # ==== Arrancar/Parar la comunicacion
  # ===========================================================================================================================

  def _ArrancarPararComunicacion(self, oEvento):
  
    # **** Comprobaciones iniciales *******************************************************************************************

    if (self._bArranqueClase) : return
  
    # **** Arrancar la comunicación *******************************************************************************************
    
    if (not self._oMaqEstados.Comunicando()) :
      self._Medidas_BorrarValores()
      self._Estados_BorrarValores()
      self._Ordenes_MostrarMensaje('')
      self._Ordenes_ColorearBotones(True)
      self._tkWindow.update_idletasks()
      Rta= self._oMaqEstados.ProcesarEventos('Arrancar')
      self._ProcesarRespuestaMaqEstados(Rta)
      if (self._oMaqEstados.Comunicando()) :
        self._tkbArrancParar['bg']= self._sColorComunicando
        self._tkbArrancParar['text']= 'Parar la comunicación'
    
    # **** Parar la comunicación ***********************************************************************************************
    else :
      self._Ordenes_ColorearBotones(False)
      Rta= self._oMaqEstados.ProcesarEventos('Parar')
      self._ProcesarRespuestaMaqEstados(Rta)
      if (not self._oMaqEstados.Comunicando()) :
        self._tkbArrancParar['bg']= self._sColorNoComunica
        self._tkbArrancParar['text']= 'Arrancar la comunicación'

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
        self._ldMedidas[iIdPunto]['Valor']['text']= str(((1000.0 * tMedida[3]/PROCOME_General.MEDIDAS_FONDO_DE_ESCALA) + 0.5) // 10) + ' %'
        sTexto= 'IV' if (tMedida[1]) else ''
        sTexto+= ' OV' if (tMedida[2]) else ''       
        self._ldMedidas[iIdPunto]['Validez']['text']= sTexto.strip()
       
    return


  # **** Borrar valores ******************************************************************************************************
  
  def _Medidas_BorrarValores(self):

    for iIndice in range(0, self._iNrMedidas) : 
      self._ldMedidas[iIndice]['Valor']['text']= 'xxx.x %'
      self._ldMedidas[iIndice]['Validez']['text']= '     '
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
        self._ldEstados[iIdPunto]['Valor']['text']= '1' if tEstado[2] else '0'
        self._ldEstados[iIdPunto]['Validez']['text']= tEstado[1]      

    return


  # **** Borrar valores ******************************************************************************************************
  
  def _Estados_BorrarValores(self):

    for iIndice in range(0, self._iNrEstados) : 
      self._ldEstados[iIndice]['Valor']['text']= '.'
      self._ldEstados[iIndice]['Validez']['text']= '  '
    return  



  # ***************************************************************************************************************************
  # **** FRAME DE ORDENES: EVENTOS Y FUNCIONES
  # ***************************************************************************************************************************

  # **** Pulsado el botón de "Abrir" ******************************************************************************************

  def _OrdenAbrir(self, oEvento):

    if (self._bArranqueClase) : return
    if (not self._oMaqEstados.Comunicando()) : return

    IdBoton= id(oEvento.widget)
    for iIndice in range(0, self._iNrOrdenes):
      if (id(self._ldOrdenes[iIndice]['Abrir']) == IdBoton) :
        iNrOrden= iIndice
        break
    else :       
      print('ERROR: No se ha encontrado de que botón es el evento')
      return      

    Rta= self._oMaqEstados.ProcesarEventos('PetOrden', [iNrOrden, 'OFF'])
    self._ProcesarRespuestaMaqEstados(Rta)
    return

  # **** Pulsado el botón de "Cerrar" ******************************************************************************************

  def _OrdenCerrar(self, oEvento):

    if (self._bArranqueClase) : return
    if (not self._oMaqEstados.Comunicando()) : return

    IdBoton= id(oEvento.widget)
    for iIndice in range(0, self._iNrOrdenes): 
      if (id(self._ldOrdenes[iIndice]['Cerrar']) == IdBoton) :
        iNrOrden= iIndice
        break
    else :       
      print('ERROR: No se ha encontrado de que botón es el evento')
      return      

    Rta= self._oMaqEstados.ProcesarEventos('PetOrden', [iNrOrden, 'ON'])
    self._ProcesarRespuestaMaqEstados(Rta)
    return

  # **** Mostar un mensaje en la zona de mensajes ******************************************************************************

  def _Ordenes_MostrarMensaje(self, sMensaje):

    self._tklOrdenes_Mensaje['text']= sMensaje
    return    

  # **** Limpiar la zona de mensajes *******************************************************************************************

  def _Orden_LimpiarMensaje(self) :
    self._tklOrdenes_Mensaje['text']= ''
    return    
  


  # **** Colorear botones ******************************************************************************************************

  def _Ordenes_ColorearBotones(self, bColorear):

    for iIndice in range(0, self._iNrOrdenes): 
      if (bColorear) :
        self._ldOrdenes[iIndice]['Abrir']['bg']=  self._sColorBotonAbrir
        self._ldOrdenes[iIndice]['Cerrar']['bg']= self._sColorBotonCerrar
      else :
        self._ldOrdenes[iIndice]['Abrir']['bg']=  self._sColorGris
        self._ldOrdenes[iIndice]['Cerrar']['bg']= self._sColorGris


  # ***************************************************************************************************************************
  # **** FRAME DE LA BARRA DE ESTADO: EVENTOS Y FUNCIONES
  # ***************************************************************************************************************************

  # ===========================================================================================================================
  # ==== Canal serie
  # ===========================================================================================================================

  # **** Mostrar configuración del canal serie en la barra de estado **********************************************************

  def _CSerie_MostrarCfg(self, sTxtAux):
    self._tklCSerieCfg['text']= sTxtAux
    pass

  # **** Avanzar el "Piloto de transmisión" ***********************************************************************************

  def AvanzarPilotoTrm(self):
    sJuegoCaracteres= '-\\|/'
    iPosic= sJuegoCaracteres.find(self._tklCSerieTrmM['text']) + 1
    if (iPosic >= len(sJuegoCaracteres)) : iPosic= 0
    self._tklCSerieTrmM['text']= sJuegoCaracteres[iPosic]
    return
    
  # **** Avanzar el "Piloto de recepción" *************************************************************************************

  def AvanzarPilotoRcp(self):
    sJuegoCaracteres= '-\\|/'
    iPosic= sJuegoCaracteres.find(self._tklCSerieRcpM['text']) + 1
    if (iPosic >= len(sJuegoCaracteres)) : iPosic= 0
    self._tklCSerieRcpM['text']= sJuegoCaracteres[iPosic]
    return


  # ===========================================================================================================================
  # ==== Equipo
  # ===========================================================================================================================

  def _ActualizarDatosEquipo(self, sIdEquipo, iNrMedidas, iNrEstados, sVersProcome):
    if (sIdEquipo is not None)  : self._tklEquipoValor['text']= sIdEquipo
    if (iNrMedidas is not None) : self._tklEqNrMed_Valor['text']= str(iNrMedidas)
    if (iNrEstados is not None) : self._tklEqNrEstD_Valor['text']= str(iNrEstados)
    if (sVersProcome is not None) : self._tklVersP_Valor['text']= sVersProcome
    return

    
  # ***************************************************************************************************************************
  # **** PROCESAR EVENTOS DE MENU
  # ***************************************************************************************************************************  

  # ===========================================================================================================================
  # ==== Menus - Archivo - Salir
  # ===========================================================================================================================
  #
  # Acciones a realizar cuando se sale del programa
  
  def _MenuArchivoSalir(self):  
    # self._oFichCfg.SalvarEnFichero()
    self._tkWindow.destroy()
    self._tkWindow= None


  # ***************************************************************************************************************************
  # **** BUCLE PERIODICO
  # ***************************************************************************************************************************

  # ===========================================================================================================================
  # ==== Bucle
  # ===========================================================================================================================

  def _BuclePeriodico(self):
  
    # -------------------------------------------------------------------------------------------------------------------------
    # ---- Rearmar el temporizado cicclico
    # -------------------------------------------------------------------------------------------------------------------------
  
    self._tkWindow.after(self._K_fTmoTempBuclePeriodico_ms, self._BuclePeriodico)

  
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
              
              # ···· Tiene ASDU= 100 (Medidas y cambios de estado) ····························································
              
              if (iASDU == 100) :
                dRta= PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_100(lTramaRcp)
                self._Medidas_ActualizarValor(dRta['Medidas'])
                self._Estados_ActualizarValor(dRta['CambiosED'])
                self._ActualizarDatosEquipo(None, len(dRta['Medidas']), None, None)
                # self._tkWindow.update_idletasks()
            
              # ···· ASDU 103 (Transmisión de estados digitales de control) ···················································

              elif (iASDU == 103) :
                dRta= PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_103(lTramaRcp)
                self._Estados_ActualizarValor(dRta['EstadosDig'])
                self._ActualizarDatosEquipo(None, None, len(dRta['EstadosDig']), None)
                # self._tkWindow.update_idletasks()
            
              # ···· ASDU 5 (Transmisión de estados digitales de control) ·····················································

              elif (iASDU == 5) :
                dRta= PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_5(lTramaRcp)
                self._ActualizarDatosEquipo(dRta['TxtIdEquipo'], None, None, dRta['VersProcome'])
                # self._tkWindow.update_idletasks()

              # ···· ASDU 121 (Confirmación de orden) ··········································································

              elif (iASDU == 121) :
                dRta= PROCOME_AnalizarTramaRcp.InterpretarPaquetesSecundario_ASDU_121(lTramaRcp)
                self._Ordenes_MostrarMensaje('Respuesta a Peticion de orden S' + str(dRta['NrOden'] + 1) + ' a ' + dRta['TipoOperacion'] + ': ' + dRta['ResultadoOper'])
                # self._tkWindow.update_idletasks()

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
        self._tkbArrancParar['bg']= self._sColorNoComunica
        self._tkbArrancParar['text']= 'Arrancar la comunicación'

    return

# #############################################################################################################################
