@echo off
taskkill /FI "WINDOWTITLE eq AGEN Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AGEN Frontend*" /T /F >nul 2>&1
taskkill /IM agen-api.exe /T /F >nul 2>&1
echo AGEN services stopped.