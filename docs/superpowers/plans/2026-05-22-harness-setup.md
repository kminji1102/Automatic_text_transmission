# Lightweight Harness 적용 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Python CLI 프로젝트(interview-sms)에 경량 harness를 적용해 Claude Code 권한·훅·검증 스크립트·에이전트 규칙을 세팅한다.

**Architecture:** `.claude/hooks/` 스크립트로 안전 훅을 구성하고, `.claude/settings.json`으로 권한과 훅을 Claude Code에 등록하며, `CLAUDE.md`/`AGENTS.md`로 프로젝트 규칙을 명시하고, `validate-quick.ps1`로 pytest 기반 검증 루프를 완성한다.

**Tech Stack:** PowerShell 5.1, Python 3.10+, pytest, Claude Code CLI

---

## 파일 목록

| 경로 | 동작 |
|---|---|
| `.claude/hooks/pre-bash.ps1` | 신규 생성 — Bash 실행 전 .env 커밋·위험 명령 차단 |
| `.claude/hooks/post-write.ps1` | 신규 생성 — .py 파일 편집 후 검증 권장 메시지 |
| `.claude/settings.json` | 신규 생성 — 허용 명령어 + 훅 등록 |
| `CLAUDE.md` | 신규 생성 — Claude 역할 규칙 |
| `AGENTS.md` | 신규 생성 — 코딩 표준 |
| `docs/agents/security.md` | 신규 생성 — 보안 규칙 |
| `docs/agents/coding-standards.md` | 신규 생성 — 코딩 기준 |
| `docs/agents/feedback-rules.md` | 신규 생성 — 학습 루프 (초기 빈 파일) |
| `validate-quick.ps1` | 신규 생성 — pytest + .env staged 검사 |

---

## Task 1: 훅 스크립트 생성

**Files:**
- Create: `.claude/hooks/pre-bash.ps1`
- Create: `.claude/hooks/post-write.ps1`

- [ ] **Step 1: `.claude/hooks/` 디렉터리 생성**

```powershell
New-Item -ItemType Directory -Force -Path ".claude\hooks"
```

Expected: 디렉터리 생성 또는 이미 존재 메시지

- [ ] **Step 2: `pre-bash.ps1` 생성**

파일: `.claude/hooks/pre-bash.ps1`

```powershell
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
```

- [ ] **Step 3: `post-write.ps1` 생성**

파일: `.claude/hooks/post-write.ps1`

```powershell
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
```

- [ ] **Step 4: pre-bash 차단 동작 확인 — .env 케이스**

```powershell
echo '{"command":"git add .env"}' | powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/pre-bash.ps1
echo "Exit code: $LASTEXITCODE"
```

Expected:
```
⛔ .env 커밋 시도 차단됨. .env는 절대 커밋하지 마세요.
Exit code: 2
```

- [ ] **Step 5: pre-bash 통과 동작 확인 — 일반 명령**

```powershell
echo '{"command":"pytest tests/ -v"}' | powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/pre-bash.ps1
echo "Exit code: $LASTEXITCODE"
```

Expected:
```
Exit code: 0
```

- [ ] **Step 6: 커밋**

```bash
git add .claude/hooks/pre-bash.ps1 .claude/hooks/post-write.ps1
git commit -m "feat: add claude hook scripts for safety checks"
```

---

## Task 2: `.claude/settings.json` 생성

**Files:**
- Create: `.claude/settings.json`

> `.claude/skills/`는 이미 존재하지만 `settings.json`은 없음 (사전 확인 완료).

- [ ] **Step 1: `settings.json` 생성**

파일: `.claude/settings.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(pytest*)",
      "Bash(python main.py*)",
      "Bash(python -m pytest*)",
      "Bash(pip install*)",
      "Bash(pip freeze*)",
      "Bash(flake8*)",
      "Bash(git status*)",
      "Bash(git log*)",
      "Bash(git diff*)",
      "Bash(git add*)",
      "Bash(git commit*)",
      "Bash(powershell*validate-quick*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/pre-bash.ps1"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/post-write.ps1"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: JSON 유효성 확인**

```powershell
Get-Content ".claude/settings.json" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

Expected: 파싱 오류 없이 JSON 내용 출력됨

- [ ] **Step 3: 커밋**

```bash
git add .claude/settings.json
git commit -m "feat: configure claude code permissions and hooks"
```

---

## Task 3: `CLAUDE.md` 생성

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: `CLAUDE.md` 생성**

파일: `CLAUDE.md`

