import pytest
from config import COHORT_SENDER_MAP, resolve_cohort, validate_config


class TestValidateConfig:
    def test_raises_on_missing_notion_token(self, monkeypatch):
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        with pytest.raises(ValueError, match="NOTION_TOKEN"):
            validate_config()

    def test_raises_on_missing_ppurio_id(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "token")
        monkeypatch.delenv("PPURIO_ID", raising=False)
        with pytest.raises(ValueError, match="PPURIO_ID"):
            validate_config()

    def test_raises_on_missing_ppurio_key(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "token")
        monkeypatch.setenv("PPURIO_ID", "id")
        monkeypatch.delenv("PPURIO_KEY", raising=False)
        with pytest.raises(ValueError, match="PPURIO_KEY"):
            validate_config()

    def test_passes_when_all_keys_present(self, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "token")
        monkeypatch.setenv("PPURIO_ID", "id")
        monkeypatch.setenv("PPURIO_KEY", "key")
        validate_config()


class TestResolveCohort:
    """기수 포함(contains) 방식 매핑 검증"""

    def test_exact_match(self):
        assert resolve_cohort("33기") == "33기"

    def test_prefix_text(self):
        assert resolve_cohort("SFAC 33기") == "33기"

    def test_suffix_text(self):
        assert resolve_cohort("33기 수강생") == "33기"

    def test_embedded_text(self):
        assert resolve_cohort("플레이데이터 34기 수강생") == "34기"

    def test_unknown_cohort_returns_none(self):
        assert resolve_cohort("35기 지원자") is None

    def test_empty_string_returns_none(self):
        assert resolve_cohort("") is None

    def test_none_returns_none(self):
        assert resolve_cohort(None) is None


class TestCohortSenderMap:
    def test_known_cohort_has_sender(self):
        assert COHORT_SENDER_MAP.get("33기") == "01025327302"
        assert COHORT_SENDER_MAP.get("34기") == "01067757302"

    def test_resolved_cohort_maps_to_sender(self):
        """resolve_cohort 결과로 발신번호를 가져올 수 있는지 확인"""
        rc = resolve_cohort("SFAC 33기")
        assert COHORT_SENDER_MAP.get(rc) == "01025327302"

    def test_unknown_cohort_returns_none(self):
        assert COHORT_SENDER_MAP.get("99기") is None
