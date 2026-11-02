@echo off
REM ============================================================
REM   Doble clic para ejecutar todo: subir a GitHub + descargar APK
REM   v3 — Incluye auto-instalación de Git + GitHub CLI
REM ============================================================

setlocal
cd /d "%~dp0"

title Subir a GitHub + Descargar APK

echo.
echo ============================================================
echo   🚀 SUBIDA AUTOMÁTICA A GITHUB + DESCARGA APK (v3)
echo ============================================================
echo.
echo Carpeta: %CD%
echo.

REM Comprobar si python está instalado
where python >nul 2>&1
if errorlevel 1 (
    echo ❌ No se encuentra Python. Descárgalo de https://www.python.org/downloads/
    echo    Durante la instalación marca la casilla "Add Python to PATH"
    echo.
    echo Pulsa una tecla para cerrar...
    pause >nul
    exit /b 1
)

REM Ejecutar el script Python. NO usamos 'exit /b' aquí para que
REM la ventana se quede abierta siempre.
python subir_y_descargar_apk.py
set EXITCODE=%ERRORLEVEL%

echo.
echo ============================================================
if %EXITCODE% equ 0 (
    echo   ✅ Proceso terminado correctamente ^(código %EXITCODE%^)
) else (
    echo   ⚠  El script terminó con código %EXITCODE%
    echo   Revisa los mensajes anteriores para ver qué pasó.
)
echo.
echo   ℹ  NO cierres esta ventana hasta que hayas copiado la ruta del APK
echo   o hayas leído el mensaje de error.
echo.
echo   Pulsa CUALQUIER tecla para cerrar la ventana...
echo ============================================================
pause >nul

exit /b %EXITCODE%
