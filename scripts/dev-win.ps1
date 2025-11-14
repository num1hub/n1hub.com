Param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$engineDir = Join-Path $repoRoot "apps\engine"
$venvDir = Join-Path $engineDir ".venv"

Write-Host ">>> N1Hub dev bootstrap (Windows PowerShell)" -ForegroundColor Cyan

if (-not (Test-Path $venvDir)) {
    Write-Host "Creating Python virtual environment at $venvDir" -ForegroundColor DarkGray
    & $Python "-m" "venv" $venvDir
}

$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip = Join-Path $venvDir "Scripts\pip.exe"

Write-Host "Upgrading pip + installing engine dependencies (editable + dev extras)" -ForegroundColor DarkGray
& $venvPython "-m" "pip" "install" "--upgrade" "pip" | Out-Null
& $venvPip "install" "-e" "$engineDir[dev]"

Write-Host "Starting data services via docker compose..." -ForegroundColor DarkGray
Push-Location (Join-Path $repoRoot "infra")
docker compose up -d | Out-Null
Pop-Location

Write-Host ""
Write-Host "CapsuleStore Postgres:`tpostgres://postgres:postgres@localhost:5432/n1hub"
Write-Host "Redis events:`t`tredis://localhost:6379/0"
Write-Host "FastAPI Engine:`thttp://127.0.0.1:8000"
Write-Host "Interface:`t`tRun 'pnpm dev' (root app) in another terminal."
Write-Host ""
Write-Host "Starting Uvicorn (Ctrl+C to stop)..." -ForegroundColor Cyan

Set-Location $engineDir
& $venvPython "-m" "uvicorn" "app.main:app" "--host" "0.0.0.0" "--port" "8000" "--reload"
