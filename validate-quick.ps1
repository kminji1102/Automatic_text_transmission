Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== validate-quick 시작 ===" -ForegroundColor Cyan

# Step 1: Python 실행 경로 결정
if (Test-Path "venv\Scripts\python.exe") {
    $python = "venv\Scripts\python.exe"
    Write-Host "✓ venv 감지됨" -ForegroundColor Green
} else {
    $python = "python"
    Write-Host "⚠ venv 없음 — 시스템 Python 사용" -ForegroundColor Yellow
}

# Step 2: pytest 실행
Write-Host ""
Write-Host "--- pytest tests/ -v ---" -ForegroundColor Cyan
& $python -m pytest tests/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 테스트 실패 — 검증 중단" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 테스트 전체 통과" -ForegroundColor Green

# Step 3: .env staged 검사
Write-Host ""
Write-Host "--- .env staged 검사 ---" -ForegroundColor Cyan
$staged = git status --porcelain 2>$null
if ($staged -match '^\S+ .env$') {
    Write-Host "⛔ 경고: .env가 git staging에 포함되어 있습니다!" -ForegroundColor Red
    Write-Host "   git restore --staged .env 로 해제하세요."
    exit 1
}
Write-Host "✓ .env staging 없음" -ForegroundColor Green

# 완료
Write-Host ""
Write-Host "✅ 검증 완료" -ForegroundColor Green
Write-Host "==========================" -ForegroundColor Cyan
exit 0
