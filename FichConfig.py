# -*- coding: utf-8 -*-

# #############################################################################################################################
# #### Dependencias
# #############################################################################################################################

from xml.dom.minidom import Document, parse, Node
import os

# #############################################################################################################################
# #### Clase FichConfig
# #############################################################################################################################

class FichConfig:

  # ***************************************************************************************************************************
  # **** __init__ 
  # ***************************************************************************************************************************
  #
  # No se permite especificar ninguno de los parametros porque alguno podria estar mal
  
  def __init__(self):
    
    # **** Inicializar variables ********************************************************

    self._sNombreFich_Def= 'PROCOME.cfg'
    self._ValoresPorDefecto()
    

  # ***************************************************************************************************************************
  # *** _ValoresPorDefecto 
  # ***************************************************************************************************************************
  #
  # No se permite especificar ninguno de los parametros porque alguno podria estar mal
  
  def _ValoresPorDefecto(self):

    self._dParametros= { 'Medidas.NrMedidas'         : 35,
                         'EstadosDigitales.NrEstDig' : 64,
                         'Ordenes.NrOrdenes'         : 4,
                         'PuertoSerie.Puerto'        : 'COM1',
                         'PuertoSerie.Baudios'       : 9600,
                         'PuertoSerie.BitsDatos'     : 8,
                         'PuertoSerie.Paridad'       : 'E',
                         'PuertoSerie.BitsStop'      : 2,
                         'Protocolo.DirRemota'       : 1,
                         'Telegram.Habilitado'       : False,
                         'Telegram.NombreBot'        : '',
                         'Telegram.Token'            : '',
                         'Telegram.ChatID'           : '',
                         # Configuración multi-tarjeta (6 tarjetas)
                         'Tarjeta1.Habilitada'       : True,
                         'Tarjeta1.DirRemota'        : 1,
                         'Tarjeta1.TestsHabilitados' : False,
                         'Tarjeta2.Habilitada'       : False,
                         'Tarjeta2.DirRemota'        : 2,
                         'Tarjeta2.TestsHabilitados' : False,
                         'Tarjeta3.Habilitada'       : False,
                         'Tarjeta3.DirRemota'        : 3,
                         'Tarjeta3.TestsHabilitados' : False,
                         'Tarjeta4.Habilitada'       : False,
                         'Tarjeta4.DirRemota'        : 4,
                         'Tarjeta4.TestsHabilitados' : False,
                         'Tarjeta5.Habilitada'       : False,
                         'Tarjeta5.DirRemota'        : 5,
                         'Tarjeta5.TestsHabilitados' : False,
                         'Tarjeta6.Habilitada'       : False,
                         'Tarjeta6.DirRemota'        : 6,
                         'Tarjeta6.TestsHabilitados' : False,
                         # Configuración de la consola
                         'Consola.MaxLineas'         : 5000,
                         'Consola.ModoMensajes'      : 'explicado'  # 'explicado' o 'hex'
                       }
    self._sNombreFich= self._sNombreFich_Def
    
  
  # ***************************************************************************************************************************
  # *** Cambiar el valor de los parametros
  # ***************************************************************************************************************************
  
  # *** Parametro= NrMedidas **************************************************************************************************

  def NrMedidas_Set(self, Valor): 
    if ((type(Valor) != int) or (Valor < 1)) : return False
    self._dParametros['Medidas.NrMedidas']= Valor
    return True


  # *** Parametro= NrEstDig ***************************************************************************************************

  def NrEstDig_Set(self, Valor): 
    if ((type(Valor) != int) or (Valor < 1)) : return False
    self._dParametros['EstadosDigitales.NrEstDig']= Valor
    return True


  # *** Parametro= NrOrdenes **************************************************************************************************

  def NrOrdenes_Set(self, Valor): 
    if ((type(Valor) != int) or (Valor < 1)) : return False
    self._dParametros['Ordenes.NrOrdenes']= Valor
    return True


  # *** Parametro= PuertoSerie.Puerto *****************************************************************************************

  def PuertoSerie_Puerto_Set(self, Valor): 
    if ((type(Valor) != str) or (Valor == '')) : return False
    self._dParametros['PuertoSerie.Puerto']= Valor
    return True


  # *** Parametro= PuertoSerie.Baudios ****************************************************************************************

  def PuertoSerie_Baudios_Set(self, Valor): 
    if ((type(Valor) != int) or (Valor not in (300,600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200))) : return False
    self._dParametros['PuertoSerie.Baudios']= Valor
    return True


  # *** Parametro= PuertoSerie.BitsDatos **************************************************************************************

  def PuertoSerie_BitsDatos_Set(self, Valor): 
    if ((type(Valor) != int) or (Valor not in (7, 8))) : return False
    self._dParametros['PuertoSerie.BitsDatos']= Valor
    return True


  # *** Parametro= PuertoSerie.Paridad ****************************************************************************************

  def PuertoSerie_Paridad_Set(self, Valor):
    if ((type(Valor) != str) or (Valor not in ('N', 'E', 'O'))) :
      return False
    self._dParametros['PuertoSerie.Paridad']= Valor
    return True


  # *** Parametro= PuertoSerie.BitsStop ***************************************************************************************

  def PuertoSerie_BitsStop_Set(self, Valor): 
    if ((type(Valor) != int) or (Valor not in (1, 2))) : return False
    self._dParametros['PuertoSerie.BitsStop']= Valor
    return True


  # *** Parametro= Protocolo.DirRemota ****************************************************************************************

  def Protocolo_DirRemota_Set(self, Valor):
    if ((type(Valor) != int) or (Valor not in range(1, 254))) : return False
    self._dParametros['Protocolo.DirRemota']= Valor
    return True


  # *** Parametro= Telegram.Habilitado ****************************************************************************************

  def Telegram_Habilitado_Set(self, Valor):
    if (type(Valor) != bool) : return False
    self._dParametros['Telegram.Habilitado']= Valor
    return True


  # *** Parametro= Telegram.NombreBot *****************************************************************************************

  def Telegram_NombreBot_Set(self, Valor):
    if (type(Valor) != str) : return False
    self._dParametros['Telegram.NombreBot']= Valor.strip()
    return True


  # *** Parametro= Telegram.Token *********************************************************************************************

  def Telegram_Token_Set(self, Valor):
    if (type(Valor) != str) : return False
    self._dParametros['Telegram.Token']= Valor.strip()
    return True


  # *** Parametro= Telegram.ChatID ********************************************************************************************

  def Telegram_ChatID_Set(self, Valor):
    if (type(Valor) != str) : return False
    self._dParametros['Telegram.ChatID']= Valor.strip()
    return True


  # *** Parametro= Consola.MaxLineas ******************************************************************************************

  def Consola_MaxLineas_Set(self, Valor):
    if ((type(Valor) != int) or (Valor < 20) or (Valor > 100000)) : return False
    self._dParametros['Consola.MaxLineas']= Valor
    return True

  # *** Parametro= Consola.ModoMensajes ****************************************************************************************

  def Consola_ModoMensajes_Set(self, Valor):
    if ((type(Valor) != str) or (Valor not in ['explicado', 'hex'])) : return False
    self._dParametros['Consola.ModoMensajes']= Valor
    return True


  # *** Parametros= Tarjetas (1-6) ********************************************************************************************

  def Tarjeta_Habilitada_Set(self, iNrTarjeta, Valor):
    if (type(iNrTarjeta) != int) or (iNrTarjeta < 1) or (iNrTarjeta > 6) : return False
    if (type(Valor) != bool) : return False
    self._dParametros[f'Tarjeta{iNrTarjeta}.Habilitada']= Valor
    return True

  def Tarjeta_DirRemota_Set(self, iNrTarjeta, Valor):
    if (type(iNrTarjeta) != int) or (iNrTarjeta < 1) or (iNrTarjeta > 6) : return False
    if (type(Valor) != int) or (Valor not in range(1, 254)) : return False
    self._dParametros[f'Tarjeta{iNrTarjeta}.DirRemota']= Valor
    return True

  def Tarjeta_TestsHabilitados_Set(self, iNrTarjeta, Valor):
    if (type(iNrTarjeta) != int) or (iNrTarjeta < 1) or (iNrTarjeta > 6) : return False
    if (type(Valor) != bool) : return False
    self._dParametros[f'Tarjeta{iNrTarjeta}.TestsHabilitados']= Valor
    return True


  # ***************************************************************************************************************************
  # *** Obtener todos los parámetros en un diccionario
  # ***************************************************************************************************************************
  #
  # Devuelve un texto
  
  def Parametros_Get(self): 
    return self._dParametros.copy()


  # ***************************************************************************************************************************
  # *** Obtener el nombre del fichero de configuracion
  # ***************************************************************************************************************************
  #
  # Devuelve un texto
  
  def NombreFichCfg_Get(self): 
    return self._sNombreFich


  # ***************************************************************************************************************************
  # *** Cambiar el nombre del fichero de configuracion
  # ***************************************************************************************************************************
  #
  # Espera recibir un texto. No se comprueba nada
  
  def NombreFichCfg_Set(self, Valor):
    if ((type(Valor) != str) or (Valor == '')) : return
    self._sNombreFich= Valor.strip()


  # ***************************************************************************************************************************
  # *** Salvar la configuracion en un fichero
  # ***************************************************************************************************************************
  #
  # Devuelve True si no ha habido ningun error

  def SalvarEnFichero(self):

    # **** Crear la estructura inicial ****************************************************************************************
    
    documento= Document()
    raiz = documento.createElement('PROCOME')
    #raiz.appendChild(documento.createComment('Para meter un comentario'))

    # **** Crear apartado 'Medidas' *******************************************************************************************

    esteApartado = documento.createElement('Medidas')
    sNombreParametro= 'Medidas.NrMedidas'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], str(self._dParametros[sNombreParametro]))
    raiz.appendChild(esteApartado)

    # **** Crear apartado 'EstadosDigitales' **********************************************************************************

    esteApartado = documento.createElement('EstadosDigitales')
    sNombreParametro= 'EstadosDigitales.NrEstDig'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], str(self._dParametros[sNombreParametro]))
    raiz.appendChild(esteApartado)

    # **** Crear apartado 'Ordenes' *******************************************************************************************

    esteApartado = documento.createElement('Ordenes')
    sNombreParametro= 'Ordenes.NrOrdenes'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], str(self._dParametros[sNombreParametro]))
    raiz.appendChild(esteApartado)

    # **** Crear apartado 'PuertoSerie' ***************************************************************************************

    esteApartado = documento.createElement('PuertoSerie')

    sNombreParametro= 'PuertoSerie.Puerto'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], self._dParametros[sNombreParametro])
    
    sNombreParametro= 'PuertoSerie.Baudios'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], str(self._dParametros[sNombreParametro]))

    sNombreParametro= 'PuertoSerie.BitsDatos'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], str(self._dParametros[sNombreParametro]))

    sNombreParametro= 'PuertoSerie.Paridad'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], self._dParametros[sNombreParametro])

    sNombreParametro= 'PuertoSerie.BitsStop'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], str(self._dParametros[sNombreParametro]))

    raiz.appendChild(esteApartado)

    # **** Crear apartado 'Protocolo' *****************************************************************************************

    esteApartado = documento.createElement('Protocolo')
    sNombreParametro= 'Protocolo.DirRemota'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], str(self._dParametros[sNombreParametro]))
    raiz.appendChild(esteApartado)

    # **** Crear apartado 'Telegram' ******************************************************************************************

    esteApartado = documento.createElement('Telegram')

    sNombreParametro= 'Telegram.Habilitado'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], 'True' if self._dParametros[sNombreParametro] else 'False')

    sNombreParametro= 'Telegram.NombreBot'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], self._dParametros[sNombreParametro])

    sNombreParametro= 'Telegram.Token'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], self._dParametros[sNombreParametro])

    sNombreParametro= 'Telegram.ChatID'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], self._dParametros[sNombreParametro])

    raiz.appendChild(esteApartado)

    # **** Crear apartados 'Tarjeta1' a 'Tarjeta6' ****************************************************************************

    for iNrTarjeta in range(1, 7):
      esteApartado = documento.createElement(f'Tarjeta{iNrTarjeta}')

      sNombreParametro= f'Tarjeta{iNrTarjeta}.Habilitada'
      esteApartado.setAttribute('Habilitada', 'True' if self._dParametros[sNombreParametro] else 'False')

      sNombreParametro= f'Tarjeta{iNrTarjeta}.DirRemota'
      esteApartado.setAttribute('DirRemota', str(self._dParametros[sNombreParametro]))

      sNombreParametro= f'Tarjeta{iNrTarjeta}.TestsHabilitados'
      esteApartado.setAttribute('TestsHabilitados', 'True' if self._dParametros[sNombreParametro] else 'False')

      raiz.appendChild(esteApartado)

    # **** Crear apartado 'Consola' *******************************************************************************************

    esteApartado = documento.createElement('Consola')
    sNombreParametro= 'Consola.MaxLineas'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], str(self._dParametros[sNombreParametro]))
    sNombreParametro= 'Consola.ModoMensajes'
    esteApartado.setAttribute(sNombreParametro.split('.')[1], str(self._dParametros[sNombreParametro]))
    raiz.appendChild(esteApartado)

    # **** Finalizar la creacion de la configuracion **************************************************************************

    documento.appendChild(raiz)

    # **** Escribir la configuracion en fichero *******************************************************************************

    fchXml=None
    try:
      fchXml= open(self._sNombreFich, 'wb')
      fchXml.write(documento.toprettyxml(indent='  ', newl='\n', encoding="UTF-8"))
    except:
      if fchXml != None : fchXml.close()
      return False
    else:    
      fchXml.close()

    # **** Salir sin error ****************************************************************************************************

    return True


  # *************************************************************************************
  # *** Leer la configuracion desde un fichero
  # *************************************************************************************
  #
  # Si no hay error:
  # - La funcion devuelve un texto vacio
  # - En self._dParametros estan todos los parametros, actualizados al valor leido del fichero
  # Si hay error:
  # - La funcion devuelve un texto con una descripcion del error
  # - Los valores que estn en self._dParametros no son fiables
  
  def LeerDeFichero(self):
  
    # **** Comprobar si el fichero existe *************************************************************************************
    
    if not os.path.exists(self._sNombreFich) : return 'El fichero <' + self._sNombreFich + '"> no existe'
    if not os.path.isfile(self._sNombreFich) : return '<' + self._sNombreFich + '"> no es un fichero'

    # **** Abrir el fichero ***************************************************************************************************
    
    fchXml=None
    try:
      fchXml= open(self._sNombreFich, 'rt')
    except:
      if fchXml != None : fchXml.close()
      return 'ERROR: No se ha podido abrir el fichero <' + self._sNombreFich + '>'

    # **** Cargar el fichero y preprocesar su contenido ***********************************************************************

    try:
      documento= parse(fchXml)
    except:
      fchXml.close()
      return 'ERROR al procesar el fichero <' + self._sNombreFich + '>. No es un fichero XML correcto'
    else:    
      fchXml.close()

    # **** Extraer los datos **************************************************************************************************

    dictAux={}
    for oElemento in documento.documentElement.childNodes:
      if oElemento.nodeType == Node.ELEMENT_NODE:
        sNombreApartado= oElemento.nodeName
        for sNombreParametro, sValorParametro in oElemento.attributes.items():
          dictAux[sNombreApartado+ '.' + sNombreParametro]= sValorParametro   
    # for clave, valor in dictAux.items() : print(clave, '->', valor)      
    # print()

    # **** Comprobar que no falta ni sobra ningun parametro *******************************************************************
    
    sMensajes= ''
    iHayError= 0
    tNombreParametrosEsperados= list(self._dParametros)
    tNombreParametrosRecibidos= list(dictAux)

    if len(tNombreParametrosEsperados) != len(tNombreParametrosRecibidos) :
      sRetorno= 'ERROR al leer el fichero de configuracion: Los numero de parametros recibidos no coincide con el de los esperados'
      iHayError= 3
    else :
      for sNombre in tNombreParametrosEsperados :
        if not sNombre in tNombreParametrosRecibidos :
          if iHayError < 1 : sMensajes= sMensajes + '- Parametros esperados pero no recibidos:'
          sMensajes= sMensajes + '   ' + sNombre
          iHayError= 1
    
      for sNombre in tNombreParametrosRecibidos :
        if not sNombre in tNombreParametrosEsperados :
          if iHayError < 2 : sMensajes= sMensajes + '- Parametros recibidos pero no esperados:'
          sMensajes= sMensajes + '   ' + sNombre
          bHayError= True
          
      if iHayError > 0 :     
        sRetorno= 'ERROR al leer el fichero de configuracion: Los parametros recibidos no coinciden con los esperados'

    if iHayError > 0 : 
      sRetorno+= 'Nombre del fichero de configuracion:\n  <' + self._sNombreFich + '>'
      sRetorno+= '\nListado de errores:\n' + sMensajes
      return sRetorno
    
    # **** Comprobar todos los datos antes de aceptarlos. Asignar los datos leidos a las variables ****************************

    dBackup= self._dParametros.copy()
    sTxtError=''

    for sNombreParametro in tNombreParametrosRecibidos :

      bHayError= False
      
      # --- Medidas.NrMedidas -------------------------------------------------------------------------------------------------

      if sNombreParametro == 'Medidas.NrMedidas' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.NrMedidas_Set(int(sValor)))

      # --- EstadosDigitales.NrEstDig -----------------------------------------------------------------------------------------

      elif sNombreParametro == 'EstadosDigitales.NrEstDig' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.NrEstDig_Set(int(sValor)))

      # --- Ordenes.NrOrdenes -------------------------------------------------------------------------------------------------

      elif sNombreParametro == 'Ordenes.NrOrdenes' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.NrOrdenes_Set(int(sValor)))

      # --- PuertoSerie.Puerto ------------------------------------------------------------------------------------------------

      elif sNombreParametro == 'PuertoSerie.Puerto' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.PuertoSerie_Puerto_Set(sValor))

      # --- PuertoSerie.Baudios -----------------------------------------------------------------------------------------------

      elif sNombreParametro == 'PuertoSerie.Baudios' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.PuertoSerie_Baudios_Set(int(sValor)))

      # --- PuertoSerie.Paridad -----------------------------------------------------------------------------------------------

      elif sNombreParametro == 'PuertoSerie.Paridad' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.PuertoSerie_Paridad_Set(sValor))

      # --- PuertoSerie.BitsDatos ---------------------------------------------------------------------------------------------

      elif sNombreParametro == 'PuertoSerie.BitsDatos' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.PuertoSerie_BitsDatos_Set(int(sValor)))

      # --- PuertoSerie.BitsStop ----------------------------------------------------------------------------------------------

      elif sNombreParametro == 'PuertoSerie.BitsStop' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.PuertoSerie_BitsStop_Set(int(sValor)))

      # --- Protocolo.DirRemota -----------------------------------------------------------------------------------------------

      elif sNombreParametro == 'Protocolo.DirRemota' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.Protocolo_DirRemota_Set(int(sValor)))

      # --- Telegram.Habilitado -----------------------------------------------------------------------------------------------

      elif sNombreParametro == 'Telegram.Habilitado' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.Telegram_Habilitado_Set(sValor == 'True'))

      # --- Telegram.NombreBot ------------------------------------------------------------------------------------------------

      elif sNombreParametro == 'Telegram.NombreBot' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.Telegram_NombreBot_Set(sValor))

      # --- Telegram.Token ----------------------------------------------------------------------------------------------------

      elif sNombreParametro == 'Telegram.Token' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.Telegram_Token_Set(sValor))

      # --- Telegram.ChatID ---------------------------------------------------------------------------------------------------

      elif sNombreParametro == 'Telegram.ChatID' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.Telegram_ChatID_Set(sValor))

      # --- Tarjeta[1-6].Habilitada -------------------------------------------------------------------------------------------

      elif sNombreParametro.startswith('Tarjeta') and sNombreParametro.endswith('.Habilitada') :
        iNrTarjeta= int(sNombreParametro[7])
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.Tarjeta_Habilitada_Set(iNrTarjeta, sValor == 'True'))

      # --- Tarjeta[1-6].DirRemota --------------------------------------------------------------------------------------------

      elif sNombreParametro.startswith('Tarjeta') and sNombreParametro.endswith('.DirRemota') :
        iNrTarjeta= int(sNombreParametro[7])
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.Tarjeta_DirRemota_Set(iNrTarjeta, int(sValor)))

      # --- Tarjeta[1-6].TestsHabilitados -------------------------------------------------------------------------------------

      elif sNombreParametro.startswith('Tarjeta') and sNombreParametro.endswith('.TestsHabilitados') :
        iNrTarjeta= int(sNombreParametro[7])
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.Tarjeta_TestsHabilitados_Set(iNrTarjeta, sValor == 'True'))

      # --- Consola.MaxLineas -------------------------------------------------------------------------------------------------

      elif sNombreParametro == 'Consola.MaxLineas' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.Consola_MaxLineas_Set(int(sValor)))

      # --- Consola.ModoMensajes ----------------------------------------------------------------------------------------------

      elif sNombreParametro == 'Consola.ModoMensajes' :
        sValor= dictAux[sNombreParametro].strip()
        bHayError= not (self.Consola_ModoMensajes_Set(sValor))

      if (bHayError) :
        sTxtError+= '- ERROR: Valor de ' + sNombreParametro + ' no vlido. Valor= ' + sValor + '\n'

    if (sTxtError != "") :
      self._dParametros= dBackup.copy()
      if (sTxtError[-1] == '\n') : sTxtError= sTxtError[:-1]
      return sTxtError

    # **** Salida sin error ***************************************************************************************************

    return ''

# #############################################################################################################################
