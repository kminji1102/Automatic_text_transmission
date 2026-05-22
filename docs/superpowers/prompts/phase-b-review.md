# Phase B — 코드 리뷰 프롬프트 (Claude Code)

> Phase A 구현 완료 + `.\validate-quick.ps1` PASS 확인 후 이 프롬프트를 사용하세요.

---

## 프롬프트

Phase A에서 구현된 코드를 리뷰해줘. `bmad-code-review` 스킬을 사용해서 3단계 병렬 리뷰를 진행해줘.

**리뷰 대상 파일:**
- `config.py`
- `notion_client.py`
- `ppurio_client.py`
- `logger.py`
- `main.py`
- `tests/test_config.py`
- `tests/test_notion_client.py`
- `tests/test_ppurio_client.py`
- `tests/test_logger.py`

---

### 리뷰 체크 포인트

**1. FRD AC 준수 여부 (FRD §3 전체)**

- [ ] M-001: `.env` 없을 때 1초 이내 오류 출력 후 종료
- [ ] M-001: 예정자 0명이면 "오늘 인터뷰 예정자 없습니다" 출력 후 종료
- [ ] M-001: N 입력 시 발송 없이 종료
- [ ] M-001: 정상 실행 시 60초 이내 완료
- [ ] M-003: KST 00:00~23:59 범위 예정자만 반환
- [ ] M-003: `+82-10-1234-5678` → `01012345678` 정규화
- [ ] M-003: `031-123-4567`은 `형식오류` 처리
- [ ] M-003: 동일 연락처 2건이면 1건만 발송
- [ ] M-003: `"SFAC 33기"` → `resolved_cohort="33기"`
- [ ] M-003: 알려진 키워드 없으면 `resolved_cohort=None` → `매핑없음`
- [ ] M-004: `sender=None`이면 `결과=매핑없음` 반환
- [ ] M-004: API 타임아웃 30초 후 `결과=실패(타임아웃)` 반환
- [ ] M-005: 오늘 성공 발송된 번호는 `중복건너뜀`
- [ ] M-005: 실패 기록은 중복 대상 아님 (재발송 가능)
- [ ] M-005: `logs/` 없으면 자동 생성
- [ ] M-005: CSV 인코딩 UTF-8-BOM
- [ ] M-005: `cohort`와 `resolved_cohort` 분리 컬럼

**2. 보안 (`docs/agents/security.md`)**

- `.env`에서 자격증명 로드 확인 (코드 하드코딩 없음)
- `logs/*.csv`에 개인정보 노출 범위 적절한지
- `REQUIRED_ENV_KEYS` 검증 로직 동작 여부

**3. 테스트 커버리지**

- TRD §7 전체 테스트 케이스 구현 여부
- 엣지 케이스 누락 여부 (None 입력, 빈 리스트, 타임아웃 등)
- 실패하는 테스트가 있는지

**4. 코딩 표준 (`docs/agents/coding-standards.md`)**

- 함수 시그니처 AGENTS.md와 일치 여부
- API_TIMEOUT = 30 일관 적용 여부
- KST 기준 날짜 처리 여부
- CSV 컬럼 순서 고정 여부

---

### 리뷰 결과 처리

**REJECTED 항목**: 직접 수정 후 커밋
```bash
git add <수정된 파일>
git commit -m "fix: <수정 내용>"
```

**수정 완료 후:**
```powershell
.\validate-quick.ps1
```
전체 PASS 확인 필수.

---

### 완료 기준

- REJECTED 항목 0개
- `.\validate-quick.ps1` PASS
- `git log --oneline` 으로 fix 커밋 확인

완료 후 `docs/agents/feedback-rules.md`에 반복 패턴 발견 시 규칙 추가.
