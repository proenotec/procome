# -*- coding: cp1252 -*-

# #############################################################################################################################
# #############################################################################################################################
# ####
# #### PROTOCOLO PROCOME: Construir Tramas para transmitir
# ####
# #############################################################################################################################
# #############################################################################################################################

# #############################################################################################################################
# #### Dependencias
# #############################################################################################################################

import datetime
import PROCOME_General


# #############################################################################################################################
# #### FUNCIONES
# #############################################################################################################################

# *****************************************************************************************************************************
# **** Construir una Trama corta
# *****************************************************************************************************************************

def TramaCorta_Construir(BitPRM, BitFCB_ACD, Bit_FCV_DFC, Funcion, Direccion):

  # **** Comprobaciones iniciales *********************************************************************************************

  if not (0 <= Direccion <= 255) : return None

  # **** Mensaje del Primario *************************************************************************************************
      
  if (BitPRM) :
    byCampoControl= 0x40
    if (Funcion in (0, 4, 9)) :
      # FCV= 0, FCB= 0
      byCampoControl|= Funcion
    elif (Funcion in (3, 10, 11)) :
      byCampoControl|= 0x10                     # FCV= 1
      if (BitFCB_ACD) : byCampoControl|= 0x20
      byCampoControl|= Funcion
    else :
      return None                               # Error de software o caso aun no contemplado
       
  # **** Mensaje del Secundario ***********************************************************************************************

  else :
    byCampoControl= 0x00
    if (BitFCB_ACD) : byCampoControl|= 0x20 
    if (BitFCV_DFC) : byCampoControl|= 0x10 
    byCampoControl|= Funcion
        
  # **** Comun para ambos casos ***********************************************************************************************
        
  byChecksum= (byCampoControl + Direccion) & 0x00FF
  return [PROCOME_General.TRAMACORTA_START, byCampoControl, Direccion, byChecksum, PROCOME_General.TRAMACORTA_END]   

# **** FIN **** Construir una Trama corta *************************************************************************************


# *****************************************************************************************************************************
# **** Construir una Trama larga
# *****************************************************************************************************************************

def TramaLarga_Construir(BitPRM, BitFCB_ACD, Bit_FCV_DFC, Funcion, Direccion, ASDU):

  # **** Comprobaciones iniciales *********************************************************************************************

  if not (0 <= Direccion <= 255) : return None

  # ===========================================================================================================================
  # ==== Construir la cabecera de la capa de enlace
  # ===========================================================================================================================

  lTrama= [PROCOME_General.TRAMALARGA_START, 2 + len(ASDU), 2 + len(ASDU),  PROCOME_General.TRAMALARGA_START]

  # **** Mensaje del Primario *************************************************************************************************
      
  if (BitPRM) :
    byCampoControl= 0x40
    if (Funcion in (4, 6)) :
      if (BitFCB_ACD) : byCampoControl|= 0x20
      if (Bit_FCV_DFC) : byCampoControl|= 0x10
      byCampoControl|= Funcion
    elif (Funcion in (3, 8)) :
      byCampoControl|= 0x10                     # FCV= 1
      if (BitFCB_ACD) : byCampoControl|= 0x20
      byCampoControl|= Funcion
    else :
      return None                               # Error de software o caso aun no contemplado

  # **** Mensaje del Secundario ***********************************************************************************************

  else :
    byCampoControl= 0x00
    if (BitFCB_ACD) : byCampoControl|= 0x20 
    if (BitFCV_DFC) : byCampoControl|= 0x10 
    byCampoControl|= Funcion

  # **** Comun para ambos casos ***********************************************************************************************

  lTrama.append(byCampoControl)
  lTrama.append(Direccion)
  byChecksum= (byCampoControl + Direccion) & 0x00FF


  # ===========================================================================================================================
  # ==== Agregar el ASDU
  # ===========================================================================================================================

  for Dato in ASDU :
    lTrama.append(Dato)
    byChecksum= (byChecksum + Dato) & 0x00FF 
  
  # ===========================================================================================================================
  # ==== Construir la cola de la capa de enlace
  # ===========================================================================================================================
  
  lTrama.append(byChecksum)
  lTrama.append(PROCOME_General.TRAMALARGA_END)

  return lTrama

# **** FIN **** Construir una Trama larga ***********************************************************************************


# ***************************************************************************************************************************
# **** Primario. Reset de linea remota
# ***************************************************************************************************************************

