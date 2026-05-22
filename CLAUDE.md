# Interview SMS — Claude Code 규칙

## 프로젝트 개요

노션 인터뷰 DB에서 당일 예정자를 조회해 뿌리오 LMS로 발송하는 Python 3.10+ CLI 스크립트.
담당자가 `python main.py` 실행 → 목록 확인 → Y 입력 → 발송.

## 기술 스택

- 언어: Python 3.10+
- 가상환경: venv
- 의존성: `requests`, `python-dotenv` (운영), `pytest` (개발)
- 실행: `python main.py` 또는 `run.bat`

## 모듈 구조 (고정 — 추가/삭제 금지)

| 파일 | 역할 |
|---|---|
| `main.py` | 전체 흐름 실행, Y/N 발송 확인 |
| `config.py` | API 키·기수 매핑·문자 내용, `resolve_cohort()` |
| `notion_client.py` | 노션 DB 조회 + 정규화 + 기수 resolve |
| `ppurio_client.py` | 뿌리오 LMS 1건 발송 |
| `logger.py` | CSV 결과 기록 + 중복 발송 확인 |

## 완료 기준

- `pytest tests/ -v` 전체 통과 필수
- FRD §3 AC 체크리스트 항목 확인
- `.\validate-quick.ps1` PASS

## 절대 금지

- `.env` 파일 직접 읽기 금지 (`.env.example`만 참조)
- 모듈 추가/삭제/리팩터 금지 (5개 파일 고정)
- 뿌리오 API 엔드포인트 임의 추측 금지 → 플레이스홀더 `[뿌리오 API 엔드포인트 확인 후 기입]` 유지
- 새 외부 패키지 추가 금지 (`requests`, `python-dotenv`, `pytest` 외)

## 고정 명세

- CSV 컬럼 순서: `executed_at, name, phone, cohort, resolved_cohort, sender_number, result, error_msg`
- 날짜 기준: KST (`timezone(timedelta(hours=9))`)
- 로그 인코딩: UTF-8-BOM
- API 타임아웃: 30초

## 미해결 항목 (구현 금지)

- 뿌리오 API 엔드포인트: 플레이스홀더 유지
- 뿌리오 인증 방식: Basic Auth 추정 — 공식 문서 확인 전 구현 금지

## 피드백 규칙

반복 실수 발생 시 `docs/agents/feedback-rules.md`에 추가 (최대 10개).
