# 피드백 규칙

> 최대 10개 유지. 에픽 2회 동안 재발 없으면 삭제.

## 활성 규칙

### 규칙 1: Optional 파라미터 타입 힌트 명시
- **패턴**: `None`을 받을 수 있는 함수인데 `def f(x: str)`처럼 `str`만 선언
- **올바른 방법**: `def f(x: str | None)` — 실제로 `None`을 전달하는 테스트가 있다면 선언에도 반영
- **발생 에픽**: 에픽 1 (`resolve_cohort`)

### 규칙 2: run.bat pause 방식 — 무조건부 사용
- **패턴**: `if errorlevel 1 pause` (조건부)로 구현 → 정상 실행 시 창이 바로 닫혀 결과 확인 불가
- **올바른 방법**: `pause` 무조건부 — 담당자가 결과를 확인하고 직접 닫을 수 있어야 함
- **발생 에픽**: 에픽 1 (`run.bat` AC-8)

### 규칙 3: 테스트 환경변수 완전 격리
- **패턴**: 하나의 키를 `delenv`할 때 나머지 키들을 `setenv`로 명시하지 않음 → 실행 환경에 따라 테스트 동작이 달라짐
- **올바른 방법**: 테스트 내에서 검증 대상 이외의 모든 관련 환경변수를 `monkeypatch.setenv`로 명시적으로 설정
- **발생 에픽**: 에픽 1 (`test_raises_on_missing_ppurio_id`)

### 규칙 4: 스펙에 에러 종류별 결과값이 명시된 경우 예외 분기 처리
- **패턴**: `except Exception as exc: return {"result": "실패"}` — 모든 예외를 동일 결과값으로 처리
- **올바른 방법**: FRD에 `결과=실패(타임아웃)` 등 구체적 결과값이 명시된 경우 `except requests.exceptions.Timeout`을 별도 분기로 먼저 잡고 해당 결과값 반환
- **발생 에픽**: 에픽 2 (`ppurio_client.send_lms`)

### 규칙 5: 공개 함수(exported)와 실제 코드 경로 일치 확인
- **패턴**: 테스트로 검증되는 공개 함수가 실제 실행 경로에서는 호출되지 않고, 다른 내부 함수가 사용됨 (dead code)
- **올바른 방법**: 공개 함수를 정의할 때 실제 호출 여부 확인. 내부 전용이면 `_` prefix 사용; 두 함수의 동작이 다르면 어느 쪽이 맞는지 명확히 결정
- **발생 에픽**: 에픽 2 (`notion_client.dedup_by_phone` vs `_dedup_preserving_invalid_phone`)
