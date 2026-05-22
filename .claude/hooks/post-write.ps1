$raw = $input | Out-String
try {
    $data = $raw | ConvertFrom-Json
    $path = $data.file_path
} catch {
    exit 0
}

if ($path -match '\.py$') {
    Write-Host ""
    Write-Host "💡 .py 파일 수정 완료 → .\validate-quick.ps1 실행을 권장합니다"
}
exit 0
