from unittest.mock import MagicMock, patch

from ppurio_client import PPURIO_API_URL, send_lms


class TestSendLms:
    def test_keeps_ppurio_api_url_placeholder(self):
        assert PPURIO_API_URL == "[뿌리오 API 엔드포인트 확인 후 기입]"

    def test_returns_mapping_missing_when_no_sender_without_api_call(self):
        with patch("ppurio_client.requests.post") as mock_post:
            result = send_lms(phone="01012345678", sender=None, message="테스트")

        assert result == {"result": "매핑없음"}
        mock_post.assert_not_called()

    def test_returns_failure_on_api_error(self):
        with patch("ppurio_client.requests.post") as mock_post:
            mock_post.side_effect = Exception("Connection error")
            result = send_lms(
                phone="01012345678", sender="01025327302", message="테스트"
            )

        assert result["result"] == "실패"
        assert "Connection error" in result["error_msg"]

    def test_sends_lms_request_body_with_timeout(self):
        response = MagicMock()
        response.json.return_value = {"result": "success"}
        with patch("ppurio_client.requests.post", return_value=response) as mock_post:
            result = send_lms(
                phone="010-1234-5678",
                sender="010-2532-7302",
                message="안녕하세요. SK네트웍스 Family AI 캠프입니다.",
            )

        response.raise_for_status.assert_called_once()
        assert result["result"] == "성공"
        assert mock_post.call_args.kwargs["timeout"] == 30
        assert mock_post.call_args.kwargs["json"] == {
            "type": "lms",
            "from": "01025327302",
            "to": "01012345678",
            "content": "안녕하세요. SK네트웍스 Family AI 캠프입니다.",
        }
