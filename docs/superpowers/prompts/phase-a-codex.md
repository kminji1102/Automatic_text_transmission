# Phase A — 구현 프롬프트 (Codex / Claude Code)

> 이 파일의 내용을 Codex Desktop 또는 Claude Code에 그대로 붙여넣어 사용하세요.

---

## 프롬프트

아래 4개 기획 문서를 기반으로 인터뷰 SMS 자동 발송 Python 스크립트를 완전히 구현해줘.

**참조 문서:**
- `_bmad-output/implementation-artifacts/서비스정의서.md`
- `_bmad-output/implementation-artifacts/PRD.md`
- `_bmad-output/implementation-artifacts/FRD.md`
- `_bmad-output/implementation-artifacts/TRD.md`

---

### 구현 규칙 (반드시 준수)

**파일 구조 (TRD §2 고정)**

```
main.py
config.py
notion_client.py
ppurio_client.py
logger.py
run.bat
tests/__init__.py
tests/test_config.py
tests/test_notion_client.py
tests/test_ppurio_client.py
tests/test_logger.py
logs/.gitkeep
.env.example
requirements.txt
requirements-dev.txt
```

**구현 순서 (TDD — 이 순서대로 진행)**

1. `config.py` + `tests/test_config.py`
2. `notion_client.py` + `tests/test_notion_client.py`
3. `logger.py` + `tests/test_logger.py`
4. `ppurio_client.py` + `tests/test_ppurio_client.py`
5. `main.py` (테스트 없음 — 통합 진입점)
6. `run.bat`, `.env.example`, `requirements.txt`, `requirements-dev.txt`

각 모듈마다: 테스트 먼저 작성 → 실행해서 실패 확인 → 구현 → 테스트 통과 확인 → 커밋

---

### 필수 구현 조건

1. **config.py** — FRD §5 코드 그대로 사용 (`resolve_cohort()` 포함)
2. **notion_client.py** — FRD §6 노션 API 필터 코드 그대로 사용
   - 각 행마다 `resolve_cohort()` 호출해 `resolved_cohort` 필드 세팅
   - `normalize_phone()`, `dedup_by_phone()` FRD §2 그대로 구현
3. **logger.py** — `is_already_sent_today()` FRD §2 그대로 구현
   - CSV 인코딩: UTF-8-BOM
   - 실패/매핑없음 행을 CSV 상단에 위치
   - `cohort`(원본값)와 `resolved_cohort`(매핑키) 분리 컬럼
4. **ppurio_client.py** — FRD §7 플레이스홀더 유지
   - `sender=None`이면 `결과=매핑없음` 반환
   - API 타임아웃 30초
5. **main.py** — FRD §8 Y/N 발송 확인 로직
   - 노션 조회는 자동, 발송은 Y 입력해야만 실행
   - 예정자 0명이면 "오늘 인터뷰 예정자 없습니다" 출력 후 종료
6. **테스트** — TRD §7 전체 코드 그대로 사용

---

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

- 뿌리오 API 엔드포인트 임의 구현 금지 → `[뿌리오 API 엔드포인트 확인 후 기입]` 플레이스홀더 유지
- `.env` 직접 읽기 금지
- 새 외부 패키지 추가 금지 (`requests`, `python-dotenv`, `pytest` 외)
- 모듈 추가/삭제 금지

---

### 완료 기준

모든 구현 완료 후 아래를 실행해서 전체 통과해야 함:

```powershell
.\validate-quick.ps1
```

FRD §3 AC 체크리스트 항목도 직접 확인할 것.

---

### 커밋 단위 (모듈별로 커밋)

```bash
git add config.py tests/test_config.py
git commit -m "feat: implement config module with resolve_cohort"

git add notion_client.py tests/test_notion_client.py
git commit -m "feat: implement notion client with normalize and dedup"

git add logger.py tests/test_logger.py
git commit -m "feat: implement logger with duplicate send check"

git add ppurio_client.py tests/test_ppurio_client.py
git commit -m "feat: implement ppurio client with lms send"

git add main.py run.bat .env.example requirements.txt requirements-dev.txt logs/.gitkeep tests/__init__.py
git commit -m "feat: implement main flow with Y/N confirmation"
```
