import base64
import re

import requests

from config import API_TIMEOUT, PPURIO_ID, PPURIO_KEY, SMS_TYPE

PPURIO_TOKEN_URL = "https://message.ppurio.com/v1/token"
PPURIO_SEND_URL = "https://message.ppurio.com/v1/message"


def _get_access_token() -> str:
    encoded = base64.b64encode(f"{PPURIO_ID}:{PPURIO_KEY}".encode()).decode()
    response = requests.post(
        PPURIO_TOKEN_URL,
        headers={"Authorization": f"Basic {encoded}"},
        timeout=API_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["token"]


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
        token = _get_access_token()
        response = requests.post(
            PPURIO_SEND_URL,
            headers={"Authorization": f"Bearer {token}"},
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
