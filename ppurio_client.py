import base64
import re
import uuid

import requests

from config import API_TIMEOUT, PPURIO_ID, PPURIO_KEY, SMS_TYPE

PPURIO_TOKEN_URL = "https://message.ppurio.com/v1/token"
PPURIO_SEND_URL = "https://message.ppurio.com/v1/message"


def _get_access_token() -> str:
    encoded = base64.b64encode(f"{PPURIO_ID}:{PPURIO_KEY}".encode()).decode()
    response = requests.post(
        PPURIO_TOKEN_URL,
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        },
        json={},
        timeout=API_TIMEOUT,
    )
    _raise_for_status_with_body(response)
    body = response.json()
    token = body.get("token")
    if not token:
        raise RuntimeError(f"토큰 응답에 token 없음: {body}")
    return token


def send_lms(phone: str, sender: str | None, message: str) -> dict:
    if not sender:
        return {"result": "매핑없음"}

    request_body = {
        "account": PPURIO_ID,
        "messageType": SMS_TYPE.upper(),
        "from": _digits_only(sender),
        "content": message,
        "duplicateFlag": "N",
        "refKey": uuid.uuid4().hex,
        "targetCount": 1,
        "targets": [
            {
                "to": _digits_only(phone),
            }
        ],
    }

    try:
        token = _get_access_token()
        response = requests.post(
            PPURIO_SEND_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=request_body,
            timeout=API_TIMEOUT,
        )
        _raise_for_status_with_body(response)
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


def _raise_for_status_with_body(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        body = (response.text or "").strip()
        if body:
            raise RuntimeError(f"{exc} - {body}") from exc
        raise
