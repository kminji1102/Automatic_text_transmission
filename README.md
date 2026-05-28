# Interview SMS

인터뷰 예정자에게 LMS 안내 문자를 발송하기 위한 Python 스크립트입니다.

## 설치

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

`.env` 파일에 아래 값을 입력합니다.

```dotenv
NOTION_TOKEN=secret_...
PPURIO_ID=...
PPURIO_KEY=...
```

발신번호는 `.env`가 아니라 `config.py`의 `COHORT_SENDER_MAP`에서 관리합니다.

## 실행 방법

```powershell
python main.py
```

Windows에서는 `run.bat`을 더블클릭해 실행할 수 있습니다.

```bat
venv\Scripts\python.exe main.py
```

오류가 발생하면 배치 파일이 `pause`로 창을 유지합니다.

## 신규 기수 추가

`config.py`의 `COHORT_SENDER_MAP`에만 한 줄을 추가합니다.

```python
COHORT_SENDER_MAP = {
    "33기": "01025327302",
    "34기": "01067757302",
    "35기": "010XXXXXXXX",
}
```

노션 기수 필드값에 키가 포함되어 있으면 자동 매핑됩니다.
예를 들어 `SFAC 35기`, `플레이데이터 35기 수강생`은 모두 `"35기"`로 처리됩니다.

## 발신번호 변경

`config.py`의 해당 기수 번호만 수정합니다.

```python
COHORT_SENDER_MAP = {
    "33기": "01025327302",
    "34기": "01067757302",
}
```

새 발신번호는 뿌리오에 사전 등록되어 있어야 합니다.

## 중복 발송 방지

오늘 이미 성공 발송된 번호는 재실행 시 `중복건너뜀`으로 처리되어 다시 발송하지 않습니다.
실패 건이나 형식 오류 건은 성공 발송 기록이 아니므로 재실행 시 다시 처리될 수 있습니다.

중복 판단 기준 날짜는 `KST = timezone(timedelta(hours=9))`입니다.
