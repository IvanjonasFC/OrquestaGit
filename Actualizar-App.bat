@echo off
setlocal
title OrquestaGit - Actualizar y abrir
cd /d "%~dp0"
echo ============================================================
echo   OrquestaGit - Compilar y abrir
echo ============================================================
where npm >nul 2>nul || ( echo [ERROR] Falta Node.js/npm: https://nodejs.org & pause & exit /b 1 )
where cargo >nul 2>nul || ( echo [ERROR] Falta Rust: https://rustup.rs & pause & exit /b 1 )
if not exist node_modules ( echo [*] Instalando dependencias ^(primera vez^)... & call npm install )
echo [*] Compilando (npm run tauri build)...
call npm run tauri build
if errorlevel 1 ( echo. & echo [ERROR] Fallo la compilacion. Revisa arriba. & pause & exit /b 1 )
echo [*] Abriendo...
set "EXE="
for /f "delims=" %%f in ('dir /b /a-d /o-d "src-tauri\target\release\*.exe" 2^>nul') do ( if not defined EXE set "EXE=src-tauri\target\release\%%f" )
if defined EXE ( start "" "%EXE%" ) else ( echo [AVISO] No encuentro el .exe en src-tauri\target\release. )
echo.
echo LISTO.
pause
