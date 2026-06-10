import csv
import glob
import os
import threading
from datetime import datetime

from config import KST, LOG_DIR

USAGE_COLUMNS = [
    "executed_at",
    "user_name",
    "client_ip",
    "action",
    "result",
    "detail",
]

_WRITE_LOCK = threading.Lock()


def _usage_log_path(log_dir: str, target_date: str | None = None) -> str:
    date_str = target_date or datetime.now(KST).strftime("%Y-%m-%d")
    return os.path.join(log_dir, f"usage-{date_str}.csv")


def normalize_user_name(raw: str | None) -> str:
    normalized = " ".join((raw or "").strip().split())
    return normalized[:80]


def write_usage_event(
    user_name: str,
    action: str,
    result: str,
    detail: str = "",
    client_ip: str = "",
    log_dir: str = LOG_DIR,
    target_date: str | None = None,
) -> str:
    os.makedirs(log_dir, exist_ok=True)
    log_path = _usage_log_path(log_dir, target_date)
    row = {
        "executed_at": datetime.now(KST).isoformat(timespec="seconds"),
        "user_name": normalize_user_name(user_name) or "unknown",
        "client_ip": client_ip,
        "action": action,
        "result": result,
        "detail": detail,
    }

    with _WRITE_LOCK:
        should_write_header = not os.path.exists(log_path) or os.path.getsize(log_path) == 0
        with open(log_path, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=USAGE_COLUMNS)
            if should_write_header:
                writer.writeheader()
            writer.writerow({column: row.get(column, "") for column in USAGE_COLUMNS})

    return log_path


def read_usage_events(log_dir: str = LOG_DIR, limit: int = 100) -> list[dict]:
    pattern = os.path.join(log_dir, "usage-*.csv")
    rows: list[dict] = []
    for path in sorted(glob.glob(pattern)):
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows.extend(csv.DictReader(f))
    return rows[-limit:]
