from unittest.mock import MagicMock, patch

import requests

from ppurio_client import PPURIO_SEND_URL, PPURIO_TOKEN_URL, send_lms


class TestSendLms:
    def test_uses_official_ppurio_endpoints(self):
        assert PPURIO_TOKEN_URL == "https://message.ppurio.com/v1/token"
        assert PPURIO_SEND_URL == "https://message.ppurio.com/v1/message"

    def test_returns_mapping_missing_when_no_sender_without_api_call(self):
        with patch("ppurio_client.requests.post") as mock_post:
            result = send_lms(phone="01012345678", sender=None, message="테스트")

        assert result == {"result": "매핑없음"}
        mock_post.assert_not_called()

    def test_returns_timeout_failure_on_requests_timeout(self):
        with patch("ppurio_client.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout()
            result = send_lms(
                phone="01012345678", sender="01025327302", message="테스트"
            )

        assert result["result"] == "실패(타임아웃)"

    def test_returns_failure_on_api_error(self):
        with patch("ppurio_client.requests.post") as mock_post:
            mock_post.side_effect = Exception("Connection error")
            result = send_lms(
                phone="01012345678", sender="01025327302", message="테스트"
            )

        assert result["result"] == "실패"
        assert "Connection error" in result["error_msg"]

    def test_issues_token_then_sends_with_bearer(self):
        token_response = MagicMock()
        token_response.json.return_value = {"token": "access-token-123"}
        send_response = MagicMock()
        send_response.json.return_value = {"result": "success"}
        with (
            patch("ppurio_client.PPURIO_ID", "account-id"),
            patch("ppurio_client.PPURIO_KEY", "api-key"),
            patch("ppurio_client.uuid.uuid4") as mock_uuid4,
            patch(
                "ppurio_client.requests.post",
                side_effect=[token_response, send_response],
            ) as mock_post,
        ):
            mock_uuid4.return_value.hex = "ref-key-123"
            result = send_lms(
                phone="010-1234-5678",
                sender="010-2532-7302",
                message="안녕하세요. SK네트웍스 Family AI 캠프입니다.",
            )

        assert result["result"] == "성공"
        assert mock_post.call_count == 2

        token_call = mock_post.call_args_list[0]
        assert token_call.args[0] == PPURIO_TOKEN_URL
        assert token_call.kwargs["headers"]["Authorization"].startswith("Basic ")
        assert token_call.kwargs["headers"]["Content-Type"] == "application/json"
        assert token_call.kwargs["json"] == {}
        assert token_call.kwargs["timeout"] == 30

        send_call = mock_post.call_args_list[1]
        assert send_call.args[0] == PPURIO_SEND_URL
        assert send_call.kwargs["headers"]["Authorization"] == "Bearer access-token-123"
        assert send_call.kwargs["headers"]["Content-Type"] == "application/json"
        assert send_call.kwargs["timeout"] == 30
        assert send_call.kwargs["json"] == {
            "account": "account-id",
            "messageType": "LMS",
            "from": "01025327302",
            "content": "안녕하세요. SK네트웍스 Family AI 캠프입니다.",
            "duplicateFlag": "N",
            "refKey": "ref-key-123",
            "targetCount": 1,
            "targets": [
                {
                    "to": "01012345678",
                }
            ],
        }
