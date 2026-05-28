Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== validate-quick start ===" -ForegroundColor Cyan

# Step 1: Resolve Python executable
if (Test-Path "venv\Scripts\python.exe") {
    $python = "venv\Scripts\python.exe"
    Write-Host "OK: venv detected" -ForegroundColor Green
} else {
    $python = "python"
    Write-Host "WARN: venv not found; using system Python" -ForegroundColor Yellow
}

# Step 2: Run pytest
Write-Host ""
Write-Host "--- pytest tests/ -v ---" -ForegroundColor Cyan
& $python -m pytest tests/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "FAIL: tests failed; validation stopped" -ForegroundColor Red
    exit 1
}
Write-Host "OK: all tests passed" -ForegroundColor Green

# Step 3: Check .env is not staged
Write-Host ""
Write-Host "--- .env staged check ---" -ForegroundColor Cyan
$staged = git status --porcelain 2>$null
if ($staged -match '^\S+ .env$') {
    Write-Host "FAIL: .env is staged!" -ForegroundColor Red
    Write-Host "Run: git restore --staged .env"
    exit 1
}
Write-Host "OK: .env is not staged" -ForegroundColor Green

Write-Host ""
Write-Host "OK: validation complete" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Cyan
exit 0
