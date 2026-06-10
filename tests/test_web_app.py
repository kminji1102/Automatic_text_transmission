from config import SMS_MESSAGE
from web_app import InterviewSmsHandler, _normalize_message, _render_result_row


def _handler() -> InterviewSmsHandler:
    return object.__new__(InterviewSmsHandler)


class TestWebAppRendering:
    def test_page_links_frontend_assets(self):
        page = _handler()._render_page("테스트", "<p>본문</p>", "minji")

        assert '<link rel="stylesheet" href="/static/app.css">' in page
        assert '<script src="/static/app.js" defer></script>' in page
        assert "minji" in page

    def test_preview_contains_selection_controls_and_confirmation(self):
        preview = {
            "candidates": [
                {"name": "A", "phone": "01000000001", "cohort": "33기", "resolved_cohort": "33기"},
            ],
            "send_candidates": [
                {"name": "A", "phone": "01000000001", "cohort": "33기", "resolved_cohort": "33기"},
            ],
            "prechecked_results": [],
        }

        page = _handler()._render_preview("minji", preview)

        assert 'data-send-form' in page
        assert 'data-recipient-search' in page
        assert 'data-select-all' in page
        assert 'data-clear-selection' in page
        assert 'data-confirm-dialog' in page
        assert 'name="message"' in page
        assert 'data-message-editor' in page
        assert SMS_MESSAGE.splitlines()[0] in page

    def test_result_row_renders_status_badge(self):
        row = _render_result_row({"name": "A", "phone": "01000000001", "result": "성공", "error_msg": ""})

        assert "status-badge success" in row
        assert "성공" in row

    def test_normalize_message_trims_and_normalizes_newlines(self):
        assert _normalize_message("  안녕\r\n하세요  ") == "안녕\n하세요"
