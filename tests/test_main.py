import pytest

from main import parse_selection_indices


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
