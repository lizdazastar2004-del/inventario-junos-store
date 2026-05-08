@echo off
title Juno's Store - Inventario
color 0D
echo.
echo  ====================================
echo    Juno's Store - Inventario :3
echo  ====================================
echo.
echo  Iniciando... por favor espera...
echo.

cd /d "%~dp0"

timeout /t 2 /nobreak >nul
start http://localhost:5000

python app.py

echo.
echo  El programa se cerro.
pause
