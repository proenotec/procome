# -*- coding: utf-8 -*-

# #############################################################################################################################
# #############################################################################################################################
# ####
# #### PROTOCOLO PROCOME: Clase "PROCOME_MaqEstados"
# ####
# #############################################################################################################################
# #############################################################################################################################

# #############################################################################################################################
# #### Dependencias
# #############################################################################################################################

import PROCOME_General
import PROCOME_ConstruirTramaTrm
import PROCOME_AnalizarTramaRcp
# import serial

# #############################################################################################################################
# #### Clase PROCOME_MaqEstados
# #############################################################################################################################

class PROCOME_MaqEstados:

  # ***************************************************************************************************************************
  # **** Constructor
  # ***************************************************************************************************************************

  def __init__(self, iDireccion, dTemporizados, oConstrTramaRcp, oCanalSerie, oFormPpal, iMostrarMensajesDebug):

    # **** Constantes *********************************************************************************************************

    self._K_iNrMaxIntentos= 3
    self._K_fTmoRcp_Std_seg= 1.0
    self._K_fTmoSincrPeriodica_seg=     15.0 # % 10.0 * 60
    self._K_fTmoPetGralPeriodica_seg=   2.0 # % 5.0
    self._K_fTmoPetEstDigPeriodica_seg= 5.0 # % 15.0


    self._tEventos= ('Procesado', 'ProcesarDeNuevo', 'RecibidaTramaValida', 'RecibidaTramaErronea', \
                     'Arrancar', 'Parar', 'RecibidaTrama', \
                     'TimeoutRcp',  'TimeoutEspera', 'TimeoutPetGral', 'TimeoutPetEstDig', 'TimeoutSincr', 'PetOrden'\
                    ) 

    self._tSuperEstados=  ('Enlace', 'Inicializacion', 'Bucle', 'Control')
    self._tEstadosEnlace= ('Reposo', 'SinComunicacion', 'RstLinRemota', 'VaciarBufferClase1')
    self._tEstadosInicializacion= ('Sincronizacion', 'PeticionEstadosDig', 'PeticionMedidas', 'PeticionClase1')
    self._tEstadosBucle= ('Entrada', 'TiempoLibre', 'PeticionMedidas', 'PeticionEstadosDig', 'Sincronizacion', 'PeticionClase1', 'PeticionOrden')
    self._tEstadosControl=   ('Parar')


    # **** Variables **********************************************************************************************************

    self._lTramaTrm= None
    self._lTramaRcp= None

    self._lEstado= ['Enlace', 'Reposo']
    self._sEstadoCom= 'Reposo'
    self._lEstado_Ret= None
    self._sEstCom_Ret= None

    self._EnvioSincrPeriodica= False
    self._PetGralPeriodica= False
    self._PetEstDigPeriodica= False
    
    self._iIntentosTrmQuedan= 0
    self._bHayTransmision= False


    # **** Inicializaciones. Comprobaciones ***********************************************************************************

    self._bVerMensDbg_Evento=      ((iMostrarMensajesDebug & 0x01) != 0)
    self._bVerMensDbg_Estado=      ((iMostrarMensajesDebug & 0x02) != 0)
    self._bVerMensDbg_TipoMensTrm= ((iMostrarMensajesDebug & 0x04) != 0)
    self._bVerMensDbg_MensajeTrm=  ((iMostrarMensajesDebug & 0x08) != 0)
    self._bVerMensDbg_TipoMensRcp= ((iMostrarMensajesDebug & 0x10) != 0)
    self._bVerMensDbg_MensajeRcp=  ((iMostrarMensajesDebug & 0x20) != 0)
    #
    self._bVerMensDbg_DEBUG     =  ((iMostrarMensajesDebug & 0x80) != 0)

    self._iDir= iDireccion if (PROCOME_General.PROCOME_DIR_MIN <= iDireccion <= PROCOME_General.PROCOME_DIR_MAX) else PROCOME_General.PROCOME_DIR_MAX

    self._dTemp= dTemporizados
    self._dTemp['TmpRcp_seg']= 0.0
    self._dTemp['TmpEspera_seg']= 0.0
    self._dTemp['TmpSincr_seg']= 0.0
    self._dTemp['TmpPetGral_seg']= 0.0
    self._dTemp['TmpPetEstDig_seg']= 0.0
    
    self._oConstrTramaRcp= oConstrTramaRcp
    self._oCanalSerie= oCanalSerie
    self._oFormPpal= oFormPpal
    
    
    # **** Fin ****************************************************************************************************************

    return

  # **** Constructor (Fin) ****************************************************************************************************


  # ***************************************************************************************************************************
  # **** ProcesarEventos
  # ***************************************************************************************************************************
  #
  # Devuelve:
  # - Un texto nulo: Si es una salida sin error y sin nada particular que informar
  # - Un texto con la descripcin de un error
  
  def ProcesarEventos(self, sEvento, xDato= None):

    if (self._bVerMensDbg_Evento or self._bVerMensDbg_Estado) : 
      print('====================================================================================================') 
      sTexto=''
      if (self._bVerMensDbg_Evento) : sTexto+= 'Evento= <' + sEvento + '>'
      if (self._bVerMensDbg_Evento and self._bVerMensDbg_Estado) : sTexto+= '.'
      if (self._bVerMensDbg_Estado) : sTexto+= 'Estado= ' + self._lEstado[0] + '.' + self._lEstado[1] + ' / ' + self._sEstadoCom
      print('  << ProcesarEventos.Entrada >>  ' + sTexto)
 

    # =========================================================================================================================
    # ==== Inicializaciones. Comprobaciones iniciales
    # =========================================================================================================================

    self._bHayTransmision= False
    
    # **** Comprobar si sEvento es uno de los esperados ***********************************************************************
    
    if (sEvento not in self._tEventos[4:]) : return 'ERROR DE SOFTWARE: No existe el Evento <' + sEvento + '>' 

    if (sEvento == 'Arrancar') and (self._lEstado != ['Enlace', 'Reposo']) :
      sRta= 'ERROR DE SOFTWARE: Se ha recibido un evento de "Arrancar" en un Estado que no es "Reposo". Estado= <' + self._sEstado[0] + '.' + self._sEstado[1] + '>'
      self._CancelarLaComunicacion()
      return sRta

    # **** Comprobar si el Evento es "Parar" **********************************************************************************

    if (sEvento == 'Parar') :
      self._lEstado= ['Control', 'Parar']


    # **** Comprobar y preprocesar la trama recibida **************************************************************************
    
    elif (sEvento == 'RecibidaTrama') :
      if (type(xDato) is not list) :
        self._CancelarLaComunicacion()
        return 'ERROR DE SOFTWARE: Se ha recibido un evento de "RecibidaTrama" pero en "xDato" no viene una trama. Tipo de "xDato": ' + type(xDato)
      #
      self._lTramaRcp= xDato
      dTrama= PROCOME_AnalizarTramaRcp.AnalizarTrama(self._lTramaRcp)
      sEvento= 'RecibidaTramaValida' if (dTrama['TramaValida']) else 'RecibidaTramaErronea'
    
    else :
      self._lTramaRcp= None
      dTrama= None

    if (self._bVerMensDbg_Evento or self._bVerMensDbg_Estado) : sEventoBackup= sEvento


    # =========================================================================================================================
    # ==== Procesar en funcin del estado actual
    # =========================================================================================================================

    while(sEvento != 'Procesado') :

      if (self._bVerMensDbg_Evento or self._bVerMensDbg_Estado) : 
        if (sEvento != sEventoBackup) :
          sTexto=''
          if (self._bVerMensDbg_Evento) : sTexto+= 'Evento= <' + sEvento + '>'
          if (self._bVerMensDbg_Evento and self._bVerMensDbg_Estado) : sTexto+= '.'
          if (self._bVerMensDbg_Estado) : sTexto+= 'Estado= ' + self._lEstado[0] + '.' + self._lEstado[1] + ' / ' + self._sEstadoCom
          print('  << ProcesarEventos.Bucle >>    ' + sTexto)

      sSuperEstado= self._lEstado[0]
      sEstado= self._lEstado[1]

      if (sSuperEstado not in self._tSuperEstados) : 
        self._CancelarLaComunicacion()
        return 'ERROR DE SOFTWARE: El SuperEstado <' + sSuperEstado + '> no existe'


      # -----------------------------------------------------------------------------------------------------------------------
      # ---- SuperEstado: 'Enlace'
      # -----------------------------------------------------------------------------------------------------------------------

      if (sSuperEstado == 'Enlace') :
      
        if (sEstado not in self._tEstadosEnlace) : 
          self._CancelarLaComunicacion()
          return 'ERROR DE SOFTWARE: El Estado <' + self._lEstado[0] + '.' + self._lEstado[1] + '> no existe o aÃÂºn no tiene programa asociado'
  
  
        # 
        #  Estado= Enlace.Reposo
        # 

        if (sEstado == 'Reposo') :

          # **** Evento: 'Arrancar' *******************************************************************************************

          if (sEvento == 'Arrancar') :
            if (self._oCanalSerie.is_open) :
              self._CancelarLaComunicacion()
              return 'ERROR DE SOFTWARE: Al intentar abrir el canal serie <'  + sNombreCanalserie + '>, ya estÃÂ¡ abierto por este programa'
            else :
              try :
                self._oCanalSerie.open()
              except :
                self._CancelarLaComunicacion()
                return 'ERROR: Al intentar abrir el canal serie <'  + self._oCanalSerie.port + '>. Puede ser que ese canal serie no exista o que est ocupado'
                #
            self._oConstrTramaRcp.Reset()           # Borrar lo que haya en el buffer de las tramas de recepcion
            self._oCanalSerie.reset_input_buffer()  # Borrar lo que haya en el buffer de recepcion
            self._oCanalSerie.reset_output_buffer() # Borrar lo que haya en el buffer de transmisin
            self._oCanalSerie.rts= False            # Desactivar la seal RTS para no permitir la transmisin por el RS485

            # ==== Cancelar cualquier Timeout en marcha =======================================================================
            #
            # No debera ser necesario
            
            self._dTemp['TmpRcp_seg']= 0
            self._dTemp['TmpEspera_seg']= 0
            self._dTemp['TmpSincr_seg']= 0
            self._dTemp['TmpPetGral_seg']= 0
            self._dTemp['TmpPetEstDig_seg']= 0
            
            # ==== Llevar las variables a su estado de arranque ===============================================================
            
            self._EnvioSincrPeriodica= False
            self._PetGralPeriodica= False
            self._PetEstDigPeriodica= False
            
            # ==== Arrancar el estado siguiente ===============================================================================
            
            self._lEstado= ['Enlace', 'RstLinRemota']
            self._sEstadoCom= 'PrepTrm'
            sEvento= 'ProcesarDeNuevo'


        # 
        #  Estado= Enlace.RstLinRemota
        # 

        elif (sEstado == 'RstLinRemota') :
    
          # **** Estado de la comunicación= Preparando la transmisin *********************************************************

          if (self._sEstadoCom == 'PrepTrm') :
            self._lTramaTrm= PROCOME_ConstruirTramaTrm.ConstruirMensaje_ResetLineaRemota(self._iDir)
            self._iIntentosTrmQuedan= self._K_iNrMaxIntentos
            self._sEstadoCom= 'Trm'
            sEvento= 'ProcesarDeNuevo'
                       
          # **** Estado de la comunicación= Transmitir el mensaje *************************************************************

          elif (self._sEstadoCom == 'Trm') :
            self._oConstrTramaRcp.Reset()           # Borrar lo que haya en el buffer de las tramas de recepcion
            self._oCanalSerie.reset_input_buffer()  # Borrar lo que haya en el buffer de recepcion
            self._dTemp['TmpRcp_seg']= self._K_fTmoRcp_Std_seg
            self._TransmitirTrama()
            if (self._bVerMensDbg_TipoMensTrm) : print(self._lEstado[0] + ': Transmitido un mensaje de "Reset de linea remota"')
            if (self._bVerMensDbg_MensajeTrm)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaTrm)
            self._sEstadoCom= 'EspRcp'
            sEvento= 'Procesado'

          # **** Estado de la comunicación= Esperando mensaje de recepcin *****************************************************

          elif (self._sEstadoCom == 'EspRcp') :
        
            # ==== Evento= Recibida trama vlida ===============================================================================
          
            if (sEvento == 'RecibidaTramaValida') :
              iFuncion= dTrama['Funcion']
              bBitACD= dTrama['BitFcbAcd']
            
              if (iFuncion == PROCOME_General.PROCOME_CONFIRM_NACK) :
                self._dTemp['TmpRcp_seg']= 0
                if (self._bVerMensDbg_TipoMensRcp) : print('Recibido un NACK (CONFIRM)"')
                if (self._bVerMensDbg_MensajeRcp)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaRcp)
                self._lEstado= ['Enlace', 'SinComunicacion']
                self._sEstadoCom= 'Reposo'
                self._dTemp['TmpEspera_seg']= 3.0
                sEvento= 'Procesado'

              elif (iFuncion == PROCOME_General.PROCOME_CONFIRM_ACK) :
                self._dTemp['TmpRcp_seg']= 0
                self._bBitFCB= False
                if (bBitACD) : 
                  if (self._bVerMensDbg_TipoMensRcp) : print('Recibido un ACK (CONFIRM) con ACD= 1')
                  if (self._bVerMensDbg_MensajeRcp)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaRcp)
                  self._lEstado= ['Enlace', 'VaciarBufferClase1']
                else : 
                  if (self._bVerMensDbg_TipoMensRcp) : print('Recibido un ACK (CONFIRM) con ACD= 0')
                  if (self._bVerMensDbg_MensajeRcp)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaRcp)
                  self._lEstado= ['Inicializacion', 'Sincronizacion']
                #  
                self._sEstadoCom= 'PrepTrm'
                sEvento= 'ProcesarDeNuevo'
              
              else :  
                self._RecibidoMensajeNoEsperado(self._lEstado, self._lTramaRcp)
                sEvento= 'Procesado'

            # ==== Evento= Recibida trama erronea =============================================================================
          
            elif (sEvento == 'RecibidaTramaErronea') :
              sEvento= 'Procesado'                    # De momento no hacer nada, esperar al Timeout
          
            # ==== Evento= Timeout de recepcin ===============================================================================
          
            elif (sEvento == 'TimeoutRcp') :
              sEvento= self._Reintentar()


        # 
        #  Estado= Enlace.SinComunicacion
        # 

        elif (sEstado == 'SinComunicacion') :

          # **** Evento: 'TimeoutEspera' **************************************************************************************

          if (sEvento == 'TimeoutEspera') :
            self._lEstado= ['Enlace', 'RstLinRemota']
            self._sEstadoCom= 'PrepTrm'
            sEvento= 'ProcesarDeNuevo'


        # 
        #  Estado= Enlace.VaciarBufferClase1
        # 

        elif (sEstado == 'VaciarBufferClase1') :
        
          dAux= {'Estado' : ['Inicializacion', 'Sincronizacion'], 'EstadoCom'  : 'PrepTrm'}
          sEvento= self._ProcesarEstado_PeticionClase1(sEvento, dTrama, dAux)


        # 
        #  Estado: No vlido
        # 

        else :  
          self._CancelarLaComunicacion()
          return 'ERROR DE SOFTWARE: El Estado <' + self._lEstado[0] + '.' + self._lEstado[1] + '> no existe o aÃÂºn no tiene programa asociado'


      # -----------------------------------------------------------------------------------------------------------------------
      # ---- SuperEstado: 'Inicializacion'
      # -----------------------------------------------------------------------------------------------------------------------

      elif (sSuperEstado == 'Inicializacion') :

        if (sEstado not in self._tEstadosInicializacion) : 
          self._CancelarLaComunicacion()
          return 'ERROR DE SOFTWARE: El Estado <' + self._lEstado[0] + '.' + self._lEstado[1] + '> no existe o aÃÂºn no tiene programa asociado'


        # 
        #  Estado= Inicializacion.Sincronizacion
        # 

        if (sEstado == 'Sincronizacion') :
          sEvento= self._ProcesarEstado_Sincronizacion(sEvento, ['Inicializacion', 'PeticionEstadosDig'], 'PrepTrm')


        # 
        #  Estado= Inicializacion.PeticionEstadosDig
        # 

        elif (sEstado == 'PeticionEstadosDig') :
        
          dAux= {'ACD1' : {'Estado'     : ['Inicializacion', 'PeticionClase1'], \
                           'Estado_Ret' : ['Inicializacion', 'PeticionMedidas'], \
                           'EstadoCom'  : 'PrepTrm', \
                           'EstCom_Ret' : 'PrepTrm'}, \
                 'ACD0' : {'Estado'     : ['Inicializacion', 'PeticionMedidas'], \
                           'Estado_Ret' : None, \
                           'EstadoCom'  : 'PrepTrm', \
                           'EstCom_Ret' : 'PrepTrm'} \
                }
          sEvento= self._ProcesarEstado_PeticionEstadosDig(sEvento, dTrama, dAux)


        # 
        #  Estado= Inicializacion.PeticionMedidas
        # 

        elif (sEstado == 'PeticionMedidas') :
        
          dAux= {'ACD1' : {'Estado'     : ['Inicializacion', 'PeticionClase1'], \
                           'Estado_Ret' : ['Bucle', 'Entrada'], \
                           'EstadoCom'  : 'PrepTrm', \
                           'EstCom_Ret' : 'Reposo'}, \
                 'ACD0' : {'Estado'     : ['Bucle', 'Entrada'], \
                           'Estado_Ret' : None, \
                           'EstadoCom'  : 'Reposo', \
                           'EstCom_Ret' : 'Reposo'} \
                }
          sEvento= self._ProcesarEstado_PeticionMedidas(sEvento, dTrama, dAux)


        # 
        #  Estado= Inicializacion.PeticionClase1
        # 

        elif (sEstado == 'PeticionClase1') :

          dAux= {'Estado' : self._lEstado_Ret, 'EstadoCom' : self._sEstCom_Ret}
          sEvento= self._ProcesarEstado_PeticionClase1(sEvento, dTrama, dAux)


        # 
        #  Estado: No vlido
        # 

        else :  
          self._CancelarLaComunicacion()
          return 'ERROR DE SOFTWARE: El Estado <' + self._lEstado[0] + '.' + self._lEstado[1] + '> no existe o aÃÂºn no tiene programa asociado'


      # -----------------------------------------------------------------------------------------------------------------------
      # ---- SuperEstado: 'Bucle'
      # -----------------------------------------------------------------------------------------------------------------------

      elif (sSuperEstado == 'Bucle') :
      
        if (sEstado not in self._tEstadosBucle) : 
          self._CancelarLaComunicacion()
          return 'ERROR DE SOFTWARE: El Estado <' + self._lEstado[0] + '.' + self._lEstado[1] + '> no existe o aÃÂºn no tiene programa asociado'


        # 
        #  Comprobar si hace falta memorizar alguna de las peticiones
        # 

        if (sEstado != 'TiempoLibre') :

          if (sEvento == 'PetOrden') :
            self._ArrancarPetOrden= True
            self._DatosOrden= xDato
            sEvento= 'Procesado'

          elif (sEvento == 'TimeoutPetGral') :
            self._ArrancarPetGral= True
            self._dTemp['TmpPetGral_seg']= self._K_fTmoPetGralPeriodica_seg
            sEvento= 'Procesado'
            
          elif (sEvento == 'TimeoutPetEstDig') :
            self._ArrancarPetEstDig= True
            self._dTemp['TmpPetEstDig_seg']= self._K_fTmoPetEstDigPeriodica_seg
            sEvento= 'Procesado'
            
          elif (sEvento == 'TimeoutSincrPer') :
            print(self._dTemp)
            self._ArrancarEnvioSincr= True
            self._dTemp['TmpSincr_seg']= self._K_fTmoSincrPeriodica_seg
            sEvento= 'Procesado'


        # 
        #  Estado= Bucle.Entrada
        # 

        if (sEstado == 'Entrada') :
           
          # ==== Cancelar cualquier Timeout en marcha =======================================================================
            
          self._dTemp['TmpRcp_seg']= 0
          self._dTemp['TmpEspera_seg']= 0
          self._dTemp['TmpSincr_seg']= 0
          self._dTemp['TmpPetGral_seg']= 0
          self._dTemp['TmpPetEstDig_seg']= 0
            
          # ==== Llevar las variables a su estado de arranque ===============================================================
            
          self._ArrancarEnvioSincr= False
          self._ArrancarPetGral= False
          self._ArrancarPetEstDig= False
          self._ArrancarPetOrden= False
          self._DatosOrden= None
            
          # ==== Arrancar temporizaciones de peticiones periodicas ==========================================================
            
          self._dTemp['TmpSincr_seg']= self._K_fTmoSincrPeriodica_seg
          self._dTemp['TmpPetGral_seg']= self._K_fTmoPetGralPeriodica_seg
          self._dTemp['TmpPetEstDig_seg']= self._K_fTmoPetEstDigPeriodica_seg

          # ==== Arrancar el estado siguiente ===============================================================================
            
          self._lEstado= ['Bucle', 'TiempoLibre'] ; self._sEstadoCom= 'Reposo'
          sEvento= 'ProcesarDeNuevo'


        # 
        #  Estado= Bucle.TiempoLibre
        # 
        
        elif (sEstado == 'TiempoLibre') :

          if ((sEvento == 'PetOrden') or self._ArrancarPetOrden) :
            self._ArrancarPetOrden= False
            if (sEvento == 'PetOrden') : self._DatosOrden= xDato
            self._lEstado= ['Bucle', 'PeticionOrden']
            self._sEstadoCom= 'PrepTrm'
            sEvento= 'ProcesarDeNuevo'

          elif ((sEvento == 'TimeoutPetGral') or self._ArrancarPetGral) :
            self._ArrancarPetGral= False
            self._dTemp['TmpPetGral_seg']= self._K_fTmoPetGralPeriodica_seg
            self._lEstado= ['Bucle', 'PeticionMedidas']
            self._sEstadoCom= 'PrepTrm'
            sEvento= 'ProcesarDeNuevo'
            
          elif ((sEvento == 'TimeoutPetEstDig') or self._ArrancarPetEstDig):
            self._ArrancarPetEstDig= False
            self._dTemp['TmpPetEstDig_seg']= self._K_fTmoPetEstDigPeriodica_seg
            self._lEstado= ['Bucle', 'PeticionEstadosDig']
            self._sEstadoCom= 'PrepTrm'
            sEvento= 'ProcesarDeNuevo'
            
          elif ((sEvento == 'TimeoutSincr') or self._ArrancarEnvioSincr) :
            self._ArrancarEnvioSincr= False
            self._dTemp['TmpSincr_seg']= self._K_fTmoSincrPeriodica_seg
            self._lEstado= ['Bucle', 'Sincronizacion']
            self._sEstadoCom= 'PrepTrm'
            sEvento= 'ProcesarDeNuevo'
            
          else : 
            sEvento= 'Procesado'


        # 
        #  Estado= Bucle.PeticionMedidas
        # 

        elif (sEstado == 'PeticionMedidas') :
        
          dAux= {'ACD1' : {'Estado'     : ['Bucle', 'PeticionClase1'], \
                           'EstadoCom'  : 'PrepTrm', \
                           'Estado_Ret' : ['Bucle', 'TiempoLibre'], \
                           'EstCom_Ret' : 'Reposo'}, \
                 'ACD0' : {'Estado'     : ['Bucle', 'TiempoLibre'], \
                           'EstadoCom'  : 'Reposo',  \
                           'Estado_Ret' : None,      \
                           'EstCom_Ret' : None}     \
                }
          sEvento= self._ProcesarEstado_PeticionMedidas(sEvento, dTrama, dAux)
          self._dTemp['TmpPetGral_seg']= self._K_fTmoPetGralPeriodica_seg


        # 
        #  Estado= Bucle.PeticionClase1
        # 

        elif (sEstado == 'PeticionClase1') :

          dAux= {'Estado' : self._lEstado_Ret, 'EstadoCom' : self._sEstCom_Ret}
          sEvento= self._ProcesarEstado_PeticionClase1(sEvento, dTrama, dAux)


        # 
        #  Estado= Bucle.PeticionEstadosDig
        # 

        elif (sEstado == 'PeticionEstadosDig') :

          dAux= {'ACD1' : {'Estado'     : ['Bucle', 'PeticionClase1'], \
                           'EstadoCom'  : 'PrepTrm', \
                           'Estado_Ret' : ['Bucle', 'TiempoLibre'], \
                           'EstCom_Ret' : 'Reposo'}, \
                 'ACD0' : {'Estado'     : ['Bucle', 'TiempoLibre'], \
                           'EstadoCom'  : 'Reposo', \
                           'Estado_Ret' : None, \
                           'EstCom_Ret' : None} \
                }
          sEvento= self._ProcesarEstado_PeticionEstadosDig(sEvento, dTrama, dAux)
          self._dTemp['TmpPetEstDig_seg']= self._K_fTmoPetEstDigPeriodica_seg


        # 
        #  Estado= Bucle.Sincronizacion
        # 

        elif (sEstado == 'Sincronizacion') :
               
          sEvento= self._ProcesarEstado_Sincronizacion(sEvento, ['Bucle', 'TiempoLibre'], 'Reposo')
          self._dTemp['TmpSincr_seg']= self._K_fTmoSincrPeriodica_seg



        # 
        #  Estado= Bucle.PeticionOrden
        # 

        elif (sEstado == 'PeticionOrden') :

          # **** Estado de la comunicación= Preparando la transmisin *********************************************************

          if (self._sEstadoCom == 'PrepTrm') :
            self._lTramaTrm= PROCOME_ConstruirTramaTrm.ConstruirMensaje_PetOrden(self._iDir, self._bBitFCB, self._DatosOrden[0], self._DatosOrden[1])
            self._iIntentosTrmQuedan= self._K_iNrMaxIntentos
            self._sEstadoCom= 'Trm'
            sEvento= 'ProcesarDeNuevo'

          # **** Estado de la comunicación= Transmitir el mensaje *************************************************************

          elif (self._sEstadoCom == 'Trm') :
            self._oConstrTramaRcp.Reset()           # Borrar lo que haya en el buffer de las tramas de recepcion
            self._oCanalSerie.reset_input_buffer()  # Borrar lo que haya en el buffer de recepcion
            self._dTemp['TmpRcp_seg']= self._K_fTmoRcp_Std_seg
            self._TransmitirTrama()
            sTxtAux= 'Enviada orden: Orden S' + str(self._DatosOrden[0] + 1) + ', operaciÃÂ³n ' + self._DatosOrden[1]
            self._oFormPpal._Ordenes_MostrarMensaje(sTxtAux)
            #
            if (self._bVerMensDbg_TipoMensTrm) :
              sTexto= self._lEstado[0] + ': Transmitido un mensaje de "PeticiÃÂ³n de orden" para dar una orden de '
              if (self._lTramaTrm[-3] == 1) :
                sTexto+= 'Abrir'
              else : 
                sTexto+= 'Cerrar'
              print(sTexto + ' al relÃÂ© con NrOrden ' + str(self._lTramaTrm[-5]))
            if (self._bVerMensDbg_MensajeTrm)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaTrm)
            self._sEstadoCom= 'EspRcp'
            sEvento= 'Procesado'

          # **** Estado de la comunicación= Esperando mensaje de recepcin *****************************************************

          elif (self._sEstadoCom == 'EspRcp') :
        
            # ==== Evento= Recibida trama vlida ===============================================================================
          
            if (sEvento == 'RecibidaTramaValida') :
              iFuncion= dTrama['Funcion']
              bBitACD= dTrama['BitFcbAcd']

              if (iFuncion in (PROCOME_General.PROCOME_CONFIRM_ACK, PROCOME_General.PROCOME_CONFIRM_NACK)) :
                self._dTemp['TmpRcp_seg']= 0
                self._bBitFCB= not self._bBitFCB
                #
                if (self._bVerMensDbg_TipoMensRcp) : 
                  sTxtAux= 'Recibido un "'
                  if (iFuncion == PROCOME_General.PROCOME_CONFIRM_ACK) :
                    sTxtAux+= 'ACK'
                  else :
                    sTxtAux+= 'NACK'
                  sTxtAux+= ' (CONFIRM)" con ACD= '
                  if (bBitACD) :
                    sTxtAux+= '1'
                  else :
                    sTxtAux+= '0'
                  print(sTxtAux)                 
                if (self._bVerMensDbg_MensajeRcp)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaRcp)
                #
                self._lEstado= ['Bucle', 'TiempoLibre']
                self._sEstadoCom= 'Reposo'

                sEvento= 'Procesado'
                # dAux= {'Estado' : ['Bucle', 'TiempoLibre'], 'EstadoCom'  : 'Reposo'}
                # sEvento= self._ProcesarEstado_PeticionClase1(sEvento, dTrama, dAux)
                

              else :
                self._RecibidoMensajeNoEsperado(self._lEstado, self._lTramaRcp)
                sEvento= 'Procesado'

            # ==== Evento= Recibida trama erronea =============================================================================
          
            elif (sEvento == 'RecibidaTramaErronea') :
              sEvento= 'Procesado'                    # De momento no hacer nada, esperar al Timeout
          
            # ==== Evento= Timeout de recepcin ===============================================================================
          
            elif (sEvento == 'TimeoutRcp') :
              sEvento= self._Reintentar()


        # 
        #  Estado: No vlido
        # 

        else :  
          self._CancelarLaComunicacion()
          return 'ERROR DE SOFTWARE: El Estado <' + self._lEstado[0] + '.' + self._lEstado[1] + '> no existe o aÃÂºn no tiene programa asociado'


      # -----------------------------------------------------------------------------------------------------------------------
      # ---- SuperEstado: 'Control'
      # -----------------------------------------------------------------------------------------------------------------------

      elif (sSuperEstado == 'Control') :
        if (sEstado not in self._tEstadosControl) : 
          self._CancelarLaComunicacion()
          return 'ERROR DE SOFTWARE: El Estado <' + self._lEstado[0] + '.' + self._lEstado[1] + '> no existe o aÃÂºn no tiene programa asociado'

        if (sEstado == 'Parar') :
          self._CancelarLaComunicacion()
          self._lEstado= ['Enlace', 'Reposo']
          self._dTemp['TmpRcp_seg']= 0
          self._dTemp['TmpEspera_seg']= 0
          self._dTemp['TmpSincr_seg']= 0
          self._dTemp['TmpPetGral_seg']= 0
          self._dTemp['TmpPetEstDig_seg']= 0
          sEvento= 'Procesado'


        # 
        #  Estado: No vlido
        # 

        else :  
          self._CancelarLaComunicacion()
          return 'ERROR DE SOFTWARE: El Estado <' + self._lEstado[0] + '.' + self._lEstado[1] + '> no existe o aÃÂºn no tiene programa asociado'


      # -----------------------------------------------------------------------------------------------------------------------
      # ---- SuperEstado: No vlido
      # -----------------------------------------------------------------------------------------------------------------------
      
      else :  
        self._CancelarLaComunicacion()
        return 'ERROR DE SOFTWARE: El Estado <' + self._lEstado[0] + '.' + self._lEstado[1] + '> no existe o aÃÂºn no tiene programa asociado'


      # -----------------------------------------------------------------------------------------------------------------------
      # ---- Comprobaciones al final de este ciclo
      # -----------------------------------------------------------------------------------------------------------------------

      if (sEvento not in('Procesado', 'ProcesarDeNuevo')) :
        sTexto=  'ERROR DE SOFTWARE: Se ha finalizado el programa con un evento pendiente de procesar\n'
        sTexto+= ' - Estado=    <' + self._lEstado[0] + '.' + self._lEstado[1] + '>\n' 
        sTexto+= ' - EstadoCom= <' + self._sEstadoCom + '>\n'
        sTexto+= ' - sEvento=   <' + sEvento + '>'  
        self._CancelarLaComunicacion()
        return sTexto  
                


    # =========================================================================================================================
    # ==== Final de la funcin
    # =========================================================================================================================

    if (self._bVerMensDbg_Evento or self._bVerMensDbg_Estado) : 
      sTexto=''
      if (self._bVerMensDbg_Evento) : sTexto+= 'Evento= <' + sEvento + '>'
      if (self._bVerMensDbg_Evento and self._bVerMensDbg_Estado) : sTexto+= '.'
      if (self._bVerMensDbg_Estado) : sTexto+= 'Estado= ' + self._lEstado[0] + '.' + self._lEstado[1] + ' / ' + self._sEstadoCom
      print('  << ProcesarEventos.Salida >>   ' + sTexto)

    return ''  

  # **** ProcesarEventos (Fin) ************************************************************************************************


  # ***************************************************************************************************************************
  # **** Hacer reintentos de la comunicación 
  # ***************************************************************************************************************************

  def _Reintentar(self):
    self._iIntentosTrmQuedan-= 1
    if (self._iIntentosTrmQuedan > 0) :
      self._sEstadoCom= 'Trm'
      sEvento= 'ProcesarDeNuevo' 
    else :
      self._lEstado= ['Enlace', 'SinComunicacion']
      self._sEstadoCom= 'Reposo'

      # Cancelar cualquier Temporizacin en marcha

      self._dTemp['TmpRcp_seg']= 0
      self._dTemp['TmpEspera_seg']= 0
      self._dTemp['TmpSincr_seg']= 0
      self._dTemp['TmpPetGral_seg']= 0
      self._dTemp['TmpPetEstDig_seg']= 0

      # Cancelar la peticiones periodicas pendientes
      # 
      # self._EnvioSincrPeriodica= False
      # self._PetGralPeriodica= False
      # self._PetEstDigPeriodica= False

      self._dTemp['TmpEspera_seg']= 3.0
      sEvento= 'Procesado'
    return  sEvento


  # ***************************************************************************************************************************
  # **** Finalizar por error critico
  # ***************************************************************************************************************************

  def _CancelarLaComunicacion(self):

    # **** Cancelar temporizados **********************************************************************************************
    
    self._dTemp['TmpRcp_seg']= 0
    self._dTemp['TmpEspera_seg']= 0
    self._dTemp['TmpSincr_seg']= 0
    self._dTemp['TmpPetGral_seg']= 0
    self._dTemp['TmpPetEstDig_seg']= 0

    # **** Cerrar el canal serie **********************************************************************************************
  
    if (self._oCanalSerie.is_open) : self._oCanalSerie.close()
    
    # **** Pasar a estado de reposo *******************************************************************************************

    self._lEstado= ['Enlace', 'Reposo']
    print('  << ProcesarEventos.Abortar por error critico>>')

    return
  
  
  # ***************************************************************************************************************************
  # **** Tratar algunos Errores de Software 
  # ***************************************************************************************************************************


  def _RecibidoMensajeNoEsperado(self, lEstado, lTrama):
    if (self._bVerMensDbg_TipoMensRcp or self._bVerMensDbg_MensRcp) :
      print('Recibido un mensaje no esperado. Se ignora')
      print('- Estado= '  + lEstado[0] + '.' + lEstado[1])
      PROCOME_General.ImprimirTrama_Hex('- Mensaje: ', lTrama)
      return


  # ***************************************************************************************************************************
  # **** Procesar estados comunes
  # ***************************************************************************************************************************
  #
  # Devuelve el evento de salida

  # ===========================================================================================================================
  # ==== Procesar estado: PeticionClase1
  # ===========================================================================================================================
  
  def _ProcesarEstado_PeticionClase1(self, sEvento, dTrama, dCambiosDeEstado):

    # **** Estado de la comunicación= Preparando la transmisin ***************************************************************

    if (self._sEstadoCom == 'PrepTrm') :
      self._lTramaTrm= PROCOME_ConstruirTramaTrm.ConstruirMensaje_PetDatosClase1(self._iDir, self._bBitFCB)
      self._iIntentosTrmQuedan= self._K_iNrMaxIntentos
      self._sEstadoCom= 'Trm'
      return 'ProcesarDeNuevo'

    # **** Estado de la comunicación= Transmitir el mensaje *******************************************************************

    elif (self._sEstadoCom == 'Trm') :
      self._oConstrTramaRcp.Reset()           # Borrar lo que haya en el buffer de las tramas de recepcion
      self._oCanalSerie.reset_input_buffer()  # Borrar lo que haya en el buffer de recepcion
      self._dTemp['TmpRcp_seg']= self._K_fTmoRcp_Std_seg
      self._TransmitirTrama()
      if (self._bVerMensDbg_TipoMensTrm) : print(self._lEstado[0] + ': Transmitido un mensaje de "Peticion de datos de clase 1"')
      if (self._bVerMensDbg_MensajeTrm)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaTrm)
      self._sEstadoCom= 'EspRcp'
      return 'Procesado'

    # **** Estado de la comunicación= Esperando mensaje de recepcin ****************************************************

    elif (self._sEstadoCom == 'EspRcp') :

      # ==== Evento= Recibida trama vlida ===============================================================================
          
      if (sEvento == 'RecibidaTramaValida') :
        iFuncion= dTrama['Funcion']
        bBitACD= dTrama['BitFcbAcd']

        if (iFuncion in (PROCOME_General.PROCOME_RESPOND_DATOSUSUARIO, PROCOME_General.PROCOME_RESPOND_NACK)) :
          self._dTemp['TmpRcp_seg']= 0
          self._bBitFCB= not self._bBitFCB
          #
          if (self._bVerMensDbg_TipoMensRcp) :
            sTexto= 'Recibido un mensaje con ' 
            if (iFuncion == PROCOME_General.PROCOME_RESPOND_DATOSUSUARIO) :
              sTexto+= 'Datos de usuario (RESPOND),'
            else :
              sTexto+= 'NACK (RESPOND),'
            sTexto+= ' con ACD= '
            sTexto+= '1' if (bBitACD) else '0'
            print(sTexto)
          if (self._bVerMensDbg_MensajeRcp) : PROCOME_General.ImprimirTrama_Hex('Mensaje: ', self._lTramaRcp)
          #
          if (bBitACD) :
            self._sEstadoCom= 'PrepTrm'
            return 'ProcesarDeNuevo'
          else :
            self._lEstado=    dCambiosDeEstado['Estado']
            self._sEstadoCom= dCambiosDeEstado['EstadoCom']
            return 'ProcesarDeNuevo'
          
        else :  
          self._RecibidoMensajeNoEsperado(self._lEstado, self._lTramaRcp)
          return 'Procesado'

      # ==== Evento= Recibida trama erronea =============================================================================
          
      elif (sEvento == 'RecibidaTramaErronea') :
        return 'Procesado'                    # De momento no hacer nada, esperar al Timeout
          
      # ==== Evento= Timeout de recepcin ===============================================================================
          
      elif (sEvento == 'TimeoutRcp') :
        return self._Reintentar()

    # **** Resto de casos *****************************************************************************************************
    
    return sEvento


  # =========================================================================================================================
  # ==== Procesar estado: PeticionMedidas
  # =========================================================================================================================
  
  def _ProcesarEstado_PeticionMedidas(self, sEvento, dTrama, dCambiosDeEstado):
      
    # **** Estado de la comunicación= Preparando la transmisin ***************************************************************

    if (self._sEstadoCom == 'PrepTrm') :
      self._lTramaTrm= PROCOME_ConstruirTramaTrm.ConstruirMensaje_PetDatosCtrl(self._iDir, self._bBitFCB)
      self._iIntentosTrmQuedan= self._K_iNrMaxIntentos
      self._sEstadoCom= 'Trm'
      return 'ProcesarDeNuevo'

    # **** Estado de la comunicación= Transmitir el mensaje *******************************************************************

    elif (self._sEstadoCom == 'Trm') :
      self._oConstrTramaRcp.Reset()           # Borrar lo que haya en el buffer de las tramas de recepcion
      self._oCanalSerie.reset_input_buffer()  # Borrar lo que haya en el buffer de recepcion
      self._dTemp['TmpRcp_seg']= self._K_fTmoRcp_Std_seg
      self._TransmitirTrama()
      if (self._bVerMensDbg_TipoMensTrm) : print(self._lEstado[0] + ': Transmitido un mensaje de "Peticion de datos de control (medidas)"')
      if (self._bVerMensDbg_MensajeTrm)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaTrm)
      self._sEstadoCom= 'EspRcp'
      return 'Procesado'

    # **** Estado de la comunicación= Esperando mensaje de recepcin **********************************************************

    elif (self._sEstadoCom == 'EspRcp') :

      # ==== Evento= Recibida trama vlida ======================================================================================
          
      if (sEvento == 'RecibidaTramaValida') :
        iFuncion= dTrama['Funcion']
        iTYP= dTrama['TYP']
        bBitACD= dTrama['BitFcbAcd']

        if ((iFuncion == PROCOME_General.PROCOME_RESPOND_DATOSUSUARIO) and (dTrama['TYP'] == 100)) :
          self._dTemp['TmpRcp_seg']= 0
          self._bBitFCB= not self._bBitFCB
          #
          if (self._bVerMensDbg_TipoMensRcp) : 
            sTexto= 'Recibido un mensaje de "TransmisiÃÂ³n de medidas y cambios digitales de control" con ACD= '
            sTexto+= '1' if (bBitACD) else '0'
            print(sTexto)
          if (self._bVerMensDbg_MensajeRcp)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaRcp)
          #
          if (bBitACD) :
            self._lEstado=     dCambiosDeEstado['ACD1']['Estado']
            self._sEstadoCom=  dCambiosDeEstado['ACD1']['EstadoCom']
            self._lEstado_Ret= dCambiosDeEstado['ACD1']['Estado_Ret']
            self._sEstCom_Ret= dCambiosDeEstado['ACD1']['EstCom_Ret']
            return 'ProcesarDeNuevo'
          else :
            self._lEstado=     dCambiosDeEstado['ACD0']['Estado']
            self._sEstadoCom=  dCambiosDeEstado['ACD0']['EstadoCom']
            self._lEstado_Ret= None
            self._sEstCom_Ret= None
            return 'ProcesarDeNuevo'
            
        else :  
          self._RecibidoMensajeNoEsperado(self._lEstado, self._lTramaRcp)
          return 'Procesado'

      # ==== Evento= Recibida trama erronea =====================================================================================
          
      elif (sEvento == 'RecibidaTramaErronea') :
        return 'Procesado'                         # De momento no hacer nada, esperar al Timeout
          
      # ==== Evento= Timeout de recepcin =======================================================================================
          
      elif (sEvento == 'TimeoutRcp') :
        return self._Reintentar()

    # **** Resto de casos *****************************************************************************************************
    
    return sEvento


  # ===========================================================================================================================
  # ==== Procesar estado: PeticionEstadosDig
  # ===========================================================================================================================
  
  def _ProcesarEstado_PeticionEstadosDig(self, sEvento, dTrama, dCambiosDeEstado):

    # **** Estado de la comunicación= Preparando la transmisin ***************************************************************

    if (self._sEstadoCom == 'PrepTrm') :
      self._lTramaTrm= PROCOME_ConstruirTramaTrm.ConstruirMensaje_PetEstadosDigCtrl(self._iDir, self._bBitFCB)
      self._iIntentosTrmQuedan= self._K_iNrMaxIntentos
      self._sEstadoCom= 'Trm'
      return 'ProcesarDeNuevo'

    # **** Estado de la comunicación= Transmitir el mensaje *******************************************************************

    elif (self._sEstadoCom == 'Trm') :
      self._oConstrTramaRcp.Reset()           # Borrar lo que haya en el buffer de las tramas de recepcion
      self._oCanalSerie.reset_input_buffer()  # Borrar lo que haya en el buffer de recepcion
      self._dTemp['TmpRcp_seg']= self._K_fTmoRcp_Std_seg
      self._TransmitirTrama()
      if (self._bVerMensDbg_TipoMensTrm) : print(self._lEstado[0] + ': Transmitido un mensaje de "Peticion de estados digitales de control"')
      if (self._bVerMensDbg_MensajeTrm)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaTrm)
      self._sEstadoCom= 'EspRcp'
      return 'Procesado'

    # **** Estado de la comunicación= Esperando mensaje de recepcin **********************************************************

    elif (self._sEstadoCom == 'EspRcp') :

      # ==== Evento= Recibida trama vlida ====================================================================================
          
      if (sEvento == 'RecibidaTramaValida') :
        iFuncion= dTrama['Funcion']
        iTYP= dTrama['TYP']
        bBitACD= dTrama['BitFcbAcd']

        if ((iFuncion == PROCOME_General.PROCOME_RESPOND_DATOSUSUARIO) and (dTrama['TYP'] == 103)) :
          self._dTemp['TmpRcp_seg']= 0
          self._bBitFCB= not self._bBitFCB
          #
          if (self._bVerMensDbg_TipoMensRcp) : 
            sTexto= 'Recibido un mensaje de "TransmisiÃÂ³n de estados digitales de control" con ACD= '
            sTexto+= '1' if (bBitACD) else '0'
            print(sTexto)
          if (self._bVerMensDbg_MensajeRcp)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaRcp)
          #
          if (bBitACD) :
            self._lEstado=     dCambiosDeEstado['ACD1']['Estado']
            self._sEstadoCom=  dCambiosDeEstado['ACD1']['EstadoCom']
            self._lEstado_Ret= dCambiosDeEstado['ACD1']['Estado_Ret']
            self._sEstCom_Ret= dCambiosDeEstado['ACD1']['EstCom_Ret']
            return 'ProcesarDeNuevo'
          else :
            self._lEstado=     dCambiosDeEstado['ACD0']['Estado']
            self._sEstadoCom=  dCambiosDeEstado['ACD0']['EstadoCom']
            self._lEstado_Ret= None
            self._sEstCom_Ret= None
            return 'ProcesarDeNuevo'
            
        else :  
          self._RecibidoMensajeNoEsperado(self._lEstado, self._lTramaRcp)
          return 'Procesado'

      # ==== Evento= Recibida trama erronea ===================================================================================
          
      elif (sEvento == 'RecibidaTramaErronea') :
        return 'Procesado'                    # De momento no hacer nada, esperar al Timeout
          
      # ==== Evento= Timeout de recepcin =====================================================================================
          
      elif (sEvento == 'TimeoutRcp') :
        return self._Reintentar()

    # **** Resto de casos *****************************************************************************************************
    
    return sEvento


  # ===========================================================================================================================
  # ==== Procesar estado: Sincronizacion
  # ===========================================================================================================================
  #
  # Al ser un mensaje que se envia sin esperar confirmacin se prepara la transmisin, se transmite, se espera un pequeo tiempo
  # y se pasa al estado siguiente

  def _ProcesarEstado_Sincronizacion(self, sEvento, lEstado_Sig, sEstadoCom_Sig):

    # **** Estado de la comunicación= Preparando la transmisin ***************************************************************

    if (self._sEstadoCom == 'PrepTrm') :
      self._lTramaTrm= PROCOME_ConstruirTramaTrm.ConstruirMensaje_SincrUniv(self._iDir)
      self._oConstrTramaRcp.Reset()           # Borrar lo que haya en el buffer de las tramas de recepcion
      self._oCanalSerie.reset_input_buffer()  # Borrar lo que haya en el buffer de recepcion
      self._dTemp['TmpRcp_seg']= 0
      self._dTemp['TmpEspera_seg']= 0.1    # Darle un tiempo para no mandar 2 mensajes seguidos
      if (self._bVerMensDbg_TipoMensTrm) : print(self._lEstado[0] + ': Transmitido un mensaje de "Sincronizacion universal"')
      if (self._bVerMensDbg_MensajeTrm)  : PROCOME_General.ImprimirTrama_Hex('  Mensaje:', self._lTramaTrm)
      self._TransmitirTrama()
      self._sEstadoCom= 'Reposo'
      return 'Procesado'
         
    # ==== Evento= Timeout de la Espera =================================================================================
          
    elif (sEvento == 'TimeoutEspera') :
      self._lEstado= lEstado_Sig
      self._sEstadoCom= sEstadoCom_Sig
      
      return 'ProcesarDeNuevo'

    # ==== Evento no procesado ================================================================================================

    else :
      return sEvento


  # ===========================================================================================================================
  # ==== Comunicacion en marcha
  # ===========================================================================================================================

  def Comunicando(self):
    return self._lEstado != ['Enlace', 'Reposo']


  # ===========================================================================================================================
  # ==== Obtener el estado actual
  # ===========================================================================================================================

  def EstadoActual(self):
    return self._lEstado


  # ===========================================================================================================================
  # ==== Transmitir una Trama
  # ===========================================================================================================================

  def _TransmitirTrama(self):
    self._oCanalSerie.rts= True
    self._oCanalSerie.write(bytes(self._lTramaTrm))
    # & self._oCanalSerie.rts= False
    self._oFormPpal.AvanzarPilotoTrm()
    return

# #############################################################################################################################
