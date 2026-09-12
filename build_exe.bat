@echo off
setlocal
cd /d "%~dp0"

echo === GestionCours : build Windows .exe (PySide6 bureau) ===
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo pip install failed
  pause
  exit /b 1
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

python -m PyInstaller --noconfirm GestionCours.spec
if errorlevel 1 (
  echo PyInstaller failed
  pause
  exit /b 1
)

echo.
echo OK : dist\GestionCours.exe
echo Fenetre bureau native (comme Gestion_app) — PAS de navigateur.
echo.
pause
