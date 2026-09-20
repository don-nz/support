@echo off
:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :admin
) else (
    echo [*] Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:admin
:: Switch drive letter AND directory to the USB location of this script
cd /d "%~dp0"

echo [+] Running with Administrator privileges in: %CD%

:: Launch diag.py targeting drive C: (or pass drive letter argument %1 if provided)
if "%~1"=="" (
    python diag.py C
) else (
    python diag.py %~1
)

pause
