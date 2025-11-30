@echo off
REM Script para compilar PROCOME Qt a un ejecutable standalone en Windows
REM Usa PyInstaller para crear un .exe con todas las dependencias incluidas

echo ================================================
echo   Compilando PROCOME Qt a ejecutable Windows
echo ================================================
echo.

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Descarga Python desde: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Verificar que pip está instalado
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip no está instalado
    pause
    exit /b 1
)

REM Instalar dependencias
echo Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

REM Limpiar compilaciones anteriores
echo Limpiando compilaciones anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist PROCOME.spec del PROCOME.spec

REM Compilar con PyInstaller
echo.
echo Compilando aplicación...
echo Esto puede tardar varios minutos...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name PROCOME ^
    --add-data "PROCOME.cfg;." ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import serial ^
    --hidden-import serial.tools.list_ports ^
    --collect-all PySide6 ^
    PROCOME_Arranque_Qt.py

if errorlevel 1 (
    echo.
    echo ERROR: La compilación falló
    pause
    exit /b 1
)

REM Copiar archivo de configuración
copy PROCOME.cfg dist\

REM Verificar que se compiló correctamente
if exist "dist\PROCOME.exe" (
    echo.
    echo ================================================
    echo   Compilación exitosa!
    echo ================================================
    echo.
    echo Ejecutable creado en: dist\PROCOME.exe
    for %%A in (dist\PROCOME.exe) do echo Tamaño: %%~zA bytes
    echo.
    echo Para ejecutar:
    echo   dist\PROCOME.exe
    echo.
    echo Para distribuir, copia el archivo 'dist\PROCOME.exe' junto con 'dist\PROCOME.cfg'
    echo.
) else (
    echo.
    echo ERROR: El ejecutable no se creó
    pause
    exit /b 1
)

pause
