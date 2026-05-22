# 경량 하네스 적용 설계 (harness-starter B안)

> 작성일: 2026-05-22
> 프로젝트: 인터뷰 SMS 자동 발송 (Python 3.10+ CLI)
> 참조: https://github.com/itconnect-ai/harness-starter

---

## 1. 배경 및 목적

harness-starter의 전체 하네스를 그대로 적용하는 대신, 이 프로젝트(5모듈 Python CLI 스크립트)의 규모에 맞는 컴포넌트만 선별 적용한다. GitHub Actions CI/CD, smoke 테스트, Docker 규칙, 멀티 에픽 오케스트레이션은 제외한다.

**적용 목표:**
- Claude Code가 프로젝트 규칙을 자동으로 인식하도록 설정
- `.env` 커밋 등 치명적 실수를 훅으로 차단
- 스토리 완료 시 pytest를 자동 권장하는 검증 루프 수립
- 반복 실수를 feedback-rules에 누적해 학습 루프 형성

---

## 2. 적용 컴포넌트 목록

| 컴포넌트 | 경로 | 포함 | 제외 이유 |
|---|---|---|---|
| Claude 설정 + 훅 | `.claude/settings.json` | ✅ | |
| Claude 역할 규칙 | `CLAUDE.md` | ✅ | |
| 에이전트 코딩 표준 | `AGENTS.md` | ✅ | |
| 빠른 검증 스크립트 | `validate-quick.ps1` | ✅ | |
| 보안 규칙 | `docs/agents/security.md` | ✅ | |
| 코딩 표준 규칙 | `docs/agents/coding-standards.md` | ✅ | |
| 피드백 규칙 | `docs/agents/feedback-rules.md` | ✅ | |
| GitHub Actions CI/CD | `.github/workflows/` | ❌ | 로컬 CLI 도구 — 불필요 |
| smoke 테스트 | `smoke.ps1` | ❌ | 수동 Y/N 확인 도구에 부적합 |
| Docker/DB 환경 선언 | — | ❌ | 해당 없음 |
| 멀티 에픽 오케스트레이션 | — | ❌ | 단일 에픽 |

---

## 3. 디렉터리 구조

```
playdata_test/                          ← 워크스페이스 루트
│
├── [기존] .claude/skills/              ← BMAD 스킬 (유지)
├── [기존] .agents/skills/              ← BMAD 스킬 (유지)
├── [기존] _bmad-output/                ← 기획 문서 (유지)
│
├── [신규] .claude/settings.json        ← 하네스: 권한 + 훅
├── [신규] CLAUDE.md                    ← 하네스: Claude 역할 규칙
├── [신규] AGENTS.md                    ← 하네스: 코딩 표준
│
├── [신규] docs/agents/
│   ├── security.md
│   ├── coding-standards.md
│   └── feedback-rules.md
│
├── [신규] validate-quick.ps1
│
├── [코드] main.py                      ← TRD §2 구조 그대로
├── [코드] config.py
├── [코드] notion_client.py
├── [코드] ppurio_client.py
├── [코드] logger.py
├── [코드] run.bat
├── [코드] tests/
├── [코드] logs/
├── .env                                ← gitignore
└── .env.example
```

---

## 4. `.claude/settings.json` 설계

### 4.1 허용 명령어 (자동 승인)
- `pytest tests/` — 테스트 실행
- `python main.py` — 메인 스크립트 실행
- `pip install` — 패키지 설치
- `flake8` — 린트 검사
- `git status`, `git log`, `git diff` — 읽기 전용 git

### 4.2 안전 훅 3개

**훅 1: `.env` 커밋 차단**
- 트리거: `git add` 또는 `git commit` 실행 전 (PreToolUse)
- 조건: 명령어에 `.env`가 포함된 경우
- 동작: 즉시 차단 + "⛔ .env 커밋 금지" 경고 출력

**훅 2: 검증 알림**
- 트리거: Write/Edit 도구 실행 후 (PostToolUse)
- 조건: `.py` 파일 편집 완료
- 동작: "✅ 파일 수정 완료 → `.\validate-quick.ps1` 실행을 권장합니다" 출력

**훅 3: 위험 명령 차단**
- 트리거: Bash 도구 실행 전 (PreToolUse)
- 조건: `rm -rf` 또는 `--force`가 포함된 명령어
- 동작: 차단 + 경고 출력

---

## 5. `CLAUDE.md` 설계

**프로젝트 컨텍스트:**
- 언어: Python 3.10+, 가상환경 venv
- 의존성: `requests`, `python-dotenv`, `pytest`만 허용
- 모듈: main.py, config.py, notion_client.py, ppurio_client.py, logger.py 고정

**완료 기준:**
- `pytest tests/ -v` 전체 통과 필수
- FRD §3 AC 체크리스트 항목 확인

**금지 사항:**
- `.env` 파일 직접 읽기 금지 → `.env.example`만 참조
- 뿌리오 API 엔드포인트는 플레이스홀더 유지 (TRD §12 미해결 항목)
- 모듈 추가/삭제/리팩터 금지

**고정 명세:**
- CSV 컬럼 순서: FRD §4 그대로
- KST 기준 날짜 처리 필수

---

## 6. `AGENTS.md` 설계

**코딩 표준:**
- `normalize_phone`, `dedup_by_phone`, `resolve_cohort` 시그니처 변경 금지
- 새 기수 추가: `config.py` `COHORT_SENDER_MAP`만 수정
- 예외 처리: FRD §1 예외 상태 표 기준
- 테스트 구조: `TestXxx` 클래스 + `test_xxx` 메서드 유지

**고정값:**
- API 타임아웃: 30초
- 로그 인코딩: UTF-8-BOM
- SMS 타입: `lms`

---

## 7. `validate-quick.ps1` 설계

실행 순서:
1. venv 존재 확인 → `venv\Scripts\python.exe` 또는 시스템 `python` 선택
2. `pytest tests/ -v` 실행 → 실패 시 exit 1로 즉시 중단
3. `git status --porcelain` 으로 `.env`가 staged 상태인지 검사 → 발견 시 경고
4. 전체 통과 시 `✅ 검증 완료` 출력

---

## 8. `docs/agents/` 규칙 파일 설계

### security.md
- `.env` 절대 커밋 금지, `.env.example`만 커밋
- `NOTION_TOKEN`, `PPURIO_ID`, `PPURIO_KEY`는 코드 하드코딩 금지
- `logs/*.csv`는 gitignore (수신자 개인정보 포함)
- 새 환경변수 추가 시 반드시 `.env.example`에도 추가

### coding-standards.md
- 함수 시그니처·모듈 경계 변경 금지
- 타임아웃: 노션·뿌리오 각 30초 (`API_TIMEOUT = 30`)
- 날짜: KST 기준 (`timezone(timedelta(hours=9))`)
- 중복 방지: 성공 발송 기록만 중복 대상 (실패는 재발송 가능)

### feedback-rules.md
- 초기 상태: 빈 파일 (규칙 없음)
- 구현 중 반복 실수 발견 시 규칙 추가 (최대 10개)
- 에픽 2회 동안 재발 없으면 해당 규칙 삭제

---

## 9. 구현 범위 외 (의도적 제외)

| 항목 | 이유 |
|---|---|
| GitHub Actions | 로컬 전용 CLI 도구 — CI 서버 불필요 |
| smoke.ps1 | 수동 Y/N 확인이 이미 안전장치 역할 |
| Docker 규칙 | 의존성 없음 |
| 멀티 에픽 스토리 관리 | 단일 에픽으로 충분 |
