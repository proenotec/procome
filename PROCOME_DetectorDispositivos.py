# -*- coding: utf-8 -*-

# #############################################################################################################################
# #############################################################################################################################
# ####
# #### PROTOCOLO PROCOME: Detector de Dispositivos en Modo Monitor
# ####
# #############################################################################################################################
# #############################################################################################################################

# #############################################################################################################################
# #### Dependencias
# #############################################################################################################################

import threading
import time
import PROCOME_AnalizarTramaRcp
import PROCOME_General

# #############################################################################################################################
# #### Clase DetectorDispositivos
# #############################################################################################################################

class DetectorDispositivos:
    """
    Clase para detectar y rastrear dispositivos PROCOME en el bus RS-485.
    Diseñada para operar en modo Monitor pasivo (sin transmitir).

    Thread-safe: Usa threading.Lock() interno para todas las operaciones.
    """

    # ***************************************************************************************************************************
    # **** Constructor
    # ***************************************************************************************************************************

    def __init__(self, fTimeoutSegundos=30.0):
        """
        Constructor del detector de dispositivos.

        Args:
            fTimeoutSegundos: Tiempo en segundos sin actividad para marcar dispositivo como 'Timeout' (default: 30.0)
        """
        self._fTimeoutSegundos = fTimeoutSegundos
        self._dDispositivos = {}  # Diccionario {direccion: info_dispositivo}
        self._lock = threading.Lock()  # Lock para thread-safety

    # ***************************************************************************************************************************
    # **** Registrar Trama Recibida
    # ***************************************************************************************************************************

    def RegistrarTrama(self, lTrama):
        """
        Analiza una trama recibida y registra el dispositivo detectado.

        IMPORTANTE: Solo registra dispositivos que TRANSMITEN (responden), no los que son interrogados.
        Esto se logra filtrando tramas con PRM=0 (Secundario/Slave responde).
        Si PRM=1 (Primario/Master interroga), el campo 'Dir' es el destino, no el origen.

        Args:
            lTrama: Lista de bytes con la trama completa recibida

        Returns:
            True si se registró correctamente, False si la trama no es válida o es del master
        """
        # Analizar la trama usando la función existente
        dAnalisis = PROCOME_AnalizarTramaRcp.AnalizarTrama(lTrama)

        # Solo registrar tramas válidas
        if not dAnalisis['TramaValida']:
            return False

        # FILTRO CRÍTICO: Solo registrar tramas de dispositivos que TRANSMITEN (PRM=0)
        # Si PRM=1, es el master interrogando, no un dispositivo respondiendo
        if dAnalisis['BitPRM']:
            return False

        # Obtener dirección del dispositivo (que está transmitiendo)
        iDireccion = dAnalisis['Dir']

        # Ignorar dirección universal (broadcast)
        if iDireccion == PROCOME_General.PROCOME_DIR_UNIVERSAL:
            return False

        # Validar rango de direcciones
        if iDireccion < PROCOME_General.PROCOME_DIR_MIN or iDireccion > PROCOME_General.PROCOME_DIR_MAX:
            return False

        # Obtener timestamp actual
        fAhora = time.time()

        # Registrar con thread-safety
        with self._lock:
            # Si es un dispositivo nuevo
            if iDireccion not in self._dDispositivos:
                self._dDispositivos[iDireccion] = {
                    'Direccion': iDireccion,
                    'UltimaActividad': fAhora,
                    'Contador': 1,
                    'TiposMensajes': set(),
                    'Estado': 'Activo',
                    'PrimeraMencion': fAhora
                }
            else:
                # Actualizar dispositivo existente
                self._dDispositivos[iDireccion]['UltimaActividad'] = fAhora
                self._dDispositivos[iDireccion]['Contador'] += 1
                self._dDispositivos[iDireccion]['Estado'] = 'Activo'

            # Registrar tipo de mensaje (ASDU) si es trama larga
            if not dAnalisis['TramaCorta'] and dAnalisis['TYP'] != -1:
                self._dDispositivos[iDireccion]['TiposMensajes'].add(dAnalisis['TYP'])

            # Registrar función de trama corta si aplica
            if dAnalisis['TramaCorta']:
                iFuncion = dAnalisis['Funcion']
                # Registrar función con prefijo 'F' para distinguir de ASDU
                self._dDispositivos[iDireccion]['TiposMensajes'].add(f'F{iFuncion}')

        return True

    # ***************************************************************************************************************************
    # **** Actualizar Timeouts
    # ***************************************************************************************************************************

    def ActualizarTimeouts(self):
        """
        Verifica todos los dispositivos y marca como 'Timeout' aquellos
        que no han tenido actividad durante más de fTimeoutSegundos.

        Debe ser llamado periódicamente (ej: cada segundo) desde un thread vigilante.
        """
        fAhora = time.time()

        with self._lock:
            for iDireccion, dInfo in self._dDispositivos.items():
                fTiempoSinActividad = fAhora - dInfo['UltimaActividad']

                if fTiempoSinActividad > self._fTimeoutSegundos:
                    dInfo['Estado'] = 'Timeout'
                else:
                    dInfo['Estado'] = 'Activo'

    # ***************************************************************************************************************************
    # **** Obtener Dispositivos Detectados
    # ***************************************************************************************************************************

    def ObtenerDispositivos(self):
        """
        Devuelve una copia del diccionario de dispositivos detectados.
        Thread-safe: Devuelve una copia profunda para evitar problemas de concurrencia.

        Returns:
            dict: Diccionario {direccion: info_dispositivo}
                  info_dispositivo contiene:
                    - Direccion: int (1-254)
                    - UltimaActividad: float (timestamp)
                    - Contador: int (número de tramas recibidas)
                    - TiposMensajes: set (tipos ASDU o funciones detectados)
                    - Estado: str ('Activo' | 'Timeout')
                    - PrimeraMencion: float (timestamp primera detección)
        """
        with self._lock:
            # Crear copia profunda del diccionario
            dCopia = {}
            for iDireccion, dInfo in self._dDispositivos.items():
                dCopia[iDireccion] = {
                    'Direccion': dInfo['Direccion'],
                    'UltimaActividad': dInfo['UltimaActividad'],
                    'Contador': dInfo['Contador'],
                    'TiposMensajes': dInfo['TiposMensajes'].copy(),  # Copiar set
                    'Estado': dInfo['Estado'],
                    'PrimeraMencion': dInfo['PrimeraMencion']
                }
            return dCopia

    # ***************************************************************************************************************************
    # **** Reset del Detector
    # ***************************************************************************************************************************

    def Reset(self):
        """
        Limpia completamente el historial de dispositivos detectados.
        Thread-safe.
        """
        with self._lock:
            self._dDispositivos.clear()

    # ***************************************************************************************************************************
    # **** Obtener Estadísticas
    # ***************************************************************************************************************************

    def ObtenerEstadisticas(self):
        """
        Devuelve estadísticas generales del detector.

        Returns:
            dict: Estadísticas con:
                - TotalDispositivos: número total de dispositivos detectados
                - DispositivosActivos: número de dispositivos activos
                - DispositivosTimeout: número de dispositivos con timeout
        """
        with self._lock:
            iTotal = len(self._dDispositivos)
            iActivos = sum(1 for d in self._dDispositivos.values() if d['Estado'] == 'Activo')
            iTimeout = iTotal - iActivos

            return {
                'TotalDispositivos': iTotal,
                'DispositivosActivos': iActivos,
                'DispositivosTimeout': iTimeout
            }

# #############################################################################################################################
