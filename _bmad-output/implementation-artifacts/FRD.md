# 인터뷰 SMS 자동 발송 FRD v4.0 — Claude Code 입력용 핸드오프 팩

> 작성일: 2026-05-22
> 버전: v4.0
> 변경 이유:
> - `resolve_cohort()` 신규 추가 — 기수 필드값 포함(contains) 방식 매핑
> - CSV에 `cohort`(원본값)·`resolved_cohort`(매핑키) 분리 기록
> - "노션 자동 조회 + 담당자 수동 발송 확인" 구조 코드 수준에서 명시

---

## §1. 모듈 ID 카탈로그

| ID | 파일명 | 역할 | 입력 | 출력 |
|---|---|---|---|---|
| M-001 | `main.py` | 전체 흐름 실행, Y/N 발송 확인 | 없음 (수동 실행) | 없음 (결과는 CSV) |
| M-002 | `config.py` + `.env` | API 키·기수 매핑·문자 내용 관리 | `.env` 파일 | 설정값 딕셔너리 |
| M-003 | `notion_client.py` | 노션 DB 당일 예정자 조회 + 정규화 + 기수 resolve | 오늘 날짜, DB ID, 토큰 | `List[dict]` |
| M-004 | `ppurio_client.py` | 뿌리오 LMS 1건 발송 | 수신번호, 발신번호, 문자내용 | `dict` (결과) |
| M-005 | `logger.py` | CSV 결과 기록 + 중복 발송 확인 | 결과 리스트, 날짜 | `logs/YYYY-MM-DD.csv` |

### 모듈별 예외 상태

| 모듈 | 예외 조건 | 처리 | exit code |
|---|---|---|---|
| M-001 | 담당자 N 입력 | 즉시 종료, 발송 없음 | 0 |
| M-002 | `.env` 없음 또는 필수 키 누락 | 오류 메시지 출력 후 종료 | 1 |
| M-003 | 노션 API 타임아웃·4xx/5xx | 예외 raise → M-001이 CSV 기록 후 종료 | 1 |
| M-003 | 연락처 형식 오류 | 해당 건 `형식오류` 표시, 계속 진행 | 0 |
| M-003 | 중복 연락처 (노션 DB 내부) | 첫 번째만 남기고 중복 제거 | 0 |
| M-003 | 기수 필드에 알려진 키워드 없음 | `resolved_cohort=None` 세팅, M-004에서 처리 | 0 |
| M-004 | `sender=None` (기수 매핑 실패) | `결과=매핑없음` 반환, 다음 건 진행 | 0 |
| M-004 | 뿌리오 API 타임아웃·오류 | `결과=실패` 반환, 다음 건 진행 | 0 |
| M-005 | 오늘 이미 성공 발송된 번호 | `결과=중복건너뜀`, 발송 제외 | 0 |
| M-005 | CSV 쓰기 실패 | 콘솔 출력 후 종료 | 1 |

---

## §2. 검증 규칙

### 2.1 연락처 정규화 (normalize_phone)

```python
import re

def normalize_phone(raw: str) -> str | None:
    """
    입력된 연락처를 11자리 숫자로 정규화. 불가 시 None 반환.
    """
    if not raw:
        return None
    raw = str(raw).strip()
    if raw.startswith('+82'):
        digits = '0' + re.sub(r'[^0-9]', '', raw[3:])
    else:
        digits = re.sub(r'[^0-9]', '', raw)
    if len(digits) == 11 and digits.startswith('010'):
        return digits
    return None
```

### 2.2 노션 DB 내부 중복 제거 (dedup_by_phone)

```python
def dedup_by_phone(interviewees: list[dict]) -> list[dict]:
    """동일 연락처 기준 중복 제거. 첫 번째 행만 유지."""
    seen = set()
    result = []
    for item in interviewees:
        phone = item.get('phone')
        if phone and phone not in seen:
            seen.add(phone)
            result.append(item)
    return result
```

### 2.3 기수 포함 여부 매핑 (resolve_cohort) ★ 신규

