import logging
import os
import sys
from datetime import datetime

from config import COHORT_SENDER_MAP, KST, LOG_DIR, SMS_MESSAGE, resolve_cohort, validate_config
from logger import write_results
from logger import is_already_sent_today
from notion_client import fetch_today_interviewees
from ppurio_client import send_lms


def setup_logger(name: str = "interview_sms") -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    app_logger = logging.getLogger(name)
    app_logger.setLevel(logging.INFO)
    if app_logger.handlers:
        return app_logger

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    app_logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(
        os.path.join(LOG_DIR, "app.log"),
        encoding="utf-8",
        mode="a",
    )
    file_handler.setFormatter(formatter)
    app_logger.addHandler(file_handler)
    return app_logger


def show_preview(candidates: list[dict]) -> None:
    print("\n" + "=" * 60)
    print(f"오늘 인터뷰 예정자 - 발송 목록 ({len(candidates)}명)")
    print("=" * 60)
    for index, candidate in enumerate(candidates, 1):
        resolved_cohort = candidate.get("resolved_cohort") or "매핑없음"
        sender = COHORT_SENDER_MAP.get(candidate.get("resolved_cohort"), "번호없음")
        print(
            f"  {index}. {candidate.get('name', '')} | {candidate.get('phone', '')} "
            f"| 기수: {candidate.get('cohort', '')} -> {resolved_cohort} | 발신: {sender}"
        )
    print("=" * 60)
    print("노션 조회는 자동 완료되었습니다. 아래에서 발송 여부를 직접 확인하세요.")


def confirm_send() -> bool:
    answer = input("\n위 목록으로 발송하시겠습니까? (Y/N): ").strip().upper()
    return answer == "Y"


def parse_selection_indices(raw: str, count: int) -> list[int]:
    raw = (raw or "").strip()
    if not raw:
        return list(range(1, count + 1))
    indices: list[int] = []
    for token in raw.replace(",", " ").split():
        if not token.isdigit():
            raise ValueError(f"잘못된 입력: {token}")
        num = int(token)
        if num < 1 or num > count:
            raise ValueError(f"범위를 벗어난 번호: {num}")
        if num not in indices:
            indices.append(num)
    return sorted(indices)


def main() -> int:
    app_logger = setup_logger()

    try:
        validate_config()
    except ValueError as exc:
        print(f"오류: {exc}")
        app_logger.error("설정 검증 실패: %s", exc)
        return 1

    try:
        candidates = fetch_today_interviewees()
    except Exception as exc:
        error_msg = str(exc)
        print(f"오류: 노션 API 조회 실패 - {error_msg}")
        app_logger.exception("노션 API 조회 실패")
        _write_results_or_fail([_result_row(result="실패", error_msg=error_msg)])
        return 1

    if not candidates:
        print("오늘 인터뷰 예정자 없습니다")
        app_logger.info("오늘 인터뷰 예정자 없음")
        return 0

    prechecked_results, send_candidates = _precheck_candidates(candidates)

    if not send_candidates:
        print("오늘 발송 대상 없습니다")
        return _write_results_or_fail(prechecked_results)

    show_preview(send_candidates)
    if not confirm_send():
        print("발송을 취소했습니다")
        app_logger.info("담당자 확인에서 발송 취소")
        return 0

    send_results = []
    for candidate in send_candidates:
        sender = COHORT_SENDER_MAP.get(candidate.get("resolved_cohort"))
        send_result = send_lms(candidate["phone"], sender, SMS_MESSAGE)
        send_results.append(_row_from_send_result(candidate, sender, send_result))

    all_results = prechecked_results + send_results
    write_status = _write_results_or_fail(all_results)
    if write_status == 0:
        _print_summary(all_results)
    return write_status


def _precheck_candidates(candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    prechecked_results = []
    send_candidates = []

    for candidate in candidates:
        candidate["resolved_cohort"] = candidate.get("resolved_cohort") or resolve_cohort(
            candidate.get("cohort", "")
        )

        if not candidate.get("phone"):
            prechecked_results.append(
                _result_row(
                    candidate,
                    result="형식오류",
                    error_msg="연락처 형식 오류",
                )
            )
            continue

        if is_already_sent_today(candidate["phone"], LOG_DIR):
            prechecked_results.append(
                _result_row(
                    candidate,
                    sender=COHORT_SENDER_MAP.get(candidate.get("resolved_cohort")),
                    result="중복건너뜀",
                    error_msg="오늘 이미 성공 발송됨",
                )
            )
            continue

        send_candidates.append(candidate)

    return prechecked_results, send_candidates


def _row_from_send_result(candidate: dict, sender: str | None, send_result: dict) -> dict:
    result = send_result.get("result", "실패")
    error_msg = send_result.get("error_msg", "")
    if result == "매핑없음" and not error_msg:
        cohort = candidate.get("cohort") or "기수"
        error_msg = f"{cohort} 발신번호 없음"

    return _result_row(
        candidate,
        sender=sender,
        result=result,
        error_msg=error_msg,
    )


def _result_row(
    candidate: dict | None = None,
    sender: str | None = None,
    result: str = "",
    error_msg: str = "",
) -> dict:
    candidate = candidate or {}
    return {
        "executed_at": datetime.now(KST).isoformat(timespec="seconds"),
        "name": candidate.get("name", ""),
        "phone": candidate.get("phone") or "",
        "cohort": candidate.get("cohort", ""),
        "resolved_cohort": candidate.get("resolved_cohort") or "",
        "sender_number": sender or "",
        "result": result,
        "error_msg": error_msg,
    }


def _write_results_or_fail(rows: list[dict]) -> int:
    if not rows:
        return 0
    try:
        write_results(rows, LOG_DIR)
        return 0
    except Exception as exc:
        print(f"오류: CSV 기록 실패 - {exc}")
        logging.getLogger("interview_sms").exception("CSV 기록 실패")
        return 1


def _print_summary(rows: list[dict]) -> None:
    counts = {}
    for row in rows:
        result = row.get("result", "")
        counts[result] = counts.get(result, 0) + 1

    summary = ", ".join(f"{result} {count}건" for result, count in counts.items())
    print(f"발송 처리 완료: {summary}")


if __name__ == "__main__":
    sys.exit(main())
