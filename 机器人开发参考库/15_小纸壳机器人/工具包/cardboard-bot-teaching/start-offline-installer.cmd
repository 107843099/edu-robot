@echo off
setlocal

rem Start the offline installer on a local HTTP origin so Web Serial can be used.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-offline-installer.ps1"

if errorlevel 1 (
    echo.
    echo The offline installer could not start. See the message above.
    pause
)

endlocal
