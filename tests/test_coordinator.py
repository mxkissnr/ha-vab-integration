from datetime import datetime
from unittest.mock import patch

import pytest

from custom_components.vab.coordinator import _apply_filters, _parse_db, _parse_efa


# ──────────────────────────────────────────────────────────────────────────────
#  Fixtures
# ──────────────────────────────────────────────────────────────────────────────

def _efa_dep(line="10", direction="Schweinheim", minutes=5, delay=0, monitored=True, cancelled=False):
    now = datetime.now()
    effective = datetime(now.year, now.month, now.day, now.hour, now.minute) if minutes == 0 else now
    # Build a minimal EFA departure dict
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


def _db_dep(line="RE 58", direction="Frankfurt", minutes=10, delay=0):
    now = datetime.now()
    from datetime import timedelta
    sched = (now + timedelta(minutes=minutes - delay)).isoformat()
    real = (now + timedelta(minutes=minutes)).isoformat()
    return {
        "train": {"number": line},
        "destination": direction,
        "departure": {"scheduledTime": sched, "time": real},
    }


# ──────────────────────────────────────────────────────────────────────────────
#  _apply_filters
# ──────────────────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────────────────
#  _parse_efa
# ──────────────────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────────────────
#  _parse_db
# ──────────────────────────────────────────────────────────────────────────────

class TestParseDb:
    def test_basic_departure_parsed(self):
        raw = [_db_dep(line="RE 58", direction="Frankfurt", minutes=10)]
        result = _parse_db(raw)
        assert len(result) == 1
        assert result[0]["line"] == "RE 58"
        assert result[0]["direction"] == "Frankfurt"

    def test_delay_calculated(self):
        raw = [_db_dep(minutes=10, delay=2)]
        result = _parse_db(raw)
        assert result[0]["delay_minutes"] == 2

    def test_sorted_by_minutes_until(self):
        raw = [_db_dep(line="ICE 28", minutes=20), _db_dep(line="RE 58", minutes=5)]
        result = _parse_db(raw)
        assert result[0]["line"] == "RE 58"