def ConstruirMensaje_ResetLineaRemota(Direccion):
  return TramaCorta_Construir(True, False, False, 0, Direccion)


# *****************************************************************************************************************************
# **** Primario. Peticion de datos de Clase 1
# *****************************************************************************************************************************

def ConstruirMensaje_PetDatosClase1(Direccion, BitFCB):
  return TramaCorta_Construir(True, BitFCB, None, 10, Direccion)


# *****************************************************************************************************************************
# **** Primario. Construir un mensaje de "Peticion de datos de control" (medidas y cambios de estado)
# *****************************************************************************************************************************

def ConstruirMensaje_PetDatosCtrl(Direccion, BitFCB):

  # **** Construir ASDU *******************************************************************************************************
  
  lASDU= [0x64, 0x81, 0x64, Direccion, 0x64, 0xC8] 

  # **** Construir el paquete completo ****************************************************************************************

  return TramaLarga_Construir(True, BitFCB, True, 6, Direccion, lASDU)


# *****************************************************************************************************************************
# **** Primario. Construir un mensaje de "Petición de estados digitales de control"
# *****************************************************************************************************************************

def ConstruirMensaje_PetEstadosDigCtrl(Direccion, BitFCB):

  # **** Construir ASDU *******************************************************************************************************
  
  lASDU= [0x67, 0x81, 0x67, Direccion, 0x64, 0x00]

  # **** Construir el paquete completo ****************************************************************************************

  return TramaLarga_Construir(True, BitFCB, True, 6, Direccion, lASDU)


# *****************************************************************************************************************************
# **** Primario. Construir un mensaje de sincronización a la dirección universal
# *****************************************************************************************************************************

def ConstruirMensaje_SincrUniv(Direccion):

  # ===========================================================================================================================
  # ==== Construir ASDU
  # ===========================================================================================================================
  
  lASDU= [0x06, 0x81, 0x08, 0xFF, 0xFF, 0x00] 
  oAhora= datetime.datetime.now()
  
  # **** Segundos con milisegundos ********************************************************************************************
  
  iAux= int(oAhora.microsecond/1000) + 1000 * oAhora.second
  lASDU.append(iAux % 256)
  lASDU.append(iAux // 256) 
  
  # **** IV, Res1 y Minutos ***************************************************************************************************
  #
  # Habria que procesar los bit de3 IV y Res1 que en PROCOME se utiliza pero no tengo muy claro para que. Se ignoran (a 0)

  lASDU.append(oAhora.minute)
  
  # **** SU, Res2 y Horas *****************************************************************************************************
  #
  # Habria que mirar cuando es horario de verano para generar el bit SU. Se ignora (a 0)

  lASDU.append(oAhora.hour)

  # **** Dia de la semana y Día del mes **************************************************************************************

  iDiaDeLaSemana= oAhora.isoweekday() + 1
  if (iDiaDeLaSemana > 7) : iDiaDeLaSemana= 1
  lASDU.append((iDiaDeLaSemana << 5) + oAhora.day)
  
  # **** Res3 y Mes ***********************************************************************************************************

  lASDU.append(oAhora.month)

  # **** Res4 y Año ***********************************************************************************************************
  
  lASDU.append(oAhora.year % 1000)

  # ===========================================================================================================================
  # ==== Construir el paquete completo
  # ===========================================================================================================================

  return TramaLarga_Construir(True, False, False, 4, 0xFF, lASDU)

# **** FIN **** Primario. Construir un mensaje de sincronización a la dirección universal *************************************


# *****************************************************************************************************************************
# **** Primario. Construir un mensaje de "Ordenes de mando" (ASDU= 121, 0x79)
# *****************************************************************************************************************************
#
# iOperacion:
#  1: OFF
#  2: ON 

def ConstruirMensaje_PetOrden(Direccion, BitFCB, iNrOrden, sOperacion):

  # **** Construir ASDU *******************************************************************************************************
  
  
  if (sOperacion not in ('OFF', 'ON')) : return None


  
  lASDU= [0x79, 0x01, 0x79, Direccion, 0x64, 0x00, iNrOrden & 0x00FF, iNrOrden >> 8, 1 if (sOperacion == 'OFF') else 2]

  # **** Construir el paquete completo ****************************************************************************************

  return TramaLarga_Construir(True, BitFCB, True, 3, Direccion, lASDU)

# #############################################################################################################################


