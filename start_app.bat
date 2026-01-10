@echo off
echo ===================================================
echo   INICIANDO SISTEMA DE MENU - MENUSPREADER
echo ===================================================
echo 1. Iniciando Servidor del Bot (Node.js)...

:: Check if node is available
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] No se encuentra Node.js instalado o en el PATH.
    echo Por favor instala Node.js para continuar.
    pause
    exit
)

:: Start the Bot Server in a minimized window
start "Menu Bot Server" /min cmd /k "node bot-server.js"

echo Servidor lanzado. Esperando 5 segundos para conexion...
timeout /t 5 >nul

echo 2. Iniciando Aplicacion de Escritorio...
start "" "dist\MenuSpreader.exe"

echo.
echo Todo listo! Puedes cerrar esta ventana negra si quieres,
echo pero NO cierres la ventana que dice "Menu Bot Server".
echo.
pause