from datetime import datetime

import pytest

from custom_components.vab.coordinator import _apply_filters, _parse_efa


def _efa_dep(line="10", direction="Schweinheim", minutes=5, delay=0, monitored=True, cancelled=False):
    now = datetime.now()
    effective_dt = {
        "year": str(now.year), "month": str(now.month), "day": str(now.day),
        "hour": str((now.hour + (now.minute + minutes) // 60) % 24),
        "minute": str((now.minute + minutes) % 60),
    }
    return {
        "realtimeTripStatus": "MONITORED" if monitored else "PLANNED",
        "attrs": [{"name": "cancelled", "value": "true"}] if cancelled else [],
        "dateTime": effective_dt,
        "realDateTime": effective_dt if monitored else {},
        "servingLine": {
            "number": line,
            "direction": direction,
            "delay": str(delay) if delay else None,
        },
        "platformName": "A",
    }


class TestApplyFilters:
    def _dep(self, line, direction):
        return {"line": line, "direction": direction}

    def test_no_filters_returns_all(self):
        deps = [self._dep("4", "Schweinheim"), self._dep("10", "Hbf")]
        assert _apply_filters(deps, [], []) == deps

    def test_line_filter_exact(self):
        deps = [self._dep("4", "Schweinheim"), self._dep("10", "Hbf")]
        assert _apply_filters(deps, ["4"], []) == [self._dep("4", "Schweinheim")]

    def test_direction_filter_substring(self):
        deps = [self._dep("4", "Aschaffenburg Hauptbahnhof"), self._dep("10", "Schweinheim")]
        result = _apply_filters(deps, [], ["Hauptbahnhof"])
        assert result == [self._dep("4", "Aschaffenburg Hauptbahnhof")]

    def test_direction_filter_case_insensitive(self):
        deps = [self._dep("4", "Hauptbahnhof")]
        assert _apply_filters(deps, [], ["hauptbahnhof"]) == deps

    def test_both_filters_combined(self):
        deps = [
            self._dep("4", "Schweinheim"),
            self._dep("10", "Schweinheim"),
            self._dep("4", "Hbf"),
        ]
        result = _apply_filters(deps, ["4"], ["Schweinheim"])
        assert result == [self._dep("4", "Schweinheim")]


class TestParseEfa:
    def test_basic_departure_parsed(self):
        raw = [_efa_dep(line="10", direction="Schweinheim", minutes=5)]
        result = _parse_efa(raw)
        assert len(result) == 1
        assert result[0]["line"] == "10"
        assert result[0]["direction"] == "Schweinheim"
        assert result[0]["monitored"] is True

    def test_cancelled_departure_skipped(self):
        raw = [_efa_dep(cancelled=True), _efa_dep(line="4", minutes=3)]
        result = _parse_efa(raw)
        assert len(result) == 1
        assert result[0]["line"] == "4"

    def test_sorted_by_minutes_until(self):
        raw = [_efa_dep(line="10", minutes=10), _efa_dep(line="4", minutes=3)]
        result = _parse_efa(raw)
        assert result[0]["line"] == "4"
        assert result[1]["line"] == "10"

    def test_direction_normalized(self):
        raw = [_efa_dep(direction="Aschaffenburg ; Schweinheim")]
        result = _parse_efa(raw)
        assert result[0]["direction"] == "Schweinheim"
