# Phase A — 구현 프롬프트 (Codex / Claude Code)

> 이 파일의 해당 에픽 섹션을 Codex Desktop 또는 Claude Code에 그대로 붙여넣어 사용하세요.
> 순서: Epic 1 완료 후 Epic 2 진행

---

## EPIC = 1

아래 4개 기획 문서를 기반으로 Epic 1(프로젝트 초기화 및 설정 모듈)을 구현해줘.

**참조 문서:**
- `_bmad-output/implementation-artifacts/서비스정의서.md`
- `_bmad-output/implementation-artifacts/PRD.md`
- `_bmad-output/implementation-artifacts/FRD.md`
- `_bmad-output/implementation-artifacts/TRD.md`

---

### 구현 대상 파일

```
config.py
tests/__init__.py
tests/test_config.py
logs/.gitkeep
.env.example
requirements.txt
requirements-dev.txt
run.bat
README.md
```

main.py는 빈 진입점 스텁으로만 생성 (실제 로직은 Epic 2에서 완성)

### 구현 순서 (TDD)

1. `config.py` + `tests/test_config.py` → pytest 통과 확인
2. `logs/.gitkeep`, `.env.example`, `requirements.txt`, `requirements-dev.txt`, `tests/__init__.py`, `main.py`(스텁)
3. `run.bat`, `README.md`

각 단계: 테스트 먼저 작성 → 실패 확인 → 구현 → 통과 확인 → 커밋

---

### 필수 구현 조건

1. **config.py** — FRD §5 코드 그대로 (`resolve_cohort()`, `validate_config()`, `COHORT_SENDER_MAP`, `SMS_MESSAGE`)
   - `.env`에서 `NOTION_TOKEN`, `PPURIO_ID`, `PPURIO_KEY` 로드
   - 키 누락 시 `ValueError` + 키 이름 메시지
2. **tests/test_config.py** — TRD §7 `TestValidateConfig`, `TestResolveCohort`, `TestCohortSenderMap` 전체
3. **requirements.txt** — `requests==2.31.0`, `python-dotenv==1.0.1`
4. **requirements-dev.txt** — 위 두 개 + `pytest==8.1.1`
5. **run.bat** — `venv\Scripts\python.exe main.py` 실행, 오류 시 `pause`
6. **README.md** — 실행 방법, 신규 기수 추가(`COHORT_SENDER_MAP`), 발신번호 변경, 중복 발송 방지 설명

### 절대 금지

- `.env` 직접 읽기 금지
- 새 외부 패키지 추가 금지 (`requests`, `python-dotenv`, `pytest` 외)
- 모듈 추가/삭제 금지

---

### 완료 기준

```powershell
pytest tests/test_config.py -v
.\validate-quick.ps1
```

### 커밋 단위

```bash
git add config.py tests/test_config.py
git commit -m "feat: implement config module with resolve_cohort"

git add logs/.gitkeep .env.example requirements.txt requirements-dev.txt tests/__init__.py main.py
git commit -m "feat: add project skeleton and dependency files"

git add run.bat README.md
git commit -m "feat: add run.bat and README"
```

---

## EPIC = 2

아래 4개 기획 문서를 기반으로 Epic 2(핵심 발송 파이프라인)를 구현해줘.
Epic 1(config.py, 프로젝트 골격, run.bat, README)은 이미 완료된 상태임.

**참조 문서:**
- `_bmad-output/implementation-artifacts/서비스정의서.md`
- `_bmad-output/implementation-artifacts/PRD.md`
- `_bmad-output/implementation-artifacts/FRD.md`
- `_bmad-output/implementation-artifacts/TRD.md`

---

### 구현 대상 파일

```
logger.py
tests/test_logger.py
notion_client.py
tests/test_notion_client.py
ppurio_client.py
tests/test_ppurio_client.py
main.py  (Epic 1 스텁을 전체 오케스트레이션으로 완성)
```

### 구현 순서 (TDD)

1. `logger.py` + `tests/test_logger.py` → pytest 통과 확인
2. `notion_client.py` + `tests/test_notion_client.py` → pytest 통과 확인
3. `ppurio_client.py` + `tests/test_ppurio_client.py` → pytest 통과 확인
4. `main.py` (전체 플로우 통합 — 별도 테스트 없음)

각 단계: 테스트 먼저 작성 → 실패 확인 → 구현 → 통과 확인 → 커밋

---

### 필수 구현 조건

1. **logger.py** — FRD §2 그대로
   - `is_already_sent_today()`: 오늘 CSV에서 `결과=성공` 번호 확인, 실패 기록은 재발송 가능
   - CSV 인코딩: UTF-8-BOM (`utf-8-sig`)
   - 실패/매핑없음 행을 CSV 상단 배치
   - 컬럼 순서: `executed_at, name, phone, cohort, resolved_cohort, sender_number, result, error_msg`
   - `logs/` 없으면 자동 생성
2. **notion_client.py** — FRD §6 노션 API 필터 코드 그대로
   - `normalize_phone()`, `dedup_by_phone()` FRD §2 그대로
   - 각 행 `resolve_cohort()` 호출 → `resolved_cohort` 세팅
   - KST 기준 오늘 00:00~23:59 범위 필터
   - API 타임아웃 30초
3. **ppurio_client.py** — FRD §7 플레이스홀더 유지
   - `PPURIO_API_URL = "[뿌리오 API 엔드포인트 확인 후 기입]"` 반드시 유지
   - `sender=None`이면 API 호출 없이 `{"result": "매핑없음"}` 반환
   - 예외 발생 시 `{"result": "실패", "error_msg": "<오류내용>"}` 반환
   - 요청 바디: `type=lms`, `from=발신번호(하이픈 없음)`, `content=SMS_MESSAGE`
4. **main.py** — FRD §8 Y/N 확인 로직
   - `validate_config()` → 실패 시 오류 메시지 + exit code 1
   - 예정자 0명이면 "오늘 인터뷰 예정자 없습니다" 출력 후 종료
   - 미리보기: 이름, 연락처, 기수 원본값, resolved_cohort, 발신번호
   - Y 입력 시만 발송, N이면 종료
   - `is_already_sent_today` 확인 → `중복건너뜀` 처리
   - 전체 결과 `logs/YYYY-MM-DD.csv` 기록
   - `setup_logger()`: 콘솔 + `logs/app.log` 이중 로깅

### 고정값

```python
API_TIMEOUT = 30
SMS_TYPE = "lms"
LOG_DIR = "logs"
KST = timezone(timedelta(hours=9))
```

### CSV 컬럼 순서 (변경 금지)

```
executed_at, name, phone, cohort, resolved_cohort, sender_number, result, error_msg
```

### 절대 금지

- 뿌리오 API 엔드포인트 임의 구현 금지 → 플레이스홀더 유지
- `.env` 직접 읽기 금지
- 새 외부 패키지 추가 금지
- 모듈 추가/삭제 금지

---

### 완료 기준

```powershell
pytest tests/ -v
.\validate-quick.ps1
```

### 커밋 단위

```bash
git add logger.py tests/test_logger.py
git commit -m "feat: implement logger with duplicate send check"

git add notion_client.py tests/test_notion_client.py
git commit -m "feat: implement notion client with normalize and dedup"

git add ppurio_client.py tests/test_ppurio_client.py
git commit -m "feat: implement ppurio client with lms send"

git add main.py
git commit -m "feat: implement main flow with Y/N confirmation"
```
