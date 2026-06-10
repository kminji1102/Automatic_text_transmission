import csv

from usage_logger import USAGE_COLUMNS, read_usage_events, write_usage_event


class TestUsageLogger:
    def test_write_usage_event_creates_utf8_sig_csv(self, tmp_path):
        log_path = write_usage_event(
            "  minji   kim  ",
            "preview",
            "success",
            '{"sendable": 2}',
            "127.0.0.1",
            str(tmp_path),
            target_date="2026-05-28",
        )

        assert (tmp_path / "usage-2026-05-28.csv").exists()
        assert (tmp_path / "usage-2026-05-28.csv").read_bytes().startswith(b"\xef\xbb\xbf")
        assert log_path.endswith("usage-2026-05-28.csv")

        with open(log_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert reader.fieldnames == USAGE_COLUMNS
        assert rows[0]["user_name"] == "minji kim"
        assert rows[0]["client_ip"] == "127.0.0.1"

    def test_read_usage_events_returns_recent_rows(self, tmp_path):
        write_usage_event("A", "preview", "success", log_dir=str(tmp_path), target_date="2026-05-27")
        write_usage_event("B", "send", "success", log_dir=str(tmp_path), target_date="2026-05-28")

        rows = read_usage_events(str(tmp_path), limit=1)

        assert len(rows) == 1
        assert rows[0]["user_name"] == "B"
        assert rows[0]["action"] == "send"
