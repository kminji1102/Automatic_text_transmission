# Phase B — 코드 리뷰 프롬프트 (Claude Code)

> Phase A 구현 완료 + `.\validate-quick.ps1` PASS 확인 후 해당 에픽 섹션을 사용하세요.
> 순서: Epic 1 완료 후 Epic 2 진행

---

## EPIC = 1

Epic 1 구현 완료 + `.\validate-quick.ps1` PASS 확인 후 아래를 진행해줘.

`bmad-code-review` 스킬을 사용해서 Epic 1 코드를 리뷰해줘.

**리뷰 대상 파일:**
- `config.py`
- `tests/test_config.py`
- `.env.example`
- `requirements.txt`
- `requirements-dev.txt`
- `run.bat`
- `README.md`

---

### 리뷰 체크포인트

**1. FRD AC 준수**

- [ ] `validate_config()`: 키 누락 시 `ValueError`, 키 이름 메시지 포함
- [ ] `resolve_cohort("SFAC 33기")` → `"33기"` (contains 방식)
- [ ] `resolve_cohort("35기 지원자")` → `None`
- [ ] `resolve_cohort("")` 및 `None` 입력 → `None`
- [ ] `.env.example`: `NOTION_TOKEN`, `PPURIO_ID`, `PPURIO_KEY` 3개 키 + 주석
- [ ] `requirements.txt`: `requests==2.31.0`, `python-dotenv==1.0.1`
- [ ] `requirements-dev.txt`: 위 두 개 + `pytest==8.1.1`
- [ ] `run.bat`: `venv\Scripts\python.exe main.py` + `pause`
- [ ] `README.md`: 신규 기수 추가(`COHORT_SENDER_MAP`), 발신번호 변경, 중복 발송 방지 포함

**2. 보안 (`docs/agents/security.md`)**

- `.env` 직접 읽기 없음 (python-dotenv 사용)
- API 키 코드 하드코딩 없음

**3. 테스트 커버리지**

- `TestValidateConfig`, `TestResolveCohort`, `TestCohortSenderMap` 전체 케이스 구현
- 엣지 케이스 (None, 빈 문자열) 포함

**4. 코딩 표준 (`docs/agents/coding-standards.md`)**

- 함수 시그니처 일치, 타입 힌트

---

### 리뷰 결과 처리

REJECTED 항목 수정 후:

```bash
git add <수정된 파일>
git commit -m "fix: <수정 내용>"
```

```powershell
.\validate-quick.ps1
```

### 완료 기준

- REJECTED 항목 0개
- `pytest tests/test_config.py -v` 전체 PASS
- `.\validate-quick.ps1` PASS

완료 후 `docs/agents/feedback-rules.md` 반복 패턴 발견 시 추가.

---

## EPIC = 2

Epic 2 구현 완료 + `.\validate-quick.ps1` PASS 확인 후 아래를 진행해줘.

`bmad-code-review` 스킬을 사용해서 Epic 2 코드를 리뷰해줘.

**리뷰 대상 파일:**
- `logger.py` / `tests/test_logger.py`
- `notion_client.py` / `tests/test_notion_client.py`
- `ppurio_client.py` / `tests/test_ppurio_client.py`
- `main.py`

---

### 리뷰 체크포인트

**1. FRD AC 준수 여부 (FRD §3 전체)**

- [ ] M-001: `.env` 없을 때 1초 이내 오류 출력 후 종료 (exit code 1)
- [ ] M-001: 예정자 0명이면 "오늘 인터뷰 예정자 없습니다" 출력 후 종료
- [ ] M-001: N 입력 시 발송 없이 종료
- [ ] M-001: 정상 실행 시 60초 이내 완료
- [ ] M-003: KST 00:00~23:59 범위 예정자만 반환
- [ ] M-003: `+82-10-1234-5678` → `01012345678` 정규화
- [ ] M-003: `031-123-4567`은 `형식오류` 처리
- [ ] M-003: 동일 연락처 2건이면 1건만 발송
- [ ] M-003: `"플레이데이터 34기"` → `resolved_cohort="34기"` (contains 방식)
- [ ] M-003: 알려진 키워드 없으면 `resolved_cohort=None` → `매핑없음`
- [ ] M-004: `sender=None`이면 API 호출 없이 `결과=매핑없음` 반환
- [ ] M-004: API 타임아웃 30초 후 `결과=실패` 반환
- [ ] M-004: `PPURIO_API_URL` 플레이스홀더 유지
- [ ] M-005: 오늘 성공 발송된 번호는 `중복건너뜀`
- [ ] M-005: 실패 기록은 중복 대상 아님 (재발송 가능)
- [ ] M-005: `logs/` 없으면 자동 생성
- [ ] M-005: CSV 인코딩 UTF-8-BOM
- [ ] M-005: `cohort`와 `resolved_cohort` 분리 컬럼
- [ ] M-005: 실패/매핑없음 행 CSV 상단 배치

**2. 보안 (`docs/agents/security.md`)**

- 자격증명 `.env`에서만 로드
- `logs/*.csv` 개인정보 노출 범위 적절한지

**3. 테스트 커버리지**

- `TestIsAlreadySentToday`, `TestNormalizePhone`, `TestDedupByPhone`, `TestSendLms` 전체 케이스
- 엣지 케이스 (None, 빈 리스트, 타임아웃) 포함

**4. 코딩 표준 (`docs/agents/coding-standards.md`)**

- `API_TIMEOUT = 30` 일관 적용
- KST 기준 날짜 처리
- CSV 컬럼 순서: `executed_at, name, phone, cohort, resolved_cohort, sender_number, result, error_msg`

---

### 리뷰 결과 처리

REJECTED 항목 수정 후:

```bash
git add <수정된 파일>
git commit -m "fix: <수정 내용>"
```

```powershell
.\validate-quick.ps1
```

### 완료 기준

- REJECTED 항목 0개
- `pytest tests/ -v` 전체 PASS
- `.\validate-quick.ps1` PASS

완료 후 `docs/agents/feedback-rules.md` 반복 패턴 발견 시 규칙 추가.
