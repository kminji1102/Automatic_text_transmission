# Interview SMS

노션 인터뷰 일정 DB에서 오늘 예정자를 조회한 뒤, 담당자가 대상자를 확인하고 뿌리오 LMS를 발송하는 Python 프로그램입니다. 웹 화면과 CLI 실행을 모두 지원하며, 발송 결과와 사용 이력은 CSV로 남깁니다.

## 주요 기능

- 노션 데이터 소스에서 KST 기준 오늘 인터뷰 예정자 조회
- 연락처 정규화 및 중복 연락처 제거
- 캠퍼스/지역 키워드 기반 발신번호 자동 매핑
- 오늘 이미 성공 발송된 연락처 자동 건너뜀
- 웹 화면에서 대상자 검색, 전체 선택/해제, 개별 선택, 문자 내용 수정 후 발송
- CLI에서 발송 제외 대상 입력 후 최종 확인 발송
- 뿌리오 허용 IP 오류를 `실패(허용IP)`로 구분해 안내
- 발송 결과 로그와 웹 사용 이력 로그 저장

## 빠른 시작

```powershell
git clone https://github.com/kminji1102/Automatic_text_transmission.git
cd Automatic_text_transmission

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

테스트까지 실행하려면 개발 의존성을 설치합니다.

```powershell
pip install -r requirements-dev.txt
```

## 로컬 설정

`config.py`와 `.env`는 개인 설정과 민감값을 담기 때문에 Git에 올리지 않습니다. 처음 내려받은 환경에서는 예시 파일을 복사해서 만듭니다.

```powershell
Copy-Item config.example.py config.py
Copy-Item .env.example .env
```

`.env`에 API 인증값을 입력합니다.

```dotenv
NOTION_TOKEN=secret_...
PPURIO_ID=...
PPURIO_KEY=...
```

`config.py`에서 노션 데이터 소스, 필드명, 발신번호 매핑, 기본 문자 내용을 실제 운영값으로 수정합니다.

```python
NOTION_DATA_SOURCE_ID = "노션_데이터소스_ID"
NOTION_FIELD_DATE = "인터뷰일자"
NOTION_FIELD_COHORT = "기수"
NOTION_FIELD_PHONE = "연락처"
NOTION_FIELD_NAME = "이름"

COHORT_SENDER_MAP = {
    "동작": "010-6775-7302",
    "서초": "010-2532-7302",
    "G밸리": "010-2598-7302",
}
```

발신번호 매핑은 포함 방식입니다. 예를 들어 노션 기수 값이 `SFAC 동작 33기`, `플레이데이터 G밸리 34기 수강생`처럼 들어오면 각각 `"동작"`, `"G밸리"` 키가 포함되어 있으므로 해당 발신번호로 매핑됩니다. `35기 지원자`처럼 지역 키워드가 없으면 `매핑없음`으로 처리됩니다.

## 웹 화면 실행

```powershell
venv\Scripts\activate
python web_app.py --host 0.0.0.0 --port 8000
```

Windows에서는 `run_web.bat`을 더블클릭해도 됩니다.

- 실행한 PC: `http://127.0.0.1:8000`
- 같은 네트워크의 다른 사용자: `http://<실행-PC-IP>:8000`

웹 화면 흐름은 다음과 같습니다.

1. 사용자 이름 입력
2. 오늘 발송 후보 미리보기
3. 문자 내용 확인 또는 수정
4. 발송 대상 체크박스 선택
5. 최종 확인 후 발송
6. 결과 화면과 사용 이력 확인

웹 사용 이력은 `logs/usage-YYYY-MM-DD.csv`에 저장됩니다. 주요 컬럼은 `executed_at`, `user_name`, `client_ip`, `action`, `result`, `detail`입니다.

## CLI 실행

터미널에서 기존 콘솔 방식으로 실행할 수도 있습니다.

```powershell
venv\Scripts\activate
python main.py
```

Windows에서는 `run.bat`을 더블클릭해도 됩니다.

미리보기 목록이 표시되면 발송에서 제외할 번호를 입력합니다. 제외할 대상이 없으면 Enter를 누르고, 발송을 취소하려면 `N`을 입력합니다. 마지막 Y/N 확인에서 `Y`를 입력한 경우에만 실제 발송합니다.

## 로그

발송 결과는 `logs/YYYY-MM-DD.csv`에 저장됩니다.

주요 결과값:

- `성공`: 뿌리오 발송 성공
- `실패`: API 오류 등 일반 실패
- `실패(타임아웃)`: API 응답 타임아웃
- `실패(허용IP)`: 뿌리오 관리자에 현재 공인 IP가 허용 IP로 등록되지 않음
- `형식오류`: 연락처 형식 오류
- `매핑없음`: 캠퍼스/지역 키워드로 발신번호를 찾지 못함
- `중복건너뜀`: 오늘 이미 성공 발송된 연락처라 발송 제외

로그 날짜와 중복 판단 기준은 `KST = timezone(timedelta(hours=9))`입니다. 실패, 형식 오류, 매핑 실패 기록은 성공 발송이 아니므로 다시 실행하면 재처리할 수 있습니다.

## 검증

전체 테스트:

```powershell
pytest tests/ -v
```

빠른 검증 스크립트:

```powershell
.\validate-quick.ps1
```

현재 테스트 구조는 `TestXxx` 클래스와 `test_xxx` 메서드 형식을 유지합니다.

## 파일 구조

```text
main.py              # CLI 실행 흐름
web_app.py           # 웹 서버와 HTML 렌더링
sms_service.py       # 웹/CLI 공통 발송 서비스
notion_client.py     # 노션 조회, 연락처 정규화, 중복 제거
ppurio_client.py     # 뿌리오 토큰 발급 및 LMS 발송
logger.py            # 발송 결과 CSV 로그
usage_logger.py      # 웹 사용 이력 CSV 로그
config.example.py    # config.py 생성용 예시
.env.example         # .env 생성용 예시
static/              # 웹 화면 CSS/JS
tests/               # pytest 테스트
```

## 운영 메모

- `.env`, `config.py`, `logs/*.csv`, `logs/*.log`는 Git에 올리지 않습니다.
- 신규 캠퍼스나 발신번호는 `config.py`의 `COHORT_SENDER_MAP`에만 추가합니다.
- 발신번호는 뿌리오에 사전 등록되어 있어야 합니다.
- `실패(허용IP)`가 나오면 뿌리오 관리자에서 실행 PC 또는 서버의 공인 IP를 허용 IP로 등록한 뒤 다시 발송합니다.
