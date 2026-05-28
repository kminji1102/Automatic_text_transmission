import csv
from datetime import datetime

from config import KST
from logger import CSV_COLUMNS, is_already_sent_today, write_results


class TestIsAlreadySentToday:
    def test_returns_false_when_no_log_file(self, tmp_path):
        assert is_already_sent_today("01012345678", str(tmp_path)) is False

    def test_returns_true_when_success_record_exists(self, tmp_path):
        today_str = datetime.now(KST).strftime("%Y-%m-%d")
        log_path = tmp_path / f"{today_str}.csv"
        with open(log_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerow(
                {
                    "executed_at": "2026-05-22T09:05:03",
                    "name": "홍길동",
                    "phone": "01012345678",
                    "cohort": "SFAC 33기",
                    "resolved_cohort": "33기",
                    "sender_number": "01025327302",
                    "result": "성공",
                    "error_msg": "",
                }
            )

        assert is_already_sent_today("01012345678", str(tmp_path)) is True

    def test_returns_false_when_only_failure_record(self, tmp_path):
        today_str = datetime.now(KST).strftime("%Y-%m-%d")
        log_path = tmp_path / f"{today_str}.csv"
        with open(log_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerow(
                {
                    "executed_at": "2026-05-22T09:05:03",
                    "name": "홍길동",
                    "phone": "01012345678",
                    "cohort": "SFAC 33기",
                    "resolved_cohort": "33기",
                    "sender_number": "01025327302",
                    "result": "실패",
                    "error_msg": "timeout",
                }
            )

        assert is_already_sent_today("01012345678", str(tmp_path)) is False


class TestWriteResults:
    def test_creates_log_dir_and_writes_utf8_sig_csv_with_fixed_columns(self, tmp_path):
        log_dir = tmp_path / "logs"
        write_results(
            [
                {
                    "executed_at": "2026-05-22T09:05:03",
                    "name": "홍길동",
                    "phone": "01012345678",
                    "cohort": "SFAC 33기",
                    "resolved_cohort": "33기",
                    "sender_number": "01025327302",
                    "result": "성공",
                    "error_msg": "",
                }
            ],
            str(log_dir),
            target_date="2026-05-22",
        )

        log_path = log_dir / "2026-05-22.csv"
        assert log_path.exists()
        assert log_path.read_bytes().startswith(b"\xef\xbb\xbf")

        with open(log_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == CSV_COLUMNS
            assert list(reader)[0]["result"] == "성공"

    def test_places_non_success_rows_at_top(self, tmp_path):
        write_results(
            [
                {"name": "성공", "phone": "01011112222", "result": "성공"},
                {"name": "매핑", "phone": "", "result": "매핑없음"},
                {"name": "실패", "phone": "01033334444", "result": "실패"},
            ],
            str(tmp_path),
            target_date="2026-05-22",
        )

        with open(tmp_path / "2026-05-22.csv", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

        assert [row["result"] for row in rows] == ["매핑없음", "실패", "성공"]
