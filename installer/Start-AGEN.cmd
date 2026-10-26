@echo off
setlocal EnableDelayedExpansion
title AGEN Launcher

set "AGEN_HOME=%LOCALAPPDATA%\AGEN"
if not exist "%AGEN_HOME%" mkdir "%AGEN_HOME%"

rem --- First run: create an operator-provisioned configuration ---
if not exist "%AGEN_HOME%\.env" (
  copy /Y "%~dp0.env.example" "%AGEN_HOME%\.env" >nul
  echo.
  echo   ============================================================
  echo    AGEN da tao cau hinh local tai:
  echo    %AGEN_HOME%\.env
  echo    Quan tri vien can cap cau hinh AI truoc khi chay pilot.
  echo   ============================================================
  exit /b 0
)

rem --- Load KEY=VALUE lines from .env (skip blanks and # comments) ---
for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%AGEN_HOME%\.env") do (
  set "line=%%A"
  if not "!line!"=="" set "%%A=%%B"
)

if "%GEMINI_API_KEY%"=="" if "%OPENAI_API_KEY%"=="" (
  echo AGEN chua duoc cau hinh dich vu AI boi quan tri vien.
  echo Vui long lien he nguoi van hanh pilot.
  exit /b 1
)

rem --- Desktop always uses a local SQLite DB under the user's profile ---
set "DATABASE_URL=sqlite:///%AGEN_HOME:\=/%/agen_dev.db"
set "APP_ENV=development"
set "ALLOWED_ORIGINS=http://127.0.0.1:3000"
set "AGEN_BACKEND_PORT=8000"
set "PORT=3000"
set "HOSTNAME=127.0.0.1"
set "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1"

echo Starting AGEN services...
start "AGEN Backend" /D "%~dp0" /min "%~dp0backend\agen-api.exe"
start "AGEN Frontend" /D "%~dp0frontend" /min "%~dp0node.exe" "%~dp0frontend\server.js"

rem --- Wait for the frontend to come up, then open the browser ---
timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:3000"

echo AGEN dang chay tai http://127.0.0.1:3000
echo Dong cua so nay khong tat AGEN. Dung AGEN bang Stop-AGEN.cmd.
endlocal
