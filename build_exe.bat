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
echo Double-cliquez dessus. Une console s'ouvre + le navigateur sur http://127.0.0.1:5000
echo En cas d'erreur, lisez la console ou le fichier gestioncours-error.log a cote du .exe
echo.
pause
