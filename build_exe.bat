@echo off
setlocal
cd /d "%~dp0"

echo === GestionCours : build Windows .exe ===
python -m pip install -r requirements.txt pyinstaller
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
echo Double-cliquez : le navigateur s'ouvre quand le serveur est pret.
echo La petite fenetre se minimise toute seule — restaurez-la pour Quitter.
echo.
pause