```markdown
# Interview SMS — Claude Code 규칙

## 프로젝트 개요

노션 인터뷰 DB에서 당일 예정자를 조회해 뿌리오 LMS로 발송하는 Python 3.10+ CLI 스크립트.
담당자가 `python main.py`를 실행 → 목록 확인 → Y 입력 → 발송.

## 기술 스택

- 언어: Python 3.10+
- 가상환경: venv
- 의존성: `requests`, `python-dotenv` (운영), `pytest` (개발)
- 실행: `python main.py` 또는 `run.bat`

## 모듈 구조 (고정 — 추가/삭제 금지)

| 파일 | 역할 |
|---|---|
| `main.py` | 전체 흐름 실행, Y/N 발송 확인 |
| `config.py` | API 키·기수 매핑·문자 내용, `resolve_cohort()` |
| `notion_client.py` | 노션 DB 조회 + 정규화 + 기수 resolve |
| `ppurio_client.py` | 뿌리오 LMS 1건 발송 |
| `logger.py` | CSV 결과 기록 + 중복 발송 확인 |

## 완료 기준

- `pytest tests/ -v` 전체 통과 필수
- FRD §3 AC 체크리스트 항목 확인
- `.\validate-quick.ps1` PASS

## 절대 금지

- `.env` 파일 직접 읽기 금지 (`.env.example`만 참조)
- 모듈 추가/삭제/리팩터 금지 (5개 파일 고정)
- 뿌리오 API 엔드포인트 임의 추측 금지 → 플레이스홀더 `[뿌리오 API 엔드포인트 확인 후 기입]` 유지
- 새 외부 패키지 추가 금지 (`requests`, `python-dotenv`, `pytest` 외)

## 고정 명세

- CSV 컬럼 순서: `executed_at, name, phone, cohort, resolved_cohort, sender_number, result, error_msg`
- 날짜 기준: KST (`timezone(timedelta(hours=9))`)
- 로그 인코딩: UTF-8-BOM
- API 타임아웃: 30초

## 미해결 항목 (구현 금지)

- 뿌리오 API 엔드포인트: 플레이스홀더 유지
- 뿌리오 인증 방식: Basic Auth 추정 — 공식 문서 확인 전 구현 금지

## 피드백 규칙

반복 실수 발생 시 `docs/agents/feedback-rules.md`에 추가 (최대 10개).
```

- [ ] **Step 2: 커밋**

```bash
git add CLAUDE.md
git commit -m "feat: add CLAUDE.md with project rules"
```

---

## Task 4: `AGENTS.md` 생성

**Files:**
- Create: `AGENTS.md`

- [ ] **Step 1: `AGENTS.md` 생성**

파일: `AGENTS.md`

````markdown
# Interview SMS — 에이전트 코딩 표준

## 함수 시그니처 (변경 금지)

```python
# config.py
def resolve_cohort(raw_cohort: str) -> str | None: ...

# notion_client.py
def normalize_phone(raw: str) -> str | None: ...
def dedup_by_phone(interviewees: list[dict]) -> list[dict]: ...

# logger.py
def is_already_sent_today(phone: str, log_dir: str) -> bool: ...

# ppurio_client.py
def send_lms(phone: str, sender: str | None, message: str) -> dict: ...
```

## 기수 추가 방법

`config.py`의 `COHORT_SENDER_MAP`에만 추가:

```python
COHORT_SENDER_MAP = {
    "33기": "01025327302",
    "34기": "01067757302",
    "35기": "010XXXXXXXX",  # 신규 추가 예시
}
```

노션 기수 필드값에 키가 포함(contains)되어 있으면 자동 매핑됨.
`resolve_cohort()`는 포함 방식. 정확 일치(==) 사용 금지.

## 예외 처리 기준 (FRD §1)

| 상황 | 처리 |
|---|---|
| `.env` 없음 | 오류 메시지 후 exit 1 |
| 노션 API 오류 | raise → main에서 CSV 기록 후 exit 1 |
| 연락처 형식 오류 | `형식오류` 표시, 다음 건 진행 |
| 기수 매핑 실패 | `결과=매핑없음`, 다음 건 진행 |
| 오늘 이미 성공 발송 | `결과=중복건너뜀`, 발송 제외 |

## 테스트 구조 (TRD §7 유지)

```python
class TestFeatureName:           # TestXxx 클래스 필수
    def test_specific_case(self):    # test_xxx 메서드
        ...
```

## 고정값

```python
API_TIMEOUT = 30                      # 노션·뿌리오 공통
SMS_TYPE    = "lms"                   # 변경 금지
LOG_DIR     = "logs"                  # 변경 금지
KST         = timezone(timedelta(hours=9))  # 날짜 처리 기준
```
````

- [ ] **Step 2: 커밋**

```bash
git add AGENTS.md
git commit -m "feat: add AGENTS.md with coding standards"
```

---

## Task 5: `docs/agents/` 규칙 파일 생성

**Files:**
- Create: `docs/agents/security.md`
- Create: `docs/agents/coding-standards.md`
- Create: `docs/agents/feedback-rules.md`

- [ ] **Step 1: `docs/agents/` 디렉터리 생성**

```powershell
New-Item -ItemType Directory -Force -Path "docs\agents"
```

Expected: 디렉터리 생성 또는 이미 존재 메시지

- [ ] **Step 2: `security.md` 생성**

파일: `docs/agents/security.md`

