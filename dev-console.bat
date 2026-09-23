@echo off
title OrquestaGit - Consola Dev (Claude + Antigravity)
color 0A
:loop
cls
echo ============================================================
echo   ORQUESTA GIT - WORKLOG EN VIVO
echo   Refresco cada 3s. Cierra con Ctrl+C o cerrando la ventana.
echo ============================================================
echo.
type "%~dp0ORQUESTA_WORKLOG.md"
timeout /t 3 /nobreak >nul
goto loop
