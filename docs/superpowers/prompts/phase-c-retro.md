# Phase C — 회고 프롬프트 (Claude Code)

> Phase B 리뷰 완료 + REJECTED 항목 0개 확인 후 해당 에픽 섹션을 사용하세요.
> 순서: Epic 1 완료 후 Epic 2 진행

---

## EPIC = 1

Epic 1 리뷰 완료 + REJECTED 항목 0개 확인 후 아래를 진행해줘.

`bmad-retrospective` 스킬을 사용해서 Epic 1(프로젝트 초기화 및 설정 모듈) 회고를 진행해줘.

---

### 회고 범위

**1. AC 체크리스트 최종 점검 (코드 직접 확인)**

```
config.py:
  - [ ] resolve_cohort("SFAC 33기") → "33기"
  - [ ] resolve_cohort("35기 지원자") → None
  - [ ] resolve_cohort("") / None → None
  - [ ] validate_config(): 키 누락 시 ValueError + 키 이름

프로젝트 골격:
  - [ ] main.py, config.py, notion_client.py, ppurio_client.py, logger.py 파일 존재
  - [ ] tests/__init__.py, logs/.gitkeep 존재
  - [ ] .env.example에 3개 키 + 주석

의존성:
  - [ ] requests==2.31.0, python-dotenv==1.0.1 (requirements.txt)
  - [ ] pytest==8.1.1 (requirements-dev.txt)

run.bat:
  - [ ] venv\Scripts\python.exe main.py + 오류 시 pause

README.md:
  - [ ] 신규 기수 추가 방법 (COHORT_SENDER_MAP)
  - [ ] 발신번호 변경 방법
  - [ ] 중복 발송 방지 설명
```

**2. 반복 실수 패턴**

- Phase A 구현 중 자주 틀린 것
- Phase B에서 REJECTED된 이유
- 테스트보다 구현을 먼저 한 경우

**3. 하네스 개선 사항**

- `CLAUDE.md` / `AGENTS.md`에 추가할 규칙
- `validate-quick.ps1`에 추가할 검증 항목

---

### 결과물

**`docs/agents/feedback-rules.md` 업데이트** (반복 패턴 발견 시):

```markdown
### 규칙 N: [규칙 이름]
- **패턴**: [어떤 상황에서 발생하는 실수]
- **올바른 방법**: [정확한 구현 방법]
- **발생 에픽**: 에픽 1
```

```bash
git add docs/agents/feedback-rules.md
git commit -m "retro: update feedback rules after epic 1"
```

**sprint-status.yaml 업데이트:**

`_bmad-output/implementation-artifacts/sprint-status.yaml`에서 `epic-1: done`으로 변경

### 완료 기준

- AC 체크리스트 전체 체크
- `feedback-rules.md` 업데이트 (패턴 발견 시)
- `sprint-status.yaml` epic-1 상태 → done
- `git log --oneline` 최종 이력 확인

---

## EPIC = 2

Epic 2 리뷰 완료 + REJECTED 항목 0개 확인 후 아래를 진행해줘.

`bmad-retrospective` 스킬을 사용해서 Epic 2(핵심 발송 파이프라인) 회고를 진행해줘.

---

### 회고 범위

**1. FRD §3 AC 체크리스트 최종 점검 (코드 직접 확인)**

```
M-001:
  - [ ] .env 없을 때 1초 이내 종료 + 오류 메시지
  - [ ] 발송 목록 미리보기 출력 후 Y/N 확인
  - [ ] N 입력 시 발송 없이 종료
  - [ ] 예정자 0명이면 안내 출력 후 종료
  - [ ] 정상 실행 60초 이내

M-003:
  - [ ] KST 기준 오늘 예정자만 반환
  - [ ] +82 형식 정규화
  - [ ] 031 번호 형식오류 처리
  - [ ] 노션 내부 중복 연락처 1건만 포함
  - [ ] contains 방식 기수 매핑 동작
  - [ ] 알려진 키워드 없으면 매핑없음 처리

M-004:
  - [ ] API 호출 시 type=lms 지정
  - [ ] 고정 문구 그대로 전달
  - [ ] sender=None이면 매핑없음 반환
  - [ ] 30초 타임아웃 후 실패 반환
  - [ ] PPURIO_API_URL 플레이스홀더 유지

M-005:
  - [ ] 오늘 성공 기록 있으면 중복건너뜀
  - [ ] 실패 기록은 재발송 가능
  - [ ] logs/ 없으면 자동 생성
  - [ ] UTF-8-BOM 인코딩
  - [ ] 실패/매핑없음 행 CSV 상단
  - [ ] cohort + resolved_cohort 분리 컬럼
```

**2. 반복 실수 패턴**

- Phase A 구현 중 자주 틀린 것
- Phase B에서 REJECTED된 이유
- 테스트보다 구현을 먼저 한 경우

**3. 하네스 개선 사항**

- `CLAUDE.md` / `AGENTS.md`에 추가해야 할 규칙
- `validate-quick.ps1`에 추가할 검증 항목
- `.claude/settings.json` 권한 조정 필요 여부

---

### 결과물

**`docs/agents/feedback-rules.md` 업데이트** (반복 패턴 발견 시):

```markdown
### 규칙 N: [규칙 이름]
- **패턴**: [어떤 상황에서 발생하는 실수]
- **올바른 방법**: [정확한 구현 방법]
- **발생 에픽**: 에픽 2
```

```bash
git add docs/agents/feedback-rules.md
git commit -m "retro: update feedback rules after epic 2"
```

**sprint-status.yaml 업데이트:**

`_bmad-output/implementation-artifacts/sprint-status.yaml`에서 `epic-2: done`으로 변경

### 완료 기준

- AC 체크리스트 전체 체크
- `feedback-rules.md` 업데이트 (패턴 발견 시)
- `sprint-status.yaml` epic-2 상태 → done
- `git log --oneline` 최종 이력 확인

### 다음 에픽 준비 (해당 시)

- `docs/agents/feedback-rules.md` 활성 규칙 확인
- 뿌리오 API 엔드포인트 확인 여부 검토
- PRD 2단계 기능 업데이트 여부 확인
