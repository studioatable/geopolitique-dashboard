# ============================================================================
# dev_serve.ps1 — Lance le serveur HTTP local pour le dashboard géopolitique
# ============================================================================
# Usage :
#     .\scripts\dev_serve.ps1                (au premier plan)
#     .\scripts\dev_serve.ps1 -Background    (en arrière-plan, fenêtre minimisée)
#
# URL servie : http://localhost:8000/site/
# Ctrl+C pour arrêter (mode au premier plan).
# ============================================================================

param(
    [switch]$Background
)

# Racine du repo
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# Tenter d'utiliser le venv s'il existe
$pythonExe = "python"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
}

if ($Background) {
    Write-Host "Démarrage du serveur en arrière-plan (fenêtre minimisée)..." -ForegroundColor Green
    Write-Host "URL : http://localhost:8000/site/"
    Write-Host "Pour arrêter : Get-Process python | Stop-Process"
    Start-Process -FilePath $pythonExe -ArgumentList "-m", "http.server", "8000" -WindowStyle Minimized
    Write-Host "Serveur démarré. Tu peux fermer cette fenêtre."
} else {
    Write-Host ""
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host " Géopolitique Dashboard - Serveur local" -ForegroundColor Cyan
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " URL : http://localhost:8000/site/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host " Ctrl+C pour arrêter" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "=========================================================" -ForegroundColor Cyan
    Write-Host ""
    & $pythonExe -m http.server 8000
    Write-Host ""
    Write-Host "Serveur arrêté." -ForegroundColor Yellow
}
