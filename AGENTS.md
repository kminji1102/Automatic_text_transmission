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
API_TIMEOUT = 30                       # 노션·뿌리오 공통
SMS_TYPE    = "lms"                    # 변경 금지
LOG_DIR     = "logs"                   # 변경 금지
KST         = timezone(timedelta(hours=9))  # 날짜 처리 기준
```
