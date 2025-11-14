# N1Hub Demo Dataset Loader (Windows PowerShell)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
$docsDir = Join-Path $scriptDir "documents"
$apiUrl = if ($env:API_URL) { $env:API_URL } else { "http://127.0.0.1:8000" }

Write-Host ">>> Loading N1Hub v0.1 Demo Dataset" -ForegroundColor Green
Write-Host "API URL: $apiUrl"
Write-Host ""

# Check if API is available
try {
    $null = Invoke-WebRequest -Uri "${apiUrl}/healthz" -UseBasicParsing -ErrorAction Stop
} catch {
    Write-Host "Warning: API not available at $apiUrl" -ForegroundColor Yellow
    Write-Host "Please start the backend first: npm run dev:stack:win"
    exit 1
}

function Upload-Document {
    param([string]$FilePath)
    
    $lines = Get-Content $FilePath
    $title = $lines[0] -replace "^Title: ", ""
    $content = ($lines[1..($lines.Count-1)] -join "`n")
    
    # Extract tags from filename
    $basename = [System.IO.Path]::GetFileNameWithoutExtension($FilePath)
    $tags = $basename -replace "-", " " | ForEach-Object { $_.ToLower() }
    $tagArray = ($tags -split " " | ForEach-Object { "`"$_`"" }) -join ", "
    
    Write-Host "Uploading: $title" -ForegroundColor Yellow
    
    $body = @{
        title = $title
        content = $content
        tags = @($tags -split " ")
        include_in_rag = $true
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "${apiUrl}/ingest" -Method Post -Body $body -ContentType "application/json"
        $jobId = $response.job_id
        if ($jobId) {
            Write-Host "  ✓ Job created: $jobId" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Upload may have failed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ⚠ Upload failed: $_" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# Upload all documents
if (-not (Test-Path $docsDir)) {
    Write-Host "Documents directory not found: $docsDir"
    exit 1
}

Write-Host "Found documents:"
Get-ChildItem "$docsDir\*.txt" | ForEach-Object {
    Write-Host "  - $($_.Name)"
}
Write-Host ""

# Upload each document
Get-ChildItem "$docsDir\*.txt" | ForEach-Object {
    Upload-Document $_.FullName
    Start-Sleep -Seconds 1  # Rate limiting consideration
}

Write-Host ">>> Demo dataset loading complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Check job status: curl ${apiUrl}/jobs"
Write-Host "  2. Wait for jobs to complete (check /inbox)"
Write-Host "  3. List capsules: curl ${apiUrl}/capsules"
Write-Host "  4. Try example queries from queries.md"
