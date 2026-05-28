# 인터뷰 SMS 자동 발송 TRD v4.0 — Claude Code 입력용 핸드오프 팩

> 작성일: 2026-05-22
> 버전: v4.0
> 변경 이유:
> - `resolve_cohort()` 테스트 추가 (포함 방식 매핑 검증)
> - CSV 컬럼에 `resolved_cohort` 추가
> - "노션 자동 조회 + 수동 발송 확인" 구조 테스트 반영

---

## §1. 기술 결정 전체 요약

| 항목 | 결정값 | 비고 |
|---|---|---|
| 언어 | Python 3.10 이상 | |
| 가상환경 | venv (Python 내장) | |
| 운영 패키지 | `requests`, `python-dotenv` (버전 고정) | |
| 개발 패키지 | `pytest` (버전 고정) | |
| 스케줄러 | 없음 (1단계) | 2단계로 미룸 |
| 실행 방식 | 터미널 `python main.py` 또는 `run.bat` 더블클릭 | |
| 발송 확인 | 터미널 Y/N 입력 (노션 조회는 자동, 발송은 수동 확인) | |
| 기수 매핑 방식 | 포함(contains) — `resolve_cohort()` | |
| 외부 API | 노션 API v1, 뿌리오 REST API (LMS) | |
| 외부 자동화 툴 | 사용 안 함 | |
| 총 추가 비용 | 0원 (뿌리오 크레딧 제외) | |

---

## §2. 최종 프로젝트 디렉터리 구조

