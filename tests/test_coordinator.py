from datetime import datetime, timedelta, timezone

import pytest

from custom_components.vab.coordinator import _apply_filters, _parse_efa


def _efa_dep(line="10", direction="Schweinheim", minutes=5, delay=0, monitored=True, cancelled=False):
    """Build an EFA rapidJSON stopEvent (times in UTC, like the live API)."""
    planned = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    estimated = planned + timedelta(minutes=delay)
    dep = {
        "realtimeStatus": ["MONITORED"] if monitored else [],
        "location": {"properties": {"platform": "A"}},
        "departureTimePlanned": planned.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "transportation": {"number": line, "destination": {"name": direction}},
    }
    if monitored:
        dep["departureTimeEstimated"] = estimated.strftime("%Y-%m-%dT%H:%M:%SZ")
    if cancelled:
        dep["isCancelled"] = True
    return dep


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

    def test_delay_computed_from_estimated(self):
        result = _parse_efa([_efa_dep(minutes=5, delay=3)])
        assert result[0]["delay_minutes"] == 3
        assert result[0]["platform"] == "A"

    def test_cancelled_via_realtime_status_skipped(self):
        dep = _efa_dep()
        dep["realtimeStatus"] = ["TRIP_CANCELLED"]
        assert _parse_efa([dep]) == []

    def test_times_are_naive_local(self):
        result = _parse_efa([_efa_dep(minutes=5)])
        planned = datetime.fromisoformat(result[0]["planned"])
        assert planned.tzinfo is None
        assert 3 <= result[0]["minutes_until"] <= 5
