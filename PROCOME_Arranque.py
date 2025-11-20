# -*- coding: cp1252 -*-

# #############################################################################################################################
# #### Dependencias
# #############################################################################################################################

import time
import serial
import PROCOME_FormPpal
import FichConfig


# *****************************************************************************************************************************
# **** DEBUG
# *****************************************************************************************************************************

DEBUG_VarDebug= {'TramaTrm' : None}

fTempDEBUG= 0  # %


# *****************************************************************************************************************************
# **** Constantes globales
# *****************************************************************************************************************************

iPROCOME_Direccion= 1


# *****************************************************************************************************************************
# **** Variables globales
# *****************************************************************************************************************************

g_oCSerie= None
g_oFichCfg= None
g_oFormPpal= None
g_iDirProtocolo= None
g_iNrMedidas= None
g_iNrEstadosDig= None
g_iNrOrdenes= None


# *****************************************************************************************************************************
# **** Funciones generales
# *****************************************************************************************************************************

# **** Incremento de tiempo ***************************************************************************************************

def _IncrtTmp(bReset):
    global g_fIncrT_TmpAnt
    fTmpAct= time.time()
    fIncrTmp= 0 if (bReset) else fTmpAct - g_fIncrT_TmpAnt 
    g_fIncrT_TmpAnt= fTmpAct
    return fIncrTmp


# **** Mostrar la trama en hexadecimal ****************************************************************************************

def ImprimirTrama_Hex(Titulo, Trama):
  sSalida= Titulo
  for campo in Trama :
    sValor= hex(campo)
    sValor= sValor.replace('x', '0')[-2:]
    sSalida+= ' ' + sValor
  print(sSalida)  
  return

# **** Salir de la aplicación cerrando todo ***********************************************************************************

def Salir(sMensaje):
  if (sMensaje != '') : print(sMensaje)
  if (g_oCSerie != None) : g_oCSerie.close()
  exit()


# *****************************************************************************************************************************
# **** __main__
# *****************************************************************************************************************************

if __name__ == '__main__' :

  # ===========================================================================================================================
  # ==== Inicializaciones
  # ===========================================================================================================================
 
  print('Arranque de la aplicacion')

  _IncrtTmp(True)


  # **** Obtener la configuracion por defecto *********************************************************************************

  g_oFichCfg= FichConfig.FichConfig()			# Crear el objeto y cargar los valores por defecto
  

  # **** Cargar la configuración del fichero de configuración *****************************************************************

  sRta= g_oFichCfg.LeerDeFichero()
  if (sRta != '') :
    print('Leer el fichero de configuración:')
    print(sRta)
    print('- Se arranca con la configuración por defecto')
    
  dFichCfg= g_oFichCfg.Parametros_Get()
  g_iNrMedidas= dFichCfg['Medidas.NrMedidas']
  g_iNrEstadosDig= dFichCfg['EstadosDigitales.NrEstDig']
  g_iNrOrdenes= dFichCfg['Ordenes.NrOrdenes']
  g_iDirProtocolo= dFichCfg['Protocolo.DirRemota']
  

  # **** Crear el objeto del canal serie y configurarlo. Ya se abrirá posteriormente *******************************************

  # ==== Crear el objeto =======================================================================================================

  g_oCSerie= serial.Serial()

  # ==== Traese la configuración por defecto, para partir de ella ==============================================================

  dCSerie_Parametros= g_oCSerie.get_settings()

  # ==== Configurar los parámetros antes de intentar arrancar el puerto ========================================================

  dCSerie_Parametros['baudrate']= dFichCfg['PuertoSerie.Baudios']
  dCSerie_Parametros['bytesize']= dFichCfg['PuertoSerie.BitsDatos']
  dCSerie_Parametros['parity']=   dFichCfg['PuertoSerie.Paridad']
  dCSerie_Parametros['stopbits']= dFichCfg['PuertoSerie.BitsStop']
  dCSerie_Parametros['xonxoff']=  False
  dCSerie_Parametros['rtscts']=   False
  dCSerie_Parametros['dsrdtr']=   False
  dCSerie_Parametros['timeout']=  0              #  - No se espera si no hay ningún caracter en el buffer de recepción
  dCSerie_Parametros['write_timeout']=  0        #  - No se espera a que se transmita todo lo que hay en el buffer de transmisión
  dCSerie_Parametros['inter_byte_timeout']= None #  - Timeout entre caracteres consecutivos en recepción desactivado
  try :                                          # Cargar los parametros modificados
    g_oCSerie.apply_settings(dCSerie_Parametros)
  except :
    Salir('ERROR: al intentar los parametros del canal serie, revisarlos')

  g_oCSerie.rts= False                             # RTS= 0
  g_oCSerie.drt= True                              # DTR= 1
  g_oCSerie.port= dFichCfg['PuertoSerie.Puerto']   # Indicar cual es el canal serie


  # **** Crear y abrir el formulario principal (solo hay este) *****************************************************************

  g_oFormPpal= PROCOME_FormPpal.FormPpal(g_iNrMedidas, g_iNrEstadosDig, g_iNrOrdenes, g_iDirProtocolo, g_oCSerie)
  if (g_oFormPpal is None) :  Salir('ERROR: Al intentar abrir el formulario principal')

# #############################################################################################################################