```markdown
# 보안 규칙

## 절대 금지

- `.env` 커밋 금지 — `.gitignore`에 반드시 포함
- `NOTION_TOKEN`, `PPURIO_ID`, `PPURIO_KEY`를 코드에 하드코딩 금지
- `logs/*.csv` 커밋 금지 — 수신자 개인정보(이름, 전화번호) 포함

## 필수 사항

- 새 환경변수 추가 시 `.env.example`에도 반드시 추가
- `.gitignore` 필수 항목:

  ```
  .env
  logs/*.csv
  logs/*.log
  venv/
  __pycache__/
  *.py[cod]
  .pytest_cache/
  ```
```

- [ ] **Step 3: `coding-standards.md` 생성**

파일: `docs/agents/coding-standards.md`

```markdown
# 코딩 표준

## 절대 변경 금지

- 5개 모듈 외 파일 추가/삭제 금지
- 함수 시그니처 변경 금지 (AGENTS.md 참조)
- CSV 컬럼 순서 변경 금지

## 타임아웃

노션·뿌리오 API 모두 `API_TIMEOUT = 30` 적용.

```python
response = requests.post(url, ..., timeout=API_TIMEOUT)
```

## 날짜 처리

KST 기준 필수. UTC 직접 사용 금지.

```python
from datetime import datetime, timedelta, timezone
KST = timezone(timedelta(hours=9))
now_kst = datetime.now(KST)
```

## 중복 방지 로직

`result == "성공"` 기록만 중복 대상. 실패 기록은 재발송 가능.

## 기수 매핑

`resolve_cohort()`는 포함(contains) 방식. 정확 일치(==) 사용 금지.
```

- [ ] **Step 4: `feedback-rules.md` 생성**

파일: `docs/agents/feedback-rules.md`

```markdown
# 피드백 규칙

> 최대 10개 유지. 에픽 2회 동안 재발 없으면 삭제.

## 활성 규칙

(없음 — 구현 시작 전)
```

- [ ] **Step 5: 커밋**

```bash
git add docs/agents/security.md docs/agents/coding-standards.md docs/agents/feedback-rules.md
git commit -m "feat: add agent rules (security, coding-standards, feedback)"
```

---

## Task 6: `validate-quick.ps1` 생성

**Files:**
- Create: `validate-quick.ps1`

- [ ] **Step 1: `validate-quick.ps1` 생성**

파일: `validate-quick.ps1`

```powershell
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
```

- [ ] **Step 2: 스크립트 실행 확인 (tests/ 없어도 에러 없이 실행되는지)**

```powershell
powershell -ExecutionPolicy Bypass -File .\validate-quick.ps1
```

Expected: 스크립트 자체는 실행됨. tests/ 폴더가 없으면 pytest가 "no tests ran" 또는 실패로 종료 — 이는 정상 (코드 구현 후 통과 예정).

- [ ] **Step 3: 커밋**

```bash
git add validate-quick.ps1
git commit -m "feat: add validate-quick.ps1 for story completion checks"
```

---

## Task 7: 통합 검증

- [ ] **Step 1: 전체 하네스 파일 존재 확인**

```powershell
$files = @(
    ".claude/settings.json",
    ".claude/hooks/pre-bash.ps1",
    ".claude/hooks/post-write.ps1",
    "CLAUDE.md",
    "AGENTS.md",
    "docs/agents/security.md",
    "docs/agents/coding-standards.md",
    "docs/agents/feedback-rules.md",
    "validate-quick.ps1"
)
$allOk = $true
foreach ($f in $files) {
    if (Test-Path $f) {
        Write-Host "✓ $f" -ForegroundColor Green
    } else {
        Write-Host "❌ 없음: $f" -ForegroundColor Red
        $allOk = $false
    }
}
if ($allOk) { Write-Host "`n✅ 모든 하네스 파일 확인 완료" -ForegroundColor Green }
else { Write-Host "`n❌ 누락 파일 있음" -ForegroundColor Red; exit 1 }
```

Expected: 전체 `✓` 출력 후 `✅ 모든 하네스 파일 확인 완료`

- [ ] **Step 2: pre-bash 훅 차단 기능 최종 확인**

```powershell
echo '{"command":"git add .env"}' | powershell -NoProfile -ExecutionPolicy Bypass -File .claude/hooks/pre-bash.ps1
echo "Exit code: $LASTEXITCODE"
```

Expected:
```
⛔ .env 커밋 시도 차단됨. .env는 절대 커밋하지 마세요.
Exit code: 2
```

- [ ] **Step 3: 커밋 이력 확인**

```bash
git log --oneline -10
```

Expected: Task 1~6에서 생성한 커밋 6개 이상 확인

---

## 셀프 리뷰 체크리스트

- [x] **스펙 커버리지**: 설계 섹션 1~4 전체 구현됨 (훅 3개, settings.json, CLAUDE.md, AGENTS.md, docs/agents/ 3파일, validate-quick.ps1)
- [x] **플레이스홀더 없음**: TBD/TODO 없음
- [x] **타입 일관성**: pre-bash.ps1의 `$data.command` 참조가 settings.json의 Bash matcher와 일치
- [x] **제외 항목 확인**: CI/CD, smoke 테스트, Docker 규칙 — 의도적 제외 (설계 섹션 2 승인)
