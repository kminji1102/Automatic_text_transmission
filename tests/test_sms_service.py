import main
import sms_service
from config import COHORT_SENDER_MAP


class TestSmsService:
    def test_send_selected_phones_sends_only_checked_candidates(self, monkeypatch):
        cohort = next(iter(COHORT_SENDER_MAP))
        sender = COHORT_SENDER_MAP[cohort]
        candidates = [
            {"name": "A", "phone": "01000000001", "cohort": cohort, "resolved_cohort": cohort},
            {"name": "B", "phone": "01000000002", "cohort": cohort, "resolved_cohort": cohort},
        ]
        sent = []
        written = {}

        monkeypatch.setattr(sms_service, "validate_config", lambda: None)
        monkeypatch.setattr(sms_service, "fetch_today_interviewees", lambda: candidates)
        monkeypatch.setattr(main, "is_already_sent_today", lambda phone, log_dir: False)

        def fake_send_lms(phone, sender_number, message):
            sent.append((phone, sender_number))
            return {"result": "sent"}

        def fake_write_results(rows, log_dir):
            written["rows"] = rows
            written["log_dir"] = log_dir
            return "logs/2026-05-28.csv"

        monkeypatch.setattr(sms_service, "send_lms", fake_send_lms)
        monkeypatch.setattr(sms_service, "write_results", fake_write_results)

        result = sms_service.send_selected_phones(["01000000002"])

        assert sent == [("01000000002", sender)]
        assert result["requested_count"] == 1
        assert result["sent_count"] == 1
        assert result["skipped_count"] == 1
        assert written["rows"][0]["name"] == "B"

    def test_build_preview_returns_sendable_candidates(self, monkeypatch):
        cohort = next(iter(COHORT_SENDER_MAP))
        candidates = [
            {"name": "A", "phone": "01000000001", "cohort": cohort, "resolved_cohort": cohort},
        ]

        monkeypatch.setattr(sms_service, "validate_config", lambda: None)
        monkeypatch.setattr(sms_service, "fetch_today_interviewees", lambda: candidates)
        monkeypatch.setattr(main, "is_already_sent_today", lambda phone, log_dir: False)

        preview = sms_service.build_preview()

        assert preview["send_candidates"] == candidates
        assert preview["prechecked_results"] == []

    def test_send_selected_phones_uses_custom_message(self, monkeypatch):
        cohort = next(iter(COHORT_SENDER_MAP))
        candidates = [
            {"name": "A", "phone": "01000000001", "cohort": cohort, "resolved_cohort": cohort},
        ]
        sent_messages = []

        monkeypatch.setattr(sms_service, "validate_config", lambda: None)
        monkeypatch.setattr(sms_service, "fetch_today_interviewees", lambda: candidates)
        monkeypatch.setattr(main, "is_already_sent_today", lambda phone, log_dir: False)
        monkeypatch.setattr(sms_service, "write_results", lambda rows, log_dir: "logs/2026-05-28.csv")

        def fake_send_lms(phone, sender_number, message):
            sent_messages.append(message)
            return {"result": "성공"}

        monkeypatch.setattr(sms_service, "send_lms", fake_send_lms)

        result = sms_service.send_selected_phones(["01000000001"], "수정한 문자입니다.")

        assert sent_messages == ["수정한 문자입니다."]
        assert result["message"] == "수정한 문자입니다."

    def test_send_selected_phones_rejects_empty_message(self):
        try:
            sms_service.send_selected_phones(["01000000001"], "   ")
        except sms_service.ServiceError as exc:
            assert "문자 내용을 입력" in str(exc)
        else:
            raise AssertionError("ServiceError was not raised")
