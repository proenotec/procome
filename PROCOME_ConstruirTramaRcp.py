# -*- coding: cp1252 -*-

# #############################################################################################################################
# #############################################################################################################################
# ####
# #### PROTOCOLO PROCOME: Clase "PROCOME_ConstruirTramaRcp"
# ####
# #############################################################################################################################
# #############################################################################################################################

# #############################################################################################################################
# #### Dependencias
# #############################################################################################################################

import PROCOME_General


# #############################################################################################################################
# #### Clase PROCOME_ConstruirTramaRcp
# #############################################################################################################################

class PROCOME_ConstruirTramaRcp:

  # ***************************************************************************************************************************
  # **** Constructor
  # ***************************************************************************************************************************

  def __init__(self, iMostrarMensajesDebug):

    # **** Constantes *********************************************************************************************************

    self._tSuperEstados=  ('Comun', 'TramaCorta', 'TramaLarga')
    self._tEstadosComun= ('Start', 'Checksum', 'End', 'TramaCompleta', 'Error')
    self._tEstadosTramaCorta= ('Ctrl', 'Dir')
    self._tEstadosTramaLarga= ('Long1', 'Long2', 'Start2', 'Ctrl', 'Dir', 'Datos')

    # **** Variables **********************************************************************************************************

    self._bVerMensDbg_ErrSoft=      ((iMostrarMensajesDebug & 0x01) != 0)
    self._bVerMensDbg_TramaParcial= ((iMostrarMensajesDebug & 0x02) != 0)
    self._bVerMensDbg_ErrorReal=    ((iMostrarMensajesDebug & 0x04) != 0)

    self.Reset()
  
  # **** Constructor (Fin) ****************************************************************************************************


  # ***************************************************************************************************************************
  # **** Reset
  # ***************************************************************************************************************************

  def Reset(self):

    self._lTrama= []
    self._bEsTramaCorta= None
    self._lEstado= ['Comun', 'Start']
    self._iChecksum= 0
    return

  # **** Reset (Fin) **********************************************************************************************************



  # ***************************************************************************************************************************
  # **** ConstruirTramaRcp
  # ***************************************************************************************************************************
  #
  # Devuelve:
  #    Un valor negativo si se ha detectado algún error 
  #    0: si aún la trama no está completa
  #    Una lista con la trama si ya se ha completado la trama
  
  def ConstruirTrama(self, byDatoRcp):

    # =========================================================================================================================
    # ==== Inicializaciones. Comprobaciones iniciales
    # =========================================================================================================================
        
    sSuperEstado= self._lEstado[0]
    if (sSuperEstado not in self._tSuperEstados) :
      self._lEstado= ['Comun', 'Error']
      if (self._bVerMensDbg_ErrSoft) : print('ERROR DE SOFTWARE en "PROCOME_ConstruirTramaRcp": El SuperEstado <' + sSuperEstado + '> no existe')
      return -1

    sEstado= self._lEstado[1]
        
    # =========================================================================================================================
    # ==== Procesar en función del estado actual
    # =========================================================================================================================

    # -------------------------------------------------------------------------------------------------------------------------
    # ---- SuperEstado: 'Comun'
    # -------------------------------------------------------------------------------------------------------------------------
    
    if( sSuperEstado == 'Comun') :
      if (sEstado not in self._tEstadosComun) :  
        self._lEstado= ['Comun', 'Error']
        if (self._bVerMensDbg_ErrSoft) : print('ERROR DE SOFTWARE en "PROCOME_ConstruirTramaRcp": El Estado <' + sSuperEstado + '.' + sEstado + '> no existe')
        return -10
      
      # ·······················································································································
      # ···· Estado= Comun.Start
      # ·······················································································································

      elif( sEstado == 'Start') :
      
        if (byDatoRcp == PROCOME_General.TRAMACORTA_START) : 
          self._lTrama= [byDatoRcp]
          self._bEsTramaCorta= True
          self._lEstado= ['TramaCorta', 'Ctrl']
          return 0
          
        elif (byDatoRcp == PROCOME_General.TRAMALARGA_START) :
          self._lTrama= [byDatoRcp]
          self._bEsTramaCorta= False
          self._lEstado= ['TramaLarga', 'Long1']
          return 0
        
        else :
          self._lEstado= ['Comun', 'Error']
          if (self._bVerMensDbg_ErrorReal) : print('ERROR en "PROCOME_ConstruirTramaRcp": Carácter "START" no válido. Cáracter= ' + Hex2(byDatoRcp)+ '>')
          return -11  


      # ·······················································································································
      # ···· Estado= Comun.Checksum
      # ·······················································································································

      elif (sEstado == 'Checksum') :
        self._lTrama.append(byDatoRcp)
        if (byDatoRcp != self._iChecksum) :
          self._lEstado= ['Comun', 'Error']
          if (self._bVerMensDbg_ErrorReal) : print('ERROR en "PROCOME_ConstruirTramaRcp": Checksum no válido. Recibido= ' + Hex2(byDatoRcp)+ '. Calculado= ' + Hex2(self._iChecksum)+ '>')
          if (self._bVerMensDbg_TramaParcial) : ImprimirTrama_Hex(' - Trama parcial: ', self._lTrama)
          return -12
        self._lEstado= ['Comun', 'End']
        return 0


      # ·······················································································································
      # ···· Estado= Comun.End
      # ·······················································································································

      elif (sEstado == 'End') :
        self._lTrama.append(byDatoRcp)
        bHayError= self._bEsTramaCorta and (byDatoRcp != PROCOME_General.TRAMACORTA_END)
        bHayError= bHayError or (not self._bEsTramaCorta and (byDatoRcp != PROCOME_General.TRAMALARGA_END))
        if (bHayError) :
          self._lEstado= ['Comun', 'Error']
          if (self._bVerMensDbg_ErrorReal) : print('ERROR en "PROCOME_ConstruirTramaRcp": Carácter "END" no válido. Cáracter= ' + Hex2(byDatoRcp)+ '>')
          if (self._bVerMensDbg_TramaParcial) : ImprimirTrama_Hex(' - Trama parcial: ', self._lTrama)
          return -13
        self._lEstado= ['Comun', 'TramaCompleta']
        return self._lTrama


      # ·······················································································································
      # ···· Estado= Comun.TramaCompleta
      # ·······················································································································

      elif (sEstado == 'TramaCompleta') :
        self._lEstado= ['Comun', 'Error']
        if (self._bVerMensDbg_ErrorReal) : print('ERROR en "PROCOME_ConstruirTramaRcp": Recibido un carácter cuando ya hay una trama completa')
        return -14

      # ·······················································································································
      # ···· Estado= Comun.Error
      # ·······················································································································

      elif (sEstado == 'Error') :
        if (self._bVerMensDbg_ErrorReal) : print('ERROR en "PROCOME_ConstruirTramaRcp": Recibido un carácter cuando la trama ya es erronea')
        return -15


    # -------------------------------------------------------------------------------------------------------------------------
    # ---- SuperEstado: 'TramaCorta'
    # -------------------------------------------------------------------------------------------------------------------------
    
    elif( sSuperEstado == 'TramaCorta') :
      if (sEstado not in self._tEstadosTramaCorta) :  
        self._lEstado= ['Comun', 'Error']
        if (self._bVerMensDbg_ErrSoft) : print('ERROR DE SOFTWARE en "PROCOME_ConstruirTramaRcp": El Estado <' + sSuperEstado + '.' + sEstado + '> no existe')
        return -20

      # ·······················································································································
      # ···· Estado= Comun.Ctrl
      # ·······················································································································

      if( sEstado == 'Ctrl') :
        self._lTrama.append(byDatoRcp)
        self._iChecksum= byDatoRcp
        self._lEstado= ['TramaCorta', 'Dir']
        return 0
        
      # ·······················································································································
      # ···· Estado= Comun.Dir
      # ·······················································································································

      elif( sEstado == 'Dir') :
        self._lTrama.append(byDatoRcp)
        self._iChecksum= (self._iChecksum + byDatoRcp) & 0x00FF
        self._lEstado= ['Comun', 'Checksum']
        return 0


    # -------------------------------------------------------------------------------------------------------------------------
    # ---- SuperEstado: 'TramaLarga'
    # -------------------------------------------------------------------------------------------------------------------------
    
    elif( sSuperEstado == 'TramaLarga') :
      if (sEstado not in self._tEstadosTramaLarga) :  
        self._lEstado= ['Comun', 'Error']
        if (self._bVerMensDbg_ErrSoft) : print('ERROR DE SOFTWARE en "PROCOME_ConstruirTramaRcp": El Estado <' + sSuperEstado + '.' + sEstado + '> no existe')
        return -30

   
      # ·······················································································································
      # ···· Estado= TramaLarga.Long1
      # ·······················································································································

      if (sEstado == 'Long1') :
        self._lTrama.append(byDatoRcp)
        self._LgTramaLarga= byDatoRcp
        if (self._LgTramaLarga < 2) : 
          if (self._bVerMensDbg_ErrorReal) : print('ERROR en "PROCOME_ConstruirTramaRcp": Al confirmar la longitud de la trama')
          return -31
        self._lEstado= ['TramaLarga', 'Long2']
        return 0


      # ·······················································································································
      # ···· Estado= TramaLarga.BuscLong2
      # ·······················································································································

      elif (sEstado == 'Long2') :
        self._lTrama.append(byDatoRcp)     
        if (self._LgTramaLarga != byDatoRcp) :
          if (self._bVerMensDbg_ErrorReal) : print('ERROR en "PROCOME_ConstruirTramaRcp": La longitud de la trama no puede ser menor de 2. Dato recibido= ' + Hex2(byDatoRcp)+ '>')
          if (self._bVerMensDbg_TramaParcial) : ImprimirTrama_Hex(' - Trama parcial: ', self._lTrama)
          return -32
        self._lEstado= ['TramaLarga', 'Start2']
        return 0
        
      # ·······················································································································
      # ···· Estado= TramaLarga.Start2
      # ·······················································································································

      elif (sEstado == 'Start2') :
        self._lTrama.append(byDatoRcp)
        if (byDatoRcp != PROCOME_General.TRAMALARGA_START) :
          if (self._bVerMensDbg_ErrorReal) : print('ERROR en "PROCOME_ConstruirTramaRcp": Segundo carácter "START" de una trama larga no válido. Cáracter= ' + Hex2(byDatoRcp)+ '>')
          if (self._bVerMensDbg_TramaParcial) : ImprimirTrama_Hex(' - Trama parcial: ', self._lTrama)
          return -33
        self._lEstado= ['TramaLarga', 'Ctrl']
        return 0


      # ·······················································································································
      # ···· Estado= TramaLarga.Ctrl
      # ·······················································································································

      elif( sEstado == 'Ctrl') :
        self._lTrama.append(byDatoRcp)
        self._iChecksum= byDatoRcp
        self._lEstado= ['TramaLarga', 'Dir']
        return 0

        
      # ·······················································································································
      # ···· Estado= TramaLarga.Dir
      # ·······················································································································

      elif( sEstado == 'Dir') :
        self._lTrama.append(byDatoRcp)
        self._iChecksum= (self._iChecksum + byDatoRcp) & 0x00FF
        self.iDatoPorLeer= self._LgTramaLarga - 2
        if (self.iDatoPorLeer == 0) :
          self._lEstado= ['Comun', 'Checksum']
        else :
          self._lEstado= ['TramaLarga', 'Datos']
        return 0


      # ·······················································································································
      # ···· Estado= TramaLarga.Datos
      # ·······················································································································

      elif( sEstado == 'Datos') :
        self._lTrama.append(byDatoRcp)
        self._iChecksum= (self._iChecksum + byDatoRcp) & 0x00FF
        self.iDatoPorLeer-= 1
        if (self.iDatoPorLeer == 0) : self._lEstado= ['Comun', 'Checksum']
        return 0

  # **** ConstruirTramaRcp (Fin) **********************************************************************************************

# #############################################################################################################################
