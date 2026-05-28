import os
from datetime import timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

# 비밀값 (.env에서 로드)
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PPURIO_ID = os.getenv("PPURIO_ID")
PPURIO_KEY = os.getenv("PPURIO_KEY")

# 노션 설정
NOTION_DB_ID = "8336a73c082d411c8275a1c3015cb36e"
NOTION_FIELD_DATE = "인터뷰일시"
NOTION_FIELD_COHORT = "기수"
NOTION_FIELD_PHONE = "연락처"
NOTION_FIELD_NAME = "이름"

# 기수 -> 발신번호 매핑
# 신규 기수 추가 또는 번호 변경 시 이 딕셔너리만 수정
# 매핑은 포함(contains) 방식: "SFAC 33기" -> "33기" 키로 처리됨
COHORT_SENDER_MAP = {
    "33기": "01025327302",
    "34기": "01067757302",
    # "35기": "010XXXXXXXX",  # 신규 기수 추가 예시
}


def resolve_cohort(raw_cohort: str) -> str | None:
    """
    기수 필드 원본값에서 COHORT_SENDER_MAP 키가 포함되어 있는지 확인.
    포함된 키를 반환하고, 없으면 None 반환.
    예: "SFAC 33기" -> "33기" / "35기 지원자" -> None
    """
    if not raw_cohort:
        return None
    for key in COHORT_SENDER_MAP:
        if key in raw_cohort:
            return key
    return None


SMS_MESSAGE = """안녕하세요.
SK네트웍스 Family AI 캠프입니다.
신청해주신 부트캠프 입과 인터뷰가 오늘 진행될 예정입니다.
인터뷰 세부 일정 및 진행 방식(온라인/오프라인), 접속 링크 등은 담당자가 진행 전 개별 안내드릴 예정입니다.
일정 확인 또는 변경, 취소를 원하시는 경우 아래 채팅 문의 링크를 통해 말씀 부탁드립니다.
감사합니다.
플레이데이터 드림
▶ 채널톡 문의
https://networks-aicamp.channel.io"""

API_TIMEOUT = 30
SMS_TYPE = "lms"
LOG_DIR = "logs"
KST = timezone(timedelta(hours=9))

REQUIRED_ENV_KEYS = ["NOTION_TOKEN", "PPURIO_ID", "PPURIO_KEY"]


def validate_config():
    missing = [key for key in REQUIRED_ENV_KEYS if not os.getenv(key)]
    if missing:
        raise ValueError(f"설정 파일 누락: {', '.join(missing)}")