```
interview-sms/
├── main.py
├── config.py                    ← resolve_cohort() 포함
├── notion_client.py
├── ppurio_client.py
├── logger.py
├── run.bat
│
├── tests/
│   ├── __init__.py
│   ├── test_notion_client.py    ← normalize_phone, dedup_by_phone
│   ├── test_config.py           ← validate_config, resolve_cohort, COHORT_SENDER_MAP
│   ├── test_ppurio_client.py    ← 매핑 누락 처리, API 오류 처리
│   └── test_logger.py           ← is_already_sent_today
│
├── logs/
│   ├── .gitkeep
│   ├── app.log
│   └── YYYY-MM-DD.csv
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## §3. run.bat

```batch
@echo off
cd /d "%~dp0"
venv\Scripts\python.exe main.py
if %errorlevel% neq 0 (
    echo [오류] main.py 실행 실패. exit code: %errorlevel%
    pause
)
```

---

## §4. .gitignore

```gitignore
.env
logs/*.csv
logs/*.log
venv/
__pycache__/
*.py[cod]
*$py.class
*.pyo
.pytest_cache/
.coverage
.vscode/
.idea/
*.swp
```

---

## §5. requirements.txt / requirements-dev.txt

**requirements.txt**
```
certifi==2024.2.2
charset-normalizer==3.3.2
idna==3.7
python-dotenv==1.0.1
requests==2.31.0
urllib3==2.2.1
```

**requirements-dev.txt**
```
-r requirements.txt
iniconfig==2.0.0
packaging==24.0
pluggy==1.5.0
pytest==8.1.1
```

---

## §6. logging 설정 코드

```python
import logging, os
LOG_DIR = "logs"

def setup_logger(name: str = "interview_sms") -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    fh = logging.FileHandler(os.path.join(LOG_DIR, "app.log"), encoding="utf-8", mode="a")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

logger = setup_logger()
```

---

## §7. pytest 테스트 코드 전체

```python
# tests/test_notion_client.py
import pytest
from notion_client import normalize_phone, dedup_by_phone


class TestNormalizePhone:
    def test_hyphen_format(self):
        assert normalize_phone("010-1234-5678") == "01012345678"

    def test_no_hyphen(self):
        assert normalize_phone("01012345678") == "01012345678"

    def test_space_format(self):
        assert normalize_phone("010 1234 5678") == "01012345678"

    def test_plus82_format(self):
        assert normalize_phone("+82-10-1234-5678") == "01012345678"

    def test_invalid_local_number(self):
        assert normalize_phone("031-123-4567") is None

    def test_short_number(self):
        assert normalize_phone("0101234567") is None

    def test_empty_string(self):
        assert normalize_phone("") is None

    def test_none_input(self):
        assert normalize_phone(None) is None


class TestDedupByPhone:
    def test_removes_duplicate(self):
        data = [
            {"name": "홍길동", "phone": "01012345678", "cohort": "SFAC 33기"},
            {"name": "홍길동2", "phone": "01012345678", "cohort": "SFAC 33기"},
        ]
        result = dedup_by_phone(data)
        assert len(result) == 1
        assert result[0]["name"] == "홍길동"

    def test_keeps_unique(self):
        data = [
            {"name": "홍길동", "phone": "01012345678", "cohort": "SFAC 33기"},
            {"name": "김철수", "phone": "01098765432", "cohort": "플레이데이터 34기"},
        ]
        assert len(dedup_by_phone(data)) == 2

    def test_empty_list(self):
        assert dedup_by_phone([]) == []


# tests/test_config.py
import pytest
from config import validate_config, resolve_cohort, COHORT_SENDER_MAP


class TestValidateConfig:
    def test_raises_on_missing_notion_token(self, monkeypatch):
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        with pytest.raises(ValueError, match="NOTION_TOKEN"):
            validate_config()

    def test_raises_on_missing_ppurio_id(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "token")
        monkeypatch.delenv("PPURIO_ID", raising=False)
        with pytest.raises(ValueError, match="PPURIO_ID"):
            validate_config()

    def test_raises_on_missing_ppurio_key(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "token")
        monkeypatch.setenv("PPURIO_ID", "id")
        monkeypatch.delenv("PPURIO_KEY", raising=False)
        with pytest.raises(ValueError, match="PPURIO_KEY"):
            validate_config()

    def test_passes_when_all_keys_present(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "token")
        monkeypatch.setenv("PPURIO_ID", "id")
        monkeypatch.setenv("PPURIO_KEY", "key")
        validate_config()


class TestResolveCohort:
    """기수 포함(contains) 방식 매핑 검증"""

    def test_exact_match(self):
        assert resolve_cohort("33기") == "33기"

    def test_prefix_text(self):
        assert resolve_cohort("SFAC 33기") == "33기"

    def test_suffix_text(self):
        assert resolve_cohort("33기 수강생") == "33기"

    def test_embedded_text(self):
        assert resolve_cohort("플레이데이터 34기 수강생") == "34기"

    def test_unknown_cohort_returns_none(self):
        assert resolve_cohort("35기 지원자") is None

    def test_empty_string_returns_none(self):
        assert resolve_cohort("") is None

    def test_none_returns_none(self):
        assert resolve_cohort(None) is None


class TestCohortSenderMap:
    def test_known_cohort_has_sender(self):
        assert COHORT_SENDER_MAP.get("33기") == "01025327302"
        assert COHORT_SENDER_MAP.get("34기") == "01067757302"

    def test_resolved_cohort_maps_to_sender(self):
        """resolve_cohort 결과로 발신번호를 가져올 수 있는지 확인"""
        rc = resolve_cohort("SFAC 33기")
        assert COHORT_SENDER_MAP.get(rc) == "01025327302"

    def test_unknown_cohort_returns_none(self):
        assert COHORT_SENDER_MAP.get("99기") is None


# tests/test_logger.py
import pytest
import os
import csv
from datetime import datetime, timedelta, timezone
from logger import is_already_sent_today


class TestIsAlreadySentToday:
    def test_returns_false_when_no_log_file(self, tmp_path):
        assert is_already_sent_today("01012345678", str(tmp_path)) is False

    def test_returns_true_when_success_record_exists(self, tmp_path):
        KST = timezone(timedelta(hours=9))
        today_str = datetime.now(KST).strftime("%Y-%m-%d")
        log_path = tmp_path / f"{today_str}.csv"
        with open(log_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "executed_at", "name", "phone", "cohort",
                "resolved_cohort", "sender_number", "result", "error_msg"
            ])
            writer.writeheader()
            writer.writerow({
                "executed_at": "2026-05-22T09:05:03",
                "name": "홍길동", "phone": "01012345678",
                "cohort": "SFAC 33기", "resolved_cohort": "33기",
                "sender_number": "01025327302", "result": "성공", "error_msg": ""
            })
        assert is_already_sent_today("01012345678", str(tmp_path)) is True

    def test_returns_false_when_only_failure_record(self, tmp_path):
        """실패 기록은 중복 방지 대상 아님 — 재발송 가능"""
        KST = timezone(timedelta(hours=9))
        today_str = datetime.now(KST).strftime("%Y-%m-%d")
        log_path = tmp_path / f"{today_str}.csv"
        with open(log_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "executed_at", "name", "phone", "cohort",
                "resolved_cohort", "sender_number", "result", "error_msg"
            ])
            writer.writeheader()
            writer.writerow({
                "executed_at": "2026-05-22T09:05:03",
                "name": "홍길동", "phone": "01012345678",
                "cohort": "SFAC 33기", "resolved_cohort": "33기",
                "sender_number": "01025327302", "result": "실패", "error_msg": "timeout"
            })
        assert is_already_sent_today("01012345678", str(tmp_path)) is False


# tests/test_ppurio_client.py
import pytest
from unittest.mock import patch, MagicMock
from ppurio_client import send_lms


class TestSendLms:
    def test_returns_mapping_missing_when_no_sender(self):
        """sender=None이면 매핑없음 반환"""
        result = send_lms(phone="01012345678", sender=None, message="테스트")
        assert result["result"] == "매핑없음"

    def test_returns_failure_on_api_error(self):
        with patch("ppurio_client.requests.post") as mock_post:
            mock_post.side_effect = Exception("Connection error")
            result = send_lms(
                phone="01012345678", sender="01025327302", message="테스트"
            )
        assert result["result"] == "실패"
        assert "Connection error" in result["error_msg"]

    def test_message_sent_without_modification(self):
        """고정 문구가 변환 없이 그대로 전달되는지 확인"""
        with patch("ppurio_client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}
            mock_post.return_value = mock_response

            fixed_message = "안녕하세요. SK네트웍스 Family AI 캠프입니다."
            send_lms(phone="01012345678", sender="01025327302", message=fixed_message)
            assert fixed_message in str(mock_post.call_args)
```

---

## §8. .env.example

```
NOTION_TOKEN=secret_여기에_노션_토큰을_입력하세요
PPURIO_ID=뿌리오_계정_ID를_입력하세요
PPURIO_KEY=뿌리오_API_키를_입력하세요

# 발신번호는 config.py의 COHORT_SENDER_MAP에서 관리합니다
```

---

## §9. 환경 세팅 명령 순서

```bash
git clone https://github.com/{계정}/{저장소명}.git
cd interview-sms
python -m venv venv
venv\Scripts\activate          # Windows
pip install requests python-dotenv
pip install pytest
pip freeze > requirements.txt
copy .env.example .env         # .env 파일 열어 실제 값 입력
pytest tests/ -v
python main.py
```

---

## §10. README 주의사항

```markdown
## ⚠️ 주의사항

### 실행 방법
python main.py (또는 run.bat 더블클릭)
→ 노션에서 오늘 예정자를 자동으로 가져옵니다
→ 목록이 화면에 표시됩니다 (자동 처리 완료)
→ Y를 입력해야 발송이 시작됩니다 (수동 확인 필수)
→ N을 입력하면 발송 없이 종료됩니다

### 신규 기수 추가 방법
config.py의 COHORT_SENDER_MAP에 한 줄 추가:
"35기": "010XXXXXXXX"
→ 노션 기수 필드값에 "35기"가 포함되어 있으면 자동으로 매핑됩니다

### 발신번호 변경 방법
config.py의 해당 기수 번호 수정 + 뿌리오에서 새 번호 사전 등록

### 노션 DB 필드명 변경 시
config.py의 NOTION_FIELD_* 상수를 변경된 이름으로 수정

### 중복 발송 방지
오늘 이미 성공 발송한 번호는 재실행해도 자동으로 건너뜁니다.
실패한 번호는 재실행 시 다시 발송됩니다.
```

---

## §11. Claude Code 직행 프롬프트

```
위 4개 문서(서비스정의서, PRD, FRD, TRD)를 기반으로
인터뷰 SMS 자동 발송 Python 스크립트를 완전히 구현해줘.
아래 조건을 반드시 지켜줘.

구현 조건:
1. TRD §2의 디렉터리 구조 그대로
2. FRD §5의 config.py 코드 그대로 사용 (resolve_cohort 포함)
3. FRD §6의 노션 API 필터 코드 그대로 사용
4. notion_client.py에서 각 행마다 resolve_cohort()를 호출해 resolved_cohort 필드 세팅
5. FRD §8의 Y/N 발송 확인 로직 main.py에 포함
   - 노션 조회는 자동, 발송은 Y 입력해야만 실행
6. FRD §2의 검증 규칙 (normalize_phone, dedup_by_phone) notion_client.py에 구현
7. FRD §2의 중복 발송 방지 (is_already_sent_today) logger.py에 구현
8. 뿌리오 API 엔드포인트는 [확인 필요] 플레이스홀더 유지
9. SMS_MESSAGE는 고정 문구 그대로 — 이름·변수 치환 없음
10. FRD §4의 CSV 출력 형식 그대로 (cohort + resolved_cohort 분리 컬럼)
11. TRD §7의 pytest 테스트 코드 포함
12. TRD §3의 run.bat 포함 (더블클릭 실행)
13. 환경 변수: NOTION_TOKEN, PPURIO_ID, PPURIO_KEY

모든 FRD §3의 AC 체크리스트를 만족해야 함.
```

---

## §12. 미해결 항목

| 항목 | 현재 상태 | 해결 방법 |
|---|---|---|
| 뿌리오 API 엔드포인트 | 플레이스홀더 | 뿌리오 로그인 → API 문서 확인 |
| 뿌리오 인증 방식 | 추정 (Basic Auth) | 공식 문서 확인 |
| 뿌리오 LMS 파라미터 명세 | 추정값 | 공식 문서 확인 |
| 노션 `연락처` 필드 타입 | 전화번호 또는 텍스트 추정 | 노션 DB 필드 타입 확인 |
| 노션 `기수` 필드 타입 | Select 또는 텍스트 추정 | 노션 DB 필드 타입 확인 후 파싱 방식 선택 |
