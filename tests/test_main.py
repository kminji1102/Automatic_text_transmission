import pytest

from main import parse_selection_indices, prompt_recipients


class TestParseSelectionIndices:
    def test_empty_returns_all(self):
        assert parse_selection_indices("", 4) == [1, 2, 3, 4]

    def test_whitespace_returns_all(self):
        assert parse_selection_indices("   ", 3) == [1, 2, 3]

    def test_comma_separated(self):
        assert parse_selection_indices("1,3", 4) == [1, 3]

    def test_space_separated(self):
        assert parse_selection_indices("2 4", 4) == [2, 4]

    def test_dedup(self):
        assert parse_selection_indices("1,1", 4) == [1]

    def test_sorted_output(self):
        assert parse_selection_indices("3,1", 4) == [1, 3]

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            parse_selection_indices("5", 4)

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            parse_selection_indices("0", 4)

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            parse_selection_indices("a", 4)


class TestPromptRecipients:
    def _candidates(self):
        return [
            {"name": "A", "phone": "01000000001"},
            {"name": "B", "phone": "01000000002"},
            {"name": "C", "phone": "01000000003"},
        ]

    def test_cancel_with_n(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda prompt="": "N")
        assert prompt_recipients(self._candidates()) is None

    def test_select_then_confirm_yes(self, monkeypatch):
        answers = iter(["1,3", "Y"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
        result = prompt_recipients(self._candidates())
        assert [c["name"] for c in result] == ["A", "C"]

    def test_select_then_confirm_no(self, monkeypatch):
        answers = iter(["2", "N"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
        assert prompt_recipients(self._candidates()) is None

    def test_invalid_then_valid(self, monkeypatch):
        answers = iter(["9", "2", "Y"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
        result = prompt_recipients(self._candidates())
        assert [c["name"] for c in result] == ["B"]

    def test_eof_returns_none(self, monkeypatch):
        def raise_eof(prompt=""):
            raise EOFError()
        monkeypatch.setattr("builtins.input", raise_eof)
        assert prompt_recipients(self._candidates()) is None

    def test_empty_then_yes_returns_all(self, monkeypatch):
        answers = iter(["", "Y"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
        result = prompt_recipients(self._candidates())
        assert [c["name"] for c in result] == ["A", "B", "C"]

    def test_eof_on_confirm_returns_none(self, monkeypatch):
        calls = iter(["1"])

        def fake_input(prompt=""):
            try:
                return next(calls)
            except StopIteration:
                raise EOFError()

        monkeypatch.setattr("builtins.input", fake_input)
        assert prompt_recipients(self._candidates()) is None
