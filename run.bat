@echo off
REM Wi-Fi Security Auditor - double-click launcher (Windows)
REM Opens the app window. Audit your OWN network only.
cd /d "%~dp0"
python -m wifi_auditor.gui
if errorlevel 1 (
  echo.
  echo Could not start. Install Python 3.9+ from python.org and tick
  echo "Add Python to PATH", then double-click this file again.
  echo.
  pause
)
