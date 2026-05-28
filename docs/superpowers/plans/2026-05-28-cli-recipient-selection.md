# CLI 발송 대상 선택 기능 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 미리보기 후 담당자가 발송할 번호를 선택(전체는 Enter, 취소는 N)하고 최종 Y/N으로 확인해, 선택된 인원에게만 LMS를 발송한다.

**Architecture:** `main.py` 단일 파일 안에 순수 함수 `parse_selection_indices`(입력 파싱·검증)와 얇은 입출력 래퍼 `prompt_recipients`(입력 루프·취소·최종 확인)를 추가하고, 기존 `confirm_send()`를 대체한다. 파싱 로직은 입출력과 분리해 `pytest`로 단위 검증한다.

**Tech Stack:** Python 3.10+, 표준 라이브러리만(신규 패키지 없음), pytest.

**제약:** 5개 소스 모듈 고정(새 모듈 없음) · `.env` 직접 읽기 없음 · 뿌리오 엔드포인트 무관.

**참조 스펙:** [docs/superpowers/specs/2026-05-28-cli-recipient-selection-design.md](../specs/2026-05-28-cli-recipient-selection-design.md)

---

## File Structure

- **Modify:** `main.py`
  - 추가: `parse_selection_indices(raw, count) -> list[int]` (순수 함수)
  - 추가: `prompt_recipients(send_candidates) -> list[dict] | None` (입출력 래퍼)
  - 제거: `confirm_send()` (대체됨)
  - 수정: `main()` 호출부 — `confirm_send()` → `prompt_recipients()`, 발송 루프 대상 `send_candidates` → `selected`
- **Create:** `tests/test_main.py` — 파싱·프롬프트 동작 단위 테스트
- **Modify:** `_bmad-output/implementation-artifacts/FRD.md` — M-001 §3 AC 체크리스트 갱신

---

## Task 1: 입력 파싱 순수 함수 `parse_selection_indices`

**Files:**
- Modify: `main.py` (`confirm_send()` 정의 바로 아래에 함수 추가)
- Test: `tests/test_main.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_main.py` 생성:

```python
import pytest

from main import parse_selection_indices


class TestParseSelectionIndices:
    def test_empty_returns_all(self):
        assert parse_selection_indices("", 4) == [1, 2, 3, 4]

    def test_whitespace_returns_all(self):
        assert parse_selection_indices("   ", 3) == [1, 2, 3]

    def test_comma_separated(self):
        assert parse_selection_indices("1,3", 4) == [1, 3]

    def test_space_separated(self):
        assert parse_selection_indices("2 4", 4) == [2, 4]

    def test_dedup(self):
        assert parse_selection_indices("1,1", 4) == [1]

    def test_sorted_output(self):
        assert parse_selection_indices("3,1", 4) == [1, 3]

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            parse_selection_indices("5", 4)

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            parse_selection_indices("0", 4)

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            parse_selection_indices("a", 4)
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_main.py -v`
Expected: collection 단계에서 `ImportError: cannot import name 'parse_selection_indices' from 'main'`

- [ ] **Step 3: 최소 구현 작성**

`main.py`의 `confirm_send()` 정의 아래에 추가:

```python
def parse_selection_indices(raw: str, count: int) -> list[int]:
    raw = (raw or "").strip()
    if not raw:
        return list(range(1, count + 1))
    indices: list[int] = []
    for token in raw.replace(",", " ").split():
        if not token.isdigit():
            raise ValueError(f"잘못된 입력: {token}")
        num = int(token)
        if num < 1 or num > count:
            raise ValueError(f"범위를 벗어난 번호: {num}")
        if num not in indices:
            indices.append(num)
    return sorted(indices)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_main.py -v`
Expected: 9개 테스트 모두 PASS

- [ ] **Step 5: 커밋**

```bash
git add tests/test_main.py main.py
git commit -m "feat: add recipient selection parsing (parse_selection_indices)"
```

---

## Task 2: 입출력 래퍼 `prompt_recipients`

**Files:**
- Modify: `main.py` (`parse_selection_indices()` 바로 아래에 함수 추가)
- Test: `tests/test_main.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_main.py`의 import 줄을 다음으로 교체:

```python
from main import parse_selection_indices, prompt_recipients
```

