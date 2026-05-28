---
stepsCompleted: ["step-01-validate-prerequisites", "step-02-design-epics", "step-03-create-stories", "step-04-final-validation"]
inputDocuments:
  - docs/PRD.md
  - docs/FRD.md
  - docs/TRD.md
  - docs/서비스정의서.md
---

# playdata_test - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for playdata_test (인터뷰 SMS 자동 발송 서비스), decomposing the requirements from the PRD, FRD, and TRD into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1:  .env 파일이 없거나 필수 키(NOTION_TOKEN, PPURIO_ID, PPURIO_KEY) 누락 시 1초 이내 오류 메시지 출력 후 종료 (exit code 1)
FR2:  프로그램 시작 시 노션 DB에서 KST 기준 오늘 00:00~23:59의 인터뷰 예정자를 자동 조회
FR3:  연락처를 11자리 숫자(010 시작)로 정규화(normalize_phone), 정규화 불가 시 해당 건 '형식오류' 처리하고 계속 진행
FR4:  노션 DB 내 동일 연락처 중복 건은 첫 번째만 유지(dedup_by_phone)
FR5:  기수 필드값에 알려진 기수 키워드 포함 여부로 resolved_cohort 결정 (resolve_cohort — contains 방식)
FR6:  오늘 이미 성공 발송된 번호(is_already_sent_today)는 '중복건너뜀'으로 처리하고 발송 제외
FR7:  발송 전 담당자에게 목록 미리보기 표시 (이름, 연락처, 기수 원본값, resolved_cohort, 발신번호)
FR8:  담당자가 Y를 입력해야만 뿌리오 API로 발송 실행 (N 입력 시 발송 없이 종료)
FR9:  예정자 0명일 때 "오늘 인터뷰 예정자 없습니다" 출력 후 종료
FR10: 뿌리오 LMS API로 고정 문구(SMS_MESSAGE)를 기수별 발신번호로 일괄 발송
FR11: resolved_cohort=None(기수 매핑 실패) 시 해당 건 '매핑없음' 처리, 다음 건 계속 진행
FR12: 발송 결과를 logs/YYYY-MM-DD.csv에 UTF-8-BOM으로 기록 (cohort 원본값 + resolved_cohort 분리 컬럼 포함)
FR13: 경고 행(매핑없음, 형식오류 등) CSV 상단 배치
FR14: logs/ 폴더가 없으면 자동 생성
FR15: run.bat 더블클릭으로 실행 가능 (Windows)

### NonFunctional Requirements

NFR1: 전체 실행 완료 시간 60초 이내
NFR2: 노션 API 및 뿌리오 API 각 30초 타임아웃
NFR3: 노션 API 호출 간격 1초 이상 (과호출 방지)
NFR4: 연락처 형식: 11자리 숫자 (010 시작)
NFR5: 자격증명(API 키)은 .env 파일에만 보관 (보안)
NFR6: 외부 패키지는 requests, python-dotenv 2개만 사용 (운영)
NFR7: Python 3.10 이상 필요

### Additional Requirements