```python
def resolve_cohort(raw_cohort: str, cohort_sender_map: dict) -> str | None:
    """
    노션 기수 필드 원본값에서 알려진 기수 키워드를 찾아 반환.

    노션 기수 필드값이 정확히 "33기"가 아닌 "SFAC 33기", "플레이데이터 33기 수강생"
    등 다양한 형태로 입력될 수 있으므로 포함(contains) 방식으로 매핑한다.

    반환값: COHORT_SENDER_MAP의 키 (예: "33기") 또는 None
    """
    if not raw_cohort:
        return None
    for key in cohort_sender_map:
        if key in raw_cohort:
            return key  # 매핑 키 반환 (예: "33기")
    return None  # 알려진 기수 키워드 없음
```

**동작 예시**

```python
COHORT_SENDER_MAP = {"33기": "01025327302", "34기": "01067757302"}

resolve_cohort("SFAC 33기", COHORT_SENDER_MAP)          # → "33기"
resolve_cohort("플레이데이터 34기 수강생", COHORT_SENDER_MAP)  # → "34기"
resolve_cohort("33기", COHORT_SENDER_MAP)               # → "33기"
resolve_cohort("35기 지원자", COHORT_SENDER_MAP)         # → None
resolve_cohort("", COHORT_SENDER_MAP)                   # → None
```

> `resolve_cohort()`는 config.py에 정의하고 notion_client.py에서 import해 사용한다.
> 발신번호가 필요할 때는 `COHORT_SENDER_MAP.get(resolved_cohort)` 로 가져온다.

### 2.4 중복 발송 확인 (is_already_sent_today) — 1단계 필수

```python
import os
import csv
from datetime import datetime, timedelta, timezone

def is_already_sent_today(phone: str, log_dir: str) -> bool:
    """
    오늘 날짜 CSV에 해당 연락처가 '성공'으로 기록되어 있으면 True.
    실패 기록은 중복 방지 대상 아님 — 재발송 가능.
    """
    KST = timezone(timedelta(hours=9))
    today_str = datetime.now(KST).strftime("%Y-%m-%d")
    log_path = os.path.join(log_dir, f"{today_str}.csv")
    if not os.path.exists(log_path):
        return False
    with open(log_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("phone") == phone and row.get("result") == "성공":
                return True
    return False
```

### 2.5 config.py 필수 키 검증

```python
REQUIRED_ENV_KEYS = ['NOTION_TOKEN', 'PPURIO_ID', 'PPURIO_KEY']

def validate_config():
    missing = [k for k in REQUIRED_ENV_KEYS if not os.getenv(k)]
    if missing:
        raise ValueError(f"설정 파일 누락: {', '.join(missing)}")
```

---

## §3. 인수 기준 (AC) 체크리스트

### M-001 main.py

- [ ] `.env` 파일 없을 때 1초 이내 종료되고 오류 메시지가 출력된다
- [ ] 발송 목록 미리보기가 출력된 뒤 발송할 번호 입력을 요청한다 (전체는 Enter, 취소는 N)
- [ ] 잘못된 번호 입력 시 발송·종료 없이 재입력을 요청한다
- [ ] 번호 선택 후 선택된 목록을 다시 보여주고 Y/N 최종 확인을 요청한다
- [ ] N 입력(번호 단계 또는 최종 확인) 시 발송 없이 종료된다
- [ ] 예정자 0명일 때 "오늘 인터뷰 예정자 없습니다" 출력 후 종료된다
- [ ] 정상 실행 시 전체 소요 시간 60초 이내

### M-003 notion_client.py

- [ ] 오늘 KST 00:00~23:59 범위의 예정자만 반환된다
- [ ] `+82-10-1234-5678` → `01012345678`으로 정규화된다
- [ ] `031-123-4567`은 `형식오류`로 처리되고 발송 목록에 포함되지 않는다
- [ ] 동일 연락처 2건이 노션에 있으면 1건만 발송 대상에 포함된다
- [ ] `"SFAC 33기"`처럼 기수 키워드가 포함된 필드값은 `"33기"`로 resolve된다
- [ ] `"35기 지원자"`처럼 알려진 키워드가 없으면 `resolved_cohort=None`이 되고 `매핑없음`으로 처리된다
- [ ] 노션 API 30초 타임아웃 후 예외가 raise된다

### M-004 ppurio_client.py

- [ ] API 호출 시 `type` 파라미터가 `lms`로 지정된다
- [ ] 발송되는 문자 내용이 `SMS_MESSAGE` 고정 문구 그대로다
- [ ] `sender=None` (기수 매핑 실패)이면 `결과=매핑없음`을 반환하고 다음 건 진행된다
- [ ] 뿌리오 API 30초 타임아웃 후 `결과=실패(타임아웃)`를 반환하고 다음 건 진행된다
- [ ] 발신번호는 하이픈 없이 전달된다

