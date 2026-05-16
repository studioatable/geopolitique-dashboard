@echo off
REM ============================================================================
REM dev_serve.bat — Lance le serveur HTTP local pour le dashboard géopolitique
REM ============================================================================
REM Double-clic = serveur démarré sur http://localhost:8000/site/
REM Ctrl+C dans la fenêtre = serveur arrêté.
REM Épinglable dans la barre des tâches Windows (clic droit > Épingler).
REM ============================================================================

setlocal

REM Se positionner à la racine du repo (le script vit dans scripts\)
cd /d "%~dp0\.."

REM Tenter d'utiliser le venv s'il existe, sinon le Python du système
set PYTHON_EXE=
if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
) else (
    set PYTHON_EXE=python
)

echo.
echo =========================================================
echo  Geopolitique Dashboard - Serveur local
echo =========================================================
echo.
echo  URL : http://localhost:8000/site/
echo.
echo  Pour arreter le serveur : Ctrl+C
echo  Pour fermer cette fenetre apres arret : fermer la croix
echo.
echo =========================================================
echo.

%PYTHON_EXE% -m http.server 8000

REM Si on arrive ici, le serveur s'est arrêté
echo.
echo Serveur arrete.
pause