파일 끝에 클래스 추가:

```python
class TestPromptRecipients:
    def _candidates(self):
        return [
            {"name": "A", "phone": "01000000001"},
            {"name": "B", "phone": "01000000002"},
            {"name": "C", "phone": "01000000003"},
        ]

    def test_cancel_with_n(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda prompt="": "N")
        assert prompt_recipients(self._candidates()) is None

    def test_select_then_confirm_yes(self, monkeypatch):
        answers = iter(["1,3", "Y"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
        result = prompt_recipients(self._candidates())
        assert [c["name"] for c in result] == ["A", "C"]

    def test_select_then_confirm_no(self, monkeypatch):
        answers = iter(["2", "N"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
        assert prompt_recipients(self._candidates()) is None

    def test_invalid_then_valid(self, monkeypatch):
        answers = iter(["9", "2", "Y"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
        result = prompt_recipients(self._candidates())
        assert [c["name"] for c in result] == ["B"]

    def test_eof_returns_none(self, monkeypatch):
        def raise_eof(prompt=""):
            raise EOFError()
        monkeypatch.setattr("builtins.input", raise_eof)
        assert prompt_recipients(self._candidates()) is None
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_main.py -v`
Expected: collection 단계에서 `ImportError: cannot import name 'prompt_recipients' from 'main'`

- [ ] **Step 3: 최소 구현 작성**

`main.py`의 `parse_selection_indices()` 아래에 추가:

```python
def prompt_recipients(send_candidates: list[dict]) -> list[dict] | None:
    count = len(send_candidates)
    while True:
        try:
            raw = input(
                "\n발송할 번호를 입력하세요 (예: 1,3 / 전체는 Enter / 취소는 N): "
            ).strip()
        except EOFError:
            return None
        if raw.upper() == "N":
            return None
        try:
            indices = parse_selection_indices(raw, count)
        except ValueError as exc:
            print(f"  입력 오류: {exc}. 다시 입력해주세요.")
            continue
        selected = [send_candidates[i - 1] for i in indices]
        break

    print(f"\n선택된 발송 대상 ({len(selected)}명):")
    for index, candidate in enumerate(selected, 1):
        print(f"  {index}. {candidate.get('name', '')} | {candidate.get('phone', '')}")

    try:
        answer = input("\n이대로 발송하시겠습니까? (Y/N): ").strip().upper()
    except EOFError:
        return None
    if answer != "Y":
        return None
    return selected
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_main.py -v`
Expected: 14개 테스트 모두 PASS (Task 1의 9개 + 신규 5개)

- [ ] **Step 5: 커밋**

```bash
git add tests/test_main.py main.py
git commit -m "feat: add interactive recipient prompt (prompt_recipients)"
```

---

## Task 3: `main()` 연결 및 `confirm_send()` 제거

**Files:**
- Modify: `main.py` (`main()` 호출부, `confirm_send()` 제거)

- [ ] **Step 1: `main()` 호출부 교체**

`main.py`의 다음 블록을

```python
    show_preview(send_candidates)
    if not confirm_send():
        print("발송을 취소했습니다")
        app_logger.info("담당자 확인에서 발송 취소")
        return 0

    send_results = []
    for candidate in send_candidates:
        sender = COHORT_SENDER_MAP.get(candidate.get("resolved_cohort"))
        send_result = send_lms(candidate["phone"], sender, SMS_MESSAGE)
        send_results.append(_row_from_send_result(candidate, sender, send_result))
```

다음으로 교체:

```python
    show_preview(send_candidates)
    selected = prompt_recipients(send_candidates)
    if selected is None:
        print("발송을 취소했습니다")
        app_logger.info("담당자 확인에서 발송 취소")
        return 0

    send_results = []
    for candidate in selected:
        sender = COHORT_SENDER_MAP.get(candidate.get("resolved_cohort"))
        send_result = send_lms(candidate["phone"], sender, SMS_MESSAGE)
        send_results.append(_row_from_send_result(candidate, sender, send_result))
```

- [ ] **Step 2: `confirm_send()` 제거**

`main.py`에서 다음 함수 정의를 삭제:

```python
def confirm_send() -> bool:
    answer = input("\n위 목록으로 발송하시겠습니까? (Y/N): ").strip().upper()
    return answer == "Y"
```

