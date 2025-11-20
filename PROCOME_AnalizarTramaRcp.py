# -*- coding: utf-8 -*-

# #############################################################################################################################
# #############################################################################################################################
# ####
# #### PROTOCOLO PROCOME: Analizar las tramas recibidas
# ####
# #############################################################################################################################
# #############################################################################################################################

# #############################################################################################################################
# #### Dependencias
# #############################################################################################################################

import math
import PROCOME_General


# #############################################################################################################################
# #### FUNCIONES
# #############################################################################################################################

# *****************************************************************************************************************************
# **** Analizar una Trama
# *****************************************************************************************************************************

def AnalizarTrama(lTrama):
    
  # **** Incializaciones. Comprobaciones iniciales ****************************************************************************

  dResultado= {'Error' : -99, 'TramaValida' : False, 'TramaCorta' : False, 'BitPRM' : False, 'BitFcbAcd' : False, 'BitFcvDfc' : False, 'Funcion' : 0, 'Dir' : 0, 'Checksum' : 0, 'ASDU' : [], 'TYP' : -1}

  iLgTrama= len(lTrama)
  if (iLgTrama < 1) : 
    dResultado['Error']= -1
    return dResultado
    
  iTipoTrama= lTrama[PROCOME_General.TRAMACORTA_POSIC_START]
  if (iTipoTrama not in (PROCOME_General.TRAMACORTA_START, PROCOME_General.TRAMALARGA_START)) :
    dResultado['Error']= -2
    return dResultado

  # **** Tipo de trama ********************************************************************************************************
      
  bTramaCorta= (iTipoTrama == PROCOME_General.TRAMACORTA_START)

  # **** Trama Corta **********************************************************************************************************
  
  if (bTramaCorta) :
    if (iLgTrama != PROCOME_General.TRAMACORTA_TAM_TRAMA) :
      dResultado['Error']= -10
      return dResultado
    byControl= lTrama[PROCOME_General.TRAMACORTA_POSIC_CTRL]
    bPRM= ((byControl & 0x40) != 0)
    iFuncion= byControl & 0x0F
    
    if (bPRM) :
      if (iFuncion not in (0, 9, 10, 11)) :
        dResultado['Error']= -11
        return dResultado
    else :
      if (iFuncion not in (0, 1, 5, 9, 11)) :
        dResultado['Error']= -12
        return dResultado

    iDir= lTrama[PROCOME_General.TRAMACORTA_POSIC_DIR]
    
    iChecksum= ((byControl + iDir) & 0x0FF)
    if (iChecksum != lTrama[PROCOME_General.TRAMACORTA_POSIC_CHECKSUM]) :
      dResultado['Error']= -13
      return dResultado

    if (lTrama[PROCOME_General.TRAMACORTA_POSIC_END] != PROCOME_General.TRAMACORTA_END) :
      dResultado['Error']= -14
      return dResultado
  
  # **** Trama Larga **********************************************************************************************************

  else :    
    if (iLgTrama <= PROCOME_General.TRAMALARGA_POSIC_LONG) :
      dResultado['Error']= -20
      return dResultado
    byLong= lTrama[PROCOME_General.TRAMALARGA_POSIC_LONG]
    if (byLong != lTrama[PROCOME_General.TRAMALARGA_POSIC_LONG + 1]) :
      dResultado['Error']= -21
      return dResultado
    if (iLgTrama != (PROCOME_General.TRAMALARGA_TAM_CABCOLA + byLong)) :
      dResultado['Error']= -22
      return dResultado
    if (lTrama[PROCOME_General.TRAMALARGA_POSIC_CTRL - 1] != PROCOME_General.TRAMALARGA_START) :
      dResultado['Error']= -23
      return dResultado
    byControl= lTrama[PROCOME_General.TRAMALARGA_POSIC_CTRL]
    bPRM= ((byControl & 0x40) != 0)
    iFuncion= byControl & 0x0F

    if (bPRM) :
      if (iFuncion not in (3, 4, 6)) :
        dResultado['Error']= -24
        return dResultado
    else :
      if (iFuncion not in (3, 8)) :
        dResultado['Error']= -25
        return dResultado

    iDir= lTrama[PROCOME_General.TRAMALARGA_POSIC_DIR]
    
    iChecksum= (byControl + iDir) & 0x0FF
    for iDato in lTrama[PROCOME_General.TRAMALARGA_POSIC_DIR + 1 : PROCOME_General.TRAMALARGA_POSIC_CHECKSUM] :
      iChecksum= (iChecksum + iDato) & 0x0FF
    if (iChecksum != lTrama[PROCOME_General.TRAMALARGA_POSIC_CHECKSUM]) :
      dResultado['Error']= -26
      return dResultado

    if (lTrama[PROCOME_General.TRAMALARGA_POSIC_END] != PROCOME_General.TRAMALARGA_END) :
      dResultado['Error']= -26
      return dResultado
      
    dResultado['ASDU']= lTrama[PROCOME_General.TRAMALARGA_POSIC_ASDU : PROCOME_General.TRAMALARGA_POSIC_CHECKSUM]
    dResultado['TYP']=  lTrama[PROCOME_General.TRAMALARGA_POSIC_TYP]

  # **** Salida sin error *************************************************************************************************
  
  dResultado['Error']= 0
  dResultado['TramaCorta']= bTramaCorta
  dResultado['BitPRM']= bPRM
  dResultado['BitFcbAcd']= ((byControl & 0x20) != 0)
  dResultado['BitFcvDfc']= ((byControl & 0x10) != 0)
  dResultado['Funcion']= iFuncion
  dResultado['Dir']= iDir
  dResultado['Checksum']= iChecksum
  dResultado['TramaValida']= True

  return dResultado


