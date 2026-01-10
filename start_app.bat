@echo off
title MenuSpreader Launcher
color 0A

echo ===================================================
echo   INICIANDO MENUSPREADER
echo ===================================================

:: 1. Verificar Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR CRITICO] Node.js no esta instalado.
    echo.
    echo Para usar este programa necesitas descargar Node.js:
    echo https://nodejs.org/
    echo.
    pause
    exit
)

:: 2. Verificar Dependencias (Primera ejecucion)
if not exist "node_modules" (
    echo [INFO] Primera vez iniciada. Instalando dependencias...
    call npm install
)

:: 3. Iniciar Cerebro (Servidor)
echo [1/2] Arrancando servidor WhatsApp...
start "MenuSpreader Server (NO CERRAR)" /min cmd /k "node bot-server.js"

:: Esperar un poco a que arranque
timeout /t 3 >nul

:: 4. Iniciar Interfaz (GUI)
echo [2/2] Abriendo aplicacion...
if exist "dist\MenuSpreader.exe" (
    start "" "dist\MenuSpreader.exe"
) else if exist "MenuSpreader.exe" (
    start "" "MenuSpreader.exe"
) else (
    echo [ERROR] No encuentro MenuSpreader.exe
    pause
)

echo.
echo Todo listo. Minimiza esta ventana, pero NO la cierres.
timeout /t 5 >nul