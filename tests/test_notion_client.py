from unittest.mock import MagicMock, patch

import config
from notion_client import (
    build_today_filter,
    fetch_today_interviewees,
    normalize_phone,
)


class TestNormalizePhone:
    def test_hyphen_format(self):
        assert normalize_phone("010-1234-5678") == "01012345678"

    def test_no_hyphen(self):
        assert normalize_phone("01012345678") == "01012345678"

    def test_space_format(self):
        assert normalize_phone("010 1234 5678") == "01012345678"

    def test_plus82_format(self):
        assert normalize_phone("+82-10-1234-5678") == "01012345678"

    def test_invalid_local_number(self):
        assert normalize_phone("031-123-4567") is None

    def test_short_number(self):
        assert normalize_phone("0101234567") is None

    def test_empty_string(self):
        assert normalize_phone("") is None

    def test_none_input(self):
        assert normalize_phone(None) is None


class TestBuildTodayFilter:
    def test_builds_kst_day_range_filter(self):
        payload = build_today_filter("인터뷰일시")
        date_filter = payload["filter"]["and"]

        assert date_filter[0]["property"] == "인터뷰일시"
        assert "on_or_after" in date_filter[0]["date"]
        assert date_filter[0]["date"]["on_or_after"].endswith(".000Z")
        assert date_filter[1]["property"] == "인터뷰일시"
        assert "before" in date_filter[1]["date"]
        assert date_filter[1]["date"]["before"].endswith(".000Z")


class TestFetchTodayInterviewees:
    def test_fetches_normalizes_resolves_and_dedups_rows(self, monkeypatch):
        monkeypatch.setattr(config, "NOTION_TOKEN", "secret-token")
        page = {
            "properties": {
                config.NOTION_FIELD_NAME: {
                    "title": [{"plain_text": "홍길동"}],
                },
                config.NOTION_FIELD_PHONE: {
                    "phone_number": "010-1234-5678",
                },
                config.NOTION_FIELD_COHORT: {
                    "select": {"name": "SFAC 33기"},
                },
            }
        }
        duplicate_page = {
            "properties": {
                config.NOTION_FIELD_NAME: {
                    "title": [{"plain_text": "홍길동2"}],
                },
                config.NOTION_FIELD_PHONE: {
                    "rich_text": [{"plain_text": "010 1234 5678"}],
                },
                config.NOTION_FIELD_COHORT: {
                    "rich_text": [{"plain_text": "SFAC 33기"}],
                },
            }
        }
        response = MagicMock()
        response.json.return_value = {"results": [page, duplicate_page], "has_more": False}

        with patch("notion_client.requests.post", return_value=response) as mock_post:
            result = fetch_today_interviewees()

        response.raise_for_status.assert_called_once()
        assert result == [
            {
                "name": "홍길동",
                "phone": "01012345678",
                "cohort": "SFAC 33기",
                "resolved_cohort": "33기",
            }
        ]
        request_kwargs = mock_post.call_args.kwargs
        assert request_kwargs["timeout"] == 30
        assert request_kwargs["json"] == build_today_filter(config.NOTION_FIELD_DATE)
        assert request_kwargs["headers"]["Authorization"] == "Bearer secret-token"
