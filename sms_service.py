import threading

from config import COHORT_SENDER_MAP, LOG_DIR, SMS_MESSAGE, validate_config
from logger import write_results
from main import _precheck_candidates, _result_row, _row_from_send_result
from notion_client import fetch_today_interviewees
from ppurio_client import send_lms

_SEND_LOCK = threading.Lock()


class ServiceError(RuntimeError):
    pass


def build_preview() -> dict:
    validate_config()
    try:
        candidates = fetch_today_interviewees()
    except Exception as exc:
        _write_failure_result("실패", str(exc))
        raise ServiceError(f"노션 API 조회 실패: {exc}") from exc

    prechecked_results, send_candidates = _precheck_candidates(candidates)
    return {
        "candidates": candidates,
        "prechecked_results": prechecked_results,
        "send_candidates": send_candidates,
        "summary": summarize_rows(prechecked_results),
    }


def send_selected_phones(selected_phones: list[str], message: str | None = None) -> dict:
    selected_phone_set = {phone for phone in selected_phones if phone}
    message_to_send = (message if message is not None else SMS_MESSAGE).strip()
    if not message_to_send:
        raise ServiceError("문자 내용을 입력해 주세요.")

    with _SEND_LOCK:
        preview = build_preview()
        selected_candidates = [
            candidate
            for candidate in preview["send_candidates"]
            if candidate.get("phone") in selected_phone_set
        ]

        send_results = []
        for candidate in selected_candidates:
            sender = COHORT_SENDER_MAP.get(candidate.get("resolved_cohort"))
            send_result = send_lms(candidate["phone"], sender, message_to_send)
            send_results.append(_row_from_send_result(candidate, sender, send_result))

        all_results = preview["prechecked_results"] + send_results
        log_path = write_results(all_results, LOG_DIR) if all_results else ""

    return {
        "selected_candidates": selected_candidates,
        "send_results": send_results,
        "prechecked_results": preview["prechecked_results"],
        "all_results": all_results,
        "summary": summarize_rows(all_results),
        "log_path": log_path,
        "requested_count": len(selected_phone_set),
        "sent_count": len(send_results),
        "skipped_count": len(preview["send_candidates"]) - len(selected_candidates),
        "message": message_to_send,
    }


def summarize_rows(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        result = row.get("result", "")
        counts[result] = counts.get(result, 0) + 1
    return counts


def _write_failure_result(result: str, error_msg: str) -> None:
    try:
        write_results([_result_row(result=result, error_msg=error_msg)], LOG_DIR)
    except Exception:
        pass