# *****************************************************************************************************************************
# **** Interpretar Paquetes de Secundario (con una ASDU en concreto)
# *****************************************************************************************************************************

# =============================================================================================================================
# ==== ASDU 100 (Peticin de medidas y cambios de estado)
# =============================================================================================================================

def InterpretarPaquetesSecundario_ASDU_100(lTrama):

  # **** Comprobaciones iniciales *********************************************************************************************
  # 
  # Desechar los mensajes que son de Trama corta, o del Primario o que no tienen TYP= 100
  
  dTrama= AnalizarTrama(lTrama)
  if ((dTrama['TramaCorta']) or (dTrama['BitPRM']) or (dTrama['TYP'] != 100))  : return -1

  # **** Extraer las medidas **************************************************************************************************

  iNrMedidas= lTrama[PROCOME_General.TRAMALARGA_POSIC_I0 + 3]
  iPosic= PROCOME_General.TRAMALARGA_POSIC_I0 + 5
  iIdPunto= 0
  for iNrMed in range(0, iNrMedidas) :
    iValor= lTrama[iPosic] + 256 * lTrama[iPosic + 1]
    sIV= 'IV' if (iValor & 0x0001) else ''
    iNeg= -1  if (iValor & 0x8000) else 1
    iValor= ((iValor & 0x7FF8) >> 3 ) * iNeg
    sOvf= 'OV' if (iValor == 4095) else ''
    if (iNrMed == 0) :
      lMedidas= [(iIdPunto, sIV, sOvf, iValor)]
    else :
      lMedidas.append((iIdPunto, sIV, sOvf, iValor))
    iPosic+= 2
    iIdPunto+= 1

  # **** Extraer los cambios de estado de entradas digitales *******************************************************************

  lCambiosED=[]
  iNrCambiosED= lTrama[iPosic] + 256 * lTrama[iPosic + 1]
  if (iNrCambiosED) :
    iPosic= iPosic + 2
    for iNrCambED in range(0, iNrCambiosED) :
      iValor= lTrama[iPosic] + 256 * lTrama[iPosic + 1]
      iIdPunto= (iValor & 0x03FF)
      sIV= 'IV' if (iValor & 0x1000) else ''
      iValor= 1 if (iValor & 0x2000) else 0
      if (iNrCambiosED == 0) :
        lCambiosED= [(iIdPunto, sIV, iValor)]
      else :
        lCambiosED.append((iIdPunto, sIV, iValor))
      iPosic= iPosic + 9 
      
  return {'Dir' : dTrama['Dir'], 'Medidas' : lMedidas, 'CambiosED' : lCambiosED}


