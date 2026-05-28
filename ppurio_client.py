import re

import requests

from config import API_TIMEOUT, SMS_TYPE

PPURIO_API_URL = "[뿌리오 API 엔드포인트 확인 후 기입]"


def send_lms(phone: str, sender: str | None, message: str) -> dict:
    if not sender:
        return {"result": "매핑없음"}

    request_body = {
        "type": SMS_TYPE,
        "from": _digits_only(sender),
        "to": _digits_only(phone),
        "content": message,
    }

    try:
        response = requests.post(
            PPURIO_API_URL,
            json=request_body,
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        try:
            body = response.json()
        except Exception:
            body = {}
        return {"result": "성공", "response": body}
    except requests.exceptions.Timeout:
        return {"result": "실패(타임아웃)", "error_msg": "API 응답 타임아웃"}
    except Exception as exc:
        return {"result": "실패", "error_msg": str(exc)}


def _digits_only(value: str) -> str:
    return re.sub(r"[^0-9]", "", value or "")
