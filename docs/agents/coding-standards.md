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
