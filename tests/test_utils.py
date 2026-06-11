import pytest
from custom_components.vab.utils import normalize_direction, sort_lines


class TestNormalizeDirection:
    def test_strips_city_prefix_comma(self):
        assert normalize_direction("Aschaffenburg, Hauptbahnhof") == "Hauptbahnhof"

    def test_strips_city_prefix_semicolon(self):
        assert normalize_direction("Aschaffenburg; HBF/ROB") == "HBF/ROB"

    def test_strips_city_prefix_space_semicolon(self):
        assert normalize_direction("Aschaffenburg ; HBF/ROB") == "HBF/ROB"

    def test_normalizes_spaces_around_slash(self):
        assert normalize_direction("HBF / ROB") == "HBF/ROB"

    def test_normalizes_spaces_around_semicolon(self):
        assert normalize_direction("Hbf;Schweinheim") == "Hbf; Schweinheim"

    def test_no_change_already_normalized(self):
        assert normalize_direction("Schweinheim") == "Schweinheim"

    def test_combined(self):
        assert normalize_direction("Aschaffenburg ; HBF / ROB") == "HBF/ROB"


class TestSortLines:
    def test_numeric_before_alpha(self):
        result = sort_lines(["S1", "10", "4", "RE"])
        assert result == ["4", "10", "RE", "S1"]

    def test_numeric_sorted_numerically(self):
        assert sort_lines(["10", "4", "62", "3"]) == ["3", "4", "10", "62"]

    def test_alpha_sorted_lexicographically(self):
        result = sort_lines(["RE", "IC", "S1"])
        assert result == ["IC", "RE", "S1"]

    def test_empty_list(self):
        assert sort_lines([]) == []

    def test_single_item(self):
        assert sort_lines(["4"]) == ["4"]
