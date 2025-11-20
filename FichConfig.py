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
                         'Protocolo.DirRemota'       : 1
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
    

  # ***************************************************************************************************************************
  # *** Obtener todos los parï¿½metros en un diccionario
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
  # - Los valores que estï¿½n en self._dParametros no son fiables
  
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

      if (bHayError) :
        sTxtError+= '- ERROR: Valor de ' + sNombreParametro + ' no vï¿½lido. Valor= ' + sValor + '\n'

    if (sTxtError != "") :
      self._dParametros= dBackup.copy()
      if (sTxtError[-1] == '\n') : sTxtError= sTxtError[:-1]
      return sTxtError

    # **** Salida sin error ***************************************************************************************************

    return ''

# #############################################################################################################################