- [ ] **Step 3: 전체 테스트 통과 확인**

Run: `.\venv\Scripts\python.exe -m pytest tests/ -v`
Expected: 전체 PASS (기존 34개 + 신규 14개 = 48개). `confirm_send` 참조 잔존 없음.

- [ ] **Step 4: 발송 없는 스모크 테스트 (실제 발송 금지)**

Run (선택 표시 후 최종 N으로 취소 — 실제 SMS 미발송):
```powershell
$env:PYTHONIOENCODING="utf-8"; "1`nN" | .\venv\Scripts\python.exe main.py
```
Expected 출력에 포함: 미리보기 목록, `선택된 발송 대상 (1명):`, `발송을 취소했습니다`. SMS는 발송되지 않음(최종 N).

- [ ] **Step 5: 커밋**

```bash
git add main.py
git commit -m "feat: wire recipient selection into main flow, remove confirm_send"
```

---

## Task 4: FRD M-001 AC 갱신 (스펙 동기화)

**Files:**
- Modify: `_bmad-output/implementation-artifacts/FRD.md` (§3 M-001 AC 체크리스트)

- [ ] **Step 1: §3 M-001 AC 블록 교체**

`FRD.md`의 다음 블록(§3 `### M-001 main.py` 아래)을

```markdown
- [ ] `.env` 파일 없을 때 1초 이내 종료되고 오류 메시지가 출력된다
- [ ] 발송 목록 미리보기가 출력된 뒤 Y/N 확인을 요청한다
- [ ] N 입력 시 발송 없이 종료된다 (노션 조회는 이미 됐지만 발송은 안 됨)
- [ ] 예정자 0명일 때 "오늘 인터뷰 예정자 없습니다" 출력 후 종료된다
- [ ] 정상 실행 시 전체 소요 시간 60초 이내
```

다음으로 교체:

```markdown
- [ ] `.env` 파일 없을 때 1초 이내 종료되고 오류 메시지가 출력된다
- [ ] 발송 목록 미리보기가 출력된 뒤 발송할 번호 입력을 요청한다 (전체는 Enter, 취소는 N)
- [ ] 잘못된 번호 입력 시 발송·종료 없이 재입력을 요청한다
- [ ] 번호 선택 후 선택된 목록을 다시 보여주고 Y/N 최종 확인을 요청한다
- [ ] N 입력(번호 단계 또는 최종 확인) 시 발송 없이 종료된다
- [ ] 예정자 0명일 때 "오늘 인터뷰 예정자 없습니다" 출력 후 종료된다
- [ ] 정상 실행 시 전체 소요 시간 60초 이내
```

> 참고: FRD의 §design 예시 의사코드(`confirm_send()` 스니펫)는 설명용이며, 정식 동작은 본 설계/계획 문서를 따른다. 필요 시 별도로 정리.

- [ ] **Step 2: 커밋**

```bash
git add _bmad-output/implementation-artifacts/FRD.md
git commit -m "docs: update FRD M-001 AC for recipient selection"
```

---

## Self-Review

**1. Spec coverage** — 설계 문서 항목 대비:
- 번호 선택(포함 방식) → Task 1·2 (`parse_selection_indices`, `prompt_recipients`)
- 전체(Enter)/취소(N)/재입력 → Task 1(빈입력=전체, ValueError) + Task 2(N 취소, 재입력 루프, EOF 취소)
- 선택 후 최종 Y/N → Task 2(최종 확인)
- main 연결·`confirm_send` 제거 → Task 3
- 테스트(`tests/test_main.py`) → Task 1·2
- FRD AC 갱신 → Task 4
- 범위 외(수정/추가) 미포함 확인 → 계획에 없음(YAGNI 준수)

**2. Placeholder scan** — TBD/TODO/"적절히 처리" 류 없음. 모든 코드 스텝에 실제 코드·명령·기대결과 포함.

**3. Type consistency** — `parse_selection_indices(raw: str, count: int) -> list[int]`, `prompt_recipients(send_candidates: list[dict]) -> list[dict] | None` 시그니처가 Task 1·2·3·테스트에서 동일하게 사용됨. `main()`은 반환값을 `selected`로 받아 `None` 분기 후 발송 루프에 전달 — 일관됨.
