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

미리보기 목록이 표시되면 발송에서 제외할 번호를 입력합니다.
제외할 대상이 없으면 Enter, 발송을 취소하려면 N을 입력합니다.
이후 최종 Y/N 확인에서 Y를 입력한 경우에만 발송합니다.

## 지역 키워드 추가

`config.py`의 `COHORT_SENDER_MAP`에만 한 줄을 추가합니다.

```python
COHORT_SENDER_MAP = {
    "동작": "010-6775-7302",
    "서초": "010-2532-7302",
    "G밸리": "010-2598-7302",
}
```

노션 기수 필드값에 키가 포함되어 있으면 자동 매핑됩니다.
예를 들어 `SFAC 동작 33기`, `플레이데이터 동작 수강생`은 모두 `"동작"`으로 처리됩니다.

## 발신번호 변경

`config.py`의 해당 지역 번호만 수정합니다.

```python
COHORT_SENDER_MAP = {
    "동작": "010-6775-7302",
    "서초": "010-2532-7302",
    "G밸리": "010-2598-7302",
}
```

새 발신번호는 뿌리오에 사전 등록되어 있어야 합니다.

## 중복 발송 방지

오늘 이미 성공 발송된 번호는 재실행 시 `중복건너뜀`으로 처리되어 다시 발송하지 않습니다.
실패 건이나 형식 오류 건은 성공 발송 기록이 아니므로 재실행 시 다시 처리될 수 있습니다.

중복 판단 기준 날짜는 `KST = timezone(timedelta(hours=9))`입니다.
