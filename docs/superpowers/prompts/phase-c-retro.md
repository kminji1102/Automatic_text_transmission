# Phase C — 회고 프롬프트 (Claude Code)

> Phase B 리뷰 완료 + REJECTED 항목 0개 확인 후 이 프롬프트를 사용하세요.

---

## 프롬프트

이번 에픽(인터뷰 SMS 자동 발송 구현) 회고를 진행해줘. `bmad-retrospective` 스킬을 사용해서 진행해줘.

---

### 회고 범위

**1. FRD §3 AC 체크리스트 최종 점검**

아래 항목을 코드를 직접 확인하면서 체크해줘:

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

M-005:
  - [ ] 오늘 성공 기록 있으면 중복건너뜀
  - [ ] 실패 기록은 재발송 가능
  - [ ] logs/ 없으면 자동 생성
  - [ ] UTF-8-BOM 인코딩
  - [ ] 실패/매핑없음 행 CSV 상단
  - [ ] cohort + resolved_cohort 분리 컬럼
```

**2. 이번 구현에서 발견된 반복 실수나 패턴**

- Phase A 구현 중 자주 틀린 것
- Phase B 리뷰에서 REJECTED된 이유
- 테스트를 먼저 쓰지 않고 구현부터 한 경우

**3. 하네스 개선 사항**

- `CLAUDE.md` / `AGENTS.md`에 추가해야 할 규칙
- `validate-quick.ps1`에 추가할 검증 항목
- `.claude/settings.json` 권한 조정 필요 여부

---

### 결과물

**`docs/agents/feedback-rules.md` 업데이트**

반복 실수 패턴이 있으면 아래 형식으로 추가 (최대 10개):

```markdown
## 활성 규칙

### 규칙 1: [규칙 이름]
- **패턴**: [어떤 상황에서 발생하는 실수]
- **올바른 방법**: [정확한 구현 방법]
- **발생 에픽**: 에픽 1
```

**커밋:**
```bash
git add docs/agents/feedback-rules.md
git commit -m "retro: update feedback rules after epic 1"
```

---

### 완료 기준

- AC 체크리스트 전체 체크
- `feedback-rules.md` 업데이트 (발견된 패턴 있으면)
- `git log --oneline` 최종 이력 확인

---

### 다음 에픽 준비 (해당되는 경우)

이번 회고에서 나온 규칙을 다음 에픽 시작 전에 확인:
- `docs/agents/feedback-rules.md` 활성 규칙 읽기
- 2단계 기능 (Windows 작업 스케줄러 자동 실행) PRD 업데이트 여부 확인
