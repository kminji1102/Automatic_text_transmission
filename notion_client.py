import re
from datetime import datetime, timedelta, timezone

import requests

import config
from config import KST

NOTION_API_URL = f"https://api.notion.com/v1/databases/{config.NOTION_DB_ID}/query"
NOTION_VERSION = "2022-06-28"


def normalize_phone(raw: str) -> str | None:
    """
    입력된 연락처를 11자리 숫자로 정규화. 불가 시 None 반환.
    """
    if not raw:
        return None
    raw = str(raw).strip()
    if raw.startswith("+82"):
        digits = "0" + re.sub(r"[^0-9]", "", raw[3:])
    else:
        digits = re.sub(r"[^0-9]", "", raw)
    if len(digits) == 11 and digits.startswith("010"):
        return digits
    return None


def build_today_filter(field_name: str) -> dict:
    """KST 기준 오늘 00:00 ~ 23:59를 UTC로 변환한 노션 날짜 필터"""
    now_kst = datetime.now(KST)
    today_start_kst = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start_kst = today_start_kst + timedelta(days=1)
    today_start_utc = today_start_kst.astimezone(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )
    tomorrow_start_utc = tomorrow_start_kst.astimezone(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )
    return {
        "filter": {
            "and": [
                {"property": field_name, "date": {"on_or_after": today_start_utc}},
                {"property": field_name, "date": {"before": tomorrow_start_utc}},
            ]
        }
    }


def fetch_today_interviewees() -> list[dict]:
    headers = {
        "Authorization": f"Bearer {config.NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }
    payload = build_today_filter(config.NOTION_FIELD_DATE)
    pages = []
    start_cursor = None

    while True:
        request_payload = dict(payload)
        if start_cursor:
            request_payload["start_cursor"] = start_cursor

        response = requests.post(
            NOTION_API_URL,
            headers=headers,
            json=request_payload,
            timeout=config.API_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        pages.extend(data.get("results", []))

        if not data.get("has_more"):
            break
        start_cursor = data.get("next_cursor")
        if not start_cursor:
            break

    interviewees = [_parse_page(page) for page in pages]
    return _dedup_preserving_invalid_phone(interviewees)


def _parse_page(page: dict) -> dict:
    properties = page.get("properties", {})
    name = _extract_property_text(properties.get(config.NOTION_FIELD_NAME))
    raw_phone = _extract_property_text(properties.get(config.NOTION_FIELD_PHONE))
    cohort = _extract_property_text(properties.get(config.NOTION_FIELD_COHORT))
    resolved_cohort = config.resolve_cohort(cohort)

    return {
        "name": name,
        "phone": normalize_phone(raw_phone),
        "cohort": cohort,
        "resolved_cohort": resolved_cohort,
    }


def _extract_property_text(prop: dict | str | None) -> str:
    if not prop:
        return ""
    if isinstance(prop, str):
        return prop

    if prop.get("phone_number"):
        return prop["phone_number"] or ""

    for text_key in ("title", "rich_text"):
        text_items = prop.get(text_key)
        if text_items:
            return "".join(item.get("plain_text", "") for item in text_items)

    select_value = prop.get("select")
    if select_value:
        return select_value.get("name", "")

    status_value = prop.get("status")
    if status_value:
        return status_value.get("name", "")

    multi_select = prop.get("multi_select")
    if multi_select:
        return ", ".join(item.get("name", "") for item in multi_select)

    return ""


def _dedup_preserving_invalid_phone(interviewees: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for item in interviewees:
        phone = item.get("phone")
        if not phone:
            result.append(item)
            continue
        if phone not in seen:
            seen.add(phone)
            result.append(item)
    return result
