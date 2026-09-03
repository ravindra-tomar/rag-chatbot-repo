# Always start API on port 8000
# Usage: .\start_server.ps1

Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\uvicorn.exe")) {
    Write-Host "ERROR: .venv missing. Pehle venv activate/install karo."
    exit 1
}

Write-Host "Starting server on http://127.0.0.1:8000 ..."
Write-Host "Stop karne ke liye: Ctrl + C"
Write-Host ""

.\.venv\Scripts\uvicorn.exe app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000