# =============================================================================================================================
# ==== ASDU 103 (Transmisin de estados digitales de control) 
# =============================================================================================================================

def InterpretarPaquetesSecundario_ASDU_103(lTrama):

  # **** Comprobaciones iniciales *********************************************************************************************
  # 
  # Desechar los mensajes que son de Trama corta, o del Primario o que no tienen TYP= 103
  
  dTrama= AnalizarTrama(lTrama)
  if ((dTrama['TramaCorta']) or (dTrama['BitPRM']) or (dTrama['TYP'] != 103))  : return -1


  # **** Verificar que el ASDU correcto ***************************************************************************************

  lAsdu= dTrama['ASDU']
  
  if (len(lAsdu) < 16) : return -2
  if (lAsdu[0:7] != [0x67, 0x81, 0x67, dTrama['Dir'], 0x64, 0x00, 0x01]) : return -3
  iNrEstadosDig= lAsdu[14] + 256 * lAsdu[15]
  if (len(lAsdu) != (16 + 2 * math.ceil(iNrEstadosDig/8))) : return -4
  
  # **** Interpretar la informacin que viene en el ASDU **********************************************************************
  
  # Hora= lAsdu[7:14] # Se ignora la informacin de hora

  ldEstadosDig=[]
  
  iPosic= 16
  iPosicBit= 0
  for iIndiceEstDig in range(0, iNrEstadosDig) :
    if (iPosicBit == 0) :
      byEstado= lAsdu[iPosic]
      iPosic+= 1
      byValidez= lAsdu[iPosic]
      iPosic+= 1
      byMascara= 1
      
    ldEstadosDig.append((iIndiceEstDig, 'IV' if ((byValidez & byMascara) != 0) else '', (byEstado & byMascara) != 0))
    
    byMascara<<= 1
    iPosicBit+= 1
    if (iPosicBit == 8) : iPosicBit= 0
    
  return {'Dir' : dTrama['Dir'], 'EstadosDig' : ldEstadosDig}


# =============================================================================================================================
# ==== ASDU 121 (Confirmacin de orden)
# =============================================================================================================================
#
# iTipoOperacion:
#  1: OFF
#  2: ON 
#


