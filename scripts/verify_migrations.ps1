# N1Hub Migration Verification Script (Windows PowerShell)

param(
    [Parameter(Mandatory=$false)]
    [string]$DatabaseUrl = $env:DATABASE_URL,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Show-Usage {
    Write-Host "Usage: .\verify_migrations.ps1 [OPTIONS]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -DatabaseUrl URL    PostgreSQL connection string (required)"
    Write-Host "  -Help               Show this help message"
    Write-Host ""
    Write-Host "Environment Variables:"
    Write-Host "  DATABASE_URL         PostgreSQL connection string (alternative to -DatabaseUrl)"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\verify_migrations.ps1 -DatabaseUrl 'postgresql://user:pass@localhost:5432/n1hub'"
    Write-Host "  `$env:DATABASE_URL='postgresql://...'; .\verify_migrations.ps1"
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
    exit 1
}
Write-Host ""

# Required tables (from all migrations)
$requiredTables = @(
    "capsules",
    "capsule_vectors",
    "links",
    "jobs",
    "artifacts",
    "query_logs",
    "validation_runs",
    "link_suggestions",
    "audit_logs"
)

# Required extensions
$requiredExtensions = @(
    "uuid-ossp",
    "vector"
)

# Check extensions
Write-Host "Checking PostgreSQL extensions..."
$missingExtensions = @()
foreach ($ext in $requiredExtensions) {
    $checkQuery = "SELECT 1 FROM pg_extension WHERE extname='$ext';"
    $result = $checkQuery | psql $DatabaseUrl -tA 2>&1
    if ($result -match "^1$") {
        Write-Host "✓ Extension installed: $ext" -ForegroundColor Green
    } else {
        Write-Host "✗ Extension missing: $ext" -ForegroundColor Red
        $missingExtensions += $ext
    }
}
Write-Host ""

# Check tables
Write-Host "Checking required tables..."
$missingTables = @()
foreach ($table in $requiredTables) {
    $checkQuery = "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='$table';"
    $result = $checkQuery | psql $DatabaseUrl -tA 2>&1
    if ($result -match "^1$") {
        # Get row count for verification
        $countQuery = "SELECT COUNT(*) FROM $table;"
        $rowCount = $countQuery | psql $DatabaseUrl -tA 2>&1
        if ($rowCount -match "^\d+$") {
            Write-Host "✓ Table exists: $table (rows: $rowCount)" -ForegroundColor Green
        } else {
            Write-Host "✓ Table exists: $table" -ForegroundColor Green
        }
    } else {
        Write-Host "✗ Table missing: $table" -ForegroundColor Red
        $missingTables += $table
    }
}
Write-Host ""

# Check indexes (critical ones)
Write-Host "Checking critical indexes..."
$criticalIndexes = @(
    "idx_capsule_vectors_capsule_id",
    "idx_links_src",
    "idx_links_dst",
    "idx_query_logs_query_hash",
    "idx_audit_logs_capsule_id"
)

$missingIndexes = @()
foreach ($idx in $criticalIndexes) {
    $checkQuery = "SELECT 1 FROM pg_indexes WHERE indexname='$idx';"
    $result = $checkQuery | psql $DatabaseUrl -tA 2>&1
    if ($result -match "^1$") {
        Write-Host "✓ Index exists: $idx" -ForegroundColor Green
    } else {
        Write-Host "⚠ Index missing: $idx (may be created automatically)" -ForegroundColor Yellow
        $missingIndexes += $idx
    }
}
Write-Host ""

# Summary
Write-Host "=========================================="
$issues = 0

if ($missingExtensions.Count -gt 0) {
    Write-Host "✗ Missing extensions:" -ForegroundColor Red
    foreach ($ext in $missingExtensions) {
        Write-Host "  - $ext"
    }
    $issues += $missingExtensions.Count
}

if ($missingTables.Count -gt 0) {
    Write-Host "✗ Missing tables:" -ForegroundColor Red
    foreach ($table in $missingTables) {
        Write-Host "  - $table"
    }
    $issues += $missingTables.Count
}

if ($issues -eq 0) {
    Write-Host "✓ All migrations verified successfully" -ForegroundColor Green
    Write-Host "Required tables: $($requiredTables.Count)"
    Write-Host "Required extensions: $($requiredExtensions.Count)"
    exit 0
} else {
    Write-Host "✗ Migration verification failed" -ForegroundColor Red
    Write-Host "Total issues found: $issues"
    Write-Host ""
    Write-Host "Run migrations with: .\scripts\migrate.ps1 -DatabaseUrl $DatabaseUrl"
    exit 1
}
