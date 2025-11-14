# N1Hub Database Migration Runner (Windows PowerShell)

param(
    [Parameter(Mandatory=$false)]
    [string]$DatabaseUrl = $env:DATABASE_URL,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$sqlDir = Join-Path $repoRoot "infra\sql"

function Show-Usage {
    Write-Host "Usage: .\migrate.ps1 [OPTIONS]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -DatabaseUrl URL    PostgreSQL connection string (required)"
    Write-Host "  -DryRun             Show what would be executed without running"
    Write-Host "  -Help               Show this help message"
    Write-Host ""
    Write-Host "Environment Variables:"
    Write-Host "  DATABASE_URL         PostgreSQL connection string (alternative to -DatabaseUrl)"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\migrate.ps1 -DatabaseUrl 'postgresql://user:pass@localhost:5432/n1hub'"
    Write-Host "  `$env:DATABASE_URL='postgresql://...'; .\migrate.ps1"
    Write-Host "  .\migrate.ps1 -DryRun -DatabaseUrl 'postgresql://...'"
    exit 1
}

if ($Help) {
    Show-Usage
}

if ([string]::IsNullOrEmpty($DatabaseUrl)) {
    Write-Host "Error: DATABASE_URL is required" -ForegroundColor Red
    Write-Host "Use -DatabaseUrl or set DATABASE_URL environment variable"
    Show-Usage
}

# Migration files in order
$migrations = @(
    "0001_capsule_store.sql",
    "0002_validation_and_links.sql",
    "0003_audit_logs.sql"
)

Write-Host ">>> N1Hub Database Migration Runner" -ForegroundColor Green
$dbDisplay = $DatabaseUrl -replace ':[^:@]+@', ':***@'
Write-Host "Database: $dbDisplay"
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Would execute the following migrations:" -ForegroundColor Yellow
    foreach ($migration in $migrations) {
        $migrationPath = Join-Path $sqlDir $migration
        if (Test-Path $migrationPath) {
            Write-Host "  - $migration"
        } else {
            Write-Host "  - $migration (NOT FOUND)" -ForegroundColor Red
        }
    }
    exit 0
}

# Check if psql is available
try {
    $null = Get-Command psql -ErrorAction Stop
} catch {
    Write-Host "Error: psql command not found. Please install PostgreSQL client tools." -ForegroundColor Red
    Write-Host "Download from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    exit 1
}

# Test database connection
Write-Host "Testing database connection..."
try {
    $testQuery = "SELECT 1;" | psql $DatabaseUrl 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Connection failed"
    }
    Write-Host "✓ Database connection successful" -ForegroundColor Green
} catch {
    Write-Host "Error: Failed to connect to database" -ForegroundColor Red
    Write-Host "Please check your DATABASE_URL and ensure the database is accessible"
    exit 1
}
Write-Host ""

# Run migrations
$successCount = 0
$failedMigrations = @()

foreach ($migration in $migrations) {
    $migrationPath = Join-Path $sqlDir $migration
    
    if (-not (Test-Path $migrationPath)) {
        Write-Host "✗ Migration file not found: $migration" -ForegroundColor Red
        $failedMigrations += $migration
        continue
    }
    
    Write-Host "Running migration: $migration" -ForegroundColor Yellow
    
    try {
        Get-Content $migrationPath | psql $DatabaseUrl 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Migration completed: $migration" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "✗ Migration failed: $migration" -ForegroundColor Red
            $failedMigrations += $migration
            # Show error details
            Get-Content $migrationPath | psql $DatabaseUrl 2>&1 | Select-Object -Last 5
        }
    } catch {
        Write-Host "✗ Migration failed: $migration" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        $failedMigrations += $migration
    }
    Write-Host ""
}

# Summary
Write-Host "=========================================="
if ($failedMigrations.Count -eq 0) {
    Write-Host "✓ All migrations completed successfully" -ForegroundColor Green
    Write-Host "Total migrations: $($migrations.Count)"
    exit 0
} else {
    Write-Host "✗ Some migrations failed" -ForegroundColor Red
    Write-Host "Successful: $successCount / $($migrations.Count)"
    Write-Host "Failed migrations:"
    foreach ($failed in $failedMigrations) {
        Write-Host "  - $failed"
    }
    exit 1
}
