$raw = $input | Out-String
try {
    $data = $raw | ConvertFrom-Json
    $cmd = $data.command
} catch {
    exit 0
}

if ($cmd -match 'git\s+(add|commit).*\.env[^.]') {
    Write-Host "⛔ .env 커밋 시도 차단됨. .env는 절대 커밋하지 마세요."
    exit 2
}

if ($cmd -match 'rm\s+-rf|--force') {
    Write-Host "⛔ 위험 명령어 감지됨: $cmd"
    Write-Host "계속하려면 사용자에게 명시적 승인을 받으세요."
    exit 2
}

exit 0