### M-005 logger.py

- [ ] 오늘 날짜 CSV에 `성공` 기록이 있는 번호는 `중복건너뜀`으로 처리되고 발송되지 않는다
- [ ] 실패 기록이 있는 번호는 중복 처리되지 않는다 (재발송 가능)
- [ ] `logs/` 폴더가 없으면 자동 생성된다
- [ ] CSV 인코딩은 UTF-8-BOM이다
- [ ] `결과`가 `성공`이 아닌 행이 CSV 상단에 위치한다
- [ ] `cohort`(원본값)와 `resolved_cohort`(매핑키)가 분리 기록된다

---

## §4. CSV 출력 명세 (상태별 예시)

### 정상 발송 예시 (기수 필드 원본값 다양)

```csv
executed_at,name,phone,cohort,resolved_cohort,sender_number,result,error_msg
2026-05-22T09:05:03,홍길동,01012345678,SFAC 33기,33기,01025327302,성공,
2026-05-22T09:05:05,김철수,01098765432,플레이데이터 33기 수강생,33기,01025327302,성공,
2026-05-22T09:05:07,이영희,01011112222,34기 지원자,34기,01067757302,성공,
```

### 매핑 실패 포함 예시 (경고 행 상단)

```csv
executed_at,name,phone,cohort,resolved_cohort,sender_number,result,error_msg
2026-05-22T09:05:01,박지수,,35기 수강생,,매핑없음,35기 발신번호 없음
2026-05-22T09:05:03,홍길동,01012345678,SFAC 33기,33기,01025327302,성공,
```

### 중복 포함 예시

```csv
executed_at,name,phone,cohort,resolved_cohort,sender_number,result,error_msg
2026-05-22T09:05:01,홍길동,01012345678,SFAC 33기,33기,01025327302,중복건너뜀,오늘 이미 성공 발송됨
2026-05-22T09:05:03,김철수,01098765432,SFAC 33기,33기,01025327302,성공,
```

---

## §5. config.py 전체 코드

```python
import os
from dotenv import load_dotenv

load_dotenv()

# ── 비밀값 (.env에서 로드) ──────────────────────
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PPURIO_ID = os.getenv("PPURIO_ID")
PPURIO_KEY = os.getenv("PPURIO_KEY")

# ── 노션 설정 ────────────────────────────────────
NOTION_DB_ID = "8336a73c082d411c8275a1c3015cb36e"
NOTION_FIELD_DATE = "인터뷰일시"    # 변경 시 이 값만 수정
NOTION_FIELD_COHORT = "기수"
NOTION_FIELD_PHONE = "연락처"
NOTION_FIELD_NAME = "이름"

# ── 기수 → 발신번호 매핑 ─────────────────────────
# 신규 기수 추가 또는 번호 변경 시 이 딕셔너리만 수정
# 매핑은 포함(contains) 방식: "SFAC 33기" → "33기" 키로 처리됨
COHORT_SENDER_MAP = {
    "33기": "01025327302",   # 서초캠퍼스
    "34기": "01067757302",   # G밸리캠퍼스
    # "35기": "010XXXXXXXX",  ← 신규 기수 추가 예시
}

def resolve_cohort(raw_cohort: str) -> str | None:
    """
    기수 필드 원본값에서 COHORT_SENDER_MAP 키가 포함되어 있는지 확인.
    포함된 키를 반환하고, 없으면 None 반환.
    예: "SFAC 33기" → "33기" / "35기 지원자" → None
    """
    if not raw_cohort:
        return None
    for key in COHORT_SENDER_MAP:
        if key in raw_cohort:
            return key
    return None

# ── 문자 내용 (고정 문구 — 동적 변수 없음) ──────
SMS_MESSAGE = """안녕하세요.
SK네트웍스 Family AI 캠프입니다.
신청해주신 부트캠프 입과 인터뷰가 오늘 진행될 예정입니다.
인터뷰 세부 일정 및 진행 방식(온라인/오프라인), 접속 링크 등은 담당자가 진행 전 개별 안내드릴 예정입니다.
일정 확인 또는 변경, 취소를 원하시는 경우 아래 채팅 문의 링크를 통해 말씀 부탁드립니다.
감사합니다.
플레이데이터 드림
▶ 채널톡 문의
https://networks-aicamp.channel.io"""

# ── API 공통 설정 ─────────────────────────────────
API_TIMEOUT = 30
SMS_TYPE = "lms"
LOG_DIR = "logs"

# ── 필수 환경 변수 검증 ──────────────────────────
REQUIRED_ENV_KEYS = ['NOTION_TOKEN', 'PPURIO_ID', 'PPURIO_KEY']

def validate_config():
    missing = [k for k in REQUIRED_ENV_KEYS if not os.getenv(k)]
    if missing:
        raise ValueError(f"설정 파일 누락: {', '.join(missing)}")
```

