# Interview SMS

노션 인터뷰 일정 DB에서 오늘 예정자를 조회하고, 담당자가 화면에서 대상자를 확인한 뒤 뿌리오 LMS를 발송하는 프로그램입니다.

## 웹 화면으로 실행

여러 사용자가 브라우저에서 쉽게 사용할 수 있도록 기본 웹 화면을 제공합니다.

```powershell
venv\Scripts\activate
python web_app.py --host 0.0.0.0 --port 8000
```

Windows에서는 `run_web.bat`을 더블클릭해도 됩니다.

- 실행한 PC: `http://127.0.0.1:8000`
- 같은 네트워크의 다른 사용자: `http://<실행-PC-IP>:8000`

첫 화면에서 사용자 이름을 입력하면 발송 미리보기 화면으로 이동합니다. 미리보기와 발송 시도는 `logs/usage-YYYY-MM-DD.csv`에 `user_name`, `client_ip`, `action`, `result`, `detail` 컬럼으로 기록되고, 웹 화면의 `사용 이력`에서도 최근 기록을 확인할 수 있습니다.

미리보기 화면에는 `config.py`의 기본 문자 내용이 자동으로 채워집니다. 발송 전에 화면의 문자 내용 칸에서 문구를 수정하면, 수정한 내용이 선택된 대상자에게 그대로 발송됩니다.

프론트엔드 코드는 아래 파일에 분리되어 있습니다.

- `web_app.py`: 웹 서버, 화면 HTML 렌더링, 정적 파일 제공
- `static/app.css`: 화면 스타일
- `static/app.js`: 문자 글자 수 표시, 검색, 전체 선택/해제, 선택 수 표시, 발송 전 확인창

## 설치

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

`.env` 파일에는 아래 값을 입력합니다.

```dotenv
NOTION_TOKEN=secret_...
PPURIO_ID=...
PPURIO_KEY=...
```

발신번호는 `.env`가 아니라 `config.py`의 `COHORT_SENDER_MAP`에서 관리합니다.

## CLI 실행

터미널에서 기존 방식으로 실행할 수도 있습니다.

```powershell
python main.py
```

Windows에서는 `run.bat`을 더블클릭해도 됩니다.

```bat
venv\Scripts\python.exe main.py
```

미리보기 목록이 표시되면 발송에서 제외할 번호를 입력합니다. 제외 대상이 없으면 Enter, 발송을 취소하려면 `N`을 입력합니다. 이후 최종 Y/N 확인에서 `Y`를 입력한 경우에만 발송합니다.

## 기수와 발신번호 추가

신규 기수는 `config.py`의 `COHORT_SENDER_MAP`에만 추가합니다.

```python
COHORT_SENDER_MAP = {
    "33기": "01025327302",
    "34기": "01067757302",
    "35기": "010XXXXXXXX",
}
```

노션 기수 필드값에 키가 포함되어 있으면 자동 매핑됩니다. 예를 들어 `SFAC 33기`, `플레이데이터 33기 수강생`은 모두 `"33기"`로 처리됩니다.

## 중복 발송 방지

오늘 이미 `성공`으로 기록된 연락처는 다시 실행해도 `중복건너뜀`으로 처리되고 발송되지 않습니다. 실패, 형식 오류, 매핑 실패 기록은 성공 발송이 아니므로 재처리할 수 있습니다.

중복 판단 날짜 기준은 `KST = timezone(timedelta(hours=9))`입니다.

## 검증

```powershell
pytest tests/ -v
```

빠른 검증 스크립트:

```powershell
.\validate-quick.ps1
```
