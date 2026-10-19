@echo off
rem Levanta EcoHarmony Park con un link publico (doble clic o "iniciar-demo.cmd").
rem Pasa los parametros al script de PowerShell, por ejemplo: iniciar-demo.cmd -Local
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar-demo.ps1" %*
pause