def InterpretarPaquetesSecundario_ASDU_121(lTrama):

  # **** Comprobaciones iniciales *********************************************************************************************
  # 
  # Desechar los mensajes que son de Trama corta, o del Primario o que no tienen TYP= 121
  
  dTrama= AnalizarTrama(lTrama)
  if ((dTrama['TramaCorta']) or (dTrama['BitPRM']) or (dTrama['TYP'] != 121))  : return -1

  # **** Verificar que el ASDU correcto ***************************************************************************************
  
  if (lTrama[PROCOME_General.TRAMALARGA_POSIC_ASDU : PROCOME_General.TRAMALARGA_POSIC_ASDU + 6] != [0x79, 0x01, 0x79, dTrama['Dir'], 0x64, 0x00]) : return -2
  
  # **** Interpretar la informacin que viene en el ASDU **********************************************************************

  iPosic= PROCOME_General.TRAMALARGA_POSIC_ASDU + 6
  iNrOden= lTrama[iPosic] + 256 * lTrama[iPosic + 1]
  iPosic= iPosic + 2

  iTipoOperacion= lTrama[iPosic]
  iPosic= iPosic + 1
  if (iTipoOperacion == 1) :
    sTipoOperacion= 'OFF'
  elif (iTipoOperacion == 2) :
    sTipoOperacion= 'ON'
  else :
    sTipoOperacion= 'ERROR: Tipo de operaciÃÂ³n no contemplado'

  iResultadoOper= lTrama[iPosic]
  if (iResultadoOper == 0) :
    sResultadoOper= 'Orden aceptada'
  elif (iResultadoOper == 10) :
    sResultadoOper= 'Comando erroneo'
  elif (iResultadoOper == 20) :
    sResultadoOper= 'Nr. de orden incorrecto'
  elif (iResultadoOper == 30) :
    sResultadoOper= 'El elemento ya estÃÂ¡ en la posiciÃÂ³n deseada'
  elif (iResultadoOper == 40) :
    sResultadoOper= 'No se puede ejecutar la orden debido a un bloqueo interno'
  elif (iResultadoOper == 100) :
    sResultadoOper= 'Error indefinido'
  else :
    sResultadoOper= 'Error, opciÃÂ³n no contemplada'

  # print('iNrOden= ' + str(iNrOden))
  # print('iTipoOperacion= ' + sTipoOperacion)
  # print('iResultadoOper= ' + sResultadoOper)
  return {'Dir' : dTrama['Dir'], 'NrOden' : iNrOden, 'TipoOperacion' : sTipoOperacion, 'ResultadoOper' : sResultadoOper}
    


# =============================================================================================================================
# ==== ASDU 5 (Mensaje de identificacin del tipo de equipo)
# =============================================================================================================================

def InterpretarPaquetesSecundario_ASDU_5(lTrama):

  # **** Comprobaciones iniciales *********************************************************************************************
  # 
  # Desechar los mensajes que son de Trama corta, o del Primario o que no tienen TYP= 5
  
  dTrama= AnalizarTrama(lTrama)
  if ((dTrama['TramaCorta']) or (dTrama['BitPRM']) or (dTrama['TYP'] != 5)) : return -1

  # **** Verificar que el ASDU correcto ***************************************************************************************

  lAsdu= dTrama['ASDU']
  if (lAsdu[:2] != [0x05, 0x81]) : return -2
  # El lAsdu[:2] es la COT, pero aunque hay varios valores vlidos no nos interesan
  if (lAsdu[3:5] != [dTrama['Dir'], 0xFE]) : return -3

  # **** Interpretar la informacin que viene en el ASDU **********************************************************************

  iTipoMensaje= lAsdu[5]
  if (iTipoMensaje == 2) :
    sTipoMensaje= 'Reset Bit FCB'
  if (iTipoMensaje == 3) :
    sTipoMensaje= 'Reset CU'
  elif (iTipoMensaje == 4) :
    sTipoMensaje= 'Arranque /Rearranque (start / restart)'
  elif (iTipoMensaje == 5) :
    sTipoMensaje= 'Encendido (power on)'
  else :
    sTipoMensaje= 'Con cÃÂ³digo <' + str(iTipoMensaje) + '>'
  sVersProcome= str(lAsdu[6] >> 4) + '.' + str(lAsdu[6] & 0xF)
  sTxtIdEquipo= ''
  for iIndice in range(7, 15) : sTxtIdEquipo= sTxtIdEquipo + chr(lAsdu[iIndice])
  sDatosNoProcesados= ''
  for iIndice in range(15, len(lAsdu)) :
    sDatosNoProcesados= sDatosNoProcesados + ' ' + ('0' + hex(lAsdu[iIndice])[2:])[-2:]
  return {'Dir' : dTrama['Dir'], 'TipoMensaje' : sTipoMensaje, 'VersProcome' : sVersProcome, 'TxtIdEquipo' : sTxtIdEquipo, 'DatosNoProcesados' : sDatosNoProcesados}

# #############################################################################################################################
