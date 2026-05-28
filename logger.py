import csv
import os
from datetime import datetime

from config import KST, LOG_DIR

CSV_COLUMNS = [
    "executed_at",
    "name",
    "phone",
    "cohort",
    "resolved_cohort",
    "sender_number",
    "result",
    "error_msg",
]


def _log_path(log_dir: str, target_date: str | None = None) -> str:
    date_str = target_date or datetime.now(KST).strftime("%Y-%m-%d")
    return os.path.join(log_dir, f"{date_str}.csv")


def is_already_sent_today(phone: str, log_dir: str) -> bool:
    """
    오늘 날짜 CSV에 해당 연락처가 '성공'으로 기록되어 있으면 True.
    실패 기록은 중복 방지 대상이 아니므로 재발송 가능하다.
    """
    log_path = _log_path(log_dir)
    if not os.path.exists(log_path):
        return False

    with open(log_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("phone") == phone and row.get("result") == "성공":
                return True
    return False


def write_results(
    rows: list[dict],
    log_dir: str = LOG_DIR,
    target_date: str | None = None,
) -> str:
    """
    결과를 logs/YYYY-MM-DD.csv에 UTF-8-BOM으로 기록한다.
    기존 당일 로그를 보존하고, 성공이 아닌 행을 CSV 상단에 배치한다.
    """
    os.makedirs(log_dir, exist_ok=True)
    log_path = _log_path(log_dir, target_date)

    existing_rows: list[dict] = []
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8-sig", newline="") as f:
            existing_rows = list(csv.DictReader(f))

    normalized_rows = []
    for row in [*existing_rows, *rows]:
        normalized_rows.append({column: row.get(column, "") for column in CSV_COLUMNS})

    sorted_rows = sorted(
        normalized_rows,
        key=lambda row: 1 if row.get("result") == "성공" else 0,
    )

    with open(log_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(sorted_rows)

    return log_path
