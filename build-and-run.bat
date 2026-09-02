@echo off
echo ========================================================
echo Compilando OrquestaGit en modo Produccion (Release)...
echo ========================================================
call npm run tauri build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] La compilacion ha fallado. Revisa los logs arriba.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo [EXITO] Compilacion completada con exito.
echo Lanzando OrquestaGit (Version Final)...
echo ========================================================
start src-tauri\target\release\app.exe