- AR1: TRD §2 디렉터리 구조 그대로 생성 (main.py, config.py, notion_client.py, ppurio_client.py, logger.py, run.bat, tests/, logs/)
- AR2: requirements.txt + requirements-dev.txt 생성 (버전 고정)
- AR3: .env.example 파일 생성
- AR4: .gitignore 설정 (.env, logs/*.csv, venv/ 등 제외)
- AR5: TRD §7의 pytest 테스트 코드 전체 구현 (test_notion_client, test_config, test_logger, test_ppurio_client)
- AR6: 뿌리오 API 엔드포인트는 [확인 필요] 플레이스홀더 유지
- AR7: app.log 파일에 콘솔 + 파일 이중 로깅 (setup_logger 구현)
- AR8: README.md 작성 (실행 방법 + 신규 기수 추가 방법 포함)

### UX Design Requirements

해당 없음 (CLI 도구 — UI 없음)

### FR Coverage Map

FR1:  Epic 1 — .env 검증 실패 시 즉시 종료 (validate_config)
FR2:  Epic 2 — 노션 DB 당일 예정자 자동 조회
FR3:  Epic 2 — 연락처 정규화 (normalize_phone)
FR4:  Epic 2 — 노션 내 중복 연락처 제거 (dedup_by_phone)
FR5:  Epic 2 — 기수 포함 방식 매핑 (resolve_cohort)
FR6:  Epic 2 — 오늘 성공 발송 번호 중복 제외 (is_already_sent_today)
FR7:  Epic 2 — 발송 전 목록 미리보기 표시 (show_preview)
FR8:  Epic 2 — 담당자 Y/N 수동 발송 확인 (confirm_send)
FR9:  Epic 2 — 예정자 0명 시 메시지 출력 후 종료
FR10: Epic 2 — 뿌리오 LMS API 고정 문구 일괄 발송
FR11: Epic 2 — 기수 매핑 실패 시 '매핑없음' 처리, 계속 진행
FR12: Epic 2 — 결과를 logs/YYYY-MM-DD.csv (UTF-8-BOM) 기록
FR13: Epic 2 — 경고 행 CSV 상단 배치
FR14: Epic 2 — logs/ 폴더 없으면 자동 생성
FR15: Epic 1 — run.bat 더블클릭 실행 (Windows)
AR1:  Epic 1 — 디렉터리 구조 생성
AR2:  Epic 1 — requirements.txt + requirements-dev.txt (버전 고정)
AR3:  Epic 1 — .env.example 생성
AR4:  Epic 1 — .gitignore 설정
AR5:  Epic 1, Epic 2 — 각 에픽 스토리 AC로 분산 (pytest 전량)
AR6:  Epic 2 — 뿌리오 API 플레이스홀더 유지
AR7:  Epic 2 — app.log 콘솔 + 파일 이중 로깅 (setup_logger)
AR8:  Epic 1 — README.md 작성

## Epic List

### Epic 1: 프로젝트 초기화 및 설정 모듈
개발자/담당자가 저장소를 클론하고 `.env` 파일만 채우면 즉시 실행 가능한 환경이 갖춰진다. `config.py`를 통해 기수 매핑·발신번호·문자 내용이 관리되며, 설정 오류는 실행 즉시 감지된다.
**FRs covered:** FR1, FR15, AR1, AR2, AR3, AR4, AR5(test_config), AR8

### Epic 2: 핵심 발송 파이프라인
담당자가 `python main.py`(또는 run.bat)를 실행하면 노션에서 오늘 인터뷰 예정자를 자동 조회하고, 정규화·중복 제거·기수 매핑을 거쳐 미리보기를 보여준다. 담당자가 Y를 입력하면 뿌리오 LMS를 통해 일괄 발송되고 결과가 CSV에 기록된다. 구현 순서: logger.py → notion_client.py → ppurio_client.py → main.py
**FRs covered:** FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, AR5(나머지 테스트), AR6, AR7

---

## Epic 1: 프로젝트 초기화 및 설정 모듈

개발자/담당자가 저장소를 클론하고 `.env` 파일만 채우면 즉시 실행 가능한 환경이 갖춰진다. `config.py`를 통해 기수 매핑·발신번호·문자 내용이 관리되며, 설정 오류는 실행 즉시 감지된다.

### Story 1.1: 프로젝트 골격 및 의존성 설정

As a **개발자**,
I want **프로젝트 디렉터리 구조와 의존성 파일이 준비된 저장소**,
So that **저장소를 클론한 후 `pip install -r requirements-dev.txt` 한 줄로 개발 환경을 즉시 갖출 수 있다**.

**Acceptance Criteria:**

**Given** 저장소를 클론한 빈 상태에서
**When** TRD §2의 디렉터리 구조대로 파일/폴더를 생성하면
**Then** `interview-sms/` 아래 `main.py`, `config.py`, `notion_client.py`, `ppurio_client.py`, `logger.py`, `run.bat`, `tests/__init__.py`, `logs/.gitkeep`이 모두 존재한다

**Given** `requirements.txt`와 `requirements-dev.txt`가 생성되었을 때
**When** `pip install -r requirements-dev.txt`를 실행하면
**Then** `requests==2.31.0`, `python-dotenv==1.0.1`, `pytest==8.1.1`이 설치되고 오류가 없다

**Given** `.env.example`이 존재할 때
**When** 내용을 확인하면
**Then** `NOTION_TOKEN`, `PPURIO_ID`, `PPURIO_KEY` 세 개의 키가 안내 주석과 함께 포함되어 있다

**Given** `.gitignore`가 존재할 때
**When** 내용을 확인하면
**Then** `.env`, `logs/*.csv`, `logs/*.log`, `venv/`, `__pycache__/`가 모두 포함되어 있다

### Story 1.2: config.py — 설정값 및 기수 매핑 모듈

As a **채용 운영 담당자**,
I want **기수별 발신번호 매핑과 환경 변수 검증이 config.py 한 곳에서 관리되는 것**,
So that **신규 기수 추가 시 config.py 한 줄만 수정하면 되고, 자격증명 누락 시 실행 즉시 오류가 표시된다**.

**Acceptance Criteria:**

**Given** `COHORT_SENDER_MAP = {"33기": "01025327302", "34기": "01067757302"}`가 정의되었을 때
**When** `resolve_cohort("SFAC 33기")`를 호출하면
**Then** `"33기"`를 반환한다

**Given** `resolve_cohort`를 호출할 때
**When** 기수 필드값에 알려진 키워드가 없으면 (예: `"35기 지원자"`)
**Then** `None`을 반환한다

**Given** `resolve_cohort`를 호출할 때
**When** 빈 문자열 또는 `None`을 입력하면
**Then** `None`을 반환한다

**Given** `.env`에 `NOTION_TOKEN`, `PPURIO_ID`, `PPURIO_KEY`가 모두 설정된 상태에서
**When** `validate_config()`를 호출하면
**Then** 예외 없이 정상 완료된다

**Given** `.env`에 하나 이상의 필수 키가 누락된 상태에서
**When** `validate_config()`를 호출하면
**Then** `ValueError`가 raise되고 누락된 키 이름이 메시지에 포함된다

**Given** `test_config.py`의 pytest 테스트를 실행할 때
**When** `pytest tests/test_config.py -v`를 실행하면
**Then** `TestValidateConfig`, `TestResolveCohort`, `TestCohortSenderMap` 전체 케이스가 PASS한다

### Story 1.3: run.bat 및 README 작성

As a **채용 운영 담당자**,
I want **터미널 없이 더블클릭으로 실행하고, 신규 기수 추가/발신번호 변경 방법을 README에서 찾을 수 있는 것**,
So that **개발자 도움 없이 혼자 운영할 수 있다**.

**Acceptance Criteria:**

**Given** `venv/`가 설치된 상태에서 `run.bat`을 더블클릭하면
**When** 실행되면
**Then** `venv\Scripts\python.exe main.py`가 실행되고, 오류 시 오류 코드와 함께 창이 멈춘다 (`pause`)

**Given** `README.md`가 작성되었을 때
**When** 내용을 확인하면
**Then** 실행 방법, 신규 기수 추가 방법(`COHORT_SENDER_MAP`), 발신번호 변경 방법, 노션 DB 필드명 변경 방법, 중복 발송 방지 설명이 모두 포함되어 있다

---

## Epic 2: 핵심 발송 파이프라인

담당자가 `python main.py`(또는 run.bat)를 실행하면 노션에서 오늘 인터뷰 예정자를 자동 조회하고, 정규화·중복 제거·기수 매핑을 거쳐 미리보기를 보여준다. 담당자가 Y를 입력하면 뿌리오 LMS를 통해 일괄 발송되고 결과가 CSV에 기록된다. 구현 순서: `logger.py` → `notion_client.py` → `ppurio_client.py` → `main.py`

### Story 2.1: logger.py — CSV 기록 및 중복 발송 방지

As a **채용 운영 담당자**,
I want **발송 결과가 날짜별 CSV에 자동 기록되고, 오늘 이미 성공 발송된 번호는 자동으로 건너뛰는 것**,
So that **재실행 시 이중 발송 없이 안전하게 운영할 수 있다**.

**Acceptance Criteria:**

**Given** 오늘 날짜 CSV에 특정 번호의 `결과=성공` 행이 있을 때
**When** `is_already_sent_today("01012345678", log_dir)`를 호출하면
**Then** `True`를 반환한다

**Given** 오늘 날짜 CSV에 특정 번호의 `결과=실패` 행만 있을 때
**When** `is_already_sent_today`를 호출하면
**Then** `False`를 반환한다 (실패 기록은 중복 방지 대상 아님 — 재발송 가능)

**Given** 오늘 날짜 CSV 파일이 존재하지 않을 때
**When** `is_already_sent_today`를 호출하면
**Then** `False`를 반환한다

**Given** `logs/` 폴더가 존재하지 않을 때
**When** CSV 기록 함수를 실행하면
**Then** `logs/` 폴더가 자동 생성되고 CSV가 정상 기록된다

**Given** 발송 결과 목록을 CSV로 저장할 때
**When** `결과`가 `성공`이 아닌 행이 포함되어 있으면
**Then** 해당 행이 CSV 상단에 위치한다

**Given** CSV가 저장될 때
**When** 파일 인코딩을 확인하면
**Then** UTF-8-BOM(`utf-8-sig`)이고 컬럼은 `executed_at`, `name`, `phone`, `cohort`, `resolved_cohort`, `sender_number`, `result`, `error_msg`이다

**Given** `pytest tests/test_logger.py -v`를 실행하면
**When** 테스트가 완료되면
**Then** `TestIsAlreadySentToday` 전체 케이스가 PASS한다

### Story 2.2: notion_client.py — 노션 당일 예정자 조회

As a **채용 운영 담당자**,
I want **프로그램 실행 시 노션 DB에서 오늘 KST 기준 인터뷰 예정자가 자동으로 조회되고, 연락처 정규화·중복 제거·기수 매핑까지 완료된 목록이 반환되는 것**,
So that **수작업 없이 발송 준비가 자동으로 완료된다**.

**Acceptance Criteria:**

**Given** 노션 DB에 오늘 KST 날짜의 예정자가 있을 때
**When** `fetch_today_interviewees()`를 호출하면
**Then** KST 00:00~23:59 범위의 예정자만 반환되며, UTC 변환 필터가 올바르게 적용된다

**Given** 연락처 필드값이 `"+82-10-1234-5678"` 형태일 때
**When** `normalize_phone`을 통해 정규화하면
**Then** `"01012345678"`을 반환한다

**Given** 연락처 필드값이 `"031-123-4567"` 형태일 때
**When** `normalize_phone`을 적용하면
**Then** `None`을 반환하고 해당 건은 `형식오류`로 처리된다

**Given** 노션 DB에 동일 연락처가 2건 있을 때
**When** `dedup_by_phone`을 적용하면
**Then** 첫 번째 건만 남고 중복이 제거된다

**Given** 기수 필드값이 `"플레이데이터 34기 수강생"`일 때
**When** `resolve_cohort`를 통해 매핑하면
**Then** `resolved_cohort = "34기"`가 된다

**Given** 노션 API가 30초 내에 응답하지 않을 때
**When** 타임아웃이 발생하면
**Then** 예외가 raise되어 상위 호출자(main.py)로 전파된다

**Given** `pytest tests/test_notion_client.py -v`를 실행하면
**When** 테스트가 완료되면
**Then** `TestNormalizePhone`, `TestDedupByPhone` 전체 케이스가 PASS한다

### Story 2.3: ppurio_client.py — 뿌리오 LMS 발송

As a **채용 운영 담당자**,
I want **기수별 발신번호로 고정 문구 LMS가 한 건씩 안전하게 발송되는 것**,
So that **기수 혼동 없이 정확한 번호로 발송되고, 실패 시 다음 건이 계속 진행된다**.

**Acceptance Criteria:**

**Given** `sender=None` (기수 매핑 실패)인 건을 발송하려 할 때
**When** `send_lms(phone, sender=None, message)`를 호출하면
**Then** `{"result": "매핑없음"}`을 반환하고 API 호출 없이 다음 건으로 넘어간다

**Given** 뿌리오 API 호출 중 예외가 발생할 때
**When** `send_lms`가 예외를 잡으면
**Then** `{"result": "실패", "error_msg": "<오류내용>"}`을 반환하고 다음 건으로 넘어간다

**Given** 정상 발송 요청이 전달될 때
**When** API 요청 바디를 확인하면
**Then** `type=lms`, `from=발신번호(하이픈 없음)`, `content=SMS_MESSAGE 고정 문구 그대로`가 포함된다

**Given** 뿌리오 API 엔드포인트가 아직 미확인 상태일 때
**When** `ppurio_client.py`를 확인하면
**Then** `PPURIO_API_URL = "[뿌리오 API 엔드포인트 확인 후 기입]"` 플레이스홀더가 유지된다

**Given** `pytest tests/test_ppurio_client.py -v`를 실행하면
**When** 테스트가 완료되면
**Then** `TestSendLms` 전체 케이스가 PASS한다

### Story 2.4: main.py — 전체 오케스트레이션 및 발송 확인 흐름

As a **채용 운영 담당자**,
I want **`python main.py` 실행 한 번으로 노션 조회 → 미리보기 → Y 확인 → 발송 → CSV 기록까지 완전한 흐름이 실행되는 것**,
So that **매일 아침 실행만 하면 인터뷰 SMS 발송 업무가 완료된다**.

**Acceptance Criteria:**

**Given** `.env`가 없거나 필수 키가 누락된 상태에서 실행하면
**When** `validate_config()`가 호출되면
**Then** 오류 메시지가 출력되고 1초 이내 종료된다 (exit code 1)

**Given** 오늘 인터뷰 예정자가 0명일 때
**When** 노션 조회 후 결과를 확인하면
**Then** "오늘 인터뷰 예정자 없습니다" 메시지 출력 후 종료된다

**Given** 예정자 목록이 조회되었을 때
**When** 미리보기가 표시되면
**Then** 각 행에 이름, 연락처, 기수 원본값, resolved_cohort, 발신번호가 포함된다

**Given** 미리보기가 표시된 후 담당자가 `N`을 입력하면
**When** `confirm_send()`가 실행되면
**Then** 발송 없이 종료된다 (노션 조회는 이미 완료된 상태)

**Given** 담당자가 `Y`를 입력하면
**When** 발송 루프가 실행되면
**Then** 오늘 이미 성공 발송된 번호는 건너뛰고(`is_already_sent_today`), 나머지는 `send_lms`를 호출하며, 전체 결과가 `logs/YYYY-MM-DD.csv`에 기록된다

**Given** 정상 실행 조건에서 전체 플로우가 완료될 때
**When** 완료 시간을 측정하면
**Then** 60초 이내에 종료된다 (NFR1)

**Given** `setup_logger()`가 호출될 때
**When** 로그가 출력되면
**Then** 콘솔과 `logs/app.log` 파일 양쪽에 기록된다
