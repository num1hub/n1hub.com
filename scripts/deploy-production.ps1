# N1Hub Production Deployment Orchestration Script (Windows PowerShell)

param(
    [Parameter(Mandatory=$false)]
    [string]$DatabaseUrl = $env:DATABASE_URL,
    
    [Parameter(Mandatory=$false)]
    [string]$BackendUrl = $env:BACKEND_URL,
    
    [Parameter(Mandatory=$false)]
    [string]$FrontendUrl = $env:FRONTEND_URL,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipMigrations,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipValidation,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")

function Show-Usage {
    Write-Host "Usage: .\deploy-production.ps1 [OPTIONS]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -DatabaseUrl URL      PostgreSQL connection string (required)"
    Write-Host "  -BackendUrl URL        Backend API URL (for verification)"
    Write-Host "  -FrontendUrl URL       Frontend URL (for verification)"
    Write-Host "  -SkipMigrations        Skip database migrations"
    Write-Host "  -SkipValidation        Skip environment validation"
    Write-Host "  -Help                  Show this help message"
    Write-Host ""
    Write-Host "Environment Variables:"
    Write-Host "  DATABASE_URL           PostgreSQL connection string"
    Write-Host "  BACKEND_URL            Backend API URL"
    Write-Host "  FRONTEND_URL           Frontend URL"
    exit 1
}

if ($Help) {
    Show-Usage
}

Write-Host "========================================" -ForegroundColor Blue
Write-Host "N1Hub v0.1 Production Deployment" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Step 1: Environment Validation
if (-not $SkipValidation) {
    Write-Host "Step 1: Validating environment..." -ForegroundColor Yellow
    if ([string]::IsNullOrEmpty($DatabaseUrl)) {
        Write-Host "Error: DATABASE_URL is required" -ForegroundColor Red
        Show-Usage
    }
    
    # Validate backend environment
    $validationOutput = python "${scriptDir}\validate_env.py" --target backend 2>&1
    if ($validationOutput -match "Validation PASSED") {
        Write-Host "✓ Environment validation passed" -ForegroundColor Green
    } else {
        Write-Host "Backend environment validation failed" -ForegroundColor Red
        Write-Host $validationOutput
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "Skipping environment validation" -ForegroundColor Yellow
    Write-Host ""
}

# Step 2: Database Migrations
if (-not $SkipMigrations) {
    Write-Host "Step 2: Running database migrations..." -ForegroundColor Yellow
    & "${scriptDir}\migrate.ps1" -DatabaseUrl $DatabaseUrl
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Migration failed" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    
    # Verify migrations
    Write-Host "Step 3: Verifying migrations..." -ForegroundColor Yellow
    & "${scriptDir}\verify_migrations.ps1" -DatabaseUrl $DatabaseUrl
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Migration verification failed" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "Skipping database migrations" -ForegroundColor Yellow
    Write-Host ""
}

# Step 4: Backend Health Check
if (-not [string]::IsNullOrEmpty($BackendUrl)) {
    Write-Host "Step 4: Checking backend health..." -ForegroundColor Yellow
    try {
        $healthResponse = Invoke-WebRequest -Uri "${BackendUrl}/healthz" -UseBasicParsing -ErrorAction Stop
        $healthJson = $healthResponse.Content | ConvertFrom-Json
        if ($healthJson.status -eq "ok") {
            Write-Host "✓ Backend is healthy" -ForegroundColor Green
        } else {
            Write-Host "⚠ Backend health check returned: $($healthJson.status)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "✗ Backend health check failed: $_" -ForegroundColor Red
        Write-Host "  URL: ${BackendUrl}/healthz"
    }
    Write-Host ""
}

# Step 5: Frontend Check
if (-not [string]::IsNullOrEmpty($FrontendUrl)) {
    Write-Host "Step 5: Checking frontend..." -ForegroundColor Yellow
    try {
        $frontendResponse = Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing -ErrorAction Stop
        if ($frontendResponse.StatusCode -eq 200) {
            Write-Host "✓ Frontend is accessible" -ForegroundColor Green
        } else {
            Write-Host "⚠ Frontend returned HTTP $($frontendResponse.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠ Frontend check failed: $_" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Deployment orchestration complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Verify backend: curl $($BackendUrl ?? '<backend-url>')/healthz"
if (-not [string]::IsNullOrEmpty($FrontendUrl)) {
    Write-Host "  2. Visit frontend: $FrontendUrl"
}
Write-Host "  3. Run end-to-end tests"
Write-Host "  4. Monitor observability endpoints"