---

## §6. 노션 API 필터 코드

```python
from datetime import datetime, timedelta, timezone

def build_today_filter(field_name: str) -> dict:
    """KST 기준 오늘 00:00 ~ 23:59를 UTC로 변환한 노션 날짜 필터"""
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    today_start_kst = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start_kst = today_start_kst + timedelta(days=1)
    today_start_utc = today_start_kst.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    tomorrow_start_utc = tomorrow_start_kst.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return {
        "filter": {
            "and": [
                {"property": field_name, "date": {"on_or_after": today_start_utc}},
                {"property": field_name, "date": {"before": tomorrow_start_utc}}
            ]
        }
    }
```

---

## §7. 뿌리오 API 플레이스홀더

```python
PPURIO_API_URL = "[뿌리오 API 엔드포인트 확인 후 기입]"

request_body = {
    "type": "lms",
    "from": sender_number,   # COHORT_SENDER_MAP.get(resolved_cohort)
    "to": receiver_number,
    "content": SMS_MESSAGE,  # 고정 문구 그대로
}
```

---

## §8. 발송 확인 흐름 (main.py 핵심 로직)

```python
def show_preview(candidates: list[dict]) -> None:
    """발송 전 목록 미리보기 — 노션 원본 기수값과 매핑 결과 함께 표시"""
    print("\n" + "="*60)
    print(f"📋 오늘 인터뷰 예정자 — 발송 목록 ({len(candidates)}명)")
    print("="*60)
    for i, c in enumerate(candidates, 1):
        rc = c.get('resolved_cohort') or '매핑없음'
        sender = COHORT_SENDER_MAP.get(rc, '번호없음')
        print(
            f"  {i}. {c.get('name','')} | {c['phone']} "
            f"| 기수: {c.get('cohort','')} → {rc} | 발신: {sender}"
        )
    print("="*60)
    print("  ※ 노션 조회는 자동 완료. 아래에서 발송 여부를 직접 확인하세요.")


def confirm_send() -> bool:
    """담당자 수동 발송 확인"""
    answer = input("\n위 목록으로 발송하시겠습니까? (Y/N): ").strip().upper()
    return answer == 'Y'


# main.py 실행 흐름 (의사코드)
# 1. validate_config()
# 2. candidates = fetch_today_interviewees()      # 노션 자동 조회
# 3. for each: c['resolved_cohort'] = resolve_cohort(c['cohort'])
# 4. candidates = filter_not_sent(candidates)     # 오늘 성공 발송 제외
# 5. if len(candidates) == 0: 종료
# 6. show_preview(candidates)                     # 미리보기 표시
# 7. if not confirm_send(): 종료                  # ★ 담당자 수동 확인
# 8. for each candidate:
#      sender = COHORT_SENDER_MAP.get(c['resolved_cohort'])
#      result = send_lms(phone, sender, SMS_MESSAGE)
#      log_result(result)
# 9. write_csv()
```

---

## §9. 미해결 항목

| 항목 | 현재 상태 | 해결 방법 |
|---|---|---|
| 뿌리오 API 엔드포인트 | 플레이스홀더 | 뿌리오 로그인 → API 문서 확인 |
| 뿌리오 인증 방식 | 추정 (Basic Auth) | 공식 문서 확인 |
| 뿌리오 LMS 요청 파라미터 | 추정값 | 공식 문서 확인 |
| 노션 `연락처` 필드 타입 | 전화번호 또는 텍스트 추정 | 노션 DB 필드 타입 확인 |
| 노션 `기수` 필드 타입 | Select 또는 텍스트 추정 | 노션 DB 필드 타입 확인 후 파싱 방식 선택 |
